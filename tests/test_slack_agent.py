import unittest

from slack_agent import (
    clean_slack_text,
    get_extension,
    should_process_message_event,
    strip_bot_mentions,
    strip_pipeline_command,
)


class SlackAgentTests(unittest.TestCase):
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
            strip_bot_mentions("<@U12345> Texto fonte", "U12345"),
            "Texto fonte",
        )
        self.assertEqual(
            strip_bot_mentions("<@U12345|bot> Texto fonte", "U12345"),
            "Texto fonte",
        )

    def test_clean_slack_text_removes_command_mentions_and_unescapes_entities(self):
        self.assertEqual(
            clean_slack_text("!pipeline <@U12345> A &amp; B", "U12345"),
            "A & B",
        )

    def test_should_process_direct_messages(self):
        event = {
            "channel": "D123",
            "channel_type": "im",
            "text": "Texto fonte",
        }

        self.assertTrue(should_process_message_event(event, "U999"))

    def test_should_process_channel_pipeline_command(self):
        event = {
            "channel": "C123",
            "channel_type": "channel",
            "text": "!pipeline Texto fonte",
        }

        self.assertTrue(should_process_message_event(event, "U999"))

    def test_should_process_channel_mention(self):
        event = {
            "channel": "C123",
            "channel_type": "channel",
            "text": "<@U999> Texto fonte",
        }

        self.assertTrue(should_process_message_event(event, "U999"))

    def test_should_ignore_bot_messages(self):
        event = {
            "channel": "C123",
            "channel_type": "channel",
            "text": "!pipeline Texto fonte",
            "subtype": "bot_message",
        }

        self.assertFalse(should_process_message_event(event, "U999"))


if __name__ == "__main__":
    unittest.main()
