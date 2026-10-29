import tempfile
import unittest
from pathlib import Path

from server import create_app
from word_manager import DIFFICULTIES, WordManager


class ServerTests(unittest.TestCase):
    def setUp(self):
        # Every list holds only "eagle" so outcomes are deterministic.
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        for d in DIFFICULTIES:
            (Path(tmp.name) / f"{d}.txt").write_text("eagle\n")
        self.client = create_app(WordManager(tmp.name)).test_client()

    def new_game(self, difficulty="easy"):
        res = self.client.post("/api/games", json={"difficulty": difficulty})
        self.assertEqual(res.status_code, 201)
        return res.get_json()

    def guess(self, game_id, letter):
        return self.client.post(f"/api/games/{game_id}/guess", json={"letter": letter})

    def test_create_game_all_difficulties(self):
        for d in DIFFICULTIES:
            data = self.new_game(d)
            self.assertEqual(data["difficulty"], d)
            self.assertEqual(data["pattern"], "_ _ _ _ _")
            self.assertEqual(data["remaining_guesses"], 6)
            self.assertEqual(data["status"], "playing")
            self.assertNotIn("word", data)

    def test_game_ids_unique_and_states_separate(self):
        a, b = self.new_game(), self.new_game()
        self.assertNotEqual(a["game_id"], b["game_id"])
        self.guess(a["game_id"], "z")
        b_state = self.client.get(f"/api/games/{b['game_id']}").get_json()
        self.assertEqual(b_state["remaining_guesses"], 6)

    def test_get_game(self):
        game = self.new_game()
        self.guess(game["game_id"], "e")
        res = self.client.get(f"/api/games/{game['game_id']}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.get_json()["pattern"], "e _ _ _ e")

    def test_correct_and_incorrect_guesses(self):
        gid = self.new_game()["game_id"]
        data = self.guess(gid, "e").get_json()
        self.assertEqual(data["pattern"], "e _ _ _ e")
        self.assertEqual(data["remaining_guesses"], 6)
        data = self.guess(gid, "Z").get_json()
        self.assertEqual(data["incorrect_letters"], ["z"])
        self.assertEqual(data["guessed_letters"], ["e", "z"])
        self.assertEqual(data["remaining_guesses"], 5)

    def test_repeated_and_invalid_guesses(self):
        gid = self.new_game()["game_id"]
        self.guess(gid, "z")
        for letter in ["z", "", "ab", "1", None]:
            with self.subTest(letter=letter):
                res = self.guess(gid, letter)
                self.assertEqual(res.status_code, 400)
                self.assertIn("error", res.get_json())
        state = self.client.get(f"/api/games/{gid}").get_json()
        self.assertEqual(state["guessed_letters"], ["z"])
        self.assertEqual(state["remaining_guesses"], 5)

    def test_win_reveals_word_and_blocks_more_guesses(self):
        gid = self.new_game()["game_id"]
        for letter in "eagl":
            data = self.guess(gid, letter).get_json()
        self.assertEqual(data["status"], "won")
        self.assertEqual(data["word"], "eagle")
        self.assertEqual(self.guess(gid, "z").status_code, 409)

    def test_loss_reveals_word(self):
        gid = self.new_game()["game_id"]
        for letter in "zxqwvu":
            data = self.guess(gid, letter).get_json()
        self.assertEqual(data["status"], "lost")
        self.assertEqual(data["remaining_guesses"], 0)
        self.assertEqual(data["word"], "eagle")
        self.assertEqual(self.guess(gid, "e").status_code, 409)

    def test_new_game_after_finished_game(self):
        gid = self.new_game()["game_id"]
        for letter in "eagl":
            self.guess(gid, letter)
        fresh = self.new_game()
        self.assertEqual(fresh["status"], "playing")
        self.assertEqual(fresh["guessed_letters"], [])

    def test_word_never_exposed_while_playing(self):
        gid = self.new_game()["game_id"]
        for letter in "eazxq":
            res = self.guess(gid, letter)
            self.assertNotIn(b"eagle", res.data)
        self.assertNotIn(b"eagle", self.client.get(f"/api/games/{gid}").data)

    def test_invalid_create_requests(self):
        cases = [
            {"json": {"difficulty": "expert"}},
            {"json": ["easy"]},
            {"data": "not json", "content_type": "application/json"},
            {},
        ]
        for kwargs in cases:
            with self.subTest(kwargs=kwargs):
                res = self.client.post("/api/games", **kwargs)
                self.assertEqual(res.status_code, 400)
                self.assertIn("error", res.get_json())

    def test_default_difficulty_is_medium(self):
        res = self.client.post("/api/games", json={})
        self.assertEqual(res.get_json()["difficulty"], "medium")

    def test_invalid_guess_requests(self):
        gid = self.new_game()["game_id"]
        self.assertEqual(self.client.post(f"/api/games/{gid}/guess", json={}).status_code, 400)
        res = self.client.post(f"/api/games/{gid}/guess", data="x", content_type="text/plain")
        self.assertEqual(res.status_code, 400)

    def test_unknown_game(self):
        self.assertEqual(self.client.get("/api/games/nope").status_code, 404)
        res = self.guess("nope", "e")
        self.assertEqual(res.status_code, 404)
        self.assertIn("error", res.get_json())

    def test_serves_browser_client(self):
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'<script src="app.js">', res.data)
        for asset in ["/app.js", "/style.css"]:
            with self.subTest(asset=asset):
                self.assertEqual(self.client.get(asset).status_code, 200)

    def test_browser_client_has_no_word_list(self):
        js = self.client.get("/app.js").data
        self.assertIn(b"fetch(", js)
        self.assertNotIn(b"eagle", js)
        self.assertNotIn(b"words/", js)

    def test_wrong_method_returns_json(self):
        res = self.client.delete("/api/games")
        self.assertEqual(res.status_code, 405)
        self.assertIn("error", res.get_json())


if __name__ == "__main__":
    unittest.main()
