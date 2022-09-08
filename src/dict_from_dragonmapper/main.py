from argparse import ArgumentParser, Namespace
from collections import OrderedDict
from functools import partial
from logging import getLogger
from multiprocessing.pool import Pool
from pathlib import Path
from tempfile import gettempdir
from typing import Dict, Optional, Tuple

from dragonmapper import hanzi
from ordered_set import OrderedSet
from pronunciation_dictionary import (PronunciationDict, Pronunciations, SerializationOptions, Word,
                                      save_dict)
from tqdm import tqdm
from word_to_pronunciation import Options, get_pronunciations_from_word

from dict_from_dragonmapper.argparse_helper import (DEFAULT_PUNCTUATION, ConvertToOrderedSetAction,
                                                    add_chunksize_argument, add_encoding_argument,
                                                    add_maxtaskperchild_argument,
                                                    add_n_jobs_argument, add_serialization_group,
                                                    get_optional, parse_existing_file,
                                                    parse_non_empty_or_whitespace, parse_path,
                                                    parse_positive_float)
from dict_from_dragonmapper.ipa2symb import merge_fusion_with_ignore, parse_ipa_to_symbols
from dict_from_dragonmapper.ipa_symbols import SCHWAS, TONES, VOWELS


def get_app_try_add_vocabulary_from_pronunciations_parser(parser: ArgumentParser):
  parser.description = "Command-line interface (CLI) to create a pronunciation dictionary by looking up IPA transcriptions using dragonmapper including the possibility of ignoring punctuation and splitting words on hyphens before transcribing them."
  default_oov_out = Path(gettempdir()) / "oov.txt"
  # TODO support multiple files
  parser.add_argument("vocabulary", metavar='VOCABULARY-PATH', type=parse_existing_file,
                      help="file containing the vocabulary (words separated by line)")
  add_encoding_argument(parser, "--vocabulary-encoding", "encoding of vocabulary")
  parser.add_argument("dictionary", metavar='DICTIONARY-PATH', type=parse_path,
                      help="path to output the created dictionary")
  parser.add_argument("--weight", type=parse_positive_float, metavar="WEIGHT",
                      help="weight to assign for each pronunciation", default=1.0)
  parser.add_argument("--trim", type=parse_non_empty_or_whitespace, metavar='TRIM-SYMBOL', nargs='*',
                      help="trim these symbols from the start and end of a word before lookup", action=ConvertToOrderedSetAction, default=DEFAULT_PUNCTUATION)
  parser.add_argument("--split-on-hyphen", action="store_true",
                      help="split words on hyphen symbol before lookup")
  parser.add_argument("--oov-out", metavar="OOV-PATH", type=get_optional(parse_path),
                      help="write out-of-vocabulary (OOV) words (i.e., words that can't transcribed) to this file (encoding will be the same as the one from the vocabulary file)", default=default_oov_out)
  add_serialization_group(parser)
  mp_group = parser.add_argument_group("multiprocessing arguments")
  add_n_jobs_argument(mp_group)
  add_chunksize_argument(mp_group)
  add_maxtaskperchild_argument(mp_group)
  return get_pronunciations_files


def get_pronunciations_files(ns: Namespace) -> bool:
  assert ns.vocabulary.is_file()
  logger = getLogger(__name__)

  try:
    vocabulary_content = ns.vocabulary.read_text(ns.vocabulary_encoding)
  except Exception as ex:
    logger.error("Vocabulary couldn't be read.")
    return False

  vocabulary_words = OrderedSet(vocabulary_content.splitlines())
  trim_symbols = ''.join(ns.trim)
  options = Options(trim_symbols, ns.split_on_hyphen, False, False, 1.0)

  dictionary_instance, unresolved_words = get_pronunciations(
    vocabulary_words, ns.weight, options, ns.n_jobs, ns.maxtasksperchild, ns.chunksize)

  s_options = SerializationOptions(ns.parts_sep, ns.include_numbers, ns.include_weights)

  try:
    save_dict(dictionary_instance, ns.dictionary, ns.serialization_encoding, s_options)
  except Exception as ex:
    logger.error("Dictionary couldn't be written.")
    logger.debug(ex)
    return False

  logger.info(f"Written dictionary to: \"{ns.dictionary.absolute()}\".")

  if len(unresolved_words) > 0:
    logger.warning("Not all words were contained in the reference dictionary")
    if ns.oov_out is not None:
      unresolved_out_content = "\n".join(unresolved_words)
      ns.oov_out.parent.mkdir(parents=True, exist_ok=True)
      try:
        ns.oov_out.write_text(unresolved_out_content, "UTF-8")
      except Exception as ex:
        logger.error("Unresolved output file couldn't be created!")
        return False
      logger.info(f"Written unresolved vocabulary to: \"{ns.oov_out.absolute()}\".")
  else:
    logger.info("Complete vocabulary is contained in output!")

  return True


def get_pronunciations(vocabulary: OrderedSet[Word], weight: float, options: Options, n_jobs: int, maxtasksperchild: Optional[int], chunksize: int) -> Tuple[PronunciationDict, OrderedSet[Word]]:
  lookup_method = partial(
    process_get_pronunciation,
    weight=weight,
    options=options,
  )

  with Pool(
    processes=n_jobs,
    initializer=__init_pool_prepare_cache_mp,
    initargs=(vocabulary,),
    maxtasksperchild=maxtasksperchild,
  ) as pool:
    entries = range(len(vocabulary))
    iterator = pool.imap(lookup_method, entries, chunksize)
    pronunciations_to_i = dict(tqdm(iterator, total=len(entries), unit="words"))

  return get_dictionary(pronunciations_to_i, vocabulary)


