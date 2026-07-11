# Totempælen

Arkiv-side over gamle numre af **Totempælen** – gruppeblad for [Bellahøj 21st Barking](https://b21b.dk/).

Siden er en statisk GitHub Pages-side, der viser en oversigt over bladene som et galleri af forsider, grupperet efter år. Hvert blad linker til den fulde PDF.

## Struktur

- `documents/` – PDF-numre af bladet (`YYYY-MM.pdf`, `YYYY-aarsberetning.pdf`).
- `assets/covers/` – automatisk genererede forside-miniaturer (én pr. PDF).
- `assets/style.css`, `assets/logo.png` – design (matcher <https://medlem.b21b.dk/>).
- `index.html` – genereret oversigt (må ikke redigeres i hånden).
- `build.py` – genererer `index.html` og manglende forsider.

## Tilføj et nyt blad

1. Læg PDF'en i `documents/` med korrekt navn, fx `2024-02.pdf` eller `2024-aarsberetning.pdf`.
2. Kør bygge-scriptet:

   ```sh
   python3 build.py
   ```

   Det kræver `pdftoppm` (poppler-utils) for at lave forside-miniaturen.
3. Commit og push de nye/ændrede filer.

## Deployment

GitHub Pages serveres direkte fra `main`-branchens rod
(**Settings → Pages → Deploy from a branch → `main` / `(root)`**).
Der er ingen byggefase på GitHub; `index.html` og forsiderne committes.
