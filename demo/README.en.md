# Her-Bench Demo

[中文](README.md) · **English**

Two things live here: a dashboard that lays out the timeline, the tasks, the grading config, and
the input and output of every agent call; and a reference agent backend where the Realtime API
does the talking and the codex CLI does the lookups. A single HTTP endpoint connects them, so a
different backend can be plugged in.

```bash
cd demo
python3 bench/fetch_videos.py                   # download videos (first run; --check reports status only)
python3 server.py                               # dashboard → http://localhost:8080 (Chrome recommended)
python3 agent/agent_live.py                     # agent backend → :8787 (separate terminal, codex login first)
```

The code is in three parts: `agent/` is the agent under test, `bench/` handles data, task
authoring, and judging, and `server.py` with `app/index.html` is the dashboard. The agent's
decision logic in the browser sits in its own file, `app/agent.js`, loaded by the dashboard but
independent of it. For file-by-file responsibilities, see [`CODEMAP.en.md`](CODEMAP.en.md).

For voice, put a platform key in `demo/.env` (`OPENAI_API_KEY=sk-...`, note this is a different
account from the ChatGPT login codex uses), restart `server.py`, then click 🎙 Live in the top
right. The full flow also runs without Live; answers are read out by browser TTS instead.

## Material

There are 8 containers, switchable from the top-left dropdown, mixing long and short videos:

| container | length | type |
|---|---|---|
| `hff-p1` / `portal-e01` / `mc-e01` | 2.4h / 2.7h / 2.4h | game blind playthroughs (talkative, moderate, quiet) |
| `rust-e01` / `blender-e01` | 3.8h / 5.0h | live coding / first time with a tool |
| `blender-e02` | 9.4min | recap of a week of self-taught Blender, voiced afterwards |
| `slendytubbies-e01` | 20min | horror game, first blind playthrough |
| `stanleyparable-e01` | 46min | narrative game, first blind playthrough, strictest spoiler rules |

The last three are short videos with noticeably denser tasks:

| container | tasks | density | smallest anchor gap |
|---|---|---|---|
| `blender-e02` | 9 | 63s/task | 26s |
| `slendytubbies-e01` | 11 | 110s/task | 63s |
| `stanleyparable-e01` | 22 | 125s/task | 55s |
| the five long containers | 14-18 | 573-1211s/task | — |

When two anchors are less than 60 seconds apart, check that the tasks do not interfere: different
subjects, non-overlapping answers, and triggers that do not collide. The trigger part matters
because a query task pauses the video while waiting for an answer, while a proactive task has a
30 to 100 second response window.

## Running a whole container from the command line

Both task types have an offline runner, and neither waits out the video in real time.

```bash
python3 agent/agent_live.py                       # query tasks need it running
python3 bench/run_query.py portal-e01             # query tasks
python3 bench/run_proactive.py slendytubbies-e01  # pure proactive
```

Query tasks need no real-time behavior at all. Each one is "at this anchor the streamer asked
this, how do you answer", which has nothing to do with where playback happens to be. The runner
extracts the anchor frame, sends it with the task package to the agent backend, takes the answer,
and passes it to the judge. The 11 tasks in portal-e01 finish in 1.4 minutes, bounded by codex
taking 7 to 8 seconds per task.

Pure proactive has no audio and also does not need real time. One ffmpeg pass extracts the frames,
then the runner steps through them asking "speak now or not", with several segments in parallel.
A 20-minute video finishes in 50 seconds, 31 times faster than real time.

### Cold start and following along measure different things

`bench/run_query.py` runs each task on its own, with the agent holding nothing and looking everything up
from scratch. That measures whether it can answer from a cold start. The answers are scored
correctly, but latency comes out systematically high, because in the real setting the agent has
been watching all along and has already looked much of this up.

`bench/run_stream.py` follows the video from the beginning: one frame every 5 seconds throughout, and
every so often (in video time) the most recent frames go to the prefetch channel. When playback
reaches an anchor, the agent gets a look-back strip covering everything from the start up to that
moment, together with the notes it accumulated, and first checks whether that is enough to answer
directly. It looks something up only when it is not.

