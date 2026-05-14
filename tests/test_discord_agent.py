import unittest

from discord_agent import (
    get_extension,
    strip_bot_mentions,
    strip_pipeline_command,
)


class DiscordAgentTests(unittest.TestCase):
    def test_get_extension_normalizes_filename(self):
        self.assertEqual(get_extension("FONTE.TXT"), "txt")
        self.assertEqual(get_extension("nota.investigacao.md"), "md")
        self.assertEqual(get_extension("audio.webm"), "webm")
        self.assertEqual(get_extension("sem_extensao"), "")

    def test_strip_pipeline_command(self):
        self.assertEqual(
            strip_pipeline_command("!pipeline Texto fonte"),
            "Texto fonte",
        )
        self.assertEqual(
            strip_pipeline_command("!PIPELINE Texto fonte"),
            "Texto fonte",
        )
        self.assertEqual(strip_pipeline_command("Texto livre"), "Texto livre")

    def test_strip_bot_mentions(self):
        self.assertEqual(
            strip_bot_mentions("<@12345> Texto fonte", 12345),
            "Texto fonte",
        )
        self.assertEqual(
            strip_bot_mentions("<@!12345> Texto fonte", 12345),
            "Texto fonte",
        )


if __name__ == "__main__":
    unittest.main()
