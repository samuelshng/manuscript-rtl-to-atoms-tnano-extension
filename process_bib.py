#!/usr/bin/env python3
"""Clean BibTeX files by stripping url fields and collapsing long author lists."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence, Tuple

from bib_et_al import process_bibtex
from strip_bib_urls import strip_url_fields


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Remove url fields and rewrite author lists with more than six names "
            "to 'First Author and others'. The input file is modified in place."
        )
    )
    parser.add_argument(
        "bibfile",
        type=Path,
        help="Path to the .bib file to process",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="Encoding to use when reading/writing (default: utf-8)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run the cleaners but write the result to stdout instead of the file",
    )
    return parser.parse_args(argv)


def clean_bib_content(content: str) -> Tuple[str, int, int]:
    """Apply url stripping first, then author compaction."""

    without_urls, urls_removed = strip_url_fields(content)
    cleaned_authors, authors_modified = process_bibtex(without_urls)
    return cleaned_authors, urls_removed, authors_modified


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    bib_path = args.bibfile.expanduser().resolve()

    try:
        content = bib_path.read_text(encoding=args.encoding)
    except OSError as exc:
        print(f"Failed to read {bib_path}: {exc}", file=sys.stderr)
        return 1

    new_content, urls_removed, authors_modified = clean_bib_content(content)
    total_changes = urls_removed + authors_modified

    if args.dry_run:
        sys.stdout.write(new_content)
    else:
        if total_changes == 0:
            print("No changes were necessary.")
        else:
            try:
                bib_path.write_text(new_content, encoding=args.encoding)
            except OSError as exc:
                print(f"Failed to write {bib_path}: {exc}", file=sys.stderr)
                return 1

    print(
        "Removed {} url field{}; rewrote {} author field{}.".format(
            urls_removed,
            "s" if urls_removed != 1 else "",
            authors_modified,
            "s" if authors_modified != 1 else "",
        )
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
