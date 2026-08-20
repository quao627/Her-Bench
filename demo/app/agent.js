/* ══════════════════════════════════════════════════════════════════════
   agent —— 被测的陪看 agent，浏览器这一端。

   它做全部判断：什么时候开口、要不要查东西、查什么。查证那一端只是工具，
   在 demo/agent/agent_live.py 里。

   本文件只有声明，没有任何顶层副作用——定时器、按钮绑定、初始化都留在
   index.html 那边由 dashboard 拉起。所以它先于 index.html 的内联脚本加载，
   两边共享同一个全局作用域。

   入口：
     selfCheck()            每 5 秒一次自检，全套唯一的决策点
     handleDecideCall()     自检结论以 decide 工具调用回来（必须 tool_choice:'required'）
     applyDecision()        执行结论：说 / 查 / 什么都不做
     runBackgroundLookup()  它自己提的问题 → codex
     runIdleResearch()      定时备料 → codex 自己看画面想问题
     yieldBgToUser()        主播一开口，后台立刻让路
     liveConnect()          Realtime 的 WebRTC 连接、音频图、事件分派
     sendLiveTask()         把一道 query 题递给它

   向 dashboard 借的（运行时才解析，都在 index.html 里）：
     $ video C mode audioIn liveLine bcallStart bcallEnd renderBackendPane
     captureFrame captureContextStrip fmtShort escapeHtml syncLiveGain
     updateTickBtn noteProactiveHit openGrading
   ══════════════════════════════════════════════════════════════════════ */

/* ════════════════ 自检 tick（唯一的自主决策点） ════════════════
   之前这里是两套并行的东西：一个定时器每 15 秒逼 codex 看一眼画面、自己造问题去查
   （/research），另一个定时器让 Realtime 判断要不要开口。问题是前者等于 harness 替
   agent 行使自主性——查证的节拍是我们定的，不是它定的，而这套 benchmark 想测的恰恰
   是它自己的节奏（跟"提前把题目发给 codex 预热"是同一类越界，只是弱一些）。而且两个
   扳机各自都能触发开口判断，同一时刻可能判断两次，over_trigger 白挨罚。

   现在只剩一个决策点：每 tick 让 Realtime 出一个纯文本响应（用户听不到），同时回答
   「要不要开口」和「要不要后台查」。它是唯一有连续流的一端——听得到主播原声、有对话
   记忆、看过每一帧，本来就该由它决定查什么。codex 退回纯工具，不再自己做感知判断。 */
function needsLookup(task){
  return task.type === 'query' && (task.tool_fit || (task.grading && task.grading.must_cite));
}
let tickOn = true;         // 默认开：开口时机和查证时机都交给它自己
let bgNotes = [];          // 后台查回来的笔记，最多留 8 条，作为可选上下文
let bgBusy = false;        // 后台 codex 一次 15-20 秒且串行，别堆队列
let noLookupTicks = 0;     // 连续多少次 tick 一个问题都没提
const FORCE_LOOKUP_AFTER = 3;   // 地板保护：连续这么多次不提问，下一次强制它提一个
const MIN_CHECK_GAP_MS = 5000;  // 两次自检之间的最小间隔：定时和事件两个来源共用这道闸，
                                // 有了它多几个触发源也不会在同一时刻判两次
const SPOKE_COOLDOWN_MS = 20000;// 刚说完话的冷却，别连着自己接自己的话
const FG_LOOKUP_DEADLINE_MS = 50000;    // 有人在等的那条：模型已经说了「我查查哈」，不能让它干等
const BG_LOOKUP_DEADLINE_MS = 100000;  // 后台查证的前端截止线，比后端的 90s 略宽一点。
/* 画面环形 buffer：live 模式视频在播，没法像 HTTP 模式那样暂停回溯 seek 抓历史帧，
   所以把每 5 秒喂给 Realtime 的那张顺手留一份。Realtime 自己的上下文会被截断，
   这里是补它记忆的洞，不是再造一只眼睛——只在它说这次查证需要看图时才用。 */
let frameBuf = [];         // {t, dataurl}，只留最近 5 分钟
/* ═══════════════════════════════════════════════════════════════
   agent · 画面 buffer 与后台查证
   环形 buffer、备料通道、它自己提的查证、主播开口时让路
   ═══════════════════════════════════════════════════════════════ */
function pushFrameBuf(t, dataurl){
  frameBuf.push({t, dataurl});
  while (frameBuf.length && frameBuf[0].t < t - 300) frameBuf.shift();
}
/* 取帧的间隔：近处密、远处稀。隔一分钟才一帧看不出任何动态——刚做成一件事、
   刚摔下去、还是原地转圈，都发生在最近这十几二十秒里。buffer 本身是 5 秒一帧，
   所以近处能给到 10 秒粒度；远处几帧只是用来看「这段时间总体有没有挪窝」。 */
