from typing import Tuple

from ordered_set import OrderedSet

from dict_from_dragonmapper.transcription import word_to_ipa as transcription_word_to_ipa


def word_to_ipa(word: str) -> OrderedSet[Tuple[str, ...]]:
  if not isinstance(word, str):
    raise ValueError("Parameter word: Value needs to be of type 'str'!")

  if " " in word:
    raise ValueError("Parameter word: Words containing space are not allowed!")

  if len(word) == 0:
    return tuple()

  result = transcription_word_to_ipa(word)
  return result
