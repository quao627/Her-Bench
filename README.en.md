# Her-Bench

[中文](README.md) · **English**

A task set, a runtime, and a reference implementation for evaluating live watch-along agents.
The setting is someone playing a game blind or opening an unfamiliar tool for the first time,
with an agent watching the same screen and helping when help is wanted. Scoring runs on two
separate axes: whether the answer is right (rubric points hit, citations real, no spoilers,
hint level respected), and whether this was the moment to speak at all (did the utterance land
in the annotated window, how many extra utterances were there). The two axes are reported
separately rather than folded into one number.

Design draft (Chinese): <https://quao627.github.io/Her-Bench/design-v0.4.html>

## What exists today

The task set covers 8 videos, 19.3 hours in total:

| container | length | query tasks | anchored proactive | content |
|---|---|---|---|---|
| `hff-p1` | 4.1h | 12 | 6 | Human Fall Flat, first blind playthrough |
| `portal-e01` | 2.7h | 11 | 4 | Portal, full blind playthrough |
| `mc-e01` | 2.4h | 11 | 4 | Minecraft, blind, no wiki |
| `rust-e01` | 3.8h | 10 | 4 | Rust live coding |
| `blender-e01` | 5.0h | 11 | 4 | First time using Blender |
| `blender-e02` | 0.2h | 6 | 3 | One week of self-taught Blender, recapped |
| `slendytubbies-e01` | 0.3h | 8 | 3 | Horror game, first blind playthrough |
| `stanleyparable-e01` | 0.8h | 15 | 7 | Narrative game, strictest spoiler rules |

- **84 query tasks**. The streamer asks out loud. Each task carries the question as spoken,
  the visible range (`context_window_sec`), a hint level, a rubric point list, a spoiler
  blocklist, and whether a citation is mandatory.
- **35 anchored proactive tasks** plus **16 pure proactive tasks**. Nobody asks anything;
  these test whether the agent decides to speak at the right moment on its own. The pure
  proactive set is mined from transcripts by a script and then verified against frames.
  Another 10 candidates were dropped because nothing was visible on screen.
- **Supporting material**: 39 reference documents (wiki and guide snapshots, each with a real
  source URL), 234 timeline thumbnails, 84 TTS clips of the questions. Videos are not in the
  repo; a script downloads them from the manifests.

## What the reference agent does

The agent has two halves. The Realtime API side stays connected in the browser, hears audio,
sees one frame every 5 seconds, and does the talking. The codex CLI side runs as a local HTTP
service that reads reference documents and searches the web. All judgment happens on the
talking side; codex only answers the question handed to it.

- **Self-check.** The Realtime API never speaks on its own, so every 5 seconds the browser
  sends a text-only response (inaudible to the user) that forces a call to the `decide` tool,
  returning four fields: speak or not, what to say, what to look up, and whether the lookup
  needs a frame. When it decides not to speak, nothing is heard, because that turn's modality
  is text only.
- **Three lookup channels.** `/answer` is triggered by the task file, `/lookup` is called by
  the agent itself when the streamer asks something, and `/research` runs when nobody has
  asked anything and codex picks its own question from the last ten frames. The first two use
  the foreground codex session, the last two use the background one, and `codex exec resume`
  keeps successive lookups in the same container connected.
- **The streamer takes priority.** As soon as voice activity is detected, background requests
  are aborted and the codex subprocess is killed; measured round trip is 0.8 seconds.
- **Deadlines.** 40 seconds foreground, 90 seconds background, 120 seconds for anchored tasks.
  On timeout the backend returns a sentence the agent can use directly instead of an error.
- **Independent judging.** `bench/judge.py` is a separate model and a separate call that shares
  no context with the agent. It runs automatically after each task.

## How to run it

```bash
cd demo
python3 bench/fetch_videos.py                  # download videos per manifest (needs yt-dlp + ffmpeg)
python3 server.py                              # dashboard → http://localhost:8080
python3 agent/agent_live.py                    # agent backend → :8787 (separate terminal, codex login first)
```

Open the dashboard, switch containers from the top left, and look for the ◆/◇ markers on the
timeline, which are task anchors. Playing past an anchor triggers a task, and the right-hand
panel shows every backend call with its full input and output, including the exact prompt codex
received. For voice, put a platform key in `demo/.env` (`OPENAI_API_KEY=sk-...`, a different
account from the ChatGPT login codex uses), restart `server.py`, and click 🎙 Live in the top
right. Everything else still works without Live; answers are read out by browser TTS instead.

Task authoring commands, endpoint signatures, and every tunable default are in
[`demo/README.en.md`](demo/README.en.md). File-by-file responsibilities and key function names
are in [`demo/CODEMAP.en.md`](demo/CODEMAP.en.md).

## Repository layout

```
demo/
  agent/       agent backend under test (717 lines); the decision half is app/agent.js (641 lines)
  bench/       download videos, parse transcripts, mine proactive tasks, generate TTS, judge
  server.py    dashboard entry point: static files plus the token and judging APIs
  app/         dashboard front end: main view and pure proactive view
  data/        tasks, reference snapshots, thumbnails, TTS clips
docs/          design drafts v0.1 through v0.4, published from here via GitHub Pages
live/          side experiment: a weak agent playing Pokemon directly, as a contrast to watching
```

## Videos are not in the repo

`demo/media/` and `videos/` are both in `.gitignore`, because of size and because the footage
is not ours. After cloning you have the tasks, reference documents, thumbnails, and transcripts;
the videos are one command away, since each container manifest records which video it uses and
where the file belongs:

```bash
cd demo && python3 bench/fetch_videos.py        # --check reports status only; you can also pass container ids
```

`demo/.env` is also excluded; it holds the OpenAI key.

## Not done yet

- The rule-based metrics (`window_hit`, `time_diff`, `over_trigger`) are recorded in the UI but
  are not yet an offline script.
- Query tasks are still written into JSON by hand with an agent's help. There is no authoring
  script for them; proactive tasks have `bench/mine_proactive.py`.
- In HTTP mode without Live, proactive tasks still fire at the start of the response window.
  Letting the agent choose the moment itself only works on the Live path.
- `transcript_excerpt` is empty for now and will be filled in after ASR runs.