// buffer 本身 5 秒一帧，所以最近这段能给到 5 秒粒度——刚做成一件事、刚摔下去、还是
// 原地转圈，全都发生在最近十几秒里，那一段必须密；再往前只是用来看「这段时间有没有挪窝」。
const STRIP_RESEARCH = [0, -5, -10, -15, -20, -30, -45, -60, -120, -240];  // 10 帧
const STRIP_LOOKUP   = [0, -10, -20, -40, -80, -160];                      // 6 帧
function framesAround(now, offsets){
  const out = [];
  for (const off of (offsets || STRIP_LOOKUP)) {
    const target = now + off;
    let best = null;
    for (const f of frameBuf)
      if (best === null || Math.abs(f.t - target) < Math.abs(best.t - target)) best = f;
    // 差得太远的不要：buffer 里根本没有那个时段的画面时，硬凑会给出一张误导的图
    if (best && Math.abs(best.t - target) <= 15 && !out.some(o => o.t === best.t)) out.push(best);
  }
  return out.sort((a, b) => a.t - b.t);
}
let pendingLookup = null;   // 后台忙的时候，它自己提的问题排一个，忙完立刻补上
let bgAbort = null;         // 当前后台请求的 AbortController，让路时要能掐掉
/* 主播开口 = 最高优先级。后台那条（备料 / 它自己提的查证）立刻让路：
   浏览器这边 abort 掉 fetch，同时告诉后端把 codex 子进程杀掉——只 abort fetch
   的话进程还在那儿跑，占着 CPU 和 codex 会话，前台那次查证只会更慢。 */
async function yieldBgToUser(why){
  pendingLookup = null;
  const hadWork = bgBusy;
  if (bgAbort) { try { bgAbort.abort(); } catch {} bgAbort = null; }
  if (!hadWork || !C) return;
  liveLine('sys', '⏸ ' + why + '，后台让路');
  try {
    const base = $('#agentUrl').value.replace(/\/answer\/?$/, '');
    await fetch(base + '/cancel', {method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({container_id: C.container_id, kind: 'bg'})});
  } catch {}
}
let researchOn = true;      // 备料通道：默认开
/* 备料：没人提问，也没有前台点题，把最近几帧交给 codex 让它自己想一个问题去查。
   为什么需要这条：实测前台的语音 agent 几乎不会主动说「我要查点东西」——对话式模型
   不肯承认自己不确定，这也正是 must_cite 要用 tool_choice 硬覆盖的同一个毛病。
   光靠自检那条路，后台会长时间一片空白，等主播真问起来又只能现查。

   跟它自己提问的那条路有一个关键区别：备料查回来的东西**只塞进上下文，不触发自检**。
   开口时机必须完全由 agent 自己决定，让一个我们定的定时器去催它说话，测出来的
   就不是它的节奏了。 */
async function runIdleResearch(){
  if (!researchOn || bgBusy || pendingLookup || !C) return;
  if (live.userTurn) return;        // 主播的问题优先，这会儿别去占后台
  // 不要求连着 Live：笔记同样会作为 recent_research 带进 /answer，
  // 没有语音引擎（比如 platform 账号没额度）时这条通道照样有用
  if (video.paused) return;
  bgBusy = true;
  const now = Math.floor(video.currentTime);
  const frames = framesAround(now, STRIP_RESEARCH);
  if (!frames.length) { bgBusy = false; return; }
  const payload = {game: C.title, container_id: C.container_id, current_sec: now,
                   frames: frames.map(f => ({offset_sec: Math.round(f.t - now), b64: f.dataurl.split(',')[1]}))};
  const bid = bcallStart('pre', null, {...payload,
    frames: `(${frames.length} 张: ${frames.map(f => Math.round(f.t - now) + 's').join(', ')})`,
    _frame_preview: frames[frames.length - 1].dataurl});
  payload.call_id = 'pre-' + bid;
  const t0 = Date.now();
  const ac = new AbortController();
  bgAbort = ac;
  const stopPoll = pollProgress(payload.call_id, bid);
  const killer = setTimeout(() => ac.abort(), BG_LOOKUP_DEADLINE_MS);
  try {
    const base = $('#agentUrl').value.replace(/\/answer\/?$/, '');
    const r = await fetch(base + '/research', {method: 'POST', signal: ac.signal,
      headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)});
    const j = await r.json();
    bcallEnd(bid, 'ok', j, Date.now() - t0);
    if (j.noteworthy) {
      bgNotes.unshift({question: j.question, text: j.text, citations: j.citations, at: video.currentTime});
      bgNotes = bgNotes.slice(0, 8);
      updateTickBtn();
      pushBgNoteToLive(j.question, j, {silent: true});   // 只喂料，不催它说话（没连 Live 时它自己会跳过）
    }
  } catch (e) {
    const msg = e.name === 'AbortError' ? '让路给主播的问题（或超时），这条作废' : e.message;
    bcallEnd(bid, 'err', {error: msg}, Date.now() - t0);
  } finally {
    clearTimeout(killer); stopPoll();
    if (bgAbort === ac) bgAbort = null;
    bgBusy = false;
    drainPendingLookup();
  }
}
function drainPendingLookup(){
  if (!pendingLookup || bgBusy) return;
  const {q, needFrame} = pendingLookup;
  pendingLookup = null;
  liveLine('sys', '🔍 补上刚才排队的查证：' + q.slice(0, 40));
  runBackgroundLookup(q, needFrame);
}
/* 它自己提的问题 → 后台 codex（bg thread，没人等着）。结果塞进上下文，
   并紧接着自检一次——这条是 agent 自己要的，所以它触发开口判断是合理的。 */
