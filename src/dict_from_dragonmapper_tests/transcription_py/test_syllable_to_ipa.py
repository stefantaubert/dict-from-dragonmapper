from pathlib import Path

from ordered_set import OrderedSet
from pytest import raises
from tqdm import tqdm

from dict_from_dragonmapper.transcription import syllable_to_ipa


def test_syllable_without_vowel():
  res = syllable_to_ipa("儿")
  assert res == OrderedSet([
    ('ɻ',),
    ('ɑ˧˥', 'ɻ'),
    ('ʐ', 'ə˧˥', 'n')
  ])


def test_晒_transcribes_ai_to_aɪ():
  res = syllable_to_ipa("晒")
  assert res == OrderedSet([("ʂ", "aɪ˥˩")])


def test_嗯__raises_no_error():
  res = syllable_to_ipa("嗯")
  assert res == OrderedSet([('n',), ('ŋ',)])


def test_晋__transcribes_normally():
  res = syllable_to_ipa("晋")
  assert res == OrderedSet([('tɕ', 'i˥˩', 'n')])


def test_吗__transcribes_normally_with_IPA_and_pinyin_equal():
  res = syllable_to_ipa("吗")
  assert res == OrderedSet([('m', 'a'), ('m', 'a˧˥')])


def test_english_alphabet_fails():
  with raises(ValueError) as error:
    syllable_to_ipa("X")
  assert error.value.args[0] == "Pinyin couldn't be retrieved from syllable 'X'!"


def test_test_vocabulary():
  voc = Path("res/test-vocabulary.txt").read_text("UTF-8")
  voc_syllables = {syllable for syllable in voc if syllable not in {"\n", "。", "？"}}
  all_transcriptions = OrderedSet()
  failed_syllables = OrderedSet()
  for syllable in tqdm(sorted(voc_syllables)):
    try:
      res = syllable_to_ipa(syllable)
    except ValueError as ex:
      failed_syllables.add(syllable)
      continue
    all_transcriptions |= res
    assert len(res) > 0

  unique_IPA_symbols = sorted({
    symbol
    for transcription in all_transcriptions
    for symbol in transcription
  })

  assert len(unique_IPA_symbols) == 111
  assert len(failed_syllables) == 0
