import tempfile
import unittest
from pathlib import Path

from word_manager import DIFFICULTIES, InvalidDifficultyError, WordManager, load_words


class LoadWordsTests(unittest.TestCase):
    def test_filters_normalizes_and_dedupes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "w.txt"
            path.write_text("Apple\napple\n\n  pear \nice-cream\nabc1\ncafé\n")
            self.assertEqual(load_words(path), ["apple", "pear"])


class WordManagerTests(unittest.TestCase):
    def setUp(self):
        self.manager = WordManager()

    def test_real_lists_load_and_are_clean(self):
        for difficulty in DIFFICULTIES:
            words = self.manager.words(difficulty)
            self.assertTrue(words, difficulty)
            self.assertEqual(len(words), len(set(words)))
            self.assertTrue(all(w.isalpha() and w.islower() for w in words))

    def test_random_word_comes_from_requested_list(self):
        for difficulty in DIFFICULTIES:
            for _ in range(20):
                self.assertIn(
                    self.manager.random_word(difficulty), self.manager.words(difficulty)
                )

    def test_invalid_difficulty(self):
        for bad in ["", "EASY", "expert", None]:
            with self.subTest(bad=bad), self.assertRaises(InvalidDifficultyError):
                self.manager.random_word(bad)

    def test_empty_list_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            for d in DIFFICULTIES:
                (Path(tmp) / f"{d}.txt").write_text("word\n" if d != "hard" else "\n")
            with self.assertRaises(ValueError):
                WordManager(tmp)


if __name__ == "__main__":
    unittest.main()
