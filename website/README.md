# Website source

The dedicated website folder contains editorial pages in `content/` and an explicit publication manifest, `public-sources.txt`. Canonical research protocols are reused by individual manifest entries, not copied into a second maintained protocol tree. Keep the website scientific and public-facing. Repository operational material is not a publication source.

Build from the repository root using `python scripts/build_docs.py` followed by `python -m mkdocs build --strict`. The generated output is `.build/site`. See the repository documentation build guide for local and CI verification.
