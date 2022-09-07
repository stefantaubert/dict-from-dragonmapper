from typing import Iterable, List, Optional, Set, Tuple

from dict_from_dragonmapper.ipa_symbols import (APPENDIX, CHARACTERS, CONSONANTS,
                                                ENG_ARPA_DIPHTONGS, ENG_DIPHTHONGS,
                                                PUNCTUATION_AND_WHITESPACE, SCHWAS, STRESS_PRIMARY,
                                                STRESS_SECONDARY, STRESSES, TIE_ABOVE, TIE_BELOW,
                                                TIES, TONES, VOWELS)


def parse_ipa_to_symbols(sentence: str) -> Tuple[str, ...]:
  all_symbols = tuple(sentence)
  return parse_ipa_symbols_to_symbols(all_symbols)


def parse_ipa_symbols_to_symbols(all_symbols: Tuple[str, ...]) -> Tuple[str, ...]:
  all_symbols = merge_together(
    symbols=all_symbols,
    merge_symbols=TIES,
    ignore_merge_symbols=PUNCTUATION_AND_WHITESPACE,
  )

  all_symbols = merge_right(
    symbols=all_symbols,
    merge_symbols=APPENDIX,
    ignore_merge_symbols=PUNCTUATION_AND_WHITESPACE,
    insert_symbol=None,
  )

  all_symbols = merge_left(
    symbols=all_symbols,
    merge_symbols=STRESSES,
    ignore_merge_symbols=PUNCTUATION_AND_WHITESPACE,
    insert_symbol=None,
  )

  return all_symbols


def merge_together(symbols: Tuple[str, ...], merge_symbols: Set[str], ignore_merge_symbols: Set[str]) -> Tuple[str, ...]:
  merge_or_ignore_merge_symbols = merge_symbols.union(ignore_merge_symbols)
  j = 0
  merged_symbols = []
  while j < len(symbols):
    new_symbol, j = get_next_merged_together_symbol_and_index(
      symbols, j, merge_symbols, merge_or_ignore_merge_symbols)
    merged_symbols.append(new_symbol)
  return tuple(merged_symbols)


def get_next_merged_together_symbol_and_index(symbols: Tuple[str, ...], j, merge_symbols: Set[str], merge_or_ignore_merge_symbols: Set[str]):
  assert merge_symbols.issubset(merge_or_ignore_merge_symbols)
  assert j < len(symbols)
  new_symbol = symbols[j]
  j += 1
  while symbols[j - 1] not in merge_or_ignore_merge_symbols and j < len(symbols):
    merge_symbol_concat, index = get_all_next_consecutive_merge_symbols(symbols[j:], merge_symbols)
    if len(merge_symbol_concat) > 0 and symbols[j + index] not in merge_or_ignore_merge_symbols:
      new_symbol += merge_symbol_concat + symbols[j + index]
      j += index + 1
    else:
      break
  return new_symbol, j


def get_all_next_consecutive_merge_symbols(symbols: Tuple[str, ...], merge_symbols: Set[str]) -> Tuple[str, int]:
  assert len(symbols) > 0
  merge_symbol_concat = ""
  index = None
  for index, symbol in enumerate(symbols):
    if symbol in merge_symbols:
      merge_symbol_concat += symbol
    else:
      return merge_symbol_concat, index
  assert index is not None
  return merge_symbol_concat, index


def merge_left(symbols: Tuple[str, ...], merge_symbols: Set[str], ignore_merge_symbols: Set[str], insert_symbol: Optional[str]) -> Tuple[str, ...]:
  if insert_symbol is None:
    insert_symbol = ""
  merged_symbols = merge_left_core(symbols, merge_symbols, ignore_merge_symbols)
  merged_symbols_with_insert_symbols = (
    insert_symbol.join(single_merged_symbols) for single_merged_symbols in merged_symbols)
  return tuple(merged_symbols_with_insert_symbols)


def merge_left_core(symbols: Tuple[str, ...], merge_symbols: Set[str], ignore_merge_symbols: Set[str]) -> Tuple[Tuple[str, ...]]:
  j = 0
  reversed_symbols = symbols[::-1]
  reversed_merged_symbols = []
  while j < len(reversed_symbols):
    new_symbol, j = get_next_merged_left_symbol_and_index(
      reversed_symbols, j, merge_symbols, ignore_merge_symbols)
    reversed_merged_symbols.append(new_symbol)
  merged_symbols = reversed_merged_symbols[::-1]
  return tuple(merged_symbols)


def get_next_merged_left_symbol_and_index(symbols: Tuple[str, ...], j: int, merge_symbols: Set[str], ignore_merge_symbols: Set[str]) -> Tuple[str, int]:
  new_symbol = [symbols[j]]
  j += 1
  if new_symbol[0] not in ignore_merge_symbols and new_symbol[0] not in merge_symbols:
    while j < len(symbols) and symbols[j] in merge_symbols:
      new_symbol.insert(0, symbols[j])
      j += 1
  return tuple(new_symbol), j


def merge_right(symbols: Tuple[str, ...], merge_symbols: Set[str], ignore_merge_symbols: Set[str], insert_symbol: Optional[str]) -> Tuple[str, ...]:
  if insert_symbol is None:
    insert_symbol = ""
  merged_symbols = merge_right_core(symbols, merge_symbols, ignore_merge_symbols)
  merged_symbols_with_insert_symbols = (
    insert_symbol.join(single_merged_symbols) for single_merged_symbols in merged_symbols)
  return tuple(merged_symbols_with_insert_symbols)


def merge_right_core(symbols: Tuple[str, ...], merge_symbols: Set[str], ignore_merge_symbols: Set[str]) -> Tuple[Tuple[str, ...]]:
  j = 0
  merged_symbols = []
  while j < len(symbols):
    new_symbol, j = get_next_merged_right_symbol_and_index(
      symbols, j, merge_symbols, ignore_merge_symbols)
    merged_symbols.append(new_symbol)
  return tuple(merged_symbols)


def get_next_merged_right_symbol_and_index(symbols: Tuple[str, ...], j: int, merge_symbols: Set[str], ignore_merge_symbols: Set[str]) -> Tuple[str, int]:
  new_symbol = [symbols[j]]
  j += 1
  if new_symbol[0] not in ignore_merge_symbols and new_symbol[0] not in merge_symbols:
    while j < len(symbols) and symbols[j] in merge_symbols:
      new_symbol.append(symbols[j])
      j += 1
  return tuple(new_symbol), j
