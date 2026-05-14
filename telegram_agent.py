import os
import time
from typing import Any

import requests
from dotenv import load_dotenv

from content_pipeline import AUDIO_FILE_TYPES, decode_text_file, transcribe_audio_bytes
from conversation_agent import ConversationContentAgent


load_dotenv()

TELEGRAM_MAX_MESSAGE_CHARS = 3900
TEXT_FILE_TYPES = {"txt", "md"}

HELP_MESSAGE = """
Sou o agente Pipeline de Conteudo.

Envia-me uma unica fonte e eu devolvo automaticamente:
- blog post
- post de LinkedIn
- thread para Twitter/X
- secao de newsletter

Podes enviar:
- texto numa mensagem
- ficheiro .txt ou .md
- nota de voz ou ficheiro audio

Comandos:
/start - ver esta ajuda
/help - ver esta ajuda
/ping - testar se o agente esta ativo
""".strip()


class TelegramContentAgent:
    def __init__(self, telegram_token: str):
        self.telegram_token = telegram_token
        self.api_url = f"https://api.telegram.org/bot{telegram_token}"
        self.telegram_session = requests.Session()
        self.content_agent = ConversationContentAgent()

    def request(
        self,
        method: str,
        payload: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        timeout: int = 60,
    ) -> dict[str, Any]:
        response = self.telegram_session.post(
            f"{self.api_url}/{method}",
            data=payload,
            files=files,
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
        if not data.get("ok"):
            raise RuntimeError(f"Erro Telegram em {method}: {data}")
        return data

    def send_message(self, chat_id: int, text: str) -> None:
        self.request(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": text,
                "disable_web_page_preview": True,
            },
        )

    def send_long_message(self, chat_id: int, text: str) -> None:
        remaining = text.strip()
        while remaining:
            chunk = remaining[:TELEGRAM_MAX_MESSAGE_CHARS]
            split_at = chunk.rfind("\n\n")
            if split_at > 1000 and len(remaining) > TELEGRAM_MAX_MESSAGE_CHARS:
                chunk = chunk[:split_at]

            self.send_message(chat_id, chunk.strip())
            remaining = remaining[len(chunk) :].strip()

    def send_document(self, chat_id: int, filename: str, content: str) -> None:
        files = {
            "document": (
                filename,
                content.encode("utf-8"),
                "text/markdown",
            )
        }
        self.request(
            "sendDocument",
            {
                "chat_id": chat_id,
                "caption": "Outputs completos em Markdown.",
            },
            files=files,
        )

    def get_updates(self, offset: int | None) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {
            "timeout": 30,
            "allowed_updates": '["message"]',
        }
        if offset is not None:
            payload["offset"] = offset

        return self.request("getUpdates", payload=payload, timeout=35)["result"]

    def download_telegram_file(self, file_id: str) -> tuple[str, bytes]:
        file_data = self.request("getFile", {"file_id": file_id})["result"]
        file_path = file_data["file_path"]
        url = f"https://api.telegram.org/file/bot{self.telegram_token}/{file_path}"
        response = self.telegram_session.get(url, timeout=60)
        response.raise_for_status()
        return os.path.basename(file_path), response.content

    def extract_text_source(self, message: dict[str, Any]) -> tuple[str, str] | None:
        text = message.get("text", "").strip()
        if text and not text.startswith("/"):
            return text, "mensagem de texto no Telegram"

        document = message.get("document")
        if document:
            file_name = document.get("file_name", "documento")
            extension = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
            downloaded_name, file_content = self.download_telegram_file(document["file_id"])

            if extension in TEXT_FILE_TYPES:
                return decode_text_file(file_content), f"ficheiro: {file_name}"

            if extension in AUDIO_FILE_TYPES:
                transcription = transcribe_audio_bytes(
                    self.content_agent.client,
                    downloaded_name or file_name,
                    file_content,
                )
                return transcription, f"audio: {file_name}"

            raise ValueError("Formato de ficheiro nao suportado. Envia .txt, .md ou audio.")

        voice = message.get("voice")
        if voice:
            file_name, file_content = self.download_telegram_file(voice["file_id"])
            transcription = transcribe_audio_bytes(
                self.content_agent.client,
                file_name or "voice.ogg",
                file_content,
            )
            return transcription, "nota de voz no Telegram"

        audio = message.get("audio")
        if audio:
            original_name = audio.get("file_name", "audio")
            file_name, file_content = self.download_telegram_file(audio["file_id"])
            transcription = transcribe_audio_bytes(
                self.content_agent.client,
                file_name or original_name,
                file_content,
            )
            return transcription, f"audio: {original_name}"

        return None

    def handle_command(self, chat_id: int, text: str) -> bool:
        command = text.split(maxsplit=1)[0].lower()
        if command in {"/start", "/help"}:
            self.send_message(chat_id, HELP_MESSAGE)
            return True
        if command == "/ping":
            self.send_message(chat_id, "Agente ativo.")
            return True
        return False

    def handle_message(self, message: dict[str, Any]) -> None:
        chat_id = message["chat"]["id"]
        text = message.get("text", "").strip()

        if text.startswith("/") and self.handle_command(chat_id, text):
            return

        try:
            source = self.extract_text_source(message)
            if source is None:
                self.send_message(
                    chat_id,
                    "Envia uma mensagem de texto, um ficheiro .txt/.md ou uma nota de voz.",
                )
                return

            source_text, source_description = source
            if not source_text.strip():
                self.send_message(chat_id, "A fonte recebida ficou vazia.")
                return

            self.send_message(
                chat_id,
                "Fonte recebida. Vou extrair factos e gerar os formatos.",
            )

            output = self.content_agent.process_text(
                source_text,
                source_description,
            )
            for title, content in self.content_agent.build_response_messages(output):
                self.send_long_message(chat_id, f"{title}\n\n{content}")

            self.send_document(chat_id, "content_pipeline_outputs.md", output.markdown)
            self.send_message(chat_id, "Pipeline concluida.")

        except Exception as error:
            self.send_message(chat_id, f"Ocorreu um erro: {error}")

    def handle_update(self, update: dict[str, Any]) -> None:
        message = update.get("message")
        if message:
            self.handle_message(message)

    def run(self) -> None:
        offset = None
        print("Agente Telegram ativo. Usa Ctrl+C para parar.")

        while True:
            try:
                updates = self.get_updates(offset)
                for update in updates:
                    offset = update["update_id"] + 1
                    self.handle_update(update)
            except KeyboardInterrupt:
                print("Agente Telegram parado.")
                break
            except Exception as error:
                print(f"Erro no ciclo do agente: {error}")
                time.sleep(5)


def main() -> None:
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not telegram_token:
        raise RuntimeError("A variavel TELEGRAM_BOT_TOKEN nao foi encontrada no .env.")

    agent = TelegramContentAgent(telegram_token)
    agent.run()


if __name__ == "__main__":
    main()
