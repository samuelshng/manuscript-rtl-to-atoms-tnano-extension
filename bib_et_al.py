#!/usr/bin/env python3
"""
Rewrite BibTeX author lists with more than six names to "First Author and others".

Usage:
  python3 bib_et_al.py /path/to/input.bib

Output file path:
  Same directory/name with "_et_al" inserted before the .bib suffix.

Notes:
- Keeps the original quoting/bracing style ("..." or {...}).
- Only modifies entries whose author list contains more than six persons.
- Skips entries that already contain "and others".
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Tuple
import re


def compute_output_path(input_path: Path) -> Path:
    """Insert _et_al before the .bib suffix; if no .bib suffix, append _et_al.bib."""
    if input_path.suffix.lower() == ".bib":
        return input_path.with_name(f"{input_path.stem}_et_al{input_path.suffix}")
    return input_path.with_name(f"{input_path.name}_et_al.bib")


def is_word_boundary(prev_char: Optional[str]) -> bool:
    """True if prev_char is None or not alphanumeric or underscore."""
    if prev_char is None:
        return True
    return not (prev_char.isalnum() or prev_char == "_")


def find_next_author_field(content: str, start_index: int) -> Optional[Tuple[int, int, int, str, str]]:
    """
    Find the next author field starting at start_index.

    Returns a tuple with:
    - field_start_index: index where the word 'author' starts
    - value_start_index: index of the first character inside the quotes/braces
    - value_end_index: index of the last character inside the quotes/braces (exclusive)
    - delimiter: '"' or '{' indicating the wrapper used
    - value: the raw author field value (without wrapper)

    If not found, returns None.
    """
    needle = "author"
    n = len(content)
    pos = start_index
    lower_content = content.lower()

    while True:
        idx = lower_content.find(needle, pos)
        if idx == -1:
            return None

        prev_char = None if idx == 0 else content[idx - 1]
        if not is_word_boundary(prev_char):
            pos = idx + 1
            continue

        j = idx + len(needle)
        # Skip whitespace
        while j < n and content[j].isspace():
            j += 1

        if j >= n or content[j] != '=':
            pos = idx + 1
            continue

        j += 1  # Skip '='
        while j < n and content[j].isspace():
            j += 1

        if j >= n:
            return None

        delimiter = content[j]
        if delimiter not in ('{', '"'):
            # Non-braced/quoted value (e.g., macro); skip conservatively
            pos = idx + 1
            continue

        value_start = j + 1

        if delimiter == '{':
            # Parse until matching closing brace with nesting
            level = 1
            k = value_start
            while k < n:
                c = content[k]
                if c == '{':
                    level += 1
                elif c == '}':
                    level -= 1
                    if level == 0:
                        value_end = k
                        value = content[value_start:value_end]
                        return (idx, value_start, value_end, delimiter, value)
                k += 1
            # Unbalanced braces; treat as not found
            return None
        else:
            # delimiter == '"': parse until next unescaped quote
            k = value_start
            escaped = False
            while k < n:
                c = content[k]
                if c == '"' and not escaped:
                    value_end = k
                    value = content[value_start:value_end]
                    return (idx, value_start, value_end, delimiter, value)
                if c == '\\' and not escaped:
                    escaped = True
                else:
                    escaped = False
                k += 1
            return None


def split_authors_top_level(author_value: str) -> List[str]:
    """
    Split the author field string into individual authors on top-level ' and ' boundaries.
    Respects brace nesting to avoid splitting inside grouped parts of names.
    """
    authors: List[str] = []
    buffer: List[str] = []
    level = 0
    i = 0
    s = author_value
    length = len(s)

    def matches_and_at(index: int) -> int:
        # Check for 'and' with whitespace boundaries, case-insensitive
        if index + 3 > length:
            return 0
        segment = s[index:index + 3].lower()
        if segment != 'and':
            return 0
        prev_ok = (index == 0) or s[index - 1].isspace()
        next_ok = (index + 3 >= length) or s[index + 3].isspace()
        return 3 if prev_ok and next_ok else 0

    while i < length:
        c = s[i]
        if c == '{':
            level += 1
            buffer.append(c)
            i += 1
            continue
        if c == '}':
            level = max(0, level - 1)
            buffer.append(c)
            i += 1
            continue
        if level == 0:
            m = matches_and_at(i)
            if m:
                author = ''.join(buffer).strip()
                if author:
                    authors.append(author)
                buffer = []
                i += m
                # Consume any additional whitespace after 'and'
                while i < length and s[i].isspace():
                    i += 1
                continue
        buffer.append(c)
        i += 1

    tail = ''.join(buffer).strip()
    if tail:
        authors.append(tail)

    return authors


def author_already_others(author_value: str) -> bool:
    return re.search(r"\band\s+others\b", author_value, flags=re.IGNORECASE) is not None


def transform_author_value_if_needed(author_value: str) -> Optional[str]:
    """
    If there are more than six authors and no existing 'and others', return the
    transformed value of the form 'First Author and others'. Otherwise, return None.
    """
    if author_already_others(author_value):
        return None

    authors = split_authors_top_level(author_value)
    if len(authors) <= 6:
        return None

    first_author = authors[0].strip()
    if not first_author:
        return None

    return f"{first_author} and others"


def process_bibtex(content: str) -> Tuple[str, int]:
    """Process the entire .bib content, rewriting qualifying author fields. Returns (new_content, num_modified)."""
    modified_count = 0
    i = 0
    pieces: List[str] = []
    cursor = 0

    while True:
        found = find_next_author_field(content, i)
        if not found:
            break

        field_start_index, value_start_index, value_end_index, delimiter, value = found
        replacement_value = transform_author_value_if_needed(value)
        if replacement_value is None:
            i = value_end_index + 1
            continue

        # Append untouched content up to the value start
        pieces.append(content[cursor:value_start_index])
        # Insert the transformed value
        pieces.append(replacement_value)
        cursor = value_end_index
        i = value_end_index + 1
        modified_count += 1

    # Append the remaining content
    pieces.append(content[cursor:])
    new_content = ''.join(pieces)
    return new_content, modified_count


def main() -> int:
    parser = argparse.ArgumentParser(description="Rewrite BibTeX author lists with >6 authors to 'First Author and others'.")
    parser.add_argument("input_bib", help="Path to the input .bib file")
    args = parser.parse_args()

    input_path = Path(args.input_bib).expanduser().resolve()
    if not input_path.exists():
        print(f"Error: file not found: {input_path}", file=sys.stderr)
        return 2

    try:
        content = input_path.read_text(encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        print(f"Error reading {input_path}: {exc}", file=sys.stderr)
        return 2

    new_content, modified_count = process_bibtex(content)

    output_path = compute_output_path(input_path)
    try:
        output_path.write_text(new_content, encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        print(f"Error writing {output_path}: {exc}", file=sys.stderr)
        return 2

    print(f"Wrote: {output_path}")
    print(f"Author fields modified: {modified_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