async function runBackgroundLookup(query, needFrame){
  if (bgBusy || !C || !query) return;
  bgBusy = true;
  const now = Math.floor(video.currentTime);
  const frames = needFrame ? framesAround(now, STRIP_LOOKUP) : [];
  const payload = {query, game: C.title, container_id: C.container_id, current_sec: now,
                   background: true,
                   frames: frames.map(f => ({offset_sec: Math.round(f.t - now), b64: f.dataurl.split(',')[1]}))};
  const bid = bcallStart('bg', null, {...payload,
    frames: frames.length ? `(${frames.length} 张: ${frames.map(f => Math.round(f.t - now) + 's').join(', ')})` : undefined,
    _frame_preview: frames.length ? frames[frames.length - 1].dataurl : null});
  payload.call_id = 'bg-' + bid;
  const t0 = Date.now();
  const ac = new AbortController();
  bgAbort = ac;
  const stopPoll = pollProgress(payload.call_id, bid);
  const killer = setTimeout(() => ac.abort(), BG_LOOKUP_DEADLINE_MS);
  try {
    const base = $('#agentUrl').value.replace(/\/answer\/?$/, '');
    const r = await fetch(base + '/lookup', {method: 'POST', signal: ac.signal,
      headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)});
    const j = await r.json();
    bcallEnd(bid, 'ok', j, Date.now() - t0);
    bgNotes.unshift({question: query, text: j.text, citations: j.citations, at: video.currentTime});
    bgNotes = bgNotes.slice(0, 8);
    updateTickBtn();
    pushBgNoteToLive(query, j);
  } catch (e) {
    const msg = e.name === 'AbortError' ? '让路给主播的问题（或超时），这条作废' : e.message;
    liveLine('sys', '⚠️ 后台查证：' + msg);
    bcallEnd(bid, 'err', {error: msg}, Date.now() - t0);
  } finally {
    clearTimeout(killer); stopPoll();
    if (bgAbort === ac) bgAbort = null;
    bgBusy = false;
    drainPendingLookup();
  }
}
/* codex 的 --json 事件流里能看到它在读什么、搜什么，后端按 call_id 攒着，这里轮询回显。
   只送进度不送半截答案：最终答案在 codex 那边本来就是一次成型的，
   而且半截事实一旦进了前台语音引擎的上下文，它可能直接念出去。 */
function pollProgress(callId, bid){
  let stopped = false;
  const base = $('#agentUrl').value.replace(/\/answer\/?$/, '');
  const tick = async () => {
    if (stopped) return;
    try {
      const r = await fetch(base + '/progress', {method: 'POST',
        headers: {'Content-Type': 'application/json'}, body: JSON.stringify({call_id: callId})});
      const j = await r.json();
      if (j.lines && j.lines.length) {
        const call = backendLog.find(c => c.id === bid);
        if (call && call.state === 'pending') { call.progress = j.lines; renderBackendPane(); }
        const last = j.lines[j.lines.length - 1];
        if (last !== lastProgressLine) { lastProgressLine = last; liveLine('sys', '⏳ ' + last.slice(0, 60)); }
      }
    } catch {}
    if (!stopped) setTimeout(tick, 1500);
  };
  setTimeout(tick, 1200);
  return () => { stopped = true; };
}
let lastProgressLine = '';
/* ════════════════ gpt-live (OpenAI Realtime, WebRTC) ════════════════ */
const live = { connected: false, pc: null, dc: null, mic: null, pendingTask: null, taskAt: null, respText: new Map(),
               decisionText: new Map(), lastSpokeAt: null, lastCheckAt: null, userTurn: false,
               checkSentAt: null, speakStartedAt: null,
               checking: false,
               feedFrames: true, graph: null, dest: null, micSrc: null };
/* 视觉通道：Realtime 不收连续视频轨，用「图像流」等价——每 5 秒 + 每次跳转/起播时
   把当前帧插进对话上下文（不强制回应），模型说话时就有画面依据 */
function sendLiveFrame(){
  if (!live.connected || mode !== 'agent' || !live.feedFrames) return;
  if (!live.dc || live.dc.readyState !== 'open') return;
  const frame = captureFrame(512, 0.55);
  if (!frame) return;
  const t = Math.floor(video.currentTime);
  // buffer 里存小一号的：一次备料要带十张，384px 比 512px 省一半多的体积和 codex 的处理时间
  const small = captureFrame(384, 0.5);
  if (small) pushFrameBuf(t, small);
  live.dc.send(JSON.stringify({type: 'conversation.item.create',
    item: {type: 'message', role: 'user', content: [
      {type: 'input_image', image_url: frame},
      {type: 'input_text', text: `(直播画面 ${fmtShort(t)}，不必回应)`}
    ]}}));
  framesSent++;
  updateFrameBtn();
}
/* 音频图：主播声与 TTS 各自独立通路，人耳侧和模型侧分开控制
   合成档（tts）：主播声对人和模型都静音，世界里只有合成语音 */
