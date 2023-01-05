from dict_from_dragonmapper.main import get_syllable_ipa


def test_晒_transcribes_ai_to_aɪ():
  res = get_syllable_ipa("晒")
  assert res == ("ʂ", "aɪ˥˩")

# def test_嗯__raises_error():
#   with raises(ValueError) as error:
#     get_syllable_ipa("嗯")
#   assert error.value.args[0] == 'IPA couldn\'t be retrieved from Pinyin ("ń")!'


def test_嗯__raises_no_error():
  res = get_syllable_ipa("嗯")
  assert res == ("n˧˥",)


def test_晋__transcribes_normally():
  res = get_syllable_ipa("晋")
  assert res == ("tɕ", "i˥˩", "n")


def test_吗__transcribes_normally_with_IPA_and_pinyin_equal():
  res = get_syllable_ipa("吗")
  assert res == ("m", "a")
