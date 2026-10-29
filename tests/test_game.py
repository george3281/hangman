import unittest

from game import GameOverError, HangmanGame, InvalidGuessError


class HangmanGameTests(unittest.TestCase):
    def setUp(self):
        self.game = HangmanGame("eagle")

    def test_initial_state(self):
        state = self.game.to_state()
        self.assertEqual(state["pattern"], "_ _ _ _ _")
        self.assertEqual(state["remaining_guesses"], 6)
        self.assertEqual(state["status"], "playing")
        self.assertNotIn("word", state)

    def test_correct_guess_reveals_all_positions(self):
        self.assertTrue(self.game.guess("e"))
        self.assertEqual(self.game.pattern, "e _ _ _ e")
        self.assertEqual(self.game.remaining_guesses, 6)

    def test_incorrect_guess_costs_a_life(self):
        self.assertFalse(self.game.guess("z"))
        self.assertEqual(self.game.remaining_guesses, 5)
        self.assertEqual(self.game.incorrect_letters, ["z"])

    def test_guess_is_case_insensitive(self):
        self.game.guess("E")
        self.assertEqual(self.game.guessed_letters, ["e"])

    def test_duplicate_guess_rejected_without_state_change(self):
        self.game.guess("z")
        with self.assertRaises(InvalidGuessError):
            self.game.guess("z")
        self.assertEqual(self.game.remaining_guesses, 5)
        self.assertEqual(self.game.guessed_letters, ["z"])

    def test_invalid_guesses_rejected(self):
        for bad in ["", "ee", "1", "?", " ", "é", None, 5]:
            with self.subTest(bad=bad), self.assertRaises(InvalidGuessError):
                self.game.guess(bad)
        self.assertEqual(self.game.guessed_letters, [])

    def test_win(self):
        for letter in "eagl":
            self.game.guess(letter)
        state = self.game.to_state()
        self.assertEqual(state["status"], "won")
        self.assertEqual(state["word"], "eagle")

    def test_loss(self):
        for letter in "zxqwvu":
            self.game.guess(letter)
        state = self.game.to_state()
        self.assertEqual(state["status"], "lost")
        self.assertEqual(state["remaining_guesses"], 0)
        self.assertEqual(state["word"], "eagle")

    def test_no_guesses_after_game_over(self):
        for letter in "eagl":
            self.game.guess(letter)
        with self.assertRaises(GameOverError):
            self.game.guess("z")

    def test_word_hidden_while_playing(self):
        for letter in "eazxq":
            self.game.guess(letter)
        state = self.game.to_state()
        self.assertEqual(state["status"], "playing")
        self.assertNotIn("word", state)
        self.assertNotIn("eagle", str(state))

    def test_rejects_invalid_word(self):
        for bad in ["", "two words", "abc1"]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                HangmanGame(bad)


if __name__ == "__main__":
    unittest.main()
