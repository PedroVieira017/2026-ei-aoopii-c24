import os
from io import BytesIO

import discord
from dotenv import load_dotenv

from content_pipeline import AUDIO_FILE_TYPES, decode_text_file, transcribe_audio_bytes
from conversation_agent import ConversationContentAgent


load_dotenv()

DISCORD_MAX_MESSAGE_CHARS = 1900
TEXT_FILE_TYPES = {"txt", "md"}
PIPELINE_COMMAND = "!pipeline"

HELP_MESSAGE = """
Sou o agente Pipeline de Conteudo.

Como usar:
- Em mensagem privada: envia uma fonte de texto diretamente.
- Num servidor: escreve !pipeline seguido da fonte.
- Tambem podes anexar um ficheiro .txt/.md ou audio.

Comandos:
!help - ver esta ajuda
!ping - testar se o agente esta ativo
!pipeline <texto> - gerar os formatos a partir de uma fonte
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


def strip_bot_mentions(content: str, bot_user_id: int) -> str:
    cleaned = content.replace(f"<@{bot_user_id}>", "")
    cleaned = cleaned.replace(f"<@!{bot_user_id}>", "")
    return cleaned.strip()


class DiscordContentAgent(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.content_agent = ConversationContentAgent()

    async def on_ready(self):
        print(f"Agente Discord ativo como {self.user}.")

    async def send_long_message(self, channel, text: str) -> None:
        remaining = text.strip()
        while remaining:
            chunk = remaining[:DISCORD_MAX_MESSAGE_CHARS]
            split_at = chunk.rfind("\n\n")
            if split_at > 600 and len(remaining) > DISCORD_MAX_MESSAGE_CHARS:
                chunk = chunk[:split_at]

            await channel.send(chunk.strip())
            remaining = remaining[len(chunk) :].strip()

    async def send_markdown_file(self, channel, markdown: str) -> None:
        file = discord.File(
            fp=BytesIO(markdown.encode("utf-8")),
            filename="content_pipeline_outputs.md",
        )
        await channel.send("Outputs completos em Markdown.", file=file)

    def should_process_message(self, message: discord.Message) -> bool:
        if message.guild is None:
            return True

        if message.content.strip().lower().startswith(PIPELINE_COMMAND):
            return True

        if self.user and self.user in message.mentions:
            return True

        return False

    def get_text_from_message(self, message: discord.Message) -> str:
        content = strip_pipeline_command(message.content)
        if self.user:
            content = strip_bot_mentions(content, self.user.id)
        return content.strip()

    async def extract_source(self, message: discord.Message) -> tuple[str, str] | None:
        if message.attachments:
            attachment = message.attachments[0]
            filename = attachment.filename or "ficheiro"
            extension = get_extension(filename)
            file_content = await attachment.read()

            if extension in TEXT_FILE_TYPES:
                return decode_text_file(file_content), f"ficheiro Discord: {filename}"

            if extension in AUDIO_FILE_TYPES:
                transcription = transcribe_audio_bytes(
                    self.content_agent.client,
                    filename,
                    file_content,
                )
                return transcription, f"audio Discord: {filename}"

            raise ValueError("Formato nao suportado. Envia texto, .txt, .md ou audio.")

        text = self.get_text_from_message(message)
        if text:
            return text, "mensagem Discord"

        return None

    async def handle_content_message(self, message: discord.Message) -> None:
        try:
            source = await self.extract_source(message)
            if source is None:
                await message.channel.send(
                    "Envia uma fonte de texto, um ficheiro .txt/.md ou audio."
                )
                return

            source_text, source_description = source
            await message.channel.send(
                "Fonte recebida. Vou extrair factos, gerar 4 formatos e enviar o Markdown final."
            )

            output = self.content_agent.process_text(source_text, source_description)
            for title, content in self.content_agent.build_response_messages(output):
                await self.send_long_message(message.channel, f"{title}\n\n{content}")

            await self.send_markdown_file(message.channel, output.markdown)
            await message.channel.send("Pipeline concluida.")
        except Exception as error:
            await message.channel.send(f"Ocorreu um erro: {error}")

    async def on_message(self, message: discord.Message):
        if self.user and message.author.id == self.user.id:
            return

        command = message.content.strip().lower()
        if command in {"!help", "/help"}:
            await message.channel.send(HELP_MESSAGE)
            return

        if command in {"!ping", "/ping"}:
            await message.channel.send("Agente ativo.")
            return

        if not self.should_process_message(message):
            return

        await self.handle_content_message(message)


def main() -> None:
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise RuntimeError("A variavel DISCORD_BOT_TOKEN nao foi encontrada no .env.")

    agent = DiscordContentAgent()
    agent.run(token)


if __name__ == "__main__":
    main()
