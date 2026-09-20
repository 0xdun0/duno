"""tests/test_docs.py — Testes da Central de Documentação (Estilo Docker Docs)."""
import unittest
from app import create_app
from core.docs_manager import get_all_categories, get_doc_content, search_docs


class TestDocsManager(unittest.TestCase):
    """Testes unitários do docs_manager."""

    def test_categories_and_articles_count(self):
        cats = get_all_categories()
        self.assertEqual(len(cats), 4)
        cat_ids = [c["id"] for c in cats]
        self.assertIn("get-started", cat_ids)
        self.assertIn("guides", cat_ids)
        self.assertIn("manuals", cat_ids)
        self.assertIn("reference", cat_ids)

    def test_quickstart_doc_content(self):
        doc = get_doc_content("quickstart")
        self.assertIsNotNone(doc)
        self.assertIn("Getting Started", doc["metadata"]["title"])
        self.assertIn("Docker Compose", doc["html_content"])
        self.assertTrue(len(doc["toc"]) > 0)

    def test_kids_curriculum_doc_content(self):
        doc = get_doc_content("kids-curriculum")
        self.assertIsNotNone(doc)
        self.assertIn("DUNO Kids", doc["metadata"]["title"])
        self.assertIn("Sistemas Operacionais", doc["html_content"])

    def test_manifest_spec_doc_content(self):
        doc = get_doc_content("manifest-spec")
        self.assertIsNotNone(doc)
        self.assertIn("manifest.yml", doc["metadata"]["title"])

    def test_search_docs(self):
        res = search_docs("docker")
        self.assertTrue(len(res) > 0)
        slugs = [r["slug"] for r in res]
        self.assertIn("quickstart", slugs)


class TestDocsRoutes(unittest.TestCase):
    """Testes de integração das rotas web do docs."""

    def setUp(self):
        self.app = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

    def _login(self):
        with self.client.session_transaction() as sess:
            sess["user_id"] = 1
            sess["username"] = "admin"
            sess["role"] = "admin"

    def test_docs_hub_renders(self):
        self._login()
        res = self.client.get("/docs")
        self.assertEqual(res.status_code, 200)
        html = res.data.decode("utf-8")
        self.assertIn("How can we help?", html)
        self.assertIn("What's new", html)
        self.assertIn("Get started", html)

    def test_docs_reader_renders(self):
        self._login()
        res = self.client.get("/docs/quickstart")
        self.assertEqual(res.status_code, 200)
        html = res.data.decode("utf-8")
        self.assertIn("Getting Started &amp; Setup R\u00e1pido", html)
        self.assertIn("Nesta P\u00e1gina", html)

    def test_docs_reader_404_on_invalid_slug(self):
        self._login()
        res = self.client.get("/docs/slug-que-nao-existe")
        self.assertEqual(res.status_code, 404)

    def test_docs_search_api(self):
        self._login()
        res = self.client.get("/api/docs/search?q=manifest")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(isinstance(data, list))
        self.assertTrue(any(d["slug"] == "manifest-spec" for d in data))
