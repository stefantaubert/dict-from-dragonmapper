# from dict_from_dragonmapper.main import get_ipa_from_word, get_vowel_count


# def test_get_chn_ipa():
#   result = get_ipa_from_word("堡包")

#   assert result == ('p', 'ɑʊ˧˩˧', 'p', 'ɑʊ˥')


# def test_get_chn_ipa__syllable_without_vowel():
#   result = get_ipa_from_word("儿")

#   assert result == ('ɻ',)


# def test_get_vowel_count__two():
#   result = get_vowel_count(
#     symbols=("a", "b", "aa",),
#   )

#   assert result == 2


# def test_get_vowel_count__one_diphtong():
#   result = get_vowel_count(
#     symbols=("aa",),
#   )

#   assert result == 1


# def test_get_vowel_count__one():
#   result = get_vowel_count(
#     symbols=("a",),
#   )

#   assert result == 1


# def test_get_vowel_count__zero():
#   result = get_vowel_count(
#     symbols=(),
#   )

#   assert result == 0


# # def test_chn_to_ipa():
# #   result = chn_to_ipa(
# #     chn_sentence=tuple("石头 北 冷。"),
# #     consider_annotations=False,
# #     annotation_split_symbol=None,
# #     cache=get_empty_cache(),
# #   )

# #   assert result == ('ʂ', 'ɨ˧˥', 'tʰ', 'o','ʊ', ' ', 'p', 'e','ɪ˧˩˧', ' ', 'l', 'ɤ˧˩˧', 'ŋ', '.')


# # def test_chn_to_ipa__only_vowels():
# #   result = chn_to_ipa(
# #     chn_sentence=tuple("阿阿"),
# #     consider_annotations=False,
# #     annotation_split_symbol=None,
# #     cache=get_empty_cache(),
# #   )

# #   assert result == ('a˥', 'a˥')


# # def test_chn_to_ipa__with_multiple_same_words():
# #   result = chn_to_ipa(
# #     chn_sentence=tuple("！石 石？ 石。"),
# #     consider_annotations=False,
# #     annotation_split_symbol=None,
# #     cache=get_empty_cache(),
# #   )

# #   assert result == ('!', 'ʂ', 'ɨ˧˥', ' ', 'ʂ', 'ɨ˧˥', '?', ' ', 'ʂ', 'ɨ˧˥', '.')


# # def test_chn_to_ipa__replaces_punctuation():
# #   result = chn_to_ipa(
# #     chn_sentence=tuple("石头！ 北： 冷。 ？"),
# #     consider_annotations=False,
# #     annotation_split_symbol=None,
# #     cache=get_empty_cache(),
# #   )

# #   assert result == ('ʂ', 'ɨ˧˥', 'tʰ', 'o', 'ʊ', '!', ' ', 'p', 'e', 'ɪ˧˩˧',
# #                     ':', ' ', 'l', 'ɤ˧˩˧', 'ŋ', '.', ' ', '?')


# # def test_chn_to_ipa__sentence():
# #   result = chn_to_ipa(
# #     chn_sentence=tuple("仅 绘画 而论 齐白石 是 巍巍 昆仑 可 这位 附庸风雅 的 门外汉 连 一块 石头 都 不是"),
# #     consider_annotations=False,
# #     annotation_split_symbol=None,
# #     cache=get_empty_cache(),
# #   )

# #   assert result == ('t', 'ɕ', 'i˧˩˧', 'n', ' ', 'x', 'w', 'e', 'ɪ˥˩', 'x', 'w', 'a˥˩', ' ', 'ɑ˧˥', 'ɻ', 'l', 'w', 'ə˥˩', 'n', ' ', 't', 'ɕʰ', 'i˧˥', 'p', 'a', 'ɪ˧˥', 'ʂ', 'ɨ˧˥', ' ', 'ʂ', 'ɨ˥˩', ' ', 'w', 'e', 'ɪ˥', 'w', 'e', 'ɪ˥', ' ', 'kʰ', 'w', 'ə˥', 'n', 'l', 'w', 'ə˧˥', 'n', ' ', 'kʰ', 'ɤ˧˩˧', ' ', 'ʈ',
# #                     'ʂ', 'ɤ˥˩', 'w', 'e', 'ɪ˥˩', ' ', 'f', 'u˥˩', 'y', 'ʊ˥', 'ŋ', 'f', 'ɤ˥', 'ŋ', 'j', 'a˧˩˧', ' ', 't', 'ɤ', ' ', 'm', 'ə˧˥', 'n', 'w', 'a', 'ɪ˥˩', 'x', 'a˥˩', 'n', ' ', 'l', 'j', 'ɛ˧˥', 'n', ' ', 'i˥', 'kʰ', 'w', 'a', 'ɪ˥˩', ' ', 'ʂ', 'ɨ˧˥', 'tʰ', 'o', 'ʊ', ' ', 't', 'o', 'ʊ˥', ' ', 'p', 'u˥˩', 'ʂ', 'ɨ˥˩')
