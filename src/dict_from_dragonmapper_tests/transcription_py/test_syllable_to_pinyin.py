from ordered_set import OrderedSet
from pytest import raises

from dict_from_dragonmapper.transcription import syllable_to_pinyin


def test_syllable_with_one_readings():
  res = syllable_to_pinyin("晒")
  assert res == OrderedSet(['shài'])


def test_syllable_with_two_readings():
  res = syllable_to_pinyin("吗")
  assert res == OrderedSet(['ma', 'má'])


def test_syllable_with_nine_readings():
  res = syllable_to_pinyin("嗯")
  assert res == OrderedSet(['ń', 'ň', 'ǹ', 'nǵ', 'nǧ', 'ng̀', 'ńg', 'ňg', 'ǹg'])


def test_english_alphabet_raises_value_error():
  with raises(ValueError) as error:
    syllable_to_pinyin("X")
  assert error.value.args[0] == "Pinyin couldn't be retrieved from syllable 'X'!"