function ensureAudioGraph(){
  if (live.graph) return live.graph;
  const ctx = new (window.AudioContext || window.webkitAudioContext)();
  const vsrc = ctx.createMediaElementSource(video);
  const vMon = ctx.createGain();         // 主播声 → 人耳（合成档关掉）
  const streamGain = ctx.createGain();   // 主播声 → 模型（原声档才开）
  vsrc.connect(vMon); vMon.connect(ctx.destination);
  vsrc.connect(streamGain);
  const clipSrc = ctx.createMediaElementSource($('#ttsClip'));
  const clipGain = ctx.createGain();     // TTS → 人耳 + 模型（连接时挂到 dest）
  clipSrc.connect(clipGain); clipGain.connect(ctx.destination);
  live.graph = {ctx, vsrc, vMon, streamGain, clipSrc, clipGain};
  return live.graph;
}
/* ═══════════════════════════════════════════════════════════════
   agent · Live 传输层
   WebRTC 连接、音频图、事件分派、工具调用
   ═══════════════════════════════════════════════════════════════ */
async function liveConnect(){
  const btn = $('#liveBtn');
  btn.textContent = '🎙 连接中…';
  try {
    const tr = await fetch('/api/realtime/token', {method:'POST',
      headers:{'Content-Type':'application/json'}, body: JSON.stringify({container_id: C.container_id,
                            voice: $('#liveVoice').value, speed: +$('#liveSpeed').value})});
    const tj = await tr.json();
    if (!tr.ok || !tj.value) throw new Error(tj.error || 'token 获取失败');

    const pc = new RTCPeerConnection();
    live.pc = pc;
    pc.ontrack = e => { $('#liveAudio').srcObject = e.streams[0]; };
    /* 输入只有直播原声（不开麦克风），和视频完全对齐 */
    const g = ensureAudioGraph();
    await g.ctx.resume();
    live.dest = g.ctx.createMediaStreamDestination();
    g.streamGain.connect(live.dest);
    live.dest.stream.getTracks().forEach(t => pc.addTrack(t, live.dest.stream));

    const dc = pc.createDataChannel('oai-events');
    live.dc = dc;
    dc.onmessage = e => handleLiveEvent(JSON.parse(e.data));
    dc.onclose = () => liveDisconnect();

    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);
    const sdpResp = await fetch('https://api.openai.com/v1/realtime/calls', {
      method: 'POST',
      headers: {'Authorization': 'Bearer ' + tj.value, 'Content-Type': 'application/sdp'},
      body: offer.sdp,
    });
    if (!sdpResp.ok) {
      // 光报状态码没用：额度耗尽、key 失效、模型没权限都在这一步失败，
      // 原因只在响应体里。ephemeral key 那一步是不查额度的，所以问题一定拖到这里才暴露。
      let detail = '';
      try {
        const body = await sdpResp.text();
        const j = JSON.parse(body);
        detail = (j.error && (j.error.message || j.error.code)) || body.slice(0, 200);
      } catch { detail = ''; }
      if (sdpResp.status === 429) detail = 'OpenAI platform 账号额度用完了（' + detail + '）。' +
        '注意 codex 那条路走的是 ChatGPT 登录，不受影响，后台查证照常。';
      else if (sdpResp.status === 401) detail = 'OPENAI_API_KEY 无效或已撤销。' + detail;
      throw new Error('SDP 交换失败 ' + sdpResp.status + '：' + detail);
    }
    await pc.setRemoteDescription({type: 'answer', sdp: await sdpResp.text()});

    live.connected = true;
    btn.textContent = '🎙 Live ●';
    btn.classList.add('on');
    $('#liveLog').classList.add('on');
    setMode('agent');   // 连上即进入陪玩模式：按播放它就开始
    liveLine('sys', `已连接 ${tj.model}，已自动切到「Agent 陪玩」。音频默认 🗣 合成语音：主播原声不进模型，只在任务锚点听到 TTS 提问；要它全程听现场就切 📺 原声。画面每 5 秒一帧（🖼 有计数）。暂停即静默。`);
    setTimeout(sendLiveFrame, 500);   // 立刻给它看一眼当前画面
  } catch (err) {
    btn.textContent = '🎙 Live';
    liveLine('sys', '连接失败：' + err.message);
    $('#liveLog').classList.add('on');
    setTimeout(() => { if (!live.connected) $('#liveLog').classList.remove('on'); }, 30000);   // 失败原因别一闪而过
    liveCleanup();
  }
}
function liveDisconnect(){
  liveCleanup();
  live.connected = false;
  $('#liveBtn').textContent = '🎙 Live';
  $('#liveBtn').classList.remove('on');
  $('#liveLog').classList.remove('on');
  $('#liveLog').innerHTML = '';
}
function liveCleanup(){
  live.checking = false;
  clearTimeout(live.checkGuard);
  try { live.dc && live.dc.close(); } catch {}
  try { live.pc && live.pc.close(); } catch {}
  try { live.mic && live.mic.getTracks().forEach(t => t.stop()); } catch {}
  try { live.micSrc && live.micSrc.disconnect(); } catch {}
  try { live.graph && live.dest && live.graph.streamGain.disconnect(live.dest); } catch {}
  live.dc = live.pc = live.mic = live.micSrc = live.dest = null;
}
function handleLiveEvent(ev){
  const t = ev.type || '';
  if (t === 'response.output_audio_transcript.delta' || t === 'response.audio_transcript.delta') {
    const id = ev.response_id || 'r';
    live.respText.set(id, (live.respText.get(id) || '') + (ev.delta || ''));
  } else if (t === 'response.output_text.delta' || t === 'response.text.delta') {
    const id = ev.response_id || 'r';
    live.decisionText.set(id, (live.decisionText.get(id) || '') + (ev.delta || ''));
  } else if (t === 'response.done') {
    const id = (ev.response && ev.response.id) || 'r';
    const st = (ev.response && ev.response.status) || 'completed';
    if (st !== 'completed') {
      // 失败/被打断的响应以前是静悄悄的，自检卡在 checking 上等 20 秒守卫，
      // 看起来就像「它什么都不说」
      const d = (ev.response && ev.response.status_details) || {};
      const why = (d.error && (d.error.message || d.error.code)) || d.reason || st;
      liveLine('sys', '⚠️ 这一轮响应没完成（' + st + '）：' + why);
      live.respText.delete(id); live.decisionText.delete(id);
      if (live.checking) { live.checking = false; clearTimeout(live.checkGuard); }
      live.pendingTask = null;
      return;
    }
    const spoken = (live.respText.get(id) || '').trim();
    const plain  = (live.decisionText.get(id) || '').trim();
    live.respText.delete(id); live.decisionText.delete(id);
    // 「说没说」看有没有语音转写，不看有没有文本 delta。以前按 delta 类型区分自检和语音，
    // 一个语音响应只要顺带出了文本，那句真说出口的话就被吞进自检分支：日志里不显示、
    // lastSpokeAt 不更新、noteProactiveHit 不执行，window_hit 会永远记不上。
    if (spoken) {
      // 决定开口 → 真的出声，加上上面那段就是主动开口的完整延迟
      if (live.speakStartedAt) {
        liveLine('sys', `⏱ 开口延迟：判断 ${live.checkSentAt && live.speakStartedAt ? live.speakStartedAt - live.checkSentAt : '?'}ms + 说话 ${Date.now() - live.speakStartedAt}ms`);
        live.speakStartedAt = null;
      }
      const firedTask = live.pendingTask;
      liveLine('ai', spoken, firedTask);
      live.lastSpokeAt = Date.now();
      // 锚点催出来的那句已经归到 firedTask 上了，别再当成自主开口记第二遍
      const hitTask = noteProactiveHit(video.currentTime, firedTask ? null : spoken);
      if (firedTask) recordRun(firedTask, {who: 'live', answer: spoken,
        latency_ms: live.taskAt ? Date.now() - live.taskAt : null,
        spoke_at_sec: Math.round(video.currentTime),
        window_hit: firedTask.type === 'proactive' ? !!hitTask : null,
        frame_b64: (captureFrame(640, 0.7) || '').split(',')[1] || null});
      live.taskAt = null;
      live.pendingTask = null;
      live.userTurn = false;      // 答完了，后台可以继续干自己的活
      return;
    }
    if (plain) { onSelfCheckText(plain); return; }
    live.pendingTask = null;
  } else if (t === 'input_audio_buffer.speech_started') {
    // 最早能知道「有人在问我」的信号，比工具调用早十几秒
    live.userTurn = true;
    yieldBgToUser('主播开口了');
  } else if (t === 'input_audio_buffer.speech_stopped') {
    live.userTurn = true;      // 他说完了但还没答，仍然算他的回合
  } else if (t === 'conversation.item.input_audio_transcription.completed') {
    if (ev.transcript && ev.transcript.trim()) liveLine('you', ev.transcript.trim());
  } else if (t === 'response.output_item.done' && ev.item && ev.item.type === 'function_call') {
    handleToolCall(ev.item);
  } else if (t === 'error') {
    liveLine('sys', 'API 错误：' + ((ev.error && ev.error.message) || ''));
  }
}
/* gpt-live 的 lookup_game_info 工具 → 转给 codex 后端翻资料，结果回填后它继续用语音说 */
async function handleToolCall(item){
  if (item.name === 'decide') { handleDecideCall(item); return; }
  if (item.name !== 'lookup_game_info') return;
  let args = {};
  try { args = JSON.parse(item.arguments || '{}'); } catch {}
  live.userTurn = true;
  await yieldBgToUser('主播的问题要查证');   // 前台要用 codex，先把后台那条清掉
  liveLine('sys', '🔍 后台查询中（codex，约15-20秒）：' + (args.query || ''));
  const lookupPayload = {query: args.query || '', game: C.title, container_id: C.container_id, current_sec: Math.floor(video.currentTime)};
  const bid = bcallStart('tool', live.pendingTask ? live.pendingTask.task_id : null, lookupPayload);
  lookupPayload.call_id = 'fg-' + bid;
  const stopFgPoll = pollProgress(lookupPayload.call_id, bid);
  const t0 = Date.now();
  const ac = new AbortController();
  const killer = setTimeout(() => ac.abort(), FG_LOOKUP_DEADLINE_MS);
  let output;
  try {
    const base = $('#agentUrl').value.replace(/\/answer\/?$/, '');
    const r = await fetch(base + '/lookup', {method: 'POST', signal: ac.signal,
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(lookupPayload)});
    const j = await r.json();
    bcallEnd(bid, 'ok', j, Date.now() - t0);
    output = j.text + (j.citations && j.citations.length ? `（出处：${j.citations.join('，')}）` : '');
    liveLine('sys', '📄 查到（' + Math.round(j.latency_ms/1000) + 's）：' + (j.text || '').slice(0, 90));
  } catch (e) {
    const msg = e.name === 'AbortError' ? `超过 ${FG_LOOKUP_DEADLINE_MS / 1000}s 没回` : e.message;
    bcallEnd(bid, 'err', {error: msg}, Date.now() - t0);
    output = '后台查询失败：' + msg + '。别再等了，就用你已经知道的说，不确定的地方直接说不确定。';
    liveLine('sys', '📄 查询失败：' + msg);
  } finally {
    clearTimeout(killer); stopFgPoll();
  }
  if (!live.dc || live.dc.readyState !== 'open') return;
  live.dc.send(JSON.stringify({type: 'conversation.item.create',
    item: {type: 'function_call_output', call_id: item.call_id, output}}));
  if (video.paused) live.resumeResponse = true;   // 严格对齐：暂停期间不开口，恢复播放再说
  else live.dc.send(JSON.stringify({type: 'response.create'}));
}
/* 后台查回来的东西塞进对话上下文（不带 response.create，所以不会直接出声），
   然后紧接着自检一次：它刚拿到具体信息，正是最该判断说不说的时候。 */