```bash
python3 bench/run_stream.py portal-e01 --limit 1300 --brief 120
```

The clock driving all of this is video time, not wall time, so the number of prefetches, the notes
on hand, and the frames seen all match real playback while execution stays fast.

The look-back strip is what makes this work. In the browser, every frame from the 5-second stream
stays in the context, so by any given moment the agent has seen everything since the beginning.
Offline it is not possible to resend hundreds of frames each time, so the strip samples backwards
on a logarithmic spacing, dense near the present and sparse further back, all the way to the
start. Without it, a question like "what is this device I just picked up" can only be guessed at
from the notes.

Three ways of running the same three tasks over the first 22 minutes of portal-e01:

| | cold start | following along, no strip | following along, with strip |
|---|---|---|---|
| rubric total | 9/9 | 6/9 | **9/9** |
| t01 | 7.6s · 3/3 | 3.3s · **1/3** | **3.6s · 3/3** |
| t02 | 5.7s · 3/3 | 9.0s · 3/3 | 9.4s · 3/3 |
| t11 | 7.9s · 3/3 | 2.0s · 2/3 | 8.9s · 3/3 |
| answered from what it had | 0/3 | 2/3 | 1/3 |

With notes but no strip it is faster and the answers get thinner, with t01 dropping to 1/3. Adding
the strip brings quality back to 9/9 while keeping the speed where it should be (t01 at 3.6
seconds against 7.6 for a cold start), and t11 flips from "answer from what I have" back to
"go look it up": with visual context it can tell whether it actually knows.

Watching continuously is not there to make the agent faster. It is what makes answering directly
a safe option.

## Two interfaces

| Entry point | What the agent gets | What it tests |
|---|---|---|
| `app/index.html` (main view) | frames plus audio (live audio or a TTS question) | answer quality and timing |
| `app/proactive.html` | frames only, no audio and no questions | timing |

The main view has two modes:

| Mode | Behavior |
|---|---|
| Browse | Free playback. Click the ◆/◇ markers on the timeline to inspect tasks and grading config; the agent stays quiet |
| Agent watch-along | Follows the timeline. With Live connected the video keeps playing and the agent talks as it watches; without Live the video pauses at each anchor and the task is POSTed to the backend. Dragging back re-arms the anchors |

## Pure proactive mode

A second interface that runs alongside the main one, at `app/proactive.html` or through the
「👁 纯 Proactive」 link in the top right of the main view.

The difference is that the agent only sees frames. It hears nothing and nobody asks it anything,
so when to speak and what to say are entirely its own calls.

```
python3 server.py                                  # same server, one more page at /app/proactive.html
open http://localhost:8080/app/proactive.html
```

### Where the tasks come from

```
python3 bench/mine_proactive.py <container_id> <path/to/en.vtt>
python3 bench/build_proactive_index.py
```

`bench/mine_proactive.py` runs in two stages:

1. Candidates from the transcript. Split by minute and feed to a model, looking for moments where
   he genuinely needs help: muttering a question, retrying the same spot, hunting for something he
   cannot find, misreading a rule, getting startled, or just pulling something off. Every candidate
   carries the words that led to that judgment, copied verbatim into `evidence`. This stage cannot
   see the video, so it only writes `look_for`: what should be visible if this is real.

2. Frame verification. Take eight frames inside the window, plus two leading frames, and ask a
   model looking only at those frames whether someone who cannot hear anything would notice that
   something is off. Only those survive. `visible` and `scene` are written in this stage, which
   keeps the task grounded in what is actually on screen. Rejected candidates go to
   `<id>.dropped.json`.

More candidates are dropped than kept, and that is deliberate. A moment that exists only in
complaints, with nothing visible on screen, is unanswerable for an agent that only has frames.

### What a task looks like

