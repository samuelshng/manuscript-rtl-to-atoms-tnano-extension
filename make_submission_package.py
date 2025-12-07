#!/usr/bin/env python3
"""Create a clean submission package for the IEEEtran manuscript."""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Iterable, List, Sequence

GRAPHIC_EXTENSIONS: Sequence[str] = (".pdf", ".png", ".jpg", ".jpeg", ".eps")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tex",
        default="conference_101719.tex",
        help="Entry-point LaTeX file to package (default: conference_101719.tex)",
    )
    parser.add_argument(
        "--output-dir",
        default="submission-package",
        help="Directory to populate with the submission package",
    )
    return parser.parse_args()


def unique(items: Iterable[str]) -> List[str]:
    return list(OrderedDict.fromkeys(items))


def strip_latex_comments(text: str) -> str:
    def strip_line(line: str) -> str:
        newline = ""
        if line.endswith("\n"):
            newline = "\n"
            line = line[:-1]

        result: List[str] = []
        i = 0
        while i < len(line):
            ch = line[i]
            if ch == "%":
                backslash_count = 0
                j = i - 1
                while j >= 0 and line[j] == "\\":
                    backslash_count += 1
                    j -= 1
                if backslash_count % 2 == 1:
                    result.append("%")
                    i += 1
                    continue
                break
            result.append(ch)
            i += 1

        stripped = "".join(result).rstrip()
        return (stripped + newline) if stripped else newline

    return "".join(strip_line(line) for line in text.splitlines(True))


def extract_includegraphics_paths(text: str) -> List[str]:
    pattern = re.compile(r"\\includegraphics(?:\s*\[[^\]]*\])?\s*{([^}]*)}")
    return unique(match.group(1).strip() for match in pattern.finditer(text))


def extract_graphic_search_dirs(text: str) -> List[str]:
    pattern = re.compile(r"\\graphicspath{([^}]*)}")
    dirs: List[str] = []
    for group in pattern.findall(text):
        for entry in re.findall(r"{([^{}]+)}", group):
            cleaned = entry.strip()
            if cleaned:
                dirs.append(cleaned)
    return unique(dirs)


def extract_bibliography_files(text: str) -> List[str]:
    pattern = re.compile(r"\\bibliography{([^}]*)}")
    bibs: List[str] = []
    for grp in pattern.findall(text):
        for entry in grp.split(","):
            cleaned = entry.strip()
            if cleaned:
                bibs.append(cleaned)
    return unique(bibs)


def extract_document_classes(text: str) -> List[str]:
    pattern = re.compile(r"\\documentclass(?:\[[^\]]*\])?{([^}]*)}")
    classes = []
    for cls in pattern.findall(text):
        name = cls.strip()
        if name:
            classes.append(name)
    return unique(classes)


def resolve_graphic_path(tex_dir: Path, graphic: str, extra_dirs: Sequence[str]) -> Path:
    raw_path = Path(graphic).expanduser()
    candidates: List[Path] = []

    if raw_path.is_absolute():
        candidates.append(raw_path)
    else:
        candidates.append((tex_dir / raw_path).resolve())
        if raw_path.parent == Path('.'):
            for directory in extra_dirs:
                base = Path(directory).expanduser()
                if not base.is_absolute():
                    base = (tex_dir / base).resolve()
                candidates.append(base / raw_path.name)

    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if candidate.suffix:
            if candidate.exists():
                return candidate
        else:
            for ext in GRAPHIC_EXTENSIONS:
                alt = candidate.with_suffix(ext)
                if alt.exists():
                    return alt
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Figure '{graphic}' not found relative to {tex_dir}")


def copy_file(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def locate_case_insensitive(root: Path, filename: str) -> Path | None:
    target = filename.lower()
    for path in root.rglob("*.cls"):
        if path.name.lower() == target:
            return path
    return None


def main() -> None:
    args = parse_args()
    tex_path = Path(args.tex).expanduser().resolve()
    if not tex_path.exists():
        sys.exit(f"LaTeX file '{tex_path}' not found")

    tex_dir = tex_path.parent
    package_dir = Path(args.output_dir)
    if not package_dir.is_absolute():
        package_dir = tex_dir / package_dir

    if package_dir.exists():
        shutil.rmtree(package_dir)
    (package_dir / "figs").mkdir(parents=True)

    tex_content = tex_path.read_text(encoding="utf-8")

    sanitized = strip_latex_comments(tex_content)
    (package_dir / tex_path.name).write_text(sanitized, encoding="utf-8")

    figures = extract_includegraphics_paths(tex_content)
    graphics_dirs = extract_graphic_search_dirs(tex_content)
    for figure in figures:
        source = resolve_graphic_path(tex_dir, figure, graphics_dirs)
        rel = Path(figure)
        if rel.parts and rel.parts[0] == "figs":
            rel = Path(*rel.parts[1:])
        dest = package_dir / "figs" / rel
        copy_file(source, dest)

    bib_files = extract_bibliography_files(tex_content)
    for bib in bib_files:
        bib_path = tex_dir / f"{bib}.bib"
        if not bib_path.exists():
            raise FileNotFoundError(f"Bib file '{bib_path}' not found")
        copy_file(bib_path, package_dir / bib_path.name)

    class_names = extract_document_classes(tex_content)
    for cls in class_names:
        cls_filename = f"{cls}.cls"
        cls_path = locate_case_insensitive(tex_dir, cls_filename)
        if cls_path is None:
            print(f"Warning: could not locate {cls_filename}")
            continue
        copy_file(cls_path, package_dir / cls_path.name)

    print(f"Created submission package at {package_dir}")
    if figures:
        print(" Included figures:")
        for figure in figures:
            print(f"  - {figure}")
    if bib_files:
        print(" Included bibliography files:")
        for bib in bib_files:
            print(f"  - {bib}.bib")
    if class_names:
        print(" Included class files:")
        for cls in class_names:
            print(f"  - {cls}.cls")


if __name__ == "__main__":
    main()
