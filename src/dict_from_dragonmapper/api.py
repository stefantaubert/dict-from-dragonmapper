from typing import Tuple

from dict_from_dragonmapper.main import get_ipa_from_word


def get_ipa(word: str) -> Tuple[str, ...]:
  if not isinstance(word, str):
    raise ValueError("Parameter word: Value needs to be of type 'str'!")

  if " " in word:
    raise ValueError("Parameter word: Words containing space are not allowed!")

  if len(word) == 0:
    return tuple()

  result = get_ipa_from_word(word)
  return result
