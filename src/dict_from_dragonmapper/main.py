from argparse import ArgumentParser, Namespace
from collections import OrderedDict
from functools import partial
from logging import getLogger
from multiprocessing.pool import Pool
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
                                                    parse_existing_file,
                                                    parse_non_empty_or_whitespace, parse_path,
                                                    parse_positive_float)
from dict_from_dragonmapper.ipa2symb import parse_ipa_to_symbols
from dict_from_dragonmapper.ipa_symbols import SCHWAS, TONES, VOWELS


def get_app_try_add_vocabulary_from_pronunciations_parser(parser: ArgumentParser):
  parser.description = "Transcribe vocabulary using dragonmapper."
  # TODO support multiple files
  parser.add_argument("vocabulary", metavar='VOCABULARY', type=parse_existing_file,
                      help="file containing the vocabulary (words separated by line)")
  add_encoding_argument(parser, "--vocabulary-encoding", "encoding of vocabulary")
  parser.add_argument("dictionary", metavar='DICTIONARY', type=parse_path,
                      help="path to output created dictionary")
  parser.add_argument("--weight", type=parse_positive_float,
                      help="weight to assign for each pronunciation", default=1.0)
  parser.add_argument("--trim", type=parse_non_empty_or_whitespace, metavar='SYMBOL', nargs='*',
                      help="trim these symbols from the start and end of a word before lookup", action=ConvertToOrderedSetAction, default=DEFAULT_PUNCTUATION)
  parser.add_argument("--split-on-hyphen", action="store_true",
                      help="split words on hyphen symbol before lookup")
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

  dictionary_instance = get_pronunciations(
    vocabulary_words, ns.weight, options, ns.n_jobs, ns.maxtasksperchild, ns.chunksize)

  s_options = SerializationOptions(ns.parts_sep, ns.include_numbers, ns.include_weights)

  try:
    save_dict(dictionary_instance, ns.dictionary, ns.serialization_encoding, s_options)
  except Exception as ex:
    logger.error("Dictionary couldn't be written.")
    logger.debug(ex)
    return False

  logger.info(f"Written dictionary to: \"{ns.dictionary.absolute()}\".")

  return True


def get_pronunciations(vocabulary: OrderedSet[Word], weight: float, options: Options, n_jobs: int, maxtasksperchild: Optional[int], chunksize: int) -> PronunciationDict:
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


def get_dictionary(pronunciations_to_i: Dict[int, Pronunciations], vocabulary: OrderedSet[Word]) -> PronunciationDict:
  resulting_dict = OrderedDict()

  for i, word in enumerate(vocabulary):
    pronunciations = pronunciations_to_i[i]
    assert len(pronunciations) == 1
    assert word not in resulting_dict
    resulting_dict[word] = pronunciations

  return resulting_dict


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
  result = OrderedDict((
    (result, weight),
  ))
  return result


def get_chn_ipa(word_str: str) -> Tuple[str, ...]:
  # e.g. -> 北风 = peɪ˧˩˧ fɤ˥ŋ
  assert isinstance(word_str, str)
  assert len(word_str) > 0

  syllable_split_symbol = " "
  hanzi_ipa = hanzi.to_ipa(word_str, delimiter=syllable_split_symbol, all_readings=False)
  hanzi_syllables_ipa = hanzi_ipa.split(syllable_split_symbol)
  word_ipa_symbols = []
  for hanzi_syllable_ipa in hanzi_syllables_ipa:
    syllable_ipa, tone_ipa = split_into_ipa_and_tones(hanzi_syllable_ipa)
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
        syllable_ipa_symbols_with_tones = [symbol for symbol in syllable_ipa_symbols]
        for i in range(len(syllable_ipa_symbols)):
          current_symbol = syllable_ipa_symbols[-i - 1]
          if is_vowel(current_symbol):
            syllable_ipa_symbols_with_tones[-i - 1] += tone_ipa
            break
        syllable_ipa_symbols_with_tones = tuple(syllable_ipa_symbols_with_tones)
    word_ipa_symbols.extend(syllable_ipa_symbols_with_tones)
  symbols = tuple(word_ipa_symbols)
  return symbols


def split_into_ipa_and_tones(word: str) -> Tuple[str, str]:
  word_ipa = ""
  word_tones = ""
  for character in word:
    if character in TONES:
      word_tones += character
    else:
      word_ipa += character
  return word_ipa, word_tones


def is_vowel(symbol: str) -> bool:
  vowels = VOWELS | SCHWAS
  result = all(sub_symbol in vowels for sub_symbol in tuple(symbol))
  return result


def get_vowel_count(symbols: Tuple[str, ...]) -> int:
  result = sum(1 if is_vowel(symbol) else 0 for symbol in symbols)
  return result
