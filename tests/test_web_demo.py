import unittest
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import patch

from web_demo import app, get_extension, output_to_payload


class WebDemoTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_index_loads(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Content Pipeline Agent", response.data)

    def test_examples_endpoint_returns_demo_inputs(self):
        response = self.client.get("/api/examples")
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(data["examples"]), 3)
        self.assertIn("filename", data["examples"][0])
        self.assertIn("content", data["examples"][0])

    def test_generate_requires_input(self):
        with patch("web_demo.get_agent") as get_agent:
            response = self.client.post("/api/generate", data={})
        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", data)
        get_agent.assert_not_called()

    def test_generate_rejects_unsupported_file_before_llm_client(self):
        with patch("web_demo.get_agent") as get_agent:
            response = self.client.post(
                "/api/generate",
                data={"source_file": (BytesIO(b"conteudo"), "imagem.png")},
                content_type="multipart/form-data",
            )
        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertIn("Formato nao suportado", data["error"])
        get_agent.assert_not_called()

    def test_get_extension_normalizes_filename(self):
        self.assertEqual(get_extension("MEMO.MD"), "md")
        self.assertEqual(get_extension("audio.voice.mp3"), "mp3")
        self.assertEqual(get_extension("sem_extensao"), "")

    def test_output_to_payload_adds_validation(self):
        output = SimpleNamespace(
            source_description="teste",
            source_text="Fonte",
            facts="- Facto",
            markdown="# Export",
            results={
                "blog": {"text": "Titulo\nTexto factual."},
                "linkedin": {"text": "Texto factual.\n\nOutro facto."},
                "tweet_thread": {
                    "text": "1/3 Primeiro ponto.\n2/3 Segundo ponto.\n3/3 Terceiro ponto."
                },
                "newsletter": {"text": "Titulo\nTexto curto."},
            },
        )

        payload = output_to_payload(output)

        self.assertEqual(payload["source_description"], "teste")
        self.assertEqual(payload["markdown"], "# Export")
        self.assertIn("validation", payload["outputs"]["tweet_thread"])


if __name__ == "__main__":
    unittest.main()
