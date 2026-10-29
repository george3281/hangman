"""Loads the difficulty word lists and picks random words."""

import random
from pathlib import Path

DIFFICULTIES = ("easy", "medium", "hard")
WORDS_DIR = Path(__file__).parent / "words"


class InvalidDifficultyError(ValueError):
    pass


def load_words(path):
    """Lowercased, alphabetic-only, de-duplicated words in file order."""
    words = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        word = line.strip().lower()
        if word.isalpha() and word.isascii():
            words[word] = None
    return list(words)


class WordManager:
    def __init__(self, words_dir=WORDS_DIR, rng=None):
        self._rng = rng or random.Random()
        self._lists = {d: load_words(Path(words_dir) / f"{d}.txt") for d in DIFFICULTIES}
        for difficulty, words in self._lists.items():
            if not words:
                raise ValueError(f"Word list for '{difficulty}' is empty")

    def words(self, difficulty):
        return list(self._lists[self._check(difficulty)])

    def random_word(self, difficulty):
        return self._rng.choice(self._lists[self._check(difficulty)])

    @staticmethod
    def _check(difficulty):
        if difficulty not in DIFFICULTIES:
            raise InvalidDifficultyError(
                f"Difficulty must be one of: {', '.join(DIFFICULTIES)}"
            )
        return difficulty
