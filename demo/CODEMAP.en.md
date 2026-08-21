# Code map

[中文](CODEMAP.md) · **English**

The code splits into three parts: the agent under test, the bench that authors tasks and grades
answers, and the dashboard people look at. The anchors below are function names rather than line
numbers, since line numbers drift as the code changes (`grep -n <name> <file>`).

```
demo/
  agent/     the agent under test: the talking half and the lookup half
  bench/     data, task authoring, judging: turns videos into tasks and answers into scores
  server.py  dashboard entry point, serves static files and two APIs
  app/       front end. agent.js holds the agent's decision logic; index.html and proactive.html are the dashboard
  data/      material and task sets, shared by all three parts
```

The flow is: bench authors tasks, the dashboard feeds them to the agent and records what it said,
then bench grades the recording. The agent never sees how a task was written, and the judge never
gets any of the agent's context. Both boundaries are deliberate.

---

## 1. The agent

The agent is two engines connected by a single HTTP call. Every judgment happens on the talking
side; the lookup side only answers the question it was handed.

```
browser ──audio/frames──► Realtime API ──┬──► speaks out loud
                          (persistent)   │
                                         └──► HTTP ──► agent/agent_live.py ──► codex CLI
                                                       (stateless, reads docs and searches)
```

### Decisions: `app/agent.js`

This file contains declarations only, with no top-level side effects. Timers, button handlers,
and initialization all live in `app/index.html` and are started by the dashboard, so agent.js
loads first and both files share one global scope. The symbols it uses from the dashboard
(`$`, `video`, `C`, `liveLine`, `bcallStart`, `captureFrame`, and others) resolve at call time;
the file header lists them all.

| Step | Function | Notes |
|---|---|---|
| Periodic self-check | `selfCheck()` | Sends a text-only response every 5 seconds, inaudible to the user, with `tools:[DECIDE_TOOL]` and `tool_choice:'required'`. The named form `{type:'function', name:'decide'}` is accepted by the API but not enforced |
| Receiving the decision | `handleDecideCall()` | The decision comes back as a `decide` tool call, whose arguments the API validates against the schema |
| Acting on it | `applyDecision()` | Speak means one more voice response; look up means the background channel; if the background is busy the question is queued |
| Text fallback | `onSelfCheckText()` | If it answers in prose instead of calling the tool, parse what can be parsed and otherwise treat it as "don't speak" |
| Background lookups | `runBackgroundLookup()` / `runIdleResearch()` | The first runs the question the agent asked for; the second is timed prefetching |
| Yielding | `yieldBgToUser()` | When the streamer speaks, cancel the background request and have the backend end the subprocess |
| Frame buffer | `pushFrameBuf()` / `framesAround()` | One frame every 5 seconds (384px, kept for 5 minutes), sampled densely near the present and sparsely further back |
| Transport | `liveConnect()` / `handleLiveEvent()` / `handleToolCall()` | WebRTC connection, audio graph, event dispatch |

### Lookups: `agent/agent_live.py`

| Endpoint | Function | Where the question comes from | codex session |
|---|---|---|---|
| `/answer` | `answer()` | The task file, used on the non-Live path | `fg` |
| `/lookup` | `_handle_lookup()` | The streamer asked, or the agent asked during self-check (`background:true`) | `fg` / `bg` |
| `/research` | `_handle_research()` | Nobody asked; codex picks a question from the last ten frames | `bg` |
| `/cancel` | `cancel_run()` | Ends the running codex subprocess when the streamer speaks | — |
| `/progress` | inline in the router | Polled by the front end to show what codex is reading and searching | — |

Other places worth knowing: `run_codex()` starts the subprocess, parses the `--json` event
stream, resumes sessions, and enforces the watchdog timeout; `DEADLINES` holds the three limits
(40s foreground, 90s background, 120s for anchored tasks); `get_resource_docs()` decides which
reference documents go into the prompt based on current progress; the three prompt templates are
`PROMPT_TMPL`, `LOOKUP_TMPL`, and `RESEARCH_TMPL`.

---

## 2. bench: data, task authoring, judging