```jsonc
{
  "task_id": "slendytubbies-e01-p02",
  "type": "proactive",
  "window_sec": [361, 417],          // speaking inside this window counts as catching it
  "kind": "卡住出不去",
  "need": "他不知道自己该往哪走，环境太相似",
  "visible": "这几帧一直在很像的夜晚树林里来回转视角，前后没有出现新地点",
  "evidence": [                       // why the task exists; shown to the judge, hidden from the agent
    {"t": 361, "text": "where am I going I don't know everything looks so the same"}
  ],
  "grading": {
    "help_points": ["先选一个稳定策略：沿边走、认单一地标", "..."],
    "must_not_say": ["不要直接说最后一个收集物在哪"]
  }
}
```

### How it is scored

- Speaking inside the window counts as catching it. Only the first utterance in a window counts,
  and the delay is recorded.
- Anything said outside a window counts as extra and is tallied per occurrence.
- Once caught, the content is judged: check off `help_points` one by one, then look at spoilers,
  hint level, and whether it sounds like reading from a script.

Judging goes through `/api/judge`, the same path the main view uses: one separate model, one
separate call.

### Running it from the command line

```bash
python3 bench/run_proactive.py slendytubbies-e01
```

The browser path runs in real time: a video takes as long as the video. Pure proactive has no
audio, and what the agent receives is one frame every few seconds, so nothing has to follow real
time. Offline, one ffmpeg pass extracts all the frames, then the runner walks through video time
asking "speak now or not", with several segments in parallel. How much faster it gets depends on
the API rather than the length of the video.

A 20-minute Slendytubbies run finishes in 50 seconds, 31 times faster than real time.

| Flag | Default | Notes |
|---|---|---|
| `--tick N` | 8 | Seconds between checks. Smaller is finer grained and more expensive |
| `--workers N` | 4 | How many segments run in parallel. Segments track their own utterances, which is what allows the parallelism |
| `--limit N` | 0 | Only run the first N seconds, useful for a quick look |
| `--verbose` | | Print the decision at every step, to see why it stayed quiet |
| `--no-judge` | | Run without judging, to save money |

Each run writes a JSON file into `data/runs/`: when it spoke, which windows it caught, which it
missed, how many extra utterances there were, and the judge's result for each catch.

## Runtime: one decision point, three lookup channels

Watching along requires two things that pull against each other. Speaking in real time means
picking up the thread within a few hundred milliseconds. Looking things up means reading
documents and searching the web, which takes 10 to 40 seconds per call. One model cannot hold
both ends, so the work is split between two engines:

- The Realtime API stays connected in the browser, hears audio, sees one frame every 5 seconds,
  and does the talking. It is the only part that follows the stream continuously.
- The codex CLI runs a local HTTP service (`agent/agent_live.py`). It reads reference documents
  and searches the web, but hears nothing and holds no connection. It answers the question it is
  given and makes no judgments.

### Self-check

The Realtime API never speaks on its own. Adding items to the conversation does not trigger
generation; only an explicit `response.create`, or VAD deciding that someone finished talking,
will. So there has to be a periodic decision point, which is the self-check: every 5 seconds
(configurable), the browser requests a text-only response that the user cannot hear, and forces
a call to the `decide` tool.

```
decide(speak: bool, say: str, lookup: str, need_frame: bool)
```

When `speak` is true, a second voice response says it out loud. When the decision is not to
speak, nothing is heard at all, since that turn's modality is text only and the model could not
produce audio if it tried. When `lookup` is non-empty, the question goes to the background
channel and the result is added to the context as material.

Two things trigger a self-check: the 5-second timer, and the moment background material comes
back. Both share a 5-second minimum interval and a flag that suppresses a new check while one is
outstanding, so two checks never run at the same moment. Extra utterances carry the heaviest
penalty in scoring, so being a few seconds late beats speaking twice. After speaking there is a
20-second cooldown.

