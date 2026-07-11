#!/usr/bin/env python3
"""Generate the Totempælen archive site.

Scans documents/*.pdf, renders a front-page thumbnail for each issue into
assets/covers/, and writes index.html — a grid of covers grouped by year.

Re-run this after adding a new PDF to documents/:

    python3 build.py

Requires ``pdftoppm`` (poppler-utils) on PATH for thumbnail generation.
"""

import html
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCS = ROOT / "documents"
COVERS = ROOT / "assets" / "covers"
INDEX = ROOT / "index.html"

MONTHS = {
    "02": "Februar",
    "04": "April",
    "05": "Maj",
    "08": "August",
    "09": "September",
    "10": "Oktober",
    "11": "November",
    "12": "December",
}


class Issue:
    def __init__(self, pdf: Path):
        self.pdf = pdf
        self.stem = pdf.stem  # e.g. "2019-05" or "2011-04_aprilsnar"
        self.cover = COVERS / f"{self.stem}.jpg"
        self.year, self.sort_key, self.label = self._parse(self.stem)

    @staticmethod
    def _parse(stem: str):
        """Return (year:int, sort_key:tuple, label:str) from a filename stem."""
        year = int(stem[:4])

        if stem.endswith("aarsberetning"):
            # Annual report — sort last within the year.
            return year, (99, ""), "Årsberetning"

        m = re.match(r"^\d{4}-(\d{2})(?:_(.+))?$", stem)
        if m:
            month, suffix = m.group(1), m.group(2)
            name = MONTHS.get(month, month)
            if suffix == "aprilsnar":
                # Show right after the regular April issue.
                return year, (int(month), 1), f"{name} {year} – Aprilsnar"
            return year, (int(month), 0), f"{name} {year}"

        # Fallback: use the raw stem.
        return year, (100, stem), stem


def render_cover(issue: Issue) -> None:
    if issue.cover.exists():
        return
    print(f"  rendering cover: {issue.cover.name}")
    with tempfile.TemporaryDirectory() as tmp:
        out_prefix = Path(tmp) / "cover"
        subprocess.run(
            [
                "pdftoppm", "-jpeg", "-f", "1", "-l", "1",
                "-scale-to-x", "500", "-scale-to-y", "-1",
                str(issue.pdf), str(out_prefix),
            ],
            check=True,
        )
        produced = sorted(Path(tmp).glob("cover*.jpg"))
        if not produced:
            raise RuntimeError(f"pdftoppm produced no output for {issue.pdf}")
        shutil.move(str(produced[0]), str(issue.cover))


def jpeg_size(path: Path):
    """Return (width, height) of a baseline JPEG without external deps."""
    data = path.read_bytes()
    if data[:2] != b"\xff\xd8":
        raise ValueError(f"{path} is not a JPEG")
    i = 2
    while i < len(data) - 1:
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        i += 2
        # Standalone markers (no length): padding, RSTn.
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            continue
        seg_len = int.from_bytes(data[i:i + 2], "big")
        # SOFn frame headers carry the dimensions (excl. non-SOF C4/C8/CC).
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            height = int.from_bytes(data[i + 3:i + 5], "big")
            width = int.from_bytes(data[i + 5:i + 7], "big")
            return width, height
        i += seg_len
    raise ValueError(f"no SOF marker found in {path}")


def card_html(issue: Issue) -> str:
    label = html.escape(issue.label)
    width, height = jpeg_size(issue.cover)
    return f"""        <a class="card" href="documents/{html.escape(issue.pdf.name)}">
          <img src="assets/covers/{html.escape(issue.cover.name)}" alt="Forside – {label}" width="{width}" height="{height}" loading="lazy">
          <span class="caption">{label}</span>
        </a>"""


def build_html(issues) -> str:
    by_year = {}
    for issue in issues:
        by_year.setdefault(issue.year, []).append(issue)

    sections = []
    for year in sorted(by_year, reverse=True):
        cards = sorted(by_year[year], key=lambda i: i.sort_key)
        cards_html = "\n".join(card_html(c) for c in cards)
        sections.append(
            f"""      <section class="year">
        <h2>{year}</h2>
        <div class="grid">
{cards_html}
        </div>
      </section>"""
        )
    sections_html = "\n".join(sections)

    return f"""<!DOCTYPE html>
<html lang="da">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Totempælen – Gruppeblad for Bellahøj 21st Barking</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="assets/style.css">
</head>
<body>
  <header id="header">
    <div class="container">
      <img src="assets/logo.png" alt="Bellahøj 21st Barking" class="logo">
      <h1>TOTEMPÆLEN</h1>
      <p class="lead">Gruppeblad for Bellahøj 21st Barking</p>
    </div>
  </header>

  <main id="main-content">
    <div class="container">
      <p class="intro">Arkiv over tidligere numre af Totempælen. Klik på en forside for at åbne bladet som PDF.</p>
{sections_html}
    </div>
  </main>

  <footer>
    <div class="container">
      <h3>Bellahøj 21st Barking</h3>
      <p>Spejderhuset<br>Brønshøjvej 29B<br>2700 Brønshøj</p>
      <p><a href="mailto:info@b21b.dk">info@b21b.dk</a></p>
      <p><a href="https://b21b.dk/">https://b21b.dk/</a></p>
    </div>
  </footer>
</body>
</html>
"""


def main() -> int:
    if not DOCS.is_dir():
        print(f"error: {DOCS} not found", file=sys.stderr)
        return 1
    COVERS.mkdir(parents=True, exist_ok=True)

    pdfs = sorted(DOCS.glob("*.pdf"))
    if not pdfs:
        print("error: no PDFs found in documents/", file=sys.stderr)
        return 1

    issues = [Issue(p) for p in pdfs]
    print(f"Found {len(issues)} issues.")
    for issue in issues:
        render_cover(issue)

    INDEX.write_text(build_html(issues), encoding="utf-8")
    print(f"Wrote {INDEX.relative_to(ROOT)} ({len(issues)} issues).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