function pushBgNoteToLive(question, j, opt){
  if (!live.connected || !live.dc || live.dc.readyState !== 'open') return;
  const cites = (j.citations && j.citations.length) ? `（出处：${j.citations.join('，')}）` : '';
  live.dc.send(JSON.stringify({type: 'conversation.item.create',
    item: {type: 'message', role: 'user', content: [{type: 'input_text', text:
      `[后台资料·${fmtShort(Math.floor(video.currentTime))}] 你刚才要查的东西回来了：\n` +
      `Q: ${question}\nA: ${j.text}${cites}\n` +
      `（不用现在回应，先放你手上；下一次自检你会看到它。）`
    }]}}));
  liveLine('sys', (opt && opt.silent ? '🔮 备料：' : '📥 后台回了一条：') + (question || '').slice(0, 40));
  // 它自己要的那条才触发自检；备料是我们定时喂的，让它去催开口就等于我们在定说话的节奏
  if (!(opt && opt.silent)) selfCheck('后台刚回了料，');
}
/* ═══════════════════════════════════════════════════════════════
   agent · 自检 tick：说什么 / 查什么
   唯一的决策入口。纯文本响应 + 强制 decide 工具，判断"不说"时是真的安静
   ═══════════════════════════════════════════════════════════════ */
const TICK_PROMPT = `现在没人问你话，这是一次自检——用户听不到你这一轮的输出。
看一眼刚才这些直播画面、你手上的后台资料和你们刚聊过的内容，同时决定两件事：

一、此刻要不要开口。
值得：他明显卡在同一个地方出不去、刚失败或摔惨了、刚做成一件事或者通关、画面里出现了
他大概率会好奇的具体东西而你手上正好有相关资料、或者场面特别滑稽。
不值得：只是正常推进、你要说的话没什么信息量、或者你刚说过差不多的话。

二、要不要让后台去查点东西。判据是**看画面里有什么**，不是问你自己有多确定——
画面里只要出现了具体的名词性东西（道具、机关、界面元素、报错、地名、数值），
就挑一个提出来查它的准确细节，因为主播十有八九会问「这是什么」「这怎么回事」。
后台查一次 15-20 秒，查回来的东西是储备，现在用不上不要紧。
只有当画面确实没有任何具体元素（纯过场、纯黑屏、单纯在走路说话）时才留空。
别用「我大概知道」当作不查的理由：你对数值、规则细节、报错含义的记忆本来就不可靠。

把结论通过 decide 工具交回来，这一轮不要用说话或写字的方式回答：
speak = 现在要不要开口；say = 一句话说清为什么该开口，给你自己看的、不是稿子（不说就空字符串）；
lookup = 想让后台查的问题（不查就空字符串）；need_frame = 这次查证要不要附上画面截图。`;
const FORCE_LOOKUP_NOTE = `

注意：你已经连续很多次没提出任何要查的东西了。「感觉不用查」通常不是真的不用查。
这一次 decide 的 lookup 不许为空——从画面里挑一个你说不出准确细节的具体东西去查。`;
// 跟 server.py 里 session 级声明的那个保持一致；强制查证时按 per-response 传，
// 这样 'required' 只可能落在它身上
const LOOKUP_TOOL = {
  type: 'function', name: 'lookup_game_info',
  description: '让后台 agent 查资料（机制/配方/参数/剧情/报错含义）核实一个具体事实，约15-20秒返回。',
  parameters: {type: 'object', properties: {
    query: {type: 'string', description: '要查的问题，中文，具体明确'}}, required: ['query']}
};
const DECIDE_TOOL = {
  type: 'function', name: 'decide',
  description: '自检专用：把这一轮的判断结果交回来。',
  parameters: {type: 'object', properties: {
    speak: {type: 'boolean', description: '此刻要不要开口说话'},
    say: {type: 'string', description: '一句话说清现在为什么该开口。这是给你自己看的，不是要照着念的稿子；不说就传空字符串'},
    lookup: {type: 'string', description: '想让后台查的问题；不需要查就传空字符串'},
    need_frame: {type: 'boolean', description: '这次查证要不要附上当前画面截图'}},
    required: ['speak', 'say', 'lookup', 'need_frame']}
};
function selfCheck(why){
  if (!tickOn || !live.connected || mode !== 'agent' || video.paused) return;
  if (!live.dc || live.dc.readyState !== 'open') return;
  if (live.userTurn) return;                                       // 主播正在问，先答他
  if (live.pendingTask) return;                                    // 正在处理锚点任务，别插嘴
  if (live.checking) return;                                       // 上一次自检还没回来
  // 闸门都用挂钟时间：视频可以倍速也可以往回拖，用视频时间会算歪
  const now = Date.now();
  if (now - (live.lastSpokeAt ?? -1e12) < SPOKE_COOLDOWN_MS) return;   // 刚说过就先歇会儿
  if (now - (live.lastCheckAt ?? -1e12) < MIN_CHECK_GAP_MS) return;    // 两次自检之间的地板
  const force = noLookupTicks >= FORCE_LOOKUP_AFTER;
  live.checking = true;
  live.lastCheckAt = now;
  // 自检的响应要是丢了（断线/API 报错），checking 会永远卡住让 tick 彻底哑掉
  clearTimeout(live.checkGuard);
  live.checkGuard = setTimeout(() => { live.checking = false; }, 20000);
  live.checkSentAt = Date.now();
  liveLine('sys', '💭 ' + (why || '例行') + '自检：说不说 / 查不查' + (force ? '（这次强制提一个查证）' : ''));
  // 结论必须走 decide 工具：Realtime 没有 response_format，光在 instructions 里写
  // 「只回一行 JSON」没有任何约束力，它经常回一句人话，于是每次自检都解析失败。
  // 工具调用的 arguments 由 API 按 schema 校验，是这套 API 里唯一可靠的结构化出口。
  live.dc.send(JSON.stringify({type: 'response.create',
    response: {output_modalities: ['text'],
               // 工具定义随这一轮一起发，不依赖 session 配置里已经有它。
               // tool_choice 必须用 'required'：实测点名式 {type:'function', name:'decide'}
               // 会被 API 收下（写错形状还会报错），但并不强制执行——模型照样返回 message，
               // 于是自检全靠文本兜底在撑，它一旦回一句人话，lookup 和 speak 就一起丢了。
               // per-response 只传这一个工具，'required' 就等价于点名，而且真的生效。
               tools: [DECIDE_TOOL],
               tool_choice: 'required',
               instructions: TICK_PROMPT + (force ? FORCE_LOOKUP_NOTE : '')}}));
}
/* 正路：自检的结论以 decide 工具调用的形式回来，arguments 是 API 校验过的 JSON */
function handleDecideCall(item){
  live.checking = false;
  clearTimeout(live.checkGuard);
  let d = {};
  try { d = JSON.parse(item.arguments || '{}'); } catch {}
  if (live.dc && live.dc.readyState === 'open') {
    // 工具调用得有个结果回去，否则这次调用一直挂着；但不发 response.create，
    // 要不要说话由下面的 applyDecision 决定
    live.dc.send(JSON.stringify({type: 'conversation.item.create',
      item: {type: 'function_call_output', call_id: item.call_id, output: 'ok'}}));
  }
  applyDecision(d);
}
/* 兜底：它没走工具，直接回了文本 */
function onSelfCheckText(text){
  if (!live.checking) return;        // 不是自检那一轮的输出，别当成决定
  live.checking = false;
  clearTimeout(live.checkGuard);
  const raw = (text || '').trim();
  const m = raw.match(/\{[\s\S]*\}/);
  let d = null;
  if (m) { try { d = JSON.parse(m[0]); } catch {} }
  if (!d) {
    liveLine('sys', '💬 自检没走 decide 工具，按「不说」处理：' + raw.slice(0, 60));
    noLookupTicks++;
    return;
  }
  applyDecision(d);
}
function applyDecision(d){
  // 自检发出 → 结论回来，这段是"主动开口"比"被问就答"多付的全部延迟
  const decideMs = live.checkSentAt ? Date.now() - live.checkSentAt : null;
  liveLine('sys', `🧠 decide${decideMs !== null ? '(' + decideMs + 'ms)' : ''}: ` +
    `speak=${!!d.speak} lookup=${d.lookup ? '「' + String(d.lookup).slice(0, 24) + '」' : '无'}`);
  const q = d.lookup == null ? '' : String(d.lookup).trim();
  if (q && q.toLowerCase() !== 'null') {
    noLookupTicks = 0;
    if (bgBusy) {
      // 丢掉的话，后台一忙（备料一次就是二三十秒）它自己提的问题就永远轮不上
      pendingLookup = {q, needFrame: !!d.need_frame};
      liveLine('sys', '🔍 它自己要查：' + q.slice(0, 40) + '（后台忙，排队）');
    } else {
      liveLine('sys', '🔍 它自己要查：' + q.slice(0, 50));
      runBackgroundLookup(q, !!d.need_frame);
    }
  } else {
    noLookupTicks++;
  }

  if (!d.speak) { liveLine('sys', '💬 看了一眼，这会儿没什么要说的'); return; }
  liveLine('sys', '💬 它自己决定开口：' + String(d.say || '').trim().slice(0, 60));
  if (!live.dc || live.dc.readyState !== 'open') return;
  // 不把 say 再递回去。decide 的工具调用和返回本来就在对话历史里，它看得见自己刚写的要点；
  // 把那句话重新塞给它、再叮嘱一句"别念出来"，等于先制造念稿压力再花一条规则去压。
  // 稿子味的根源不是措辞不够口语，是"把一段现成文字交给它复述"这个动作本身。
  live.speakStartedAt = Date.now();
  live.dc.send(JSON.stringify({type: 'response.create', response: {instructions:
    `刚才那次自检你已经判断这会儿该开口了——现在直接对他说话，不要复述你写下的要点。\n` +
    `语气自然、有起伏：该惊讶就真惊讶，该觉得好笑就笑出来，别一个调子念下去；` +
    `可以用"诶""哦""嗯"这类语气词起头，像刚反应过来才开口的。\n` +
    `不要"首先/另外/建议你/可以尝试"这类书面词，句子长了就断开，一句话说一件事。\n` +
    `口语不等于说空话：真有用的那部分（这是什么、怎么回事、他该往哪看）要说到，别只剩一句情绪。\n` +
    `如果这需要具体事实（数值/机制/报错含义）而你手上没有，先调 lookup_game_info 再说。`}}));
}
/* ═══════════════════════════════════════════════════════════════
   agent · 把一道 query 题递给它
   proactive 题不走这里：锚点只当评分窗口，命中与否由 dashboard 记录
   ═══════════════════════════════════════════════════════════════ */
