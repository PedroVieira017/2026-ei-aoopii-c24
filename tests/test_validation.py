import unittest

from validation import (
    build_validation_checks,
    count_sentences,
    count_words,
    has_markdown_markers,
    has_thread_numbering,
    newsletter_needs_repair,
)


class ValidationTests(unittest.TestCase):
    def test_count_words_and_sentences(self):
        text = "A sala abriu hoje. Participaram 12 alunos."

        self.assertEqual(count_words(text), 7)
        self.assertEqual(count_sentences(text), 2)

    def test_detects_markdown_markers(self):
        self.assertTrue(has_markdown_markers("**Titulo**\nTexto"))
        self.assertTrue(has_markdown_markers("- ponto"))
        self.assertFalse(has_markdown_markers("Titulo\nTexto simples"))

    def test_thread_numbering(self):
        valid_lines = ["1/3 Primeiro tweet", "2/3 Segundo tweet", "3/3 Terceiro tweet"]
        invalid_lines = ["Primeiro tweet", "2/3 Segundo tweet"]
        invalid_total = ["1/4 Primeiro tweet", "2/4 Segundo tweet", "3/4 Terceiro tweet"]
        invalid_sequence = [
            "1/3 Primeiro tweet",
            "3/3 Segundo tweet",
            "2/3 Terceiro tweet",
        ]

        self.assertTrue(has_thread_numbering(valid_lines))
        self.assertFalse(has_thread_numbering(invalid_lines))
        self.assertFalse(has_thread_numbering(invalid_total))
        self.assertFalse(has_thread_numbering(invalid_sequence))

    def test_newsletter_repair_rules(self):
        valid_newsletter = "Titulo curto\nTexto direto com menos de sessenta palavras."
        long_body = "Titulo\n" + "palavra " * 61

        self.assertFalse(newsletter_needs_repair(valid_newsletter))
        self.assertTrue(newsletter_needs_repair(long_body))

    def test_build_validation_checks_for_tweet_thread(self):
        text = "1/3 Primeiro ponto.\n2/3 Segundo ponto.\n3/3 Terceiro ponto."
        validation = build_validation_checks("tweet_thread", text)
        messages = {check["message"]: check["ok"] for check in validation["checks"]}

        self.assertTrue(messages["Thread com 3 a 6 tweets."])
        self.assertTrue(messages["Thread numerada no formato 1/n."])


if __name__ == "__main__":
    unittest.main()
