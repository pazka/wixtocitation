"""Upgrade safety net for V_citations (see TESTING.md at the repo root).

Characterization tests: Wix product CSV -> Word citation document, and the upload web page. They pin what
the app does TODAY (quirks included) so a Python, pandas, python-docx or Flask bump that changes the
output fails here. Standard library only.

Run from V_citations/:  python -m unittest discover -s tests -v
"""
import csv
import io
import os
import shutil
import sys
import tempfile
import unittest

APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, APP_DIR)

from docx import Document  # noqa: E402

from docgen import doc_gen  # noqa: E402
from main import app  # noqa: E402

COLUMNS = ["handleId", "name", "collection", "productOptionDescription2", "productOptionDescription3",
           "additionalInfoDescription2", "additionalInfoDescription3", "additionalInfoDescription4",
           "additionalInfoDescription5", "price"]
ROWS = [
    ["2", "composition viii", "wassily kandinsky", "1923", "Paris", "<p>Service photo</p>", "Huile sur toile",
     "140 X 201 CM", "Guggenheim", "10"],
    ["1", "trapèze; bleu", "anni albers", "", "Berlin", "", "Tissage<br>", "", "Bauhaus/Archiv", "5"],
    ["3", "", "", "", "", "", "", "", "", ""],
]
# Sorted by collection; empty cells skipped; HTML tags, ';' and '/' stripped; collection and name title-cased,
# name in italics; dimension lower-cased.
EXPECTED = [
    ("", []),
    ("Anni Albers, Trapèze Bleu, Tissage, BauhausArchiv, Berlin",
     [("Anni Albers", None), (", Trapèze Bleu", True), (", Tissage", None), (", BauhausArchiv", None),
      (", Berlin", None)]),
    ("Wassily Kandinsky, Composition Viii, 1923, Huile sur toile, 140 x 201 cm, Guggenheim, Paris, Service photo",
     [("Wassily Kandinsky", None), (", Composition Viii", True), (", 1923", None), (", Huile sur toile", None),
      (", 140 x 201 cm", None), (", Guggenheim", None), (", Paris", None), (", Service photo", None)]),
]


def write_csv(path, columns=COLUMNS, rows=ROWS):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(columns)
        w.writerows(rows)


def paragraphs(path):
    return [(p.text, [(r.text, r.italic) for r in p.runs if r.text]) for p in Document(path).paragraphs]


class InWorkDir(unittest.TestCase):
    """The app reads and writes ./export.csv and ./generated_citation.docx: run each test in a temp dir."""

    def setUp(self):
        self.cwd = os.getcwd()
        self.dir = tempfile.mkdtemp(prefix="citations-test-")
        os.chdir(self.dir)

    def tearDown(self):
        os.chdir(self.cwd)


class DocGenTest(InWorkDir):
    def test_citation_document(self):
        write_csv("in.csv")
        out = doc_gen("in.csv")
        self.assertEqual(out, "./generated_citation.docx")
        self.assertEqual(paragraphs(out), EXPECTED)

    def test_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            doc_gen("nope.csv")

    def test_missing_collection_column_raises_keyerror_from_the_sort(self):
        # Quirk: sort_values runs before the friendly "Keys [...] not found" check, which is never reached.
        write_csv("in.csv", columns=["a", "b"], rows=[["1", "2"]])
        with self.assertRaises(KeyError) as ctx:
            doc_gen("in.csv")
        self.assertEqual(str(ctx.exception), "'collection'")

    def test_missing_other_column_gets_the_friendly_error(self):
        cols = [c for c in COLUMNS if c != "additionalInfoDescription5"]
        write_csv("in.csv", columns=cols, rows=[r[:8] + r[9:] for r in ROWS])
        with self.assertRaises(KeyError) as ctx:
            doc_gen("in.csv")
        self.assertIn("additionalInfoDescription5", str(ctx.exception))


class WebTest(InWorkDir):
    def setUp(self):
        super().setUp()
        # In the image cwd == app.root_path == "/"; send_file resolves "./generated_citation.docx" against
        # root_path. Mirror that in the temp dir (with a copy of static/) instead of writing into the repo.
        shutil.copytree(os.path.join(APP_DIR, "static"), os.path.join(self.dir, "static"))
        self.root_path = app.root_path
        app.root_path = self.dir
        self.client = app.test_client()

    def tearDown(self):
        app.root_path = self.root_path
        super().tearDown()

    def upload(self, body, filename, content_type):
        return self.client.post("/upload", data={"export": (io.BytesIO(body), filename, content_type)},
                                content_type="multipart/form-data")

    def test_index_page(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content_type, "text/html; charset=utf-8")
        self.assertIn(b"upload", r.data.lower())
        self.assertEqual(self.client.get("/index.html").status_code, 200)

    def test_static_cannot_escape_its_folder(self):
        self.assertEqual(self.client.get("/../main.py").status_code, 404)
        self.assertEqual(self.client.get("/%2e%2e/main.py").status_code, 404)
        self.assertEqual(self.client.get("/nope.js").status_code, 404)

    def test_upload_rejects_non_csv(self):
        r = self.upload(b"a,b\n", "x.txt", "text/plain")
        self.assertEqual((r.status_code, r.data), (400, b"only csv accepted"))

    def test_upload_returns_the_docx(self):
        write_csv("in.csv")
        with open("in.csv", "rb") as f:
            r = self.upload(f.read(), "export.csv", "text/csv")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers["Content-Disposition"], "attachment; filename=generated_citation.docx")
        # Python >= 3.13 knows the .docx MIME type; older ones send application/octet-stream.
        self.assertIn(r.content_type, ("application/octet-stream",
                                       "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))
        self.assertEqual(r.data[:2], b"PK")
        with open("got.docx", "wb") as f:
            f.write(r.data)
        self.assertEqual(paragraphs("got.docx"), EXPECTED)
        self.assertTrue(os.path.isfile("export.csv"))  # the upload is kept as ./export.csv

    def test_upload_with_wrong_columns_is_a_500(self):
        r = self.upload(b"a,b\n1,2\n", "x.csv", "text/csv")
        self.assertEqual((r.status_code, r.data), (500, b"Error: 'collection'"))


if __name__ == "__main__":
    unittest.main()
