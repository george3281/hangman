# Hangman

A web-based Hangman game with a Flask REST server and an HTML/CSS/JavaScript
browser client. CSE 4095 - Agentic Programming.

**Live app:** https://hangman-3967.onrender.com/

The server holds every game and decides the result of each guess. The browser
only sends letters with `fetch()` and draws the JSON state the server returns.
The hidden word is sent to the browser only after a game is won or lost.

## How a guess works

1. The player clicks a letter or presses a key. `app.js` sends
   `POST /api/games/{game_id}/guess` with `{"letter": "e"}` using `fetch()`.
2. Flask (`server.py`) finds the game by ID, checks the request body, and
   calls `HangmanGame.guess()` in `game.py`.
3. The engine records the letter, decides hit or miss, and updates the
   pattern, remaining guesses, and status.
4. Flask returns the new state as JSON (200), or an `{"error": ...}` with
   400/404/409.
5. `app.js` redraws the pattern, letter lists, keyboard, gallows, and message
   from that JSON. It never decides hits or misses itself.

You can watch steps 1 and 4 in Chrome DevTools > Network > Fetch/XHR.

## Project layout

```
game.py            Game engine (no Flask dependency)
word_manager.py    Loads words/*.txt, picks random words by difficulty
server.py          Flask app: REST API + serves static/
static/            index.html, style.css, app.js (browser client)
words/             easy.txt, medium.txt, hard.txt
tests/             unittest suites + headless-Chrome play-through
render.yaml        Render deployment blueprint
Specification.md   Original project specification
TODO.md            Phased plan, revised to this assignment's scope
```

## Run locally

Requires Python 3.10+.

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python server.py
```

Open http://127.0.0.1:5000/ and play. Click letters or type them on your
keyboard; pick a difficulty and press **New Game** to start over.

To run the production server the same way Render does:

```bash
gunicorn --bind 0.0.0.0:5000 --workers 1 server:app
```

## Tests

```bash
python -m unittest -v                        # engine, word lists, REST API
node tests/browser_e2e.mjs http://127.0.0.1:5000/   # needs Node 22+, Chrome, running server
```

## REST API

All bodies are JSON. Errors return `{"error": "..."}`.

| Method | Endpoint | Body | Success | Errors |
|---|---|---|---|---|
| POST | `/api/games` | `{"difficulty": "easy" \| "medium" \| "hard"}` (default `medium`) | 201 | 400 bad JSON or difficulty |
| GET | `/api/games/{game_id}` | - | 200 | 404 unknown game |
| POST | `/api/games/{game_id}/guess` | `{"letter": "e"}` | 200 | 400 invalid or repeated letter, 404 unknown game, 409 game already over |

Game state (returned by all three endpoints):

```json
{
  "game_id": "b88e763fca5e",
  "difficulty": "medium",
  "pattern": "_ e _ _ e",
  "guessed_letters": ["e", "z"],
  "incorrect_letters": ["z"],
  "remaining_guesses": 5,
  "status": "playing"
}
```

`status` is `playing`, `won`, or `lost`. When it is `won` or `lost`, the
response also includes `"word"`.

Example with curl:

```bash
curl -s -X POST http://127.0.0.1:5000/api/games \
  -H 'Content-Type: application/json' -d '{"difficulty":"easy"}'
curl -s -X POST http://127.0.0.1:5000/api/games/GAME_ID/guess \
  -H 'Content-Type: application/json' -d '{"letter":"e"}'
curl -s http://127.0.0.1:5000/api/games/GAME_ID
```

## Rules

- Six incorrect guesses allowed.
- One letter (a-z) per guess, case-insensitive.
- Repeated and invalid guesses are rejected (400) and do not change the game.

## Deploy to Render

1. Push this repository to GitHub.
2. In Render, choose **New > Blueprint**, select the repository, and apply.
   `render.yaml` sets the build command (`pip install -r requirements.txt`)
   and start command (`gunicorn --bind 0.0.0.0:$PORT --workers 1 server:app`).
3. Open the `onrender.com` URL. Free instances sleep when idle, so the first
   load can take up to a minute.

## Known limitations

- Games live in server memory. They are lost when the service restarts, and
  Render's free tier restarts it after about 15 minutes idle. A player
  mid-game then gets "Game not found" and must press **New Game**.
- Because of in-memory storage, the server must run with one Gunicorn worker.
  Scaling out would need shared storage such as a database or Redis.
- Finished games are never deleted from memory. This is fine at class scale
  but would need cleanup for heavy traffic.
- After a loss, the word is shown in the message but the pattern's blanks are
  not filled in.
- `tests/browser_e2e.mjs` defaults to the macOS Chrome path; set `CHROME` on
  other systems.
- The word lists in `words/` are the course-provided lists.

## Scope

Terminal client, bots, evaluation mode, scoring, leaderboard, and replay from
`Specification.md` are out of scope for this assignment (see `TODO.md`).
