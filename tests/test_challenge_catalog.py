"""tests/test_challenge_catalog.py — Testes unitários do catálogo de desafios CTF."""
import unittest
import tempfile
from pathlib import Path
import yaml

from modules.challenges.catalog import ChallengeCatalog, get_registry_path
from modules.challenges.validate_registry import validate_registry


class TestChallengeCatalog(unittest.TestCase):

    def setUp(self):
        self.catalog = ChallengeCatalog()

    def test_load_catalog_returns_at_least_three_challenges(self):
        challenges = self.catalog.load_challenges(force_reload=True)
        self.assertGreaterEqual(len(challenges), 3, "O catálogo deve conter pelo menos 3 desafios.")

    def test_mandatory_fields_present_in_all_challenges(self):
        challenges = self.catalog.load_challenges(force_reload=True)
        mandatory_fields = [
            "id", "name", "category", "short_description",
            "difficulty", "points", "estimated_minutes",
            "solves_count", "environment_type", "status", "os"
        ]
        for ch in challenges:
            for field in mandatory_fields:
                self.assertIn(field, ch, f"Campo obrigatório '{field}' ausente no desafio {ch.get('id')}")
                self.assertIsNotNone(ch[field], f"Campo '{field}' nulo no desafio {ch.get('id')}")
            self.assertGreater(ch["points"], 0, f"Pontuação deve ser > 0 no desafio {ch['id']}")
            self.assertGreater(ch["estimated_minutes"], 0, f"Tempo estimado deve ser > 0 no desafio {ch['id']}")
            self.assertIn(ch["difficulty"], ["easy", "medium", "hard", "insane"])
            self.assertIn(ch["environment_type"], ["single", "compose", "external"])
            self.assertIn(ch["os"], ["linux", "windows"])

    def test_get_by_id_valid(self):
        ch = self.catalog.get_by_id("alpha-sqli-basics")
        self.assertIsNotNone(ch)
        self.assertEqual(ch["id"], "alpha-sqli-basics")
        self.assertEqual(ch["name"], "Alpha")
        self.assertEqual(ch["internal_port"], 5000)

    def test_get_by_identifier_numeric_index(self):
        """Busca por índice numérico 1-based (/desafio/1, /desafio/2) retorna o desafio correspondente."""
        ch1, idx1 = self.catalog.get_by_identifier(1)
        self.assertIsNotNone(ch1)
        self.assertEqual(idx1, 1)
        self.assertEqual(ch1["id"], "alpha-sqli-basics")
        self.assertEqual(ch1["name"], "Alpha")

        ch2, idx2 = self.catalog.get_by_identifier("2")
        self.assertIsNotNone(ch2)
        self.assertEqual(idx2, 2)
        self.assertEqual(ch2["id"], "bravo")
        self.assertEqual(ch2["name"], "Bravo")

        ch25, idx25 = self.catalog.get_by_identifier("25")
        self.assertIsNotNone(ch25)
        self.assertEqual(idx25, 25)
        self.assertEqual(ch25["id"], "zulu-koa-devtools")
        self.assertEqual(ch25["name"], "Zenith")

    def test_get_by_identifier_slug(self):
        """Busca por slug string retorna o desafio e o índice correspondente."""
        ch, idx = self.catalog.get_by_identifier("delta-idor-document-vault")
        self.assertIsNotNone(ch)
        self.assertEqual(idx, 6)
        self.assertEqual(ch["id"], "delta-idor-document-vault")
        self.assertEqual(ch["name"], "Foxtrot")

    def test_get_by_id_nonexistent(self):
        ch = self.catalog.get_by_id("non-existent-challenge-slug")
        self.assertIsNone(ch)

    def test_get_by_id_path_traversal_blocked(self):
        ch = self.catalog.get_by_id("../../etc/passwd")
        self.assertIsNone(ch)

    def test_validate_registry_on_real_catalog(self):
        ok, errors, warnings = validate_registry()
        self.assertTrue(ok, f"A validação do catálogo real falhou: {errors}")
        self.assertEqual(len(errors), 0)

    def test_validate_registry_catches_errors(self):
        with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as tmp:
            bad_data = [
                {
                    "id": "INVALID SLUG WITH SPACES!",
                    "name": "Bad",
                    "category": "Test",
                    "short_description": "Desc",
                    "difficulty": "super-hard",  # invalid difficulty
                    "points": -10,               # invalid points
                    "estimated_minutes": 0,      # invalid minutes
                    "environment_type": "magic", # invalid env
                    "status": "active",          # invalid status
                }
            ]
            yaml.dump(bad_data, tmp)
            tmp_path = Path(tmp.name)

        try:
            ok, errors, warnings = validate_registry(tmp_path)
            self.assertFalse(ok)
            self.assertGreater(len(errors), 0)
        finally:
            tmp_path.unlink(missing_ok=True)

    def test_all_25_challenges_mapped_with_exact_names(self):
        """Verifica se os 25 desafios estão carregados e ordenados de Alpha a Zenith."""
        challenges = self.catalog.load_challenges(force_reload=True)
        self.assertEqual(len(challenges), 25, "O catálogo deve conter exatamente 25 desafios.")

        expected_names = [
            "Alpha", "Bravo", "Charlie", "Delta", "Echo",
            "Foxtrot", "Ghost", "Hunter", "Inferno", "Joker",
            "Knight", "Lynx", "Mantis", "Nexus", "Oracle",
            "Phantom", "Raven", "Shadow", "Specter", "Titan",
            "Vector", "Viper", "Wraith", "Zero", "Zenith"
        ]

        for idx, expected_name in enumerate(expected_names, 1):
            ch, ch_idx = self.catalog.get_by_identifier(idx)
            self.assertIsNotNone(ch, f"Desafio #{idx} não encontrado.")
            self.assertEqual(ch_idx, idx)
            self.assertEqual(ch["name"], expected_name, f"Desafio #{idx} deveria ter o nome '{expected_name}' mas tem '{ch['name']}'")


if __name__ == "__main__":
    unittest.main()
