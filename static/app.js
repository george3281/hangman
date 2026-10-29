// Browser client. Holds only the game id and the last state the server sent;
// every rule (hits, misses, win/loss) is decided by the Flask server.

const els = {
  form: document.getElementById("new-game"),
  difficulty: document.getElementById("difficulty"),
  pattern: document.getElementById("pattern"),
  remaining: document.getElementById("remaining"),
  guessed: document.getElementById("guessed"),
  incorrect: document.getElementById("incorrect"),
  message: document.getElementById("message"),
  keyboard: document.getElementById("keyboard"),
  parts: document.querySelectorAll("#gallows .body > *"),
};

let gameId = null;
let state = null;
let busy = false;

for (const letter of "abcdefghijklmnopqrstuvwxyz") {
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = letter;
  button.dataset.letter = letter;
  button.addEventListener("click", () => guess(letter));
  els.keyboard.append(button);
}

async function api(path, body) {
  const res = await fetch(path, {
    method: body ? "POST" : "GET",
    headers: body ? { "Content-Type": "application/json" } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
  return data;
}

async function newGame(event) {
  event?.preventDefault();
  try {
    state = await api("/api/games", { difficulty: els.difficulty.value });
    gameId = state.game_id;
    render();
  } catch (err) {
    showMessage(err.message, "error");
  }
}

async function guess(letter) {
  if (!state || state.status !== "playing" || busy) return;
  if (state.guessed_letters.includes(letter)) return;
  busy = true;
  try {
    state = await api(`/api/games/${gameId}/guess`, { letter });
    render();
  } catch (err) {
    showMessage(err.message, "error");
  } finally {
    busy = false;
  }
}

function render() {
  const { pattern, guessed_letters, incorrect_letters, remaining_guesses, status } = state;
  els.pattern.textContent = pattern;
  els.remaining.textContent = remaining_guesses;
  els.guessed.textContent = guessed_letters.join(" ") || "-";
  els.incorrect.textContent = incorrect_letters.join(" ") || "-";

  els.parts.forEach((part, i) => part.classList.toggle("shown", i < incorrect_letters.length));

  for (const button of els.keyboard.children) {
    const letter = button.dataset.letter;
    button.disabled = status !== "playing" || guessed_letters.includes(letter);
    button.classList.toggle("hit", guessed_letters.includes(letter) && !incorrect_letters.includes(letter));
    button.classList.toggle("miss", incorrect_letters.includes(letter));
  }

  if (status === "won") showMessage(`You won! The word was "${state.word}".`, "won");
  else if (status === "lost") showMessage(`You lost. The word was "${state.word}".`, "lost");
  else showMessage("");
}

function showMessage(text, kind = "") {
  els.message.textContent = text;
  els.message.className = `message ${kind}`;
}

document.addEventListener("keydown", (event) => {
  if (event.ctrlKey || event.metaKey || event.altKey) return;
  if (event.target instanceof HTMLSelectElement) return;
  const key = event.key.toLowerCase();
  if (/^[a-z]$/.test(key)) guess(key);
});

els.form.addEventListener("submit", newGame);
newGame();