`tool_choice` has to be `'required'`. The named form `{type:'function', name:'decide'}` is
accepted by the API (a malformed shape is even rejected with an error), but it is not enforced,
and the model still returns prose. In that case the self-check runs entirely on the text
fallback, and the moment it answers in plain language, both `speak` and `lookup` are lost.
When the per-response `tools` list contains only the one tool that should be called,
`'required'` has the same effect as naming it, and it actually takes effect.

### Three lookup channels

The backend does one job: assemble the question, the reference documents selected for the current
progress, the hint level, and the spoiler rules into a prompt for codex, then return the text plus
one `SOURCES:` line. The three paths differ only in who asked the question.

| Channel | Question source | Who is waiting | codex session |
|---|---|---|---|
| `/answer` | The task file, on the non-Live path | The browser, which reads it out, so it is capped at 3 to 6 sentences | `fg` |
| `/lookup` | The streamer asked; Realtime calls the tool itself | Someone is waiting | `fg` |
| `/lookup {background}` | The agent asked during self-check | Nobody | `bg` |
| `/research` | Nobody asked; codex picks a question from the last ten frames | Nobody | `bg` |

`/research` is the prefetch channel and can be switched off in the settings panel. Every 30
seconds it hands codex the last ten frames from the ring buffer and lets it find something worth
verifying. This channel exists because in practice the front-end agent almost never asks for a
lookup on its own, the same problem that makes `must_cite` require a forced `tool_choice`:
conversational models will not admit uncertainty. Relying on self-check alone leaves the
background empty for long stretches.

Prefetching has two boundaries:

- It does not trigger a self-check. What comes back is only added to the context. Feeding material
  on a timer is fine, but the decision of when to speak has to stay with the agent, otherwise the
  timing being measured is ours rather than its own. Only a lookup the agent asked for triggers
  the next self-check when it returns.
- It does not prefetch full solutions. The first version came back with a complete walkthrough,
  which is easy to leak once it sits in the front-end agent's context. It now writes directional
  content only, and nothing about levels or plot beyond the current progress.

### The streamer takes priority

When the streamer starts talking, whatever is running in the background has to stop. The earliest
available signal is `input_audio_buffer.speech_started`, which arrives more than ten seconds
before the agent would call a tool. The browser aborts the request and `POST /cancel` tells the
backend to end the codex subprocess, since aborting the request alone leaves the process holding
CPU and that session. The killed session is discarded and the next call starts a clean one. During
this time there is no self-check and no prefetching. Measured time from cancel to return is 0.8
seconds.

### Deadlines

