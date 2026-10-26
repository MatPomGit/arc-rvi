# Building and publishing this documentation

The canonical files remain in the repository root, `docs/`, and
`experiments/`. MkDocs never maintains duplicate research protocols.

## Local verification

Python 3.11+ is required.

```bash
python -m pip install mkdocs==1.6.1
python scripts/build_docs.py
python -m mkdocs build --strict
python -m mkdocs serve
```

The staging source and built site live under ignored `.build/`. Do not edit
generated files. The site index is copied from `README.md`; experiment pages
come from their canonical protocols. Manuscript `.tex` files are provided as
source links, not interpreted as finished publications.

## Publishing

The documentation workflow validates pull requests without publishing. A
successful build on `main` uploads a static artifact and deploys it to
GitHub Pages through the restricted `github-pages` environment.

Repository administrators must select **Settings → Pages → Build and deployment
→ GitHub Actions** as the Pages publishing source if it is not already enabled.
No publication is proven until a successful deployment is observed.

The expected project URL is:
https://matpomgit.github.io/arc-rvi/

Only public synthetic examples, open documentation, and text manuscript
scaffolds are staged. Raw data, secrets, run artifacts, and equipment
identifiers must never enter the site. The site is research documentation,
not evidence of completed studies or physical safety certification.
