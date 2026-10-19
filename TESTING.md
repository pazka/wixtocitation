# Testing

## What is deployed

Only **`V_citations/`** (image `ghcr.io/pazka/wixtocitations`, https://wixcitations.hosh.it): a Flask page
where a Wix product export (CSV) is uploaded and a Word document of art citations is returned.
`V1_orig_transform/`, `V2_new_descriptions/`, `V3_new_dataset_desc/`, `v4_corrections/` and `request/` are
one-off scripts and data, not built or tested.

## Run it

Tests run inside the built image (that is where musl wheels can break):

```bash
docker build -t citations:smoke V_citations
docker run --rm -v "$PWD/V_citations:/src:ro" citations:smoke \
  sh -c 'mkdir /w && cp -r /src/. /w/ && cd /w && python -m unittest discover -s tests -v'
bash scripts/smoke.sh citations:smoke

# next base before Dependabot proposes it
sed -E 's#^FROM python:[^ ]+#FROM python:3.14-alpine#' V_citations/Dockerfile \
  | docker build -t citations:next -f - V_citations
```

(Windows Git Bash: prefix `docker run` with `MSYS_NO_PATHCONV=1`, mount `"$(cygpath -w "$PWD/V_citations")"`.)

## CI (`.github/workflows/ci.yml`)

PRs, `main`, `agent/**`. Matrix `current` (Dockerfile as committed) and `python:3.14-alpine`: build the
image, print the resolved package versions, run the unit tests inside it, run `scripts/smoke.sh`.
When the Dockerfile base moves, replace the next entry with the following Python.

## What is covered (`V_citations/tests/test_citations.py`, 9 tests, stdlib only)

- CSV → .docx: sorted by collection, empty cells skipped, HTML tags / `;` / `/` stripped, collection and
  title title-cased, title in italics, dimensions lower-cased (exact paragraphs and runs pinned).
- Missing file; missing `collection` column → `KeyError('collection')`; other missing column → the
  "Keys [...] not found" error.
- Web: index page, static files cannot escape `static/`, non-CSV → 400, CSV → .docx attachment with the
  same content, wrong columns → 500 `Error: 'collection'`.

`scripts/smoke.sh`: the built container serves the page, converts a real CSV upload to a .docx, rejects
non-CSV, logs no traceback.

## Upgrades checked (2026-10-19)

- **Python 3.10-alpine → 3.14-alpine** (Dependabot #1): builds; on 3.14 pip resolves **pandas 3.0.6**
  (2.3.3 on 3.10) and numpy 2.5 (2.2 on 3.10); 9/9 tests and smoke green, output identical → **go**.
  Only visible change: the download's `Content-Type` becomes the real .docx MIME type instead of
  `application/octet-stream` (newer `mimetypes`).

## Known gaps (pinned, not changed)

- **`main.py` runs Flask with `debug=True` on 0.0.0.0 in production** (`CMD python main.py`): the Werkzeug
  debugger is enabled on the public service. Highest-priority fix for the owner.
- `requirements.txt` is **unpinned**: every image build takes the latest pandas/numpy/Flask/python-docx.
  The CI matrix catches breakage at build time, but builds are not reproducible and Dependabot cannot
  propose bumps. Pinning (with a lock per base Python) is the recommended next step.
- The upload is written to `./export.csv` and the result to `./generated_citation.docx` in `/` (shared
  between concurrent users; image runs as root; no read-only rootfs; no HEALTHCHECK).
- `upload_file`: the "file not found" branch prints an undefined `e` (would turn a 404 into a 500).
- The friendly "Keys [...] not found" message is never reached for a missing `collection` column.
- `request/.env` is tracked in git (not read by this work): rotate whatever it held and remove it.
