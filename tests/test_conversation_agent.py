import unittest
from unittest.mock import patch

from conversation_agent import AgentOutput, ConversationContentAgent


def fake_pipeline_output():
    return {
        "facts": "- Facto principal",
        "results": {
            "blog": {"text": "Blog final"},
            "linkedin": {"text": "LinkedIn final"},
            "tweet_thread": {"text": "1/3 Um\n2/3 Dois\n3/3 Tres"},
            "newsletter": {"text": "Titulo\nTexto curto."},
        },
    }


class ConversationAgentTests(unittest.TestCase):
    def test_process_text_runs_pipeline_and_builds_markdown(self):
        client = object()

        with patch(
            "conversation_agent.run_content_pipeline",
            return_value=fake_pipeline_output(),
        ) as run_pipeline:
            agent = ConversationContentAgent(client=client)
            output = agent.process_text("Fonte original", "canal de teste")

        run_pipeline.assert_called_once_with(client, "Fonte original")
        self.assertEqual(output.source_description, "canal de teste")
        self.assertEqual(output.facts, "- Facto principal")
        self.assertIn("Blog final", output.markdown)
        self.assertIn("LinkedIn final", output.markdown)

    def test_process_text_rejects_empty_source_before_pipeline(self):
        agent = ConversationContentAgent(client=object())

        with patch("conversation_agent.run_content_pipeline") as run_pipeline:
            with self.assertRaises(ValueError):
                agent.process_text("   ")

        run_pipeline.assert_not_called()

    def test_build_response_messages_preserves_platform_order(self):
        agent = ConversationContentAgent(client=object())
        output = AgentOutput(
            source_description="teste",
            source_text="Fonte",
            facts="- Facto",
            markdown="# Export",
            results={
                "blog": {"text": "Blog"},
                "linkedin": {"text": "LinkedIn"},
                "tweet_thread": {"text": "Thread"},
                "newsletter": {"text": "Newsletter"},
            },
        )

        messages = agent.build_response_messages(output)

        self.assertEqual(
            [title for title, _ in messages],
            [
                "Factos extraidos",
                "Blog Post",
                "LinkedIn Post",
                "Tweet Thread",
                "Newsletter Section",
            ],
        )

    def test_process_audio_transcribes_before_pipeline(self):
        agent = ConversationContentAgent(client=object())

        with patch(
            "conversation_agent.transcribe_audio_bytes",
            return_value="Texto transcrito",
        ) as transcribe:
            with patch(
                "conversation_agent.run_content_pipeline",
                return_value=fake_pipeline_output(),
            ) as run_pipeline:
                output = agent.process_audio_file("memo.wav", b"audio")

        transcribe.assert_called_once_with(agent.client, "memo.wav", b"audio")
        run_pipeline.assert_called_once_with(agent.client, "Texto transcrito")
        self.assertEqual(output.source_description, "audio: memo.wav")


if __name__ == "__main__":
    unittest.main()
