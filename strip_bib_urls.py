#!/usr/bin/env python3
"""Remove all `url` fields from a BibTeX file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Sequence, Tuple


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Strip every url field from a .bib file without touching other entries."
    )
    parser.add_argument("bibfile", type=Path, help="Path to the input .bib file")
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Write the cleaned BibTeX to this path instead of stdout",
    )
    output_group.add_argument(
        "-i",
        "--in-place",
        action="store_true",
        help="Overwrite the input file with the cleaned contents",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="File encoding to use when reading/writing (default: utf-8)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress summary output on stderr",
    )
    return parser.parse_args(argv)


def strip_url_fields(content: str) -> Tuple[str, int]:
    """Return content with every top-level url field removed."""

    ranges = locate_url_field_ranges(content)
    if not ranges:
        return content, 0

    pieces: List[str] = []
    cursor = 0
    for start, end in ranges:
        if start < cursor:
            # This should not happen, but guard against overlapping ranges.
            continue
        pieces.append(content[cursor:start])
        cursor = end
    pieces.append(content[cursor:])
    return "".join(pieces), len(ranges)


def locate_url_field_ranges(text: str) -> List[Tuple[int, int]]:
    lower = text.lower()
    idx = 0
    ranges: List[Tuple[int, int]] = []
    length = len(text)

    while idx < length:
        candidate = lower.find("url", idx)
        if candidate == -1:
            break
        bounds = compute_field_bounds(text, candidate)
        if bounds is None:
            idx = candidate + 1
            continue
        start, end = bounds
        ranges.append((start, end))
        idx = end

    return ranges


def compute_field_bounds(text: str, field_index: int) -> Optional[Tuple[int, int]]:
    """Given an index pointing at 'u' in 'url', return slice bounds to remove."""

    if not is_field_name(text, field_index, 3):
        return None

    n = len(text)
    j = field_index + 3
    while j < n and text[j].isspace():
        j += 1
    if j >= n or text[j] != '=':
        return None
    j += 1
    while j < n and text[j].isspace():
        j += 1
    if j >= n:
        return None

    value_start = j
    value_end = find_value_end(text, value_start)
    if value_end is None:
        return None

    end = value_end
    # Skip spaces/tabs before the optional comma.
    while end < n and text[end] in ' \t':
        end += 1

    if end < n and text[end] == ',':
        end += 1
        while end < n and text[end] in ' \t':
            end += 1
        end = consume_linebreak(text, end)
    else:
        end = consume_linebreak(text, end)

    start = compute_field_start(text, field_index)
    return start, end


def compute_field_start(text: str, field_index: int) -> int:
    """Extend the removal to the indentation at the start of the line if present."""

    line_start = find_line_start(text, field_index)
    if text[line_start:field_index].strip():
        return field_index
    return line_start


def find_line_start(text: str, index: int) -> int:
    """Return the index of the first character in the current line."""

    newline = text.rfind('\n', 0, index)
    carriage = text.rfind('\r', 0, index)
    line_break = max(newline, carriage)
    return line_break + 1 if line_break >= 0 else 0


def consume_linebreak(text: str, pos: int) -> int:
    """Consume a single CR, LF, or CRLF sequence starting at pos."""

    n = len(text)
    if pos < n and text[pos] == '\r':
        pos += 1
        if pos < n and text[pos] == '\n':
            pos += 1
        return pos
    if pos < n and text[pos] == '\n':
        return pos + 1
    return pos


def is_field_name(text: str, index: int, length: int) -> bool:
    """True if text[index:index+length] forms a standalone field name."""

    before = text[index - 1] if index > 0 else None
    if before is not None and (before.isalnum() or before == '_' or before == '\\'):
        return False
    after_index = index + length
    if after_index < len(text):
        after = text[after_index]
        if after.isalnum() or after == '_':
            return False
    return True


def find_value_end(text: str, start: int) -> Optional[int]:
    """Return the index immediately after the value (excluding separators)."""

    n = len(text)
    if text[start] == '{':
        match = find_matching_brace(text, start)
        return match + 1 if match is not None else None
    if text[start] == '"':
        match = find_matching_quote(text, start)
        return match + 1 if match is not None else None

    i = start
    brace_depth = 0
    in_quote = False
    escaped = False
    while i < n:
        c = text[i]
        if in_quote:
            if c == '"' and not escaped:
                in_quote = False
            if c == '\\' and not escaped:
                escaped = True
            else:
                escaped = False
            i += 1
            continue
        if c == '"':
            in_quote = True
            escaped = False
            i += 1
            continue
        if c == '{':
            brace_depth += 1
            i += 1
            continue
        if c == '}':
            if brace_depth == 0:
                return i
            brace_depth -= 1
            i += 1
            continue
        if brace_depth == 0 and c == ',':
            return i
        i += 1
    return n


def find_matching_brace(text: str, open_index: int) -> Optional[int]:
    depth = 1
    i = open_index + 1
    n = len(text)
    while i < n:
        c = text[i]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return None


def find_matching_quote(text: str, open_index: int) -> Optional[int]:
    i = open_index + 1
    n = len(text)
    escaped = False
    while i < n:
        c = text[i]
        if c == '"' and not escaped:
            return i
        if c == '\\' and not escaped:
            escaped = True
        else:
            escaped = False
        i += 1
    return None


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_args(argv)
    try:
        content = args.bibfile.read_text(encoding=args.encoding)
    except OSError as exc:
        print(f"Failed to read {args.bibfile}: {exc}", file=sys.stderr)
        sys.exit(1)

    new_content, removed = strip_url_fields(content)

    if args.in_place or args.output:
        target = args.bibfile if args.in_place else args.output
        assert target is not None
        try:
            target.write_text(new_content, encoding=args.encoding)
        except OSError as exc:
            print(f"Failed to write {target}: {exc}", file=sys.stderr)
            sys.exit(1)
    else:
        sys.stdout.write(new_content)

    if not args.quiet:
        if removed == 0:
            print("No url fields were found.", file=sys.stderr)
        elif removed == 1:
            print("Removed 1 url field.", file=sys.stderr)
        else:
            print(f"Removed {removed} url fields.", file=sys.stderr)


if __name__ == "__main__":
    main()
