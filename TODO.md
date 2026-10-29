# TODO - Web-Based Hangman (Reduced Scope)

Implementation roadmap for the CSE 4095 web Hangman assignment.

The authoritative system requirements are in `Specification.md`. This plan
covers only the parts of that specification required for this assignment:
the game engine, word management, Flask REST server, browser client,
testing, and cloud deployment.

## Implementation Rules

- Implement one phase at a time and test it before moving on.
- Keep the REST API shapes defined in `Specification.md`.
- Keep the game engine independent from Flask and the browser UI.
- The server is authoritative; the browser contains no game logic.
- Never expose the hidden word while a game's status is `playing`.
- Add tests with each phase.

## Design Decisions (left open by the specification)

| Question | Decision |
|---|---|
| Duplicate guesses | Rejected with HTTP 400; state unchanged |
| Letter case | Words and guesses normalized to lowercase |
| Invalid input | Empty, multi-character, and non-letter guesses rejected with 400 |
| Pattern format | Characters separated by spaces, e.g. `_ e _ _ e` |
| Answer field | `word`, present only when status is `won` or `lost` |
| Guesses after game end | Rejected with HTTP 409 |
| `GET /api/games/{id}` body | Same shape as the guess response, plus `game_id` and `difficulty` |
| Game storage | In memory; single Gunicorn worker so all requests see the same games |

---

## Phase 1 - Project Skeleton and Core Game Engine

- [x] Create the project directory structure.
- [x] Add `words/easy.txt`, `words/medium.txt`, `words/hard.txt`.
- [x] Create `game.py` with a `HangmanGame` class.
- [x] Store the hidden word internally.
- [x] Track guessed letters and incorrect letters.
- [x] Track the maximum number of incorrect guesses (6).
- [x] Validate single-letter guesses and reject duplicates.
- [x] Generate the masked word pattern.
- [x] Detect wins and losses (`playing`, `won`, `lost`).
- [x] Reject guesses after the game ends.
- [x] Return a client-safe state dictionary; reveal the word only after the game ends.
- [x] Add unit tests for the game engine.

**Done when:** the engine is fully tested without a web server.

## Phase 2 - Word Management

- [x] Create `word_manager.py`.
- [x] Load Easy, Medium, and Hard word lists.
- [x] Keep only alphabetic words; normalize case; drop duplicates.
- [x] Select a random word by difficulty.
- [x] Raise a clear error for an invalid difficulty.
- [x] Add tests for loading and selection.

**Done when:** a random word can be requested from every difficulty and bad difficulties are rejected.

## Phase 3 - Flask Server and REST API

- [x] Create `server.py` with Flask.
- [x] Store active games in memory, keyed by a unique game ID.
- [x] `POST /api/games` - create a game (201).
- [x] `GET /api/games/{game_id}` - current state (200).
- [x] `POST /api/games/{game_id}/guess` - submit a letter (200).
- [x] Validate difficulty and guess input; reject malformed JSON (400).
- [x] Return 404 for unknown game IDs and 409 for guesses on finished games.
- [x] Return JSON for every response, including errors.
- [x] Never include the word while status is `playing`.
- [x] Add API tests.

**Done when:** a full game can be played with `curl` alone.

## Phase 4 - Browser Client

- [x] Serve `static/index.html`, `static/style.css`, `static/app.js` from Flask at `/`.
- [x] Difficulty selector and New Game button.
- [x] Display masked word, guessed letters, incorrect letters, remaining guesses.
- [x] On-screen alphabet keyboard plus physical keyboard input.
- [x] Disable already-guessed letters and the keyboard after the game ends.
- [x] Use `fetch()` for every server interaction.
- [x] SVG Hangman drawing that adds a body part per incorrect guess.
- [x] Win/loss message showing the revealed word.
- [x] Start another game without reloading the page.
- [x] Usable at desktop and phone widths.

**Done when:** a full game can be played in the browser and the JavaScript never holds the hidden word during play.

## Phase 5 - Testing and Debugging

- [ ] Games start at all three difficulties.
- [ ] Correct and incorrect guesses.
- [ ] Repeated and invalid guesses.
- [ ] Win and loss paths.
- [ ] New game after a finished game.
- [ ] Invalid API requests (bad JSON, bad difficulty, unknown ID).
- [ ] Hidden word not exposed during play.
- [ ] Static page and assets served correctly.
- [ ] Manual browser test: play several games, inspect a guess request in Chrome DevTools.

**Done when:** `python -m unittest` passes and manual play works locally.

## Phase 6 - Deployment

- [ ] Add `requirements.txt` with Flask and Gunicorn.
- [ ] Add `render.yaml` (one worker, binds to `$PORT`).
- [ ] Write `README.md` with local run instructions and API docs.
- [ ] Push to GitHub.
- [ ] Create the Render web service from the repository.
- [ ] Play a complete game on the public HTTPS URL.

**Done when:** the public URL serves the game and a full game can be played there.

---

## Out of Scope for This Assignment

These parts of `Specification.md` are not implemented:

- Human terminal client (`terminal_client.py`)
- Reference and dictionary-based bots (`bot_examples/`)
- Evaluation mode and `/api/evaluation/*` endpoints
- Official scoring
- Leaderboard
- Evaluation integrity / anti-cheating safeguards
- Logging and replay endpoints
- Persistent storage, accounts, tournaments, multiplayer
