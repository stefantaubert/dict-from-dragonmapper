from pathlib import Path

from ordered_set import OrderedSet
from pytest import raises
from tqdm import tqdm

from dict_from_dragonmapper.transcription import pinyin_to_ipa, syllable_to_pinyin


def test_晒_transcribes_ai_to_aɪ():
  # 晒
  res = pinyin_to_ipa("shài")
  assert res == ("ʂ", "aɪ˥˩")


def test_吗__transcribes_normally_with_IPA_and_pinyin_equal():
  # 吗
  res = pinyin_to_ipa("ma")
  assert res == ("m", "a")


def test_嗯__raises_no_error():
  # 嗯
  res = pinyin_to_ipa("ēn")
  assert res == ('ə˥', 'n')


def test_晋__transcribes_normally():
  # 晋
  res = pinyin_to_ipa("jìn")
  assert res == ("tɕ", "i˥˩", "n")


def test_english_alphabet_raises_value_error():
  with raises(ValueError) as error:
    pinyin_to_ipa("X")
  assert error.value.args[0] == 'IPA couldn\'t be retrieved from Pinyin ("X")!'


def test_all_transcribed_syllables_from_test_vocabulary_contain_valid_IPA():
  voc = Path("res/test-vocabulary.txt").read_text("UTF-8")
  voc_syllables = {syllable for syllable in voc if syllable not in {"\n", "。", "？"}}
  voc_pinyins = {
    pinyin
    for syllable in voc_syllables
    for pinyin in syllable_to_pinyin(syllable)
  }

  all_transcriptions = OrderedSet()

  for syllable in tqdm(sorted(voc_pinyins)):
    res = pinyin_to_ipa(syllable)
    all_transcriptions.add(res)
    assert len(res) > 0

  unique_IPA_symbols = sorted({
    symbol
    for transcription in all_transcriptions
    for symbol in transcription
  })

  assert len(unique_IPA_symbols) == 111

def test_呐():
  res = pinyin_to_ipa("jìn")
  assert res == ("tɕ", "i˥˩", "n")


def test_most_syllables_from_test_vocabulary_could_be_transcribed():
  voc = Path("res/test-vocabulary.txt").read_text("UTF-8")
  voc_syllables = {syllable for syllable in voc if syllable not in {"\n", "。", "？"}}

  all_transcriptions = OrderedSet()
  failed_syllables = OrderedSet()

  for syllable in tqdm(sorted(voc_syllables)):
    for pinyin in syllable_to_pinyin(syllable):
      try:
        res = pinyin_to_ipa(pinyin)
      except ValueError as ex:
        failed_syllables.add((syllable, pinyin))
        continue
      all_transcriptions.add(res)

  assert len(failed_syllables) == 0
