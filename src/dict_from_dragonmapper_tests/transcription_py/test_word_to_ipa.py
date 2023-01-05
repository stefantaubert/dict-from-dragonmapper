
from ordered_set import OrderedSet

from dict_from_dragonmapper.transcription import word_to_ipa


def test_晒吗_returns_two_entries():
  res = word_to_ipa("晒吗")
  assert res == OrderedSet([
    ('ʂ', 'aɪ˥˩', 'm', 'a'),
    ('ʂ', 'aɪ˥˩', 'm', 'a˧˥')
  ])


def test_北风嗯_returns_two_entries():
  res = word_to_ipa("北风嗯")
  assert res == OrderedSet([
    ('p', 'eɪ˧˩˧', 'f', 'ɤ˥', 'ŋ', 'n'),
    ('p', 'eɪ˧˩˧', 'f', 'ɤ˥', 'ŋ', 'ŋ'),
    ('p', 'eɪ˥˩', 'f', 'ɤ˥', 'ŋ', 'n'),
    ('p', 'eɪ˥˩', 'f', 'ɤ˥', 'ŋ', 'ŋ')
  ])