codex will not stop on its own for taking too long, so the limit has to come from outside. On
timeout the backend returns a sentence the agent can use directly ("couldn't find this, don't wait
on it, go with what you know") rather than an error.

| Path | Deadline | Why |
|---|---|---|
| `/lookup` foreground | 40s | The model already said it would look it up; longer than that is dead air |
| `/lookup` background · `/research` | 90s | Nobody is waiting, but it holds the bg session and the front end's "looking it up" flag |
| `/answer` | 120s | Judging looks at real latency, so leave room |

The front end has slightly looser limits of its own (50s foreground, 100s background, via
`AbortController`). If the backend hangs completely, the "looking it up" flag would otherwise never
clear and no further lookups could be sent.

### Session resume and progress display

Starting a fresh `codex exec` every time means anything looked up five minutes ago is unavailable
and has to be searched again. Using `codex exec resume <thread_id>` continues the previous turn,
with two sessions per container (`fg` and `bg`). They are separate because one session can only be
resumed serially, and sharing would put a lookup someone is waiting for behind a background call.

The `--json` event stream shows what codex is reading and searching. The backend collects it by
`call_id` and the front end polls `/progress`, showing it on the pending card in the backend panel.
Only progress is sent, never a partial answer: the final answer arrives in one piece from codex
anyway, and a half-formed fact in the voice engine's context could be read out loud.

## Endpoint reference

Agent backend, default `http://localhost:8787`:

```
POST /answer    { task_id, type, question, anchor_sec, hint_level, context_window_sec,
                  container_id, frame_jpeg_base64, transcript_excerpt,
                  context_frames?,      // proactive only: [{offset_sec, b64}, ...]
                  recent_research?, call_id? }
             →  { text, citations[], latency_ms, debug_prompt }

POST /lookup    { query, game, container_id, current_sec,
                  background?,          // true = asked during self-check, nobody waiting, bg session
                  frames?, call_id? }   // frames only when it asked to see the screen
             →  { text, citations[], latency_ms, timeout?, cancelled? }

POST /research  { game, container_id, current_sec, frames, call_id? }
             →  { noteworthy, question, text, citations[], latency_ms }

POST /cancel    { container_id, kind }        → { cancelled }
POST /progress  { call_id }                   → { lines[], done }
```

Dashboard service (`server.py`, default `:8080`):

```
POST /api/realtime/token  { container_id }  → { value, model }   // ephemeral key; the browser never sees the real one
POST /api/judge           { task, run, frame_jpeg_base64? }      // independent judging, see below
GET  /...                 static files with HTTP Range (needed for video seeking)
```

`context_frames` is only used by proactive tasks. It is a timeline of 448px thumbnails taken 240,
180, 120, 60, and 20 seconds before the anchor. Without it proactive tasks are close to
unanswerable, because every signal for whether to speak is temporal and a single anchor frame does
not carry it: the frame where Human Fall Flat is completed shows the character falling through
clouds, which is nearly identical to falling out of the map. Across 5 proactive tasks, a single
frame got 1 right, and the timeline got all 5.

## Settings and defaults

| Setting | Default | Notes |
|---|---|---|
| Audio condition | 🗣 synthetic speech | The streamer's audio is muted for the model, and only the pre-generated TTS question plays at the anchor. The 📺 live-audio condition is kept as a control, since live audio triggers VAD constantly and timing can no longer be measured cleanly |
| Self-check | 5s | Reactions like celebration or surprise are worthless 8 seconds late, so the granularity is 5 seconds. The cost is re-reading a growing context on every check |
| Prefetch | on · 30s | Turn it off entirely to run the "fully on its own" control |
| Frames | 5s | The image stream fed to Realtime; the same frame is stored in the ring buffer (384px, kept 5 minutes) |
| Frame sampling | 10 for prefetch / 6 for lookups | Prefetch samples at `0/-5/-10/-15/-20/-30/-45/-60/-120/-240` seconds, dense near the present. One frame per minute shows no dynamics: finishing something, falling, or circling in place all happen within the last ten-odd seconds |
| Voice | `cedar` | Change with `OPENAI_REALTIME_VOICE` (`alloy/ash/ballad/coral/echo/sage/shimmer/verse/marin/cedar`); the model with `OPENAI_REALTIME_MODEL` |

The Realtime API has no direct parameters for pace or tone, only text guidance in the
instructions, and switching voice is more effective than rewording. codex is a text-only coding
agent with no voice mode, so the voice layer has to go through Realtime.

## Authoring and judging tools

```bash
python3 bench/fetch_videos.py [--check] [container_id ...]     # download videos into media/ per manifest
python3 bench/mine_proactive.py <container_id> <en.vtt>        # mine proactive tasks from transcript and frames
python3 bench/build_proactive_index.py                         # refresh the proactive view's index
python3 bench/gen_tts.py                                       # generate question audio for query tasks
python3 bench/vtt.py <file.vtt> [n]                            # turn YouTube auto-captions into {t,text}
```

Judging (`bench/judge.py`) is an LLM call kept entirely apart from the watch-along agent: it does
not touch codex or the Realtime session and shares no context, taking only the task and what the
agent actually said to a text-only model. Letting one session both answer and grade itself is
grading your own work. The front end scores each task automatically once it finishes, through
`POST /api/judge`, and the model can be overridden with `HERBENCH_JUDGE_MODEL`.

### Authoring rule: anchors must be checked against frames

Setting anchors from the transcript alone produces errors, and not rarely. A full frame-by-frame
check while authoring three new videos turned up two kinds of real mistakes:

- Reversed meaning. The caption `"there's a pop-up in front of your face, but nothing happens"`
  reads like a UI popup that did nothing, but the frame shows a jump scare with the antagonist in
  his face, which had the whole task pointing the wrong way.
- Timestamp drift. Converting `mm:ss` to `anchor_sec` by hand put nearly half the anchors 25 to 50
  seconds away from the actual footage.

So every candidate anchor gets a frame extracted with `ffmpeg -ss <t> -frames:v 1` and checked by
eye, and `scene` has to describe what is on that frame. One more thing that is easy to miss: the
anchor has to fall at the moment the evidence is already visible. `hff-p1-t18` (finishing the
Water level) was originally set at the moment of falling, but finishing is only visible from the
scene change, so the anchor moved 14 seconds later to where the new scene appears, which is what
made the task answerable.

## Directory

```
demo/
  CODEMAP.md                what each file does and where the key functions are

  agent/                    ① the agent under test
    agent_live.py             backend: /answer /lookup /research /cancel /progress
                              (the decision half is in app/agent.js, see CODEMAP)

  bench/                    ② data, task authoring, judging
    fetch_videos.py           download videos per container manifest
    vtt.py                    VTT transcript parsing
    mine_proactive.py         mine proactive tasks from transcript and frames
    build_proactive_index.py  build the proactive view's index
    gen_tts.py                question audio for the synthetic-speech condition
    judge.py                  independent judging, separate model and separate call

  server.py                 ③ dashboard entry: static files + /api/realtime/token + /api/judge
  app/agent.js                the agent's decision half: self-check, speak or not, what to look up
  app/index.html              main view: timeline, panels, judging, and the agent wiring
  app/proactive.html          pure proactive view

  data/containers/*.json    per container: video, chapters, tasks, grading, reference index
  data/proactive/*.json     proactive task set, including rejected candidates in .dropped.json
  data/resources/           reference snapshots (wiki and guide markdown)
  data/thumbs/              timeline thumbnails, one every 5 minutes
  data/tts/                 question audio for the synthetic-speech condition
  media/                    browser-compatible video (720p remux, not committed)
```

## Things that had to be learned the hard way

None of these were obvious in advance.

The named form of `tool_choice` is not enforced; see the self-check section above. This affected
more than the self-check: the `must_cite` rule that a task must be verified before answering had
been doing nothing at all.

Frame difference does not work as a speaking signal. The idea was that a large change means
progress and a long flat stretch means being stuck, which measurement did not support: Human Fall
Flat has a free camera, so the view drifts even when the character stands still, and 60 seconds of
being stuck produced a frame difference of 54.9 against 45.8 for an actual level transition. Frame
difference measures camera motion, not progress.

Tasks must not be sent to codex ahead of time. An early version sent the question 150 seconds
before the anchor, so the anchor hit a cache in about 4ms. That was not prediction; the dashboard
had read future task text, which breaks the `context_window_sec` contract and distorts every
latency metric.

Splitting the decision and the utterance into two turns leaves the second turn with no veto: once
`speak=true` is written, that turn will produce audio. An A/B run of 20 rounds per arm showed the
two-turn version speaking in 3 of 10 uneventful moments against 0 of 10 for the one-turn version
(which gets a "stay silent" tool to choose instead), with time to first audio 3.3 times faster
(448ms against 1473ms) and no audio leaking in 70 silent decisions. The data supports switching to
one turn, but silence would go from a structural guarantee to a behavioral one, so the switch has
not been made.

## Known simplifications (demo ≠ full harness)

- In HTTP mode without Live, proactive tasks still fire at the start of the response window and
  only receive `context_frames`. Letting the agent choose the moment and the lookup itself works
  only on the Live path, since HTTP mode has no persistent connection and cannot run periodic
  self-checks.
- `transcript_excerpt` is empty for now and will be filled in after ASR runs.
- Automatic judging is wired up, but the rule-based metrics (`window_hit`, `time_diff`,
  `over_trigger`) are not yet an offline script and are only recorded in the UI.
