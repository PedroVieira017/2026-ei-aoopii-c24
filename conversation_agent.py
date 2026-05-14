from dataclasses import dataclass

from openai import OpenAI

from content_pipeline import (
    OUTPUT_TITLES,
    build_markdown_export,
    create_client,
    decode_text_file,
    run_content_pipeline,
    transcribe_audio_bytes,
)


@dataclass
class AgentOutput:
    source_description: str
    source_text: str
    facts: str
    results: dict
    markdown: str


class ConversationContentAgent:
    def __init__(self, client: OpenAI | None = None):
        self.client = client or create_client()

    def process_text(
        self,
        source_text: str,
        source_description: str = "mensagem de texto",
    ) -> AgentOutput:
        if not source_text.strip():
            raise ValueError("A fonte recebida ficou vazia.")

        pipeline_output = run_content_pipeline(self.client, source_text)
        facts = pipeline_output["facts"]
        results = pipeline_output["results"]
        markdown = build_markdown_export(
            source_description,
            source_text,
            facts,
            results,
        )

        return AgentOutput(
            source_description=source_description,
            source_text=source_text,
            facts=facts,
            results=results,
            markdown=markdown,
        )

    def process_text_file(
        self,
        filename: str,
        file_content: bytes,
    ) -> AgentOutput:
        source_text = decode_text_file(file_content)
        return self.process_text(source_text, f"ficheiro: {filename}")

    def process_audio_file(
        self,
        filename: str,
        file_content: bytes,
        source_description: str | None = None,
    ) -> AgentOutput:
        source_text = transcribe_audio_bytes(self.client, filename, file_content)
        return self.process_text(source_text, source_description or f"audio: {filename}")

    def build_response_messages(self, output: AgentOutput) -> list[tuple[str, str]]:
        messages = [("Factos extraidos", output.facts)]
        for key, title in OUTPUT_TITLES.items():
            messages.append((title, output.results[key]["text"]))
        return messages