```bash
python3 bench/fetch_videos.py                    # download videos into demo/media/ per manifest
python3 bench/mine_proactive.py <cid> <en.vtt>   # mine proactive tasks
python3 bench/build_proactive_index.py           # refresh the proactive view's index
python3 bench/gen_tts.py                         # generate question audio for query tasks
python3 bench/run_query.py <cid>                 # run a container's query tasks offline
python3 bench/run_proactive.py <cid>             # run pure proactive offline
python3 bench/run_stream.py <cid>                # follow the video from the start, with look-back and prefetch
python3 bench/vtt.py <file.vtt> [n]              # inspect VTT parsing
```

### Data

`bench/fetch_videos.py` is driven entirely by the container manifests. Each manifest records
which video the container uses (`video.source_url`) and where the file belongs (`video.src`),
so downloading, naming, and placing happen in one step; `--check` reports status without
downloading. Videos stay out of the repo for size and licensing reasons, while tasks and
reference documents are committed. `bench/vtt.py` turns YouTube auto-captions into a
`{t, text}` sequence, which the first authoring step needs.

### Two kinds of tasks

| | query | proactive |
|---|---|---|
| Setting | The streamer asks out loud | Nobody asks |
| Tests | Whether the answer is right | Whether this was the moment to speak |
| Stored in | `tasks[]` in `data/containers/<id>.json` | `data/proactive/<id>.json` |
| Anchor | A single moment, `anchor_sec` | A window, `window_sec` |
| Authoring code | None; written into JSON by hand with an agent's help | `bench/mine_proactive.py` |

Query task fields include `question`, `context_window_sec` (the agent only sees content before
the anchor), `hint_level`, `scene` (which must describe what is on that frame), and inside
`grading`: `rubric_points`, `spoiler_blocklist`, and `must_cite`. Two rules hold when writing
them: every anchor must be checked against an extracted frame, and the anchor must fall at the
moment the evidence is already visible.

Proactive tasks are mined in two stages by `bench/mine_proactive.py`:

| Stage | Function | What it does |
|---|---|---|
| 1. Candidates from the transcript | `mine_chunk()` | Splits by minute and looks for moments where the streamer genuinely needs help, copying his own words as `evidence`. This stage cannot see the video, so it only writes `look_for`: what should be visible on screen if this is real |
| 2. Frame verification | `verify()` | Takes eight frames inside the window and asks a model, looking at frames only, whether someone who cannot hear anything would notice that something is off. Only those survive |

More candidates are dropped than kept, and that is intentional. A moment that exists only in
complaints, with nothing visible on screen, is unanswerable for an agent that only has frames.
Dropped candidates are written to `<id>.dropped.json` for later review.

### Judging

`bench/judge.py` exposes one entry point, `judge_run()`. It does not touch codex or the Realtime
session and shares no context; it takes the task and what the agent actually said, and asks a
text-only model. Letting one session both answer and grade itself is grading your own work, so
this path stays separate. The dashboard calls it automatically after each task
(`POST /api/judge`), and the model can be overridden with `HERBENCH_JUDGE_MODEL`.

---

## 3. dashboard

| File | Contents |
|---|---|
| `server.py` | Serves static files with HTTP Range support (needed for video seeking), plus `/api/realtime/token` (exchanges the master key for an ephemeral one so the browser never holds the real key) and `/api/judge` |
| `app/index.html` | Main view: timeline, tasks, judging, backend panel, and the wiring that starts the agent |
| `app/proactive.html` | Pure proactive view: frames only, no audio and no questions |

`app/index.html` is divided by comment banners; search for `═══` to jump between them:

| Section | Contents |
|---|---|
| Timeline drawing | `draw()`: thumbnail strip, anchor markers, response windows, drag and zoom |
| Right-hand panel | Five tabs for tasks, reference documents, judging, backend calls, and runs; `renderBackendPane()` expands every backend call's input and output |
| Task triggering and judging | `triggerTask()` fires when playback reaches an anchor, `openGrading()` sends the result to the judge |
| Response windows | `armProactiveWindows()` and `noteProactiveHit()` record whether a proactive window was answered, without prompting the agent to speak |
