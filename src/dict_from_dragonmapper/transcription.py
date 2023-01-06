import itertools
from logging import getLogger
from typing import Tuple

from dragonmapper import hanzi
from ordered_set import OrderedSet

from dict_from_dragonmapper.ipa2symb import merge_fusion_with_ignore, parse_ipa_to_symbols
from dict_from_dragonmapper.ipa_symbols import SCHWAS, TONES, VOWELS

# probably does not cover all
EXCEPTIONS_WHERE_PINYIN_AND_IPA_IS_EQUAL = {
  'li', 'fu', 'lu', 'a',
  'mu', 'wa', 'la', 'fa',
  'su', 'ma', 'wan', 'san',
  'na', 'nan', 'fan',  # hng? ng?
}

# retrieved from https://www.pin1yin1.com/
# for these mappings `hanzi.to_pinyin()` returns wrong pinyin
CHN_PINYIN_MAPPING = {
  "嗯": "ēn",  # ń/ň/ǹ/nǵ/nǧ/ng̀/ńg/ňg/ǹg
  "呐": "nà",  # na
  "哪": "nǎ",  # na
  "哼": "hēng",  # hng
  "哽": "gěng",  # ńg
  "烦": "fán",  # fan
  "难": "nán",  # nan
}
# '[ne/nà/nè/na/nuò][nǎ/na/nuó/nǎi/nà/niè/né][hēng/hng][gěng/yǐng/yìng/ńg/ń][fán/fan][nán/nan/nàn]'


def word_to_ipa(word: str) -> OrderedSet[Tuple[str, ...]]:
  # e.g. -> 北风 => p eɪ˧˩˧ f ɤ˥ ŋ
  assert isinstance(word, str)
  assert len(word) > 0

  syllables_IPAs = []
  for syllable in word:
    try:
      syllable_IPAs = syllable_to_ipa(syllable)
    except ValueError as error:
      raise ValueError(f"Syllable \"{syllable}\" couldn't be transcribed!") from error
    syllables_IPAs.append(syllable_IPAs)

  all_syllable_combinations = OrderedSet(
    tuple(itertools.chain.from_iterable(combination))
    for combination in itertools.product(*syllables_IPAs)
  )

  return all_syllable_combinations


def attach_tones_to_last_vowel(syllable_ipa: str) -> Tuple[str, ...]:
  ipa_tones = separate_syllable_ipa_into_phonemes_and_tones(syllable_ipa)
  syllable_phonemes, tone_ipa = ipa_tones
  assert syllable_ipa.endswith(tone_ipa)

  syllable_ipa_symbols = parse_ipa_to_symbols(syllable_phonemes)
  syllable_vowel_count = get_vowel_count(syllable_ipa_symbols)
  assert tone_ipa == "" or syllable_vowel_count >= 1
  if syllable_vowel_count == 0:
    assert syllable_ipa == "ɻ"

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
  return syllable_ipa_symbols_with_tones


def merge_affricatives(syllable_ipa: Tuple[str, ...]) -> Tuple[str, ...]:
  result = merge_fusion_with_ignore(
    symbols=syllable_ipa,
    fusion_symbols={"ʈ", "ʂ", "t", "s", "ɕ"},
    ignore={"ʰ"}
  )
  return result


def merge_diphthongs(syllable_ipa: Tuple[str, ...]) -> Tuple[str, ...]:
  result = merge_fusion_with_ignore(
    symbols=syllable_ipa,
    fusion_symbols=VOWELS - {"y"},
    ignore={"˧", "˩", "˥"}
  )
  return result


def pinyin_to_ipa(syllable_pinyin: str) -> Tuple[str, ...]:
  # some pinyin will result in invalid IPA in the next step which is why it will be considered before for known errors
  # DEBUG    dict_from_dragonmapper.transcription:transcription.py:175 Pinyin 'ň' from syllable '嗯' couldn't be transcribed to IPA!
  # DEBUG    dict_from_dragonmapper.transcription:transcription.py:175 Pinyin 'ǹ' from syllable '嗯' couldn't be transcribed to IPA!
  # DEBUG    dict_from_dragonmapper.transcription:transcription.py:175 Pinyin 'nǵ' from syllable '嗯' couldn't be transcribed to IPA!
  # DEBUG    dict_from_dragonmapper.transcription:transcription.py:175 Pinyin 'nǧ' from syllable '嗯' couldn't be transcribed to IPA!
  # DEBUG    dict_from_dragonmapper.transcription:transcription.py:175 Pinyin 'ng̀' from syllable '嗯' couldn't be transcribed to IPA!
  # DEBUG    dict_from_dragonmapper.transcription:transcription.py:175 Pinyin 'ňg' from syllable '嗯' couldn't be transcribed to IPA!
  # DEBUG    dict_from_dragonmapper.transcription:transcription.py:175 Pinyin 'ǹg' from syllable '嗯' couldn't be transcribed to IPA!
  # if syllable_pinyin == "ń":
  #   return ("n",)
  # if syllable_pinyin == "ńg":
  #   return ("ŋ",)
  # if syllable_pinyin == "hng":
  #   return ("x", "ŋ")

  try:
    syllable_ipa = hanzi.pinyin_to_ipa(syllable_pinyin)
  except ValueError as ex:
    #print("Error in retrieving IPA from pinyin!", pinyin_str, ex.args[0])
    raise ValueError(f"IPA couldn't be retrieved from Pinyin (\"{syllable_pinyin}\")!") from ex

  # some pinyin will result in invalid IPA:
  # therefore filtering:
  no_ipa_to_pinyin_found = syllable_pinyin == syllable_ipa and syllable_pinyin not in EXCEPTIONS_WHERE_PINYIN_AND_IPA_IS_EQUAL
  if no_ipa_to_pinyin_found:
    raise ValueError(f"IPA couldn't be retrieved from Pinyin (\"{syllable_pinyin}\")!")

  # 晒 returns "ʂai˥˩" which is incorrect
  if "ai" in syllable_ipa:
    logger = getLogger(__name__)
    logger.debug(f"fix: replaced wrong 'ai' to 'aɪ' in '{syllable_ipa}'")
    syllable_ipa = syllable_ipa.replace("ai", "aɪ")

  syllable_ipa = attach_tones_to_last_vowel(syllable_ipa)
  syllable_ipa = merge_affricatives(syllable_ipa)
  syllable_ipa = merge_diphthongs(syllable_ipa)

  return syllable_ipa


