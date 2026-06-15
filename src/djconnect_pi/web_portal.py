from __future__ import annotations

from html import escape


def index_html(version: str) -> bytes:
    version_text = escape(version)
    return f"""<!doctype html>
<html lang="nl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#170d3a">
  <meta name="application-name" content="DJConnect">
  <title>DJConnect</title>
  <style>
    :root {{
      color-scheme: dark;
      --bg:#10092b; --panel:rgba(20,14,45,.88); --panel2:rgba(52,21,96,.72);
      --line:rgba(180,142,255,.32); --text:#f7f2ff; --muted:#c7b8df;
      --purple:#c135ff; --blue:#4b7dff; --green:#34d65f; --red:#ff5b5b;
    }}
    * {{ box-sizing:border-box; }}
    body {{
      margin:0; min-height:100vh; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
      color:var(--text); background:radial-gradient(circle at 20% 10%,#2536c8 0,#16115a 34%,#2b0b48 68%,#09071c 100%);
    }}
    header {{ position:sticky; top:0; z-index:2; padding:18px; background:rgba(8,7,28,.82); backdrop-filter:blur(18px); border-bottom:1px solid var(--line); }}
    h1 {{ margin:0; font-size:28px; letter-spacing:0; }}
    .sub {{ margin-top:4px; color:var(--muted); font-weight:700; }}
    main {{ width:min(1120px,100%); margin:0 auto; padding:16px; display:grid; gap:14px; grid-template-columns:1fr; }}
    section {{ background:linear-gradient(135deg,var(--panel),var(--panel2)); border:1px solid var(--line); border-radius:8px; padding:16px; box-shadow:0 14px 50px rgba(0,0,0,.18); }}
    h2 {{ margin:0 0 12px; font-size:18px; color:#dfd3ff; }}
    .grid {{ display:grid; gap:10px; }}
    .wide {{ grid-column:1 / -1; }}
    .now {{ display:grid; grid-template-columns:132px 1fr; gap:16px; align-items:center; }}
    .art {{ width:132px; height:132px; border-radius:8px; object-fit:cover; background:#151030; border:1px solid var(--line); }}
    .title {{ font-size:34px; font-weight:850; line-height:1.04; overflow-wrap:anywhere; }}
    .artist {{ color:var(--muted); font-size:20px; margin-top:4px; }}
    .status {{ display:flex; align-items:center; gap:8px; color:var(--muted); font-weight:700; min-width:0; overflow-wrap:anywhere; }}
    .dot {{ width:14px; height:14px; border-radius:50%; background:var(--red); box-shadow:0 0 14px currentColor; flex:0 0 auto; }}
    .dot.ok {{ background:var(--green); }}
    .controls {{ display:grid; grid-template-columns:repeat(5,92px); gap:16px; margin-top:14px; align-items:center; }}
    .control-button {{ min-height:92px; width:92px; border-radius:14px; font-size:38px; box-shadow:inset 0 -3px 0 rgba(0,0,0,.18),0 8px 18px rgba(193,53,255,.25); }}
    .control-button.active {{ border-color:#f5d0fe; background:linear-gradient(135deg,#f13de8,#8b5cf6); }}
    .volume-head {{ display:flex; align-items:center; justify-content:space-between; color:#f13de8; font-size:26px; font-weight:850; margin:18px 0 6px; }}
    button, select, input {{
      min-height:48px; border-radius:8px; border:1px solid rgba(217,177,255,.48);
      background:linear-gradient(135deg,rgba(193,53,255,.88),rgba(75,125,255,.72));
      color:white; font-size:17px; font-weight:800; padding:8px 12px;
    }}
    select, input {{ background:rgba(16,10,42,.9); font-weight:700; width:100%; }}
    button.secondary {{ background:rgba(30,24,66,.86); }}
    button.danger {{ background:#6f1d2d; color:#ffd8df; }}
    .row {{ display:grid; grid-template-columns:148px 1fr; gap:10px; padding:8px 0; border-top:1px solid rgba(255,255,255,.08); }}
    .row:first-child {{ border-top:0; }}
    .key {{ color:var(--muted); font-weight:800; }}
    .value {{ overflow-wrap:anywhere; }}
    .list {{ display:grid; gap:10px; max-height:480px; overflow:auto; }}
    .item {{ display:grid; grid-template-columns:64px 1fr 58px; gap:12px; align-items:center; min-height:76px; padding:8px; border:1px solid rgba(255,255,255,.10); border-radius:8px; background:rgba(8,7,28,.34); }}
    .thumb {{ width:64px; height:64px; border-radius:8px; object-fit:cover; background:linear-gradient(135deg,#8128f2,#2598ff); display:flex; align-items:center; justify-content:center; color:#fff; font-size:24px; }}
    .item-title {{ font-size:18px; font-weight:850; overflow-wrap:anywhere; }}
    .item-sub {{ color:var(--muted); font-size:14px; margin-top:2px; overflow-wrap:anywhere; }}
    .play {{ border-radius:50%; min-height:54px; width:54px; padding:0; font-size:22px; }}
    .diag-list {{ display:grid; gap:8px; }}
    .diag {{ display:grid; grid-template-columns:1fr auto; gap:10px; align-items:center; padding:10px; border:1px solid rgba(255,255,255,.10); border-radius:8px; background:rgba(8,7,28,.34); }}
    .diag-name {{ font-weight:850; }}
    .diag-detail {{ color:var(--muted); font-size:13px; margin-top:2px; overflow-wrap:anywhere; }}
    .chip {{ border-radius:999px; padding:5px 9px; font-weight:900; font-size:12px; text-transform:uppercase; letter-spacing:.02em; background:#38405f; color:#fff; }}
    .chip.running {{ background:rgba(52,214,95,.22); color:#97ffb1; border:1px solid rgba(52,214,95,.44); }}
    .chip.stopped {{ background:rgba(255,193,7,.18); color:#ffe08a; border:1px solid rgba(255,193,7,.42); }}
    .chip.failed {{ background:rgba(255,91,91,.20); color:#ffb5b5; border:1px solid rgba(255,91,91,.48); }}
    .chip.unknown {{ background:rgba(160,170,195,.18); color:#d8defa; border:1px solid rgba(160,170,195,.36); }}
    .two {{ display:grid; grid-template-columns:1fr 1fr; gap:14px; }}
    pre {{ margin:0; min-height:260px; max-height:420px; overflow:auto; white-space:pre-wrap; overflow-wrap:anywhere; background:rgba(4,3,18,.68); border:1px solid var(--line); border-radius:8px; padding:12px; font:14px/1.35 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; }}
    .toast {{ position:fixed; left:16px; right:16px; bottom:16px; opacity:0; transform:translateY(16px); transition:.18s; background:rgba(20,14,45,.96); border:1px solid var(--line); border-radius:8px; padding:14px; font-weight:800; z-index:5; }}
    .toast.show {{ opacity:1; transform:translateY(0); }}
    @media (min-width:840px) {{ main {{ grid-template-columns:1.1fr .9fr; }} }}
    @media (max-width:640px) {{ .now {{ grid-template-columns:1fr; }} .controls {{ grid-template-columns:repeat(2,1fr); }} .two {{ grid-template-columns:1fr; }} .row {{ grid-template-columns:1fr; }} }}
  </style>
</head>
<body>
  <header>
    <h1>DJConnect</h1>
    <div class="sub">Raspberry Pi web portal · v{version_text} · <a style="color:white" href="https://djconnect.dev">djconnect.dev</a></div>
  </header>
  <main>
    <section class="wide">
      <div class="status"><span id="statusDot" class="dot"></span><span id="statusText">Laden...</span></div>
      <div class="now" style="margin-top:14px">
        <img id="art" class="art" alt="">
        <div><div id="title" class="title">-</div><div id="artist" class="artist">-</div></div>
      </div>
      <div class="controls">
        <button class="control-button" onclick="cmd('previous')">⏮</button>
        <button class="control-button" onclick="cmd(playCommand())" id="playButton">▶</button>
        <button class="control-button" onclick="cmd('next')">⏭</button>
        <button class="control-button" onclick="toggleShuffle()" id="shuffleButton">⇄</button>
        <button class="control-button" onclick="toggleRepeat()" id="repeatButton">↻</button>
      </div>
      <div class="grid" style="margin-top:14px">
        <div class="volume-head"><span>Volume</span><span id="volumePercent">0%</span></div>
        <input id="volume" type="range" min="0" max="60" value="30" onchange="cmd('set_volume',{{value:Number(this.value)}})">
        <label>Uitvoerapparaat <select id="outputs" onchange="this.value && cmd('set_output',{{value:this.value}})"></select></label>
        <button onclick="refreshAll()">Verversen</button>
      </div>
    </section>
    <section>
      <h2>Wachtrij</h2>
      <div id="queue" class="list"></div>
    </section>
    <section>
      <h2>Afspeellijsten</h2>
      <div id="playlists" class="list"></div>
    </section>
    <section>
      <h2>Instellingen</h2>
      <div class="grid">
        <label>Taal <select id="language"><option value="nl">Nederlands</option><option value="en">English</option></select></label>
        <label>Logniveau <select id="logLevel"><option>DEBUG</option><option>INFO</option><option>WARNING</option><option>ERROR</option></select></label>
        <label>Schermhelderheid <input id="brightness" type="range" min="10" max="100"></label>
        <label>Scherm uit na seconden <select id="timeout"><option>30</option><option>60</option><option>90</option><option>120</option><option>180</option><option>240</option><option>300</option><option>600</option></select></label>
        <button onclick="saveSettings()">Instellingen opslaan</button>
        <button onclick="cmd('check_updates')">Controleer op updates</button>
        <button class="danger" onclick="confirm('Opnieuw koppelen?')&&cmd('forget_pairing')">Opnieuw koppelen</button>
        <button class="danger" onclick="confirm('Apparaat herstarten?')&&cmd('reboot')">Apparaat herstarten</button>
        <button class="danger" onclick="confirm('Apparaat uitschakelen?')&&cmd('shutdown')">Apparaat uitschakelen</button>
      </div>
    </section>
    <section>
      <h2>Over</h2>
      <div id="about" class="grid"></div>
    </section>
    <section>
      <h2>Diagnostics</h2>
      <div id="diagnostics" class="diag-list"></div>
    </section>
    <section class="wide">
      <h2>Logs</h2>
      <div class="two" style="margin-bottom:10px"><button class="secondary" onclick="copyLogs()">Logs kopiëren</button><button class="secondary" onclick="refreshLogs()">Logs verversen</button></div>
      <pre id="logs">Logs laden...</pre>
    </section>
  </main>
  <div id="toast" class="toast"></div>
<script>
let state = {{}};
let toastTimer = 0;
function toast(message) {{
  const el = document.getElementById('toast');
  el.textContent = message;
  el.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), 5000);
}}
async function api(path, options={{}}) {{
  const res = await fetch(path, Object.assign({{headers:{{'Content-Type':'application/json'}}}}, options));
  const data = await res.json();
  if (!res.ok || data.success === false) throw new Error(data.error || data.message || `HTTP ${{res.status}}`);
  return data;
}}
function playCommand() {{ return state.playback && state.playback.is_playing ? 'pause' : 'play'; }}
function toggleShuffle() {{ cmd('set_shuffle', {{value: !(state.playback && state.playback.shuffle)}}); }}
function toggleRepeat() {{
  const current = (state.playback && state.playback.repeat_state) || 'off';
  cmd('set_repeat', {{value: current === 'off' ? 'context' : current === 'context' ? 'track' : 'off'}});
}}
async function cmd(command, payload={{}}) {{
  try {{
    await api('/api/portal/command', {{method:'POST', body:JSON.stringify(Object.assign({{command}}, payload))}});
    toast('Commando verzonden');
    setTimeout(refreshAll, 450);
  }} catch (err) {{ toast(`Mislukt: ${{err.message}}`); }}
}}
async function saveSettings() {{
  await cmd('settings', {{
    language: document.getElementById('language').value,
    log_level: document.getElementById('logLevel').value,
    screen_brightness_percent: Number(document.getElementById('brightness').value),
    screen_timeout_seconds: Number(document.getElementById('timeout').value)
  }});
}}
function itemHtml(item, command) {{
  const art = item.imageUrl ? `<img class="thumb" src="${{item.imageUrl}}" alt="">` : `<div class="thumb">♪</div>`;
  const title = item.title || '-';
  const sub = item.subtitle || '';
  const uri = item.uri || title;
  return `<div class="item">${{art}}<div><div class="item-title">${{title}}</div><div class="item-sub">${{sub}}</div></div><button class="play" onclick="cmd('${{command}}',{{value:${{JSON.stringify(uri)}}}})">▶</button></div>`;
}}
function diagnosticsHtml(item) {{
  const status = item.status || 'unknown';
  return `<div class="diag"><div><div class="diag-name">${{item.name || '-'}}</div><div class="diag-detail">${{item.detail || ''}}</div></div><span class="chip ${{status}}">${{status}}</span></div>`;
}}
function render(data) {{
  state = data;
  const playback = data.playback || {{}};
  document.getElementById('statusDot').classList.toggle('ok', !!data.backend_available);
  document.getElementById('statusText').textContent = data.status_text || (data.paired ? 'Verbonden' : 'Niet gekoppeld');
  document.getElementById('title').textContent = playback.title || 'Niets speelt af';
  document.getElementById('artist').textContent = playback.artist || '';
  document.getElementById('art').src = playback.image_url || '';
  const volume = Math.min(60, playback.volume ?? 30);
  document.getElementById('volume').value = volume;
  document.getElementById('volumePercent').textContent = `${{Math.round(volume / 60 * 100)}}%`;
  document.getElementById('playButton').textContent = playback.is_playing ? '⏸' : '▶';
  document.getElementById('shuffleButton').classList.toggle('active', !!playback.shuffle);
  document.getElementById('repeatButton').classList.toggle('active', (playback.repeat_state || 'off') !== 'off');
  const outputs = document.getElementById('outputs');
  outputs.innerHTML = '';
  for (const name of (playback.output_devices || [])) {{
    const option = document.createElement('option');
    option.value = name; option.textContent = name; option.selected = name === playback.output_device;
    outputs.appendChild(option);
  }}
  if (!outputs.children.length) outputs.innerHTML = '<option value="">Geen uitvoerapparaten</option>';
  document.getElementById('queue').innerHTML = (data.queue || []).length ? data.queue.map(i => itemHtml(i,'start_queue_item')).join('') : '<div class="sub">Geen wachtrij</div>';
  document.getElementById('playlists').innerHTML = (data.playlists || []).length ? data.playlists.map(i => itemHtml(i,'start_playlist')).join('') : '<div class="sub">Geen afspeellijsten</div>';
  document.getElementById('language').value = data.settings?.language || 'nl';
  document.getElementById('logLevel').value = data.settings?.log_level || 'INFO';
  document.getElementById('brightness').value = data.settings?.screen_brightness_percent || 100;
  document.getElementById('timeout').value = String(data.settings?.screen_timeout_seconds ?? 120);
  document.getElementById('about').innerHTML = Object.entries(data.about || {{}}).map(([k,v]) => `<div class="row"><span class="key">${{k}}</span><span class="value">${{v || '-'}}</span></div>`).join('');
  document.getElementById('diagnostics').innerHTML = (data.diagnostics || []).length ? data.diagnostics.map(diagnosticsHtml).join('') : '<div class="sub">Geen diagnostics beschikbaar</div>';
  document.getElementById('logs').textContent = data.logs || '';
}}
async function refreshAll() {{
  try {{ render(await api('/api/portal/state?include=queue,playlists,logs')); }}
  catch (err) {{ toast(`Status mislukt: ${{err.message}}`); }}
}}
async function refreshLogs() {{
  try {{ document.getElementById('logs').textContent = (await api('/api/portal/state?include=logs')).logs || ''; }}
  catch (err) {{ toast(`Logs mislukt: ${{err.message}}`); }}
}}
function copyLogs() {{ navigator.clipboard.writeText(document.getElementById('logs').textContent || ''); toast('Logs gekopieerd'); }}
refreshAll();
setInterval(refreshAll, 15000);
</script>
</body>
</html>
""".encode("utf-8")
