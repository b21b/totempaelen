# CLAUDE.md

Guidance for working in this repo.

## What this is

A static **GitHub Pages** site: an archive of *Totempælen*, the membership
magazine ("gruppeblad") of the Danish scout group **Bellahøj 21st Barking (B21B)**.
The site shows a grid of magazine covers grouped by year; each cover links to the
full PDF. The design mirrors <https://medlem.b21b.dk/>.

Pages is served **from the repo root of `main`** — there is no build step on
GitHub. `index.html` and the cover thumbnails are generated locally by `build.py`
and committed.

## Layout

- `documents/*.pdf` — the magazine PDFs (source of truth). **Not** touched by the build.
- `assets/covers/*.jpg` — generated front-page thumbnails, one per PDF (committed).
- `assets/style.css` — styling (Poppins font, `#036` footer, `#337ab7` links).
- `assets/logo.png` — B21B emblem in brand blue; `assets/logo-white.png` is the
  original white-on-transparent version (keep it — useful on dark backgrounds).
- `index.html` — **generated; do not hand-edit.** Change `build.py` instead.
- `build.py` — regenerates covers + `index.html`.
- `.nojekyll` — makes Pages serve `assets/` and `documents/` verbatim.

## Adding new back-issue PDFs (the common task)

1. Drop the PDF(s) into `documents/` using the naming convention below.
2. Run the build (needs `pdftoppm` from poppler-utils on PATH):

   ```sh
   python3 build.py
   ```

   It renders a cover for any PDF that doesn't have one yet and rewrites
   `index.html`. Existing covers are left alone — delete a `.jpg` in
   `assets/covers/` to force it to re-render.
3. Verify (see below), then commit the new PDF(s), the new cover(s), and
   `index.html`.

### Filename convention — this drives the labels and ordering

- `YYYY-MM.pdf` → a monthly issue, e.g. `2024-05.pdf` → **"Maj 2024"**.
  Known months: `02`→Februar, `04`→April, `05`→Maj, `08`→August,
  `09`→September, `10`→Oktober, `11`→November, `12`→December. To support a new
  month, add it to the `MONTHS` dict in `build.py`.
- `YYYY-aarsberetning.pdf` → **"Årsberetning"** (annual report). Sorted last
  within its year.
- `YYYY-MM_aprilsnar.pdf` → **"April YYYY – Aprilsnar"** (April-fools special),
  shown next to the April issue.

Years are sectioned newest-first; issues within a year are ordered by month.
Anything not matching these patterns falls back to the raw filename as the label
— so stick to the convention.

## Verifying a change

Serve the site locally and confirm covers render and links resolve:

```sh
python3 -m http.server 8000
# then open http://localhost:8000/
```

Quick automated check that every card's PDF and cover return 200 (server running):

```sh
for f in $(grep -oE '(documents|assets/covers)/[^"]+\.(pdf|jpg)' index.html); do
  printf '%s %s\n' "$(curl -s -o /dev/null -w '%{http_code}' "http://localhost:8000/$f")" "$f"
done | grep -v '^200 ' || echo "all 200"
```

Optionally screenshot with headless Chrome to eyeball the layout:

```sh
google-chrome --headless --no-sandbox --disable-gpu --window-size=1200,2400 \
  --screenshot=/tmp/totempaelen.png http://localhost:8000/
```

## Deployment

Enable once in the GitHub UI: **Settings → Pages → Deploy from a branch →
`main` / `(root)`**. After that, pushing to `main` publishes the committed
`index.html` + assets. No CI/build runs on GitHub.