# def get_syllable_ipa(syllable: str) -> Tuple[str, ...]:
#   assert isinstance(syllable, str)
#   assert len(syllable) == 1

#   syllable_pinyin = hanzi.to_pinyin(syllable, delimiter=None, all_readings=False)
#   no_pinyin_found = syllable_pinyin == syllable

#   if no_pinyin_found:
#     # print(word_str, "No pinyin!")
#     raise ValueError("Pinyin couldn't be retrieved from syllable!")

#   return pinyin_to_ipa(syllable_pinyin)


def syllable_to_pinyin(syllable: str) -> OrderedSet[str]:
  assert isinstance(syllable, str)
  assert len(syllable) == 1

  # if syllable in CHN_PINYIN_MAPPING:
  #   return OrderedSet((CHN_PINYIN_MAPPING[syllable],))

  syllable_pinyin = hanzi.to_pinyin(syllable, delimiter=None, all_readings=True, container="[]")
  no_pinyin_found = syllable_pinyin == syllable
  if no_pinyin_found:
    # print(word_str, "No pinyin!")
    raise ValueError(f"Pinyin couldn't be retrieved from syllable '{syllable}'!")
  readings_without_container = syllable_pinyin[1:-1]
  readings = readings_without_container.split("/")
  result = OrderedSet(readings)
  return result


def syllable_to_ipa(syllable: str) -> OrderedSet[Tuple[str, ...]]:
  result = OrderedSet()
  error_occurred = False
  successfull_pinyin = OrderedSet()
  for pinyin in syllable_to_pinyin(syllable):
    try:
      ipa = pinyin_to_ipa(pinyin)
    except ValueError as error:
      logger = getLogger(__name__)
      logger.debug(f"Pinyin '{pinyin}' from syllable '{syllable}' couldn't be transcribed to IPA!")
      error_occurred = True
      continue
    result.add(ipa)
    successfull_pinyin.add(pinyin)
  if len(result) == 0:
    raise ValueError("Syllable could not be converted to IPA!")
  if error_occurred:
    logger = getLogger(__name__)
    logger.debug(f"Used other pinyin transcription(s): {', '.join(successfull_pinyin)}.")
  del successfull_pinyin
  del error_occurred
  return result


# def get_ipa_from_word(word_str: str) -> Tuple[str, ...]:
#   # e.g. -> 北风 => p eɪ˧˩˧ f ɤ˥ ŋ
#   assert isinstance(word_str, str)
#   assert len(word_str) > 0

#   word_ipa_symbols: List[str] = []
#   for syllable in word_str:
#     try:
#       syllable_IPAs = syllable_to_ipa(syllable)
#     except ValueError as er:
#       raise ValueError(f"Syllable \"{syllable}\" couldn't be transcribed!") from er
#     word_ipa_symbols.extend(syllable_IPAs)
#   symbols = tuple(word_ipa_symbols)
#   return symbols


def separate_syllable_ipa_into_phonemes_and_tones(syllable_ipa: str) -> Tuple[str, str]:
  syllable_phonemes = ""
  syllable_tones = ""
  for character in syllable_ipa:
    if character in TONES:
      syllable_tones += character
    else:
      # No characters after tones allowed
      assert syllable_tones == ""
      syllable_phonemes += character
  return syllable_phonemes, syllable_tones


def is_vowel(symbol: str) -> bool:
  vowels = VOWELS | SCHWAS
  result = all(sub_symbol in vowels for sub_symbol in tuple(symbol))
  return result


def get_vowel_count(symbols: Tuple[str, ...]) -> int:
  result = sum(1 if is_vowel(symbol) else 0 for symbol in symbols)
  return result
