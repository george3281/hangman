// Headless-Chrome play-through: drives the real page with key presses and
// checks the DOM after each guess. Needs Node 22+, Chrome, and a running server.
// Usage: node tests/browser_e2e.mjs [http://localhost:5000/]
// Set CHROME=/path/to/chrome if Chrome is not in the default macOS location.
import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { tmpdir } from "node:os";

const url = process.argv[2] || "http://localhost:5000/";
const chrome = spawn(
  process.env.CHROME || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  ["--headless=new", "--remote-debugging-port=9333", `--user-data-dir=${tmpdir()}/hangman-e2e`, "about:blank"],
);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

try {
  let targets;
  for (let i = 0; i < 50 && !targets; i++) {
    targets = await fetch("http://127.0.0.1:9333/json").then((r) => r.json()).catch(() => sleep(200));
  }
  const ws = new WebSocket(targets.find((t) => t.type === "page").webSocketDebuggerUrl);
  await new Promise((r) => (ws.onopen = r));

  let id = 0;
  const pending = {};
  const requests = [];
  ws.onmessage = (m) => {
    const d = JSON.parse(m.data);
    if (pending[d.id]) pending[d.id](d.result);
    if (d.method === "Network.requestWillBeSent" && d.params.request.url.includes("/api/")) {
      requests.push(`${d.params.request.method} ${new URL(d.params.request.url).pathname}`);
    }
  };
  const send = (method, params = {}) =>
    new Promise((r) => { pending[++id] = r; ws.send(JSON.stringify({ id, method, params })); });
  const evaluate = async (expression) =>
    (await send("Runtime.evaluate", { expression, returnByValue: true })).result.value;
  const press = async (key, wait = 150) => {
    await send("Input.dispatchKeyEvent", { type: "keyDown", key, text: key });
    await send("Input.dispatchKeyEvent", { type: "keyUp", key });
    await sleep(wait);
  };
  const ui = () => evaluate(`({
    pattern: pattern.textContent,
    remaining: Number(remaining.textContent),
    message: message.textContent,
    parts: document.querySelectorAll("#gallows .shown").length,
    status: state.status,
    hasWord: "word" in state,
  })`);

  await send("Network.enable");
  await send("Page.navigate", { url });
  await sleep(1500);

  let s = await ui();
  assert.equal(s.status, "playing");
  assert.equal(s.remaining, 6);
  assert.equal(s.parts, 0);
  assert.equal(s.hasWord, false, "word must not reach the browser during play");

  // Guess until the game ends; check the page after each guess.
  for (const key of "etaoinshrdlucmfwypvbgkjqxz") {
    const before = s;
    await press(key);
    s = await ui();
    assert.equal(s.parts, 6 - s.remaining, "one body part per wrong guess");
    assert.ok(s.remaining <= before.remaining);
    if (s.status !== "playing") break;
    assert.equal(s.hasWord, false);
  }
  assert.ok(["won", "lost"].includes(s.status));
  assert.match(s.message, s.status === "won" ? /You won/ : /You lost/);
  assert.equal(await evaluate("[...keyboard.children].every(b => b.disabled)"), true);

  const guessesSent = requests.filter((r) => r.endsWith("/guess")).length;
  await press("e");
  assert.equal(requests.filter((r) => r.endsWith("/guess")).length, guessesSent, "no guesses after game over");

  await evaluate(`document.querySelector("#new-game button").click()`);
  await sleep(800);
  s = await ui();
  assert.equal(s.status, "playing");
  assert.equal(s.remaining, 6);
  assert.equal(s.message, "");

  // Fast typing over a slow network (like a hosted server) must not drop letters.
  await send("Network.emulateNetworkConditions", {
    offline: false, latency: 200, downloadThroughput: -1, uploadThroughput: -1,
  });
  for (const key of "xyz") await press(key, 0);
  await sleep(2000);
  assert.deepEqual(await evaluate("state.guessed_letters"), ["x", "y", "z"]);

  console.log(`browser e2e OK (${requests.length} API requests)`);
  ws.close();
} finally {
  chrome.kill();
}
