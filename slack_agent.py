import html
import os
import re
from typing import Any

import requests
from dotenv import load_dotenv

from content_pipeline import AUDIO_FILE_TYPES, decode_text_file, transcribe_audio_bytes
from conversation_agent import ConversationContentAgent


load_dotenv()

SLACK_MAX_MESSAGE_CHARS = 3500
TEXT_FILE_TYPES = {"txt", "md"}
PIPELINE_COMMAND = "!pipeline"

HELP_MESSAGE = """
Sou o agente Pipeline de Conteudo.

Como usar no Slack:
- Em mensagem privada: envia uma fonte de texto diretamente.
- Num canal: menciona o bot com a fonte, ou escreve !pipeline seguido da fonte.
- Tambem podes anexar um ficheiro .txt/.md ou audio, desde que o bot tenha acesso ao ficheiro.
- Se configurares o slash command, podes usar /pipeline <texto>.

Comandos:
!help - ver esta ajuda
!ping - testar se o agente esta ativo
!pipeline <texto> - gerar os formatos a partir de uma fonte
/pipeline <texto> - alternativa por slash command, se configurada no Slack
""".strip()


def get_extension(filename: str) -> str:
    if "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower()


def strip_pipeline_command(content: str) -> str:
    stripped = content.strip()
    if stripped.lower().startswith(PIPELINE_COMMAND):
        return stripped[len(PIPELINE_COMMAND) :].strip()
    return stripped


def strip_bot_mentions(content: str, bot_user_id: str | None = None) -> str:
    cleaned = content
    if bot_user_id:
        cleaned = cleaned.replace(f"<@{bot_user_id}>", "")
    cleaned = re.sub(r"<@[A-Z0-9]+(?:\|[^>]+)?>", "", cleaned)
    return cleaned.strip()


def clean_slack_text(content: str, bot_user_id: str | None = None) -> str:
    cleaned = html.unescape(content or "")
    cleaned = strip_pipeline_command(cleaned)
    cleaned = strip_bot_mentions(cleaned, bot_user_id)
    return cleaned.strip()


def is_bot_message(event: dict[str, Any]) -> bool:
    return bool(event.get("bot_id")) or event.get("subtype") in {
        "bot_message",
        "message_changed",
        "message_deleted",
    }


def should_process_message_event(
    event: dict[str, Any], bot_user_id: str | None = None
) -> bool:
    if is_bot_message(event):
        return False

    text = (event.get("text") or "").strip()
    channel = event.get("channel") or ""
    channel_type = event.get("channel_type")

    if channel_type == "im" or channel.startswith("D"):
        return True

    if text.lower().startswith(PIPELINE_COMMAND):
        return True

    if bot_user_id and f"<@{bot_user_id}>" in text:
        return True

    return False