def get_dictionary(pronunciations_to_i: Dict[int, Pronunciations], vocabulary: OrderedSet[Word]) -> Tuple[PronunciationDict, OrderedSet[Word]]:
  resulting_dict = OrderedDict()
  unresolved_words = OrderedSet()

  for i, word in enumerate(vocabulary):
    pronunciations = pronunciations_to_i[i]

    if len(pronunciations) == 0:
      unresolved_words.add(word)
      continue
    assert word not in resulting_dict
    resulting_dict[word] = pronunciations

  return resulting_dict, unresolved_words


process_unique_words: OrderedSet[Word] = None


def __init_pool_prepare_cache_mp(words: OrderedSet[Word]) -> None:
  global process_unique_words
  process_unique_words = words


def process_get_pronunciation(word_i: int, weight: float, options: Options) -> Tuple[int, Pronunciations]:
  global process_unique_words
  assert 0 <= word_i < len(process_unique_words)
  word = process_unique_words[word_i]

  # TODO support all entries; also create all combinations with hyphen then
  lookup_method = partial(
    lookup_in_model,
    weight=weight,
  )

  pronunciations = get_pronunciations_from_word(word, lookup_method, options)
  #logger = getLogger(__name__)
  # logger.debug(pronunciations)
  return word_i, pronunciations


def lookup_in_model(word: Word, weight: float) -> Pronunciations:
  assert len(word) > 0
  result = get_chn_ipa(word)
  if result is None:
    return OrderedDict()
  result = OrderedDict((
    (result, weight),
  ))
  return result


def get_chn_ipa(word_str: str) -> Optional[Tuple[str, ...]]:
  # e.g. -> 北风 => p eɪ˧˩˧ f ɤ˥ ŋ
  assert isinstance(word_str, str)
  assert len(word_str) > 0

  syllable_split_symbol = " "
  pinyin_str = hanzi.to_pinyin(word_str, delimiter=syllable_split_symbol, all_readings=False)

  no_pinyin_found = pinyin_str == word_str
  if no_pinyin_found:
    # print(word_str, "No pinyin!")
    return None
  try:
    ipa_str = hanzi.pinyin_to_ipa(pinyin_str)
  except ValueError as ex:
    #print("Error in retrieving IPA from pinyin!", pinyin_str, ex.args[0])
    return None

  # some pinyin will result in invalid IPA:
  # 嗯 returns ń
  # 嗯啦 returns ńla

  # therefore filtering:
  # probably does not contain all
  exceptions_pinyin_ipa_same = {'li', 'fu', 'lu', 'a',
                                'mu', 'wa', 'la', 'fa',
                                'su', 'ma', 'wan', 'san'}

  no_ipa_to_pinyin_found = pinyin_str == ipa_str and pinyin_str not in exceptions_pinyin_ipa_same
  if no_ipa_to_pinyin_found:
    # print(word_str, "No IPA!", pinyin_str)
    return None

  hanzi_syllables_ipa = ipa_str.split(syllable_split_symbol)
  word_ipa_symbols = []
  for hanzi_syllable_ipa in hanzi_syllables_ipa:
    ipa_tones = split_into_ipa_and_tones(hanzi_syllable_ipa)
    cannot_be_separated = ipa_tones is None
    if cannot_be_separated:
      return None

    syllable_ipa, tone_ipa = ipa_tones
    assert hanzi_syllable_ipa.endswith(tone_ipa)
    syllable_ipa_symbols = parse_ipa_to_symbols(syllable_ipa)
    syllable_vowel_count = get_vowel_count(syllable_ipa_symbols)
    assert tone_ipa == "" or syllable_vowel_count >= 1
    if syllable_vowel_count == 0:
      assert hanzi_syllable_ipa == "ɻ"

    if len(tone_ipa) == 0:
      syllable_ipa_symbols_with_tones = syllable_ipa_symbols
    else:
      if syllable_vowel_count <= 1:
        syllable_ipa_symbols_with_tones = tuple(
            symbol + tone_ipa if is_vowel(symbol) else symbol for symbol in syllable_ipa_symbols)
      else:
        syllable_ipa_symbols_with_tones = list(syllable_ipa_symbols)
        for i in range(len(syllable_ipa_symbols)):
          current_symbol = syllable_ipa_symbols[-i - 1]
          if is_vowel(current_symbol):
            syllable_ipa_symbols_with_tones[-i - 1] += tone_ipa
            break
        syllable_ipa_symbols_with_tones = tuple(syllable_ipa_symbols_with_tones)

    # Merge affricates
    syllable_ipa_symbols_with_tones = merge_fusion_with_ignore(
      symbols=syllable_ipa_symbols_with_tones,
      fusion_symbols={"ʈ", "ʂ", "t", "s", "ɕ"},
      ignore={"ʰ"}
    )

    # Merge diphthongs
    syllable_ipa_symbols_with_tones = merge_fusion_with_ignore(
      symbols=syllable_ipa_symbols_with_tones,
      fusion_symbols=VOWELS - {"y"},
      ignore={"˧", "˩", "˥"}
    )

    word_ipa_symbols.extend(syllable_ipa_symbols_with_tones)
  symbols = tuple(word_ipa_symbols)
  return symbols


def split_into_ipa_and_tones(word: str) -> Optional[Tuple[str, str]]:
  word_ipa = ""
  word_tones = ""
  for character in word:
    if character in TONES:
      word_tones += character
    else:
      if word_tones == "":
        word_ipa += character
      else:
        return None
  return word_ipa, word_tones


def is_vowel(symbol: str) -> bool:
  vowels = VOWELS | SCHWAS
  result = all(sub_symbol in vowels for sub_symbol in tuple(symbol))
  return result


def get_vowel_count(symbols: Tuple[str, ...]) -> int:
  result = sum(1 if is_vowel(symbol) else 0 for symbol in symbols)
  return result