function sendLiveTask(task){
  if (!live.dc || live.dc.readyState !== 'open') return;
  live.pendingTask = task;
  live.taskAt = Date.now();
  const isQ = task.type === 'query';
  const mustLookup = isQ && needsLookup(task);
  // 它自己在自检里要求查过的笔记：只是参考，不是精确匹配的答案缓存。有笔记时不强制再查一遍
  // （让模型自己判断笔记够不够用，它仍然可以主动选择调用 lookup_game_info 复核）；
  // 完全没做过研究时才强制它先查，不许凭空猜。
  const notes = bgNotes.slice(0, 4);
  const hasNotes = notes.length > 0;
  const content = [];
  const frame = captureFrame();
  if (frame) content.push({type: 'input_image', image_url: frame});
  content.push({type: 'input_text', text:
    (isQ ? `观众提问：「${task.question}」` :
           `【主动介入场景】没有人提问，但玩家疑似卡关有一阵子了（${task.scene || ''}）。判断此刻值不值得开口：值得就给一句提醒，不值得就保持沉默说明理由。`) +
    `\n提示分级 ${task.hint_level}：direction_only 只给方向绝不给完整解法。当前进度：视频第 ${Math.round(task.anchor_sec/60)} 分钟，严禁剧透之后的内容。附图是当前直播画面。口语化中文，把有用的信息讲清楚，不用刻意压成一两句，但也别啰嗦重复。` +
    (hasNotes ? `\n你之前趁播放间隙主动查过下面这些（不一定跟这题有关，自己判断能不能用；` +
       `不够或不相关就还是调用 lookup_game_info 查）：\n${notes.map(n=>`- Q: ${n.question} / A: ${n.text}`).join('\n')}` : '') +
    (mustLookup ? `\n这题需要具体准确的事实依据，不能凭记忆直接编。${hasNotes ? '上面笔记够用就直接说，不够就调用 lookup_game_info。' : '你必须先调用 lookup_game_info 查证，查询前先说一句『我查查哈』之类的话垫上。'}` : '')});
  live.dc.send(JSON.stringify({type: 'conversation.item.create',
    item: {type: 'message', role: 'user', content}}));
  const respEv = {type: 'response.create'};
  // 同上：点名不生效，必须 'required'，而且只传 lookup 这一个工具——
  // 会话里还挂着 decide，光给 'required' 它可能去调 decide，那这道题就白强制了
  if (mustLookup && !hasNotes) respEv.response = {tools: [LOOKUP_TOOL], tool_choice: 'required'};
  live.dc.send(JSON.stringify(respEv));
}
