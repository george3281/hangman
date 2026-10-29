"""Flask REST server for Hangman. Game state lives only on the server."""

import os
import secrets
import threading

from flask import Flask, jsonify, request

from game import GameOverError, HangmanGame, InvalidGuessError
from word_manager import DIFFICULTIES, InvalidDifficultyError, WordManager


def create_app(word_manager=None):
    app = Flask(__name__, static_folder="static", static_url_path="")
    words = word_manager or WordManager()
    # ponytail: in-memory dict, games vanish on restart and need one worker; use a DB to scale out
    games = {}
    lock = threading.Lock()

    def error(message, status):
        return jsonify({"error": message}), status

    def game_state(game_id, entry):
        return {"game_id": game_id, "difficulty": entry["difficulty"], **entry["game"].to_state()}

    def json_body():
        body = request.get_json(silent=True)
        return body if isinstance(body, dict) else None

    @app.get("/")
    def index():
        return app.send_static_file("index.html")

    @app.post("/api/games")
    def create_game():
        body = json_body()
        if body is None:
            return error("Request body must be a JSON object", 400)
        difficulty = body.get("difficulty", "medium")
        try:
            word = words.random_word(difficulty)
        except InvalidDifficultyError:
            return error(f"difficulty must be one of: {', '.join(DIFFICULTIES)}", 400)
        game_id = secrets.token_hex(6)
        entry = {"game": HangmanGame(word), "difficulty": difficulty}
        with lock:
            games[game_id] = entry
        return jsonify(game_state(game_id, entry)), 201

    @app.get("/api/games/<game_id>")
    def get_game(game_id):
        entry = games.get(game_id)
        if entry is None:
            return error("Game not found", 404)
        return jsonify(game_state(game_id, entry))

    @app.post("/api/games/<game_id>/guess")
    def guess(game_id):
        entry = games.get(game_id)
        if entry is None:
            return error("Game not found", 404)
        body = json_body()
        if body is None or "letter" not in body:
            return error('Request body must be a JSON object with a "letter" field', 400)
        with lock:
            try:
                entry["game"].guess(body["letter"])
            except InvalidGuessError as e:
                return error(str(e), 400)
            except GameOverError as e:
                return error(str(e), 409)
            return jsonify(game_state(game_id, entry))

    @app.errorhandler(404)
    def not_found(_):
        return error("Not found", 404)

    @app.errorhandler(405)
    def method_not_allowed(_):
        return error("Method not allowed", 405)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=True)
