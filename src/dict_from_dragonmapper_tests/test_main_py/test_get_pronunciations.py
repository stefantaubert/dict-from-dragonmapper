from ordered_set import OrderedSet
from word_to_pronunciation import Options

from dict_from_dragonmapper.main import get_pronunciations


def test_component():
  vocabulary = OrderedSet((
    "社会语言学?",
    "鲜-亮.",
    "㐻,",
    "\"㑐",
  ))
  options = Options("?,\".", True, False, False, 1.0)

  result_dict = get_pronunciations(vocabulary, 1.0, options, 1, None, 4)

  assert len(result_dict) == 4
