"""Hangman game engine. No dependency on Flask or any UI."""

MAX_INCORRECT = 6


class InvalidGuessError(ValueError):
    """Guess is malformed or was already made."""


class GameOverError(Exception):
    """Guess made after the game already ended."""


class HangmanGame:
    def __init__(self, word, max_incorrect=MAX_INCORRECT):
        word = word.strip().lower()
        if not word.isalpha() or not word.isascii():
            raise ValueError(f"Invalid word: {word!r}")
        self._word = word
        self.max_incorrect = max_incorrect
        self.guessed_letters = []
        self.incorrect_letters = []

    @property
    def remaining_guesses(self):
        return self.max_incorrect - len(self.incorrect_letters)

    @property
    def pattern(self):
        return " ".join(c if c in self.guessed_letters else "_" for c in self._word)

    @property
    def status(self):
        if all(c in self.guessed_letters for c in self._word):
            return "won"
        if self.remaining_guesses <= 0:
            return "lost"
        return "playing"

    def guess(self, letter):
        if self.status != "playing":
            raise GameOverError("Game is already over")
        if not isinstance(letter, str):
            raise InvalidGuessError("Guess must be a single letter")
        letter = letter.strip().lower()
        if len(letter) != 1 or not letter.isalpha() or not letter.isascii():
            raise InvalidGuessError("Guess must be a single letter a-z")
        if letter in self.guessed_letters:
            raise InvalidGuessError(f"Letter '{letter}' was already guessed")
        self.guessed_letters.append(letter)
        if letter not in self._word:
            self.incorrect_letters.append(letter)
        return letter in self._word

    def to_state(self):
        """Client-safe state. The word is included only after the game ends."""
        state = {
            "pattern": self.pattern,
            "guessed_letters": list(self.guessed_letters),
            "incorrect_letters": list(self.incorrect_letters),
            "remaining_guesses": self.remaining_guesses,
            "status": self.status,
        }
        if state["status"] != "playing":
            state["word"] = self._word
        return state