class SlackContentAgent:
    def __init__(
        self,
        bot_token: str,
        content_agent: ConversationContentAgent | None = None,
        http_session: requests.Session | None = None,
    ):
        self.bot_token = bot_token
        self.content_agent = content_agent or ConversationContentAgent()
        self.http_session = http_session or requests.Session()

    def download_slack_file(self, file_info: dict[str, Any]) -> tuple[str, bytes]:
        filename = (
            file_info.get("name")
            or file_info.get("title")
            or file_info.get("id")
            or "ficheiro"
        )
        file_url = file_info.get("url_private_download") or file_info.get("url_private")
        if not file_url:
            raise ValueError("O ficheiro Slack nao tem URL privado para download.")

        response = self.http_session.get(
            file_url,
            headers={"Authorization": f"Bearer {self.bot_token}"},
            timeout=60,
        )
        response.raise_for_status()
        return filename, response.content

    def extract_source(
        self, event: dict[str, Any], bot_user_id: str | None = None
    ) -> tuple[str, str] | None:
        files = event.get("files") or []
        if files:
            filename, file_content = self.download_slack_file(files[0])
            extension = get_extension(filename)

            if extension in TEXT_FILE_TYPES:
                return decode_text_file(file_content), f"ficheiro Slack: {filename}"

            if extension in AUDIO_FILE_TYPES:
                transcription = transcribe_audio_bytes(
                    self.content_agent.client,
                    filename,
                    file_content,
                )
                return transcription, f"audio Slack: {filename}"

            raise ValueError("Formato nao suportado. Envia texto, .txt, .md ou audio.")

        text = clean_slack_text(event.get("text", ""), bot_user_id)
        if text:
            return text, "mensagem Slack"

        return None

    def send_long_message(
        self,
        client: Any,
        channel_id: str,
        text: str,
        thread_ts: str | None = None,
    ) -> None:
        remaining = text.strip()
        while remaining:
            chunk = remaining[:SLACK_MAX_MESSAGE_CHARS]
            split_at = chunk.rfind("\n\n")
            if split_at > 900 and len(remaining) > SLACK_MAX_MESSAGE_CHARS:
                chunk = chunk[:split_at]

            payload = {
                "channel": channel_id,
                "text": chunk.strip(),
            }
            if thread_ts:
                payload["thread_ts"] = thread_ts

            client.chat_postMessage(**payload)
            remaining = remaining[len(chunk) :].strip()

    def post_message(
        self,
        client: Any,
        channel_id: str,
        text: str,
        thread_ts: str | None = None,
    ) -> None:
        payload = {
            "channel": channel_id,
            "text": text,
        }
        if thread_ts:
            payload["thread_ts"] = thread_ts
        client.chat_postMessage(**payload)

    def send_markdown_file(
        self,
        client: Any,
        channel_id: str,
        markdown: str,
        thread_ts: str | None = None,
    ) -> None:
        payload = {
            "channel": channel_id,
            "filename": "content_pipeline_outputs.md",
            "title": "content_pipeline_outputs.md",
            "content": markdown,
            "initial_comment": "Outputs completos em Markdown.",
        }
        if thread_ts:
            payload["thread_ts"] = thread_ts

        try:
            client.files_upload_v2(**payload)
        except Exception:
            self.send_long_message(
                client,
                channel_id,
                "Nao consegui anexar o Markdown. Segue o conteudo completo:\n\n"
                + markdown,
                thread_ts,
            )

    def send_pipeline_output(
        self,
        client: Any,
        channel_id: str,
        source_text: str,
        source_description: str,
        thread_ts: str | None = None,
    ) -> None:
        self.post_message(
            client,
            channel_id,
            "Fonte recebida. Vou extrair factos, gerar 4 formatos e enviar o Markdown final.",
            thread_ts,
        )

        output = self.content_agent.process_text(source_text, source_description)
        for title, content in self.content_agent.build_response_messages(output):
            self.send_long_message(client, channel_id, f"{title}\n\n{content}", thread_ts)

        self.send_markdown_file(client, channel_id, output.markdown, thread_ts)
        self.post_message(client, channel_id, "Pipeline concluida.", thread_ts)

    def handle_message_event(
        self,
        event: dict[str, Any],
        client: Any,
        bot_user_id: str | None = None,
    ) -> None:
        channel_id = event["channel"]
        thread_ts = event.get("thread_ts") or event.get("ts")
        command = clean_slack_text(event.get("text", ""), bot_user_id).lower()

        if command in {"!help", "help"}:
            self.post_message(client, channel_id, HELP_MESSAGE, thread_ts)
            return

        if command in {"!ping", "ping"}:
            self.post_message(client, channel_id, "Agente ativo.", thread_ts)
            return

        try:
            source = self.extract_source(event, bot_user_id)
            if source is None:
                self.post_message(
                    client,
                    channel_id,
                    "Envia uma fonte de texto, um ficheiro .txt/.md ou audio.",
                    thread_ts,
                )
                return

            source_text, source_description = source
            self.send_pipeline_output(
                client,
                channel_id,
                source_text,
                source_description,
                thread_ts,
            )
        except Exception as error:
            self.post_message(client, channel_id, f"Ocorreu um erro: {error}", thread_ts)

    def handle_slash_pipeline(self, body: dict[str, Any], client: Any) -> None:
        channel_id = body["channel_id"]
        source_text = (body.get("text") or "").strip()

        if source_text.lower() in {"help", "-h", "--help"}:
            self.post_message(client, channel_id, HELP_MESSAGE)
            return

        if source_text.lower() == "ping":
            self.post_message(client, channel_id, "Agente ativo.")
            return

        if not source_text:
            self.post_message(
                client,
                channel_id,
                "Usa /pipeline seguido da fonte de conteudo.",
            )
            return

        try:
            self.send_pipeline_output(
                client,
                channel_id,
                source_text,
                "comando /pipeline no Slack",
            )
        except Exception as error:
            self.post_message(client, channel_id, f"Ocorreu um erro: {error}")


def build_slack_app(bot_token: str):
    from slack_bolt import App

    app = App(token=bot_token)
    agent = SlackContentAgent(bot_token)
    bot_user_id: str | None = None

    def get_bot_user_id(client: Any) -> str | None:
        nonlocal bot_user_id
        if bot_user_id is None:
            bot_user_id = client.auth_test()["user_id"]
        return bot_user_id

    @app.command("/pipeline")
    def handle_pipeline_command(ack, body, client):
        ack("Fonte recebida. Vou processar o pedido.")
        agent.handle_slash_pipeline(body, client)

    @app.event("app_mention")
    def handle_app_mention(event, client):
        agent.handle_message_event(event, client, get_bot_user_id(client))

    @app.event("message")
    def handle_message(event, client):
        user_id = get_bot_user_id(client)
        if not should_process_message_event(event, user_id):
            return
        agent.handle_message_event(event, client, user_id)

    return app


def main() -> None:
    bot_token = os.getenv("SLACK_BOT_TOKEN")
    app_token = os.getenv("SLACK_APP_TOKEN")
    if not bot_token:
        raise RuntimeError("A variavel SLACK_BOT_TOKEN nao foi encontrada no .env.")
    if not app_token:
        raise RuntimeError("A variavel SLACK_APP_TOKEN nao foi encontrada no .env.")

    from slack_bolt.adapter.socket_mode import SocketModeHandler

    app = build_slack_app(bot_token)
    print("Agente Slack ativo. Usa Ctrl+C para parar.")
    SocketModeHandler(app, app_token).start()


if __name__ == "__main__":
    main()
