from __future__ import annotations

from html import escape
import re


def index_html(version: str) -> bytes:
    version_text = escape(version)
    html = f"""<!doctype html>
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
    .volume-controls {{ display:grid; grid-template-columns:56px 1fr 56px; gap:10px; align-items:center; }}
    button, select, input {{
      min-height:48px; border-radius:8px; border:1px solid rgba(217,177,255,.48);
      background:linear-gradient(135deg,rgba(193,53,255,.88),rgba(75,125,255,.72));
      color:white; font-size:17px; font-weight:800; padding:8px 12px;
    }}
    select, input {{ background:rgba(16,10,42,.9); font-weight:700; width:100%; }}
    button.secondary {{ background:rgba(30,24,66,.86); }}
    button.warning {{ background:#8a5a12; color:#fff3c4; }}
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
    .game-wrap {{ display:grid; gap:10px; }}
    .game-tabs {{ display:grid; grid-template-columns:repeat(4,1fr); gap:8px; }}
    .game-tabs button.active {{ border-color:#fff; background:linear-gradient(135deg,#f13de8,#4b7dff); }}
    #gameCanvas {{ width:100%; aspect-ratio:320/170; border:1px solid var(--line); border-radius:8px; background:#05080a; touch-action:none; image-rendering:pixelated; }}
    .game-hud {{ display:flex; justify-content:space-between; gap:10px; color:var(--muted); font-weight:800; }}
    .game-controls {{ display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:8px; }}
    .game-controls button {{ min-height:54px; padding:6px; }}
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
    .toast {{ position:fixed; left:50%; bottom:28px; width:max-content; max-width:calc(100% - 32px); opacity:0; transform:translate(-50%,16px); transition:.18s; background:linear-gradient(90deg,#ff5a2e,#f13ccc 52%,#b731ff); border:2px solid rgba(255,255,255,.70); border-radius:999px; padding:16px 28px; font-weight:900; font-size:18px; color:white; box-shadow:0 0 44px rgba(255,91,50,.46),0 0 74px rgba(190,49,255,.32); z-index:20; }}
    .toast::before {{ content:"▶"; display:inline-block; margin-right:14px; font-size:18px; }}
    .toast.show {{ opacity:1; transform:translate(-50%,0); }}
    button.busy {{ opacity:.72; cursor:progress; }}
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
        <div class="volume-head"><span data-i18n="volume">Volume</span><span id="volumePercent">0%</span></div>
        <div class="volume-controls"><button onclick="adjustVolume(-10)">-10</button><input id="volume" type="range" min="0" max="60" value="30" onchange="cmd('set_volume',{{value:Number(this.value)}})"><button onclick="adjustVolume(10)">+10</button></div>
        <label><span data-i18n="output_device">Uitvoerapparaat</span> <select id="outputs" onchange="selectOutput(this.value)"></select></label>
        <button id="refreshButton" onclick="refreshAll(true)" data-i18n="refresh">Verversen</button>
      </div>
    </section>
    <section>
      <h2 data-i18n="queue">Wachtrij</h2>
      <div id="queue" class="list"></div>
    </section>
    <section>
      <h2 data-i18n="playlists">Afspeellijsten</h2>
      <div id="playlists" class="list"></div>
    </section>
    <section class="wide">
      <h2 data-i18n="games">Games</h2>
      <div class="game-wrap">
        <div id="gameTabs" class="game-tabs"></div>
        <div class="game-hud"><span id="gameName">Paddle Rally</span><span><span data-i18n="score">Score</span> <span id="gameScore">0</span> · <span data-i18n="high">Beste</span> <span id="gameHigh">0</span></span></div>
        <canvas id="gameCanvas" width="320" height="170"></canvas>
        <div id="gameControls" class="game-controls"></div>
        <div id="gameHelp" class="sub"></div>
      </div>
    </section>
    <section>
      <h2 data-i18n="settings">Instellingen</h2>
      <div class="grid">
        <label><span data-i18n="language">Taal</span> <select id="language" onchange="saveSettings(t('language_saved'))"><option value="nl">Nederlands</option><option value="en">English</option></select></label>
        <label><span data-i18n="log_level">Logniveau</span> <select id="logLevel" onchange="saveSettings(t('log_level_saved'))"><option>DEBUG</option><option>INFO</option><option>WARNING</option><option>ERROR</option></select></label>
        <label><span data-i18n="brightness">Schermhelderheid</span> <input id="brightness" type="range" min="10" max="100" oninput="saveSettingsDebounced(t('brightness_saved'))" onchange="saveSettings(t('brightness_saved'))"></label>
        <label><span data-i18n="screen_off">Scherm uit na seconden</span> <select id="timeout" onchange="saveSettings(t('screen_timeout_saved'))"><option>30</option><option>60</option><option>90</option><option>120</option><option>180</option><option>240</option><option>300</option><option>600</option></select></label>
        <button onclick="cmd('check_updates')" data-i18n="check_updates">Controleer op updates</button>
        <button class="danger" onclick="confirm(t('reset_pairing_confirm'))&&cmd('forget_pairing')" data-i18n="reset_pairing">Opnieuw koppelen</button>
        <button class="warning" onclick="confirm(t('reboot_confirm'))&&cmd('reboot')" data-i18n="reboot_device">Apparaat herstarten</button>
        <button class="danger" onclick="confirm(t('shutdown_confirm'))&&cmd('shutdown')" data-i18n="shutdown_device">Apparaat uitschakelen</button>
      </div>
    </section>
    <section>
      <h2 data-i18n="about">Over</h2>
      <div id="about" class="grid"></div>
    </section>
    <section>
      <h2>Diagnostics</h2>
      <div id="diagnostics" class="diag-list"></div>
    </section>
    <section class="wide">
      <h2>Logs</h2>
      <div class="two" style="margin-bottom:10px"><button class="secondary" onclick="copyLogs()" data-i18n="copy_logs">Logs kopiëren</button><button id="logsRefreshButton" class="secondary" onclick="refreshLogs(true)" data-i18n="refresh_logs">Logs verversen</button></div>
      <pre id="logs">Logs laden...</pre>
    </section>
  </main>
  <div id="toast" class="toast"></div>
<script>
let state = {{}};
let settingsTimer = 0;
let toastTimer = 0;
const I18N = {{
  nl: {{
    loading:'Laden...', connected:'Verbonden', not_paired:'Niet gekoppeld', nothing_playing:'Niets speelt af',
    volume:'Volume', output_device:'Uitvoerapparaat', none:'Geen', refresh:'Verversen', refreshing:'Verversen...',
    queue:'Wachtrij', playlists:'Afspeellijsten', settings:'Instellingen', language:'Taal', log_level:'Logniveau',
    brightness:'Schermhelderheid', screen_off:'Scherm uit na seconden', check_updates:'Controleer op updates',
    reset_pairing:'Opnieuw koppelen', reboot_device:'Apparaat herstarten', shutdown_device:'Apparaat uitschakelen',
    about:'Over', copy_logs:'Logs kopiëren', refresh_logs:'Logs verversen', logs_loading:'Logs laden...',
    command_sent:'Commando verzonden', command_failed:'Mislukt', refreshed:'Verversd', status_failed:'Status mislukt',
    logs_refreshed:'Logs ververst', logs_failed:'Logs mislukt', copied:'Gekopieerd naar klembord', copy_failed:'Kopieren mislukt',
    settings_saved:'Instellingen opgeslagen', save_failed:'Opslaan mislukt', language_saved:'Taal opgeslagen',
    log_level_saved:'Logniveau opgeslagen', brightness_saved:'Helderheid opgeslagen', screen_timeout_saved:'Schermtijd opgeslagen',
    empty_queue:'Geen wachtrij', empty_playlists:'Geen afspeellijsten', no_diagnostics:'Geen diagnostics beschikbaar',
    reset_pairing_confirm:'Opnieuw koppelen?', reboot_confirm:'Apparaat herstarten?', shutdown_confirm:'Apparaat uitschakelen?',
    games:'Games', score:'Score', high:'Beste', game_pong:'Paddle Rally', game_asteroids:'Meteor Run', game_fly:'Sky Dash', game_pacman:'Maze Chase',
    up:'Omhoog', down:'Omlaag', left:'Links', right:'Rechts', fire:'Schiet', reset:'Reset',
    game_help_pong:'Beweeg het batje omhoog en omlaag.',
    game_help_asteroids:'Beweeg links en rechts. Schiet om meteorieten te raken.',
    game_help_fly:'Vlieg omhoog of omlaag. Schiet obstakels kapot.',
    game_help_pacman:'Eet bolletjes. Power-bolletjes maken het spookje kwetsbaar.'
  }},
  en: {{
    loading:'Loading...', connected:'Connected', not_paired:'Not paired', nothing_playing:'Nothing playing',
    volume:'Volume', output_device:'Output device', none:'None', refresh:'Refresh', refreshing:'Refreshing...',
    queue:'Queue', playlists:'Playlists', settings:'Settings', language:'Language', log_level:'Log level',
    brightness:'Screen brightness', screen_off:'Screen off after seconds', check_updates:'Check for updates',
    reset_pairing:'Reset pairing', reboot_device:'Restart device', shutdown_device:'Shut down device',
    about:'About', copy_logs:'Copy logs', refresh_logs:'Refresh logs', logs_loading:'Loading logs...',
    command_sent:'Command sent', command_failed:'Failed', refreshed:'Refreshed', status_failed:'Status failed',
    logs_refreshed:'Logs refreshed', logs_failed:'Logs failed', copied:'Copied to clipboard', copy_failed:'Copy failed',
    settings_saved:'Settings saved', save_failed:'Save failed', language_saved:'Language saved',
    log_level_saved:'Log level saved', brightness_saved:'Brightness saved', screen_timeout_saved:'Screen timeout saved',
    empty_queue:'No queue', empty_playlists:'No playlists', no_diagnostics:'No diagnostics available',
    reset_pairing_confirm:'Reset pairing?', reboot_confirm:'Restart device?', shutdown_confirm:'Shut down device?',
    games:'Games', score:'Score', high:'High', game_pong:'Paddle Rally', game_asteroids:'Meteor Run', game_fly:'Sky Dash', game_pacman:'Maze Chase',
    up:'Up', down:'Down', left:'Left', right:'Right', fire:'Fire', reset:'Reset',
    game_help_pong:'Move the paddle up and down.',
    game_help_asteroids:'Move left and right. Fire to hit meteors.',
    game_help_fly:'Fly up or down. Shoot obstacles apart.',
    game_help_pacman:'Eat pellets. Power pellets make the ghost vulnerable.'
  }}
}};
function currentLanguage() {{ return (state.settings && state.settings.language) || document.getElementById('language')?.value || 'nl'; }}
function t(key) {{ const lang = currentLanguage(); return (I18N[lang] && I18N[lang][key]) || I18N.nl[key] || key; }}
function translateStatic() {{
  document.documentElement.lang = currentLanguage();
  for (const el of document.querySelectorAll('[data-i18n]')) el.textContent = t(el.dataset.i18n);
  renderGameShell();
}}
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
    toast(t('command_sent'));
    setTimeout(refreshAll, 450);
  }} catch (err) {{ toast(`${{t('command_failed')}}: ${{err.message}}`); }}
}}
function selectOutput(value) {{
  cmd('set_output', {{value}});
}}
function setBusy(id, busy, label) {{
  const el = document.getElementById(id);
  if (!el) return;
  if (busy) {{
    el.dataset.label = el.textContent;
    el.textContent = label || t('refreshing');
    el.classList.add('busy');
    el.disabled = true;
  }} else {{
    el.textContent = el.dataset.label || t('refresh');
    el.classList.remove('busy');
    el.disabled = false;
  }}
}}
function scrollLogsToBottom() {{
  const logs = document.getElementById('logs');
  logs.scrollTop = logs.scrollHeight;
}}
function settingsPayload() {{
  return {{
    language: document.getElementById('language').value,
    log_level: document.getElementById('logLevel').value,
    screen_brightness_percent: Number(document.getElementById('brightness').value),
    screen_timeout_seconds: Number(document.getElementById('timeout').value)
  }};
}}
async function saveSettings(message=t('settings_saved')) {{
  try {{
    if (!state.settings) state.settings = {{}};
    Object.assign(state.settings, settingsPayload());
    translateStatic();
    await api('/api/portal/command', {{method:'POST', body:JSON.stringify(Object.assign({{command:'settings'}}, settingsPayload()))}});
    toast(message);
    setTimeout(refreshAll, 350);
  }} catch (err) {{ toast(`${{t('save_failed')}}: ${{err.message}}`); }}
}}
function saveSettingsDebounced(message) {{
  clearTimeout(settingsTimer);
  settingsTimer = setTimeout(() => saveSettings(message), 220);
}}
function itemHtml(item, command) {{
  const art = item.imageUrl ? `<img class="thumb" src="${{item.imageUrl}}" alt="">` : `<div class="thumb">♪</div>`;
  const title = item.title || '-';
  const sub = item.subtitle || '';
  const usable = !!item.uri;
  const encoded = encodeURIComponent(JSON.stringify(item));
  const action = usable ? `playMedia('${{command}}','${{encoded}}')` : '';
  return `<div class="item" role="button" tabindex="0" ${{usable ? `onclick="${{action}}"` : 'aria-disabled="true" style="opacity:.45"'}}>${{art}}<div><div class="item-title">${{title}}</div><div class="item-sub">${{sub}}</div></div><button class="play" ${{usable ? `onclick="event.stopPropagation();${{action}}"` : 'disabled'}}>▶</button></div>`;
}}
function mediaPayload(command, item) {{
  const uri = item.uri || item.value || '';
  if (!uri) return null;
  if (command === 'start_playlist') return {{value:uri, uri:uri, context_uri:uri}};
  const payload = {{value:uri, uri:uri}};
  if (item.title) payload.title = item.title;
  if (item.artist || item.subtitle) payload.artist = item.artist || item.subtitle;
  if (Number.isInteger(item.index)) payload.index = item.index;
  const context = item.context_uri || item.contextUri || item.queue_context || item.queueContext || '';
  if (context) {{
    payload.context_uri = context;
    if (context.startsWith('spotify:playlist:') || context.startsWith('spotify:album:') || context.startsWith('spotify:show:')) payload.offset_uri = uri;
  }}
  return payload;
}}
function playMedia(command, encodedItem) {{
  const item = JSON.parse(decodeURIComponent(encodedItem));
  const payload = mediaPayload(command, item);
  if (!payload) return;
  cmd(command, payload);
}}
const gameDefs = [
  {{id:'pong', key:'game_pong'}}, {{id:'asteroids', key:'game_asteroids'}}, {{id:'fly', key:'game_fly'}}, {{id:'pacman', key:'game_pacman'}}
];
let game = {{id:'pong', score:0, high:JSON.parse(localStorage.getItem('djconnect-pi-game-high')||'{{}}'), playing:true, t:0, pause:0, flash:0, ex:[]}};
function sfx(kind) {{
  try {{
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return;
    const ctx = sfx.ctx || (sfx.ctx = new AudioCtx());
    const o = ctx.createOscillator(), g = ctx.createGain();
    const freq = {{start:220, move:180, fire:760, pellet:520, power:300, ghost:880, death:90, hit:430, wall:260, explode:120, crash:70, gameover:100}}[kind] || 240;
    o.type = 'square'; o.frequency.setValueAtTime(freq, ctx.currentTime);
    o.frequency.exponentialRampToValueAtTime(Math.max(40, freq * .55), ctx.currentTime + .09);
    g.gain.setValueAtTime(.025, ctx.currentTime); g.gain.exponentialRampToValueAtTime(.001, ctx.currentTime + .10);
    o.connect(g); g.connect(ctx.destination); o.start(); o.stop(ctx.currentTime + .11);
    if (navigator.vibrate) navigator.vibrate(8);
  }} catch (_) {{}}
}}
function gameSetScore(v) {{
  game.score = v;
  if ((game.high[game.id] || 0) < v) {{
    game.high[game.id] = v;
    localStorage.setItem('djconnect-pi-game-high', JSON.stringify(game.high));
  }}
}}
function gameReset() {{
  Object.assign(game, {{score:0, playing:true, t:0, pause:0, flash:0, ex:[], stars:Array.from({{length:34}},()=>({{x:Math.random()*320,y:25+Math.random()*135,s:.4+Math.random()*2,p:Math.random()*6}})),
    paddleY:85, ballX:160, ballY:85, ballVX:3, ballVY:2, shipX:160, bullet:false, bulletY:120, planeY:85, shot:false, shotX:58,
    pacX:46, pacY:86, pacDX:1, pacDY:0, ghostX:250, ghostY:86, vuln:0, death:0, pellets:Array.from({{length:32}},(_,i)=>i), power:[0,7,24,31] }});
  resetMeteor(); resetObstacle(); renderGameShell(); sfx('start');
}}
function resetMeteor() {{ game.metX=40+Math.random()*240; game.metY=30; game.metSize=6+Math.random()*7; game.metSpeed=.9+Math.random()*1.3+Math.min(game.score/35,1.4); game.metShape=Math.floor(Math.random()*3); }}
function resetObstacle() {{ game.obsX=310; game.obsY=48+Math.random()*92; game.obsShape=Math.floor(Math.random()*4); game.obsColor=['#9a6b3f','#e879f9','#38bdf8','#facc15'][game.obsShape]; }}
function selectGame(id) {{ game.id=id; gameReset(); }}
function gameMove(dx,dy) {{
  sfx('move');
  if (game.id==='pong') game.paddleY=Math.max(42,Math.min(126,game.paddleY+dy*13));
  else if (game.id==='asteroids') game.shipX=Math.max(24,Math.min(296,game.shipX+dx*15));
  else if (game.id==='fly') game.planeY=Math.max(52,Math.min(138,game.planeY+dy*13));
  else {{ if (dx) {{game.pacDX=dx; game.pacDY=0;}} if (dy) {{game.pacDY=dy; game.pacDX=0;}} }}
}}
function gameFire() {{ if (game.id==='asteroids'&&!game.bullet){{game.bullet=true;game.bulletY=120;sfx('fire');}} if(game.id==='fly'&&!game.shot){{game.shot=true;game.shotX=58;sfx('fire');}} }}
function gameBoom(x,y,c) {{ game.ex.push({{x,y,c,a:0}}); }}
function gameOver(kind) {{ game.flash=12; gameSetScore(0); sfx(kind||'gameover'); }}
function gameTick() {{
  game.t++;
  for (const st of game.stars||[]) {{ st.x-=st.s*(game.id==='fly'?1.8:.45); st.p+=.08; if(st.x<0){{st.x=320;st.y=25+Math.random()*135;}} }}
  for (let i=game.ex.length-1;i>=0;i--) if (++game.ex[i].a>18) game.ex.splice(i,1);
  if (game.pause>0) {{ game.pause--; drawGame(); return; }}
  if (game.flash>0) game.flash--;
  if (game.id==='pong') {{
    game.ballX+=game.ballVX; game.ballY+=game.ballVY;
    if(game.ballY<=42||game.ballY>=156){{game.ballVY*=-1;sfx('wall');}}
    if(game.ballX>=306){{game.ballVX=-Math.abs(game.ballVX);sfx('wall');}}
    if(game.ballX<=30){{ if(Math.abs(game.ballY-game.paddleY)<22){{game.ballVX=Math.abs(game.ballVX);game.hit=8;gameSetScore(game.score+1);sfx('hit');}} else {{gameOver('gameover');game.ballX=160;game.ballY=86;game.pause=28;}} }}
  }} else if (game.id==='asteroids') {{
    game.metY+=game.metSpeed;
    if(game.bullet){{game.bulletY-=8;if(game.bulletY<34)game.bullet=false;else if(Math.abs(game.metX-game.shipX)<game.metSize+8&&Math.abs(game.metY-game.bulletY)<game.metSize+8){{game.bullet=false;gameBoom(game.metX,game.metY,'#ff6fb3');gameSetScore(game.score+1);sfx('explode');resetMeteor();}}}}
    if(game.metY>152){{gameOver('gameover');resetMeteor();}}
  }} else if (game.id==='fly') {{
    game.obsX-=4+Math.min(Math.floor(game.score/6),4);
    if(game.shot){{game.shotX+=9;if(game.shotX>310)game.shot=false;else if(Math.abs(game.shotX-game.obsX)<16&&Math.abs(game.planeY-game.obsY)<24){{game.shot=false;gameBoom(game.obsX,game.obsY,'#facc15');gameSetScore(game.score+1);sfx('explode');resetObstacle();}}}}
    if(game.obsX<20){{gameSetScore(game.score+1);resetObstacle();}}
    if(game.obsX<66&&game.obsX>28&&Math.abs(game.planeY-game.obsY)<28){{gameBoom(48,game.planeY,'#ff5b5b');gameOver('crash');resetObstacle();}}
  }} else {{
    if(game.death>0){{ if(--game.death===0){{gameSetScore(0);gameReset();}} drawGame(); return; }}
    game.pacX=Math.max(28,Math.min(292,game.pacX+game.pacDX*4)); game.pacY=Math.max(44,Math.min(150,game.pacY+game.pacDY*4)); if(game.vuln>0)game.vuln--;
    const step=game.vuln>0?1:1.35+Math.min(Math.floor(game.score/14)*.45,1.8); if(Math.abs(game.ghostX-game.pacX)>2)game.ghostX+=game.ghostX<game.pacX?step:-step; if(Math.abs(game.ghostY-game.pacY)>2)game.ghostY+=game.ghostY<game.pacY?step:-step;
    for(let p=0;p<game.pellets.length;p++){{ const pellet=game.pellets[p], px=48+(pellet%8)*28, py=52+Math.floor(pellet/8)*28; if(Math.abs(px-game.pacX)<10&&Math.abs(py-game.pacY)<10){{game.pellets.splice(p,1); if(game.power.includes(pellet)){{game.vuln=210;gameSetScore(game.score+3);sfx('power');}}else{{gameSetScore(game.score+1);sfx('pellet');}} break;}} }}
    if(!game.pellets.length)gameReset();
    if(Math.abs(game.ghostX-game.pacX)<14&&Math.abs(game.ghostY-game.pacY)<14){{ if(game.vuln>0){{gameSetScore(game.score+5);game.ghostX=250;game.ghostY=86;game.vuln=0;sfx('ghost');}} else {{game.flash=12;game.death=34;sfx('death');}} }}
  }}
  drawGame();
}}
function drawGame() {{
  const c=document.getElementById('gameCanvas'); if(!c) return; const x=c.getContext('2d'); x.clearRect(0,0,320,170); x.fillStyle='#05080a'; x.fillRect(0,0,320,170);
  if(game.id==='asteroids'||game.id==='fly') for(const st of game.stars||[]){{x.fillStyle=`rgba(255,255,255,${{game.id==='fly'?.28:.32+Math.sin(st.p)*.18}})`; game.id==='fly'?x.fillRect(st.x,st.y,8+st.s*4,1):x.fillRect(st.x,st.y,1.2,1.2);}}
  x.strokeStyle='#26383d'; x.strokeRect(1,1,318,168); x.fillStyle='#c9b8ff'; x.font='14px sans-serif'; x.fillText(t(gameDefs.find(g=>g.id===game.id).key),12,20);
  if(game.id==='pong'){{x.setLineDash([5,7]);x.strokeStyle='rgba(255,255,255,.22)';x.beginPath();x.moveTo(160,28);x.lineTo(160,150);x.stroke();x.setLineDash([]);x.fillStyle='#ff9f43';x.fillRect(18-(game.hit?2:0),game.paddleY-17,game.hit?12:8,34);if(game.hit)game.hit--;x.fillStyle='#1db954';x.beginPath();x.arc(game.ballX,game.ballY,4,0,7);x.fill();}}
  else if(game.id==='asteroids'){{x.strokeStyle='#4aa3ff';x.beginPath();x.moveTo(game.shipX,128);x.lineTo(game.shipX-9,146);x.lineTo(game.shipX+9,146);x.closePath();x.stroke();x.strokeStyle=['#ff6fb3','#facc15','#a78bfa'][game.metShape];x.beginPath();game.metShape===0?x.arc(game.metX,game.metY,game.metSize,0,7):game.metShape===1?x.rect(game.metX-game.metSize,game.metY-game.metSize,game.metSize*2,game.metSize*2):(x.moveTo(game.metX,game.metY-game.metSize),x.lineTo(game.metX+game.metSize,game.metY+game.metSize),x.lineTo(game.metX-game.metSize,game.metY+game.metSize*.8),x.closePath());x.stroke();if(game.bullet){{x.fillStyle='#48d8ff';x.fillRect(game.shipX-2,game.bulletY,4,10);}}}}
  else if(game.id==='fly'){{x.fillStyle='#48d8ff';x.beginPath();x.moveTo(62,game.planeY);x.lineTo(30,game.planeY-12);x.lineTo(30,game.planeY+12);x.closePath();x.fill();x.fillStyle=game.obsColor;x.beginPath();game.obsShape===0?x.fillRect(game.obsX-8,game.obsY-18,16,36):game.obsShape===1?(x.arc(game.obsX,game.obsY,13,0,7),x.fill()):game.obsShape===2?(x.moveTo(game.obsX,game.obsY-18),x.lineTo(game.obsX+16,game.obsY),x.lineTo(game.obsX,game.obsY+18),x.lineTo(game.obsX-16,game.obsY),x.closePath(),x.fill()):x.fillRect(game.obsX-14,game.obsY-8,28,16);if(game.shot){{x.fillStyle='#d9fbff';x.fillRect(game.shotX,game.planeY-2,14,4);}}}}
  else {{x.fillStyle='rgba(255,255,255,.82)';for(const p of game.pellets){{x.beginPath();x.arc(48+(p%8)*28,52+Math.floor(p/8)*28,game.power.includes(p)?5:2,0,7);x.fill();}}const dir=game.pacDX<0?Math.PI:game.pacDY<0?4.71:game.pacDY>0?1.57:0;x.fillStyle='#ffe35a';x.beginPath();x.moveTo(game.pacX,game.pacY);x.arc(game.pacX,game.pacY,10,dir+.6,dir+6.28-.6);x.closePath();x.fill();x.fillStyle='#111827';x.beginPath();x.arc(game.pacX+(game.pacDX||.7)*3,game.pacY+(game.pacDY?game.pacDY*3:-4),1.8,0,7);x.fill();if(game.death){{x.strokeStyle='#fff7ad';x.beginPath();x.arc(game.pacX,game.pacY,16+(34-game.death)*.7,0,7);x.stroke();}}const blink=game.vuln>0&&Math.floor(game.vuln/12)%2===0;x.fillStyle=game.vuln>0?(blink?'#e0f2fe':'#3b82f6'):'#ff6fb3';x.beginPath();x.arc(game.ghostX,game.ghostY-2,9,Math.PI,0);x.lineTo(game.ghostX+9,game.ghostY+9);x.lineTo(game.ghostX+4,game.ghostY+5);x.lineTo(game.ghostX,game.ghostY+9);x.lineTo(game.ghostX-4,game.ghostY+5);x.lineTo(game.ghostX-9,game.ghostY+9);x.closePath();x.fill();}}
  for(const b of game.ex){{x.globalAlpha=Math.max(0,1-b.a/18);x.strokeStyle=b.c;x.lineWidth=3;x.beginPath();x.arc(b.x,b.y,4+b.a*1.5,0,7);x.stroke();x.globalAlpha=1;}} if(game.flash){{x.strokeStyle='#ff5b5b';x.lineWidth=5;x.strokeRect(4,4,312,162);}}
  document.getElementById('gameScore').textContent=game.score; document.getElementById('gameHigh').textContent=game.high[game.id]||0;
}}
function renderGameShell() {{
  const tabs=document.getElementById('gameTabs'); if(!tabs) return; tabs.innerHTML=gameDefs.map(g=>`<button class="${{g.id===game.id?'active':''}}" onclick="selectGame('${{g.id}}')">${{t(g.key)}}</button>`).join('');
  document.getElementById('gameName').textContent=t(gameDefs.find(g=>g.id===game.id).key); document.getElementById('gameHelp').textContent=t('game_help_'+(game.id==='pong'?'pong':game.id==='asteroids'?'asteroids':game.id==='fly'?'fly':'pacman'));
  const dirs=game.id==='pacman'?[['↑',0,-1],['↓',0,1],['←',-1,0],['→',1,0]]:game.id==='asteroids'?[['←',-1,0],['→',1,0]]:[['↑',0,-1],['↓',0,1]];
  document.getElementById('gameControls').innerHTML=dirs.map(d=>`<button onclick="gameMove(${{d[1]}},${{d[2]}})">${{d[0]}}</button>`).join('')+(game.id==='asteroids'||game.id==='fly'?`<button onclick="gameFire()">${{t('fire')}}</button>`:'')+`<button onclick="gameReset()">${{t('reset')}}</button>`;
  drawGame();
}}
document.addEventListener('keydown', e=>{{ if(e.key==='ArrowUp')gameMove(0,-1); else if(e.key==='ArrowDown')gameMove(0,1); else if(e.key==='ArrowLeft')gameMove(-1,0); else if(e.key==='ArrowRight')gameMove(1,0); else if(e.key===' ')gameFire(); }});
document.addEventListener('pointerdown', e=>{{ if(e.target&&e.target.id==='gameCanvas'){{const r=e.target.getBoundingClientRect(); const gx=(e.clientX-r.left)/r.width*320, gy=(e.clientY-r.top)/r.height*170; if(game.id==='pong')game.paddleY=Math.max(42,Math.min(126,gy)); else if(game.id==='asteroids')game.shipX=Math.max(24,Math.min(296,gx)); else if(game.id==='fly')game.planeY=Math.max(52,Math.min(138,gy)); else gameMove(Math.abs(gx-game.pacX)>Math.abs(gy-game.pacY)?(gx<game.pacX?-1:1):0,Math.abs(gx-game.pacX)>Math.abs(gy-game.pacY)?0:(gy<game.pacY?-1:1)); }}}});
function adjustVolume(delta) {{
  const current = Number(document.getElementById('volume').value || 0);
  const value = Math.max(0, Math.min(60, current + delta));
  document.getElementById('volume').value = value;
  document.getElementById('volumePercent').textContent = `${{Math.round(value / 60 * 100)}}%`;
  cmd('set_volume', {{value}});
}}
function diagnosticsHtml(item) {{
  const status = item.status || 'unknown';
  return `<div class="diag"><div><div class="diag-name">${{item.name || '-'}}</div><div class="diag-detail">${{item.detail || ''}}</div></div><span class="chip ${{status}}">${{status}}</span></div>`;
}}
function render(data) {{
  state = data;
  translateStatic();
  const playback = data.playback || {{}};
  document.getElementById('statusDot').classList.toggle('ok', !!data.backend_available);
  document.getElementById('statusText').textContent = data.status_text || (data.paired ? t('connected') : t('not_paired'));
  document.getElementById('title').textContent = playback.title || t('nothing_playing');
  document.getElementById('artist').textContent = playback.artist || '';
  document.getElementById('art').src = playback.image_url || '';
  const volume = Math.min(60, playback.volume ?? 30);
  document.getElementById('volume').value = volume;
  document.getElementById('volumePercent').textContent = `${{Math.round(volume / 60 * 100)}}%`;
  document.getElementById('playButton').textContent = playback.is_playing ? '⏸' : '▶';
  document.getElementById('shuffleButton').classList.toggle('active', !!playback.shuffle);
  document.getElementById('repeatButton').classList.toggle('active', (playback.repeat_state || 'off') !== 'off');
  const outputs = document.getElementById('outputs');
  const selectedOutput = playback.output_device;
  outputs.innerHTML = '';
  const none = document.createElement('option');
  none.value = ''; none.textContent = t('none'); none.selected = !selectedOutput;
  outputs.appendChild(none);
  for (const name of (playback.output_devices || [])) {{
    const option = document.createElement('option');
    option.value = name; option.textContent = name; option.selected = name === selectedOutput;
    outputs.appendChild(option);
  }}
  document.getElementById('queue').innerHTML = (data.queue || []).length ? data.queue.map(i => itemHtml(i,'start_queue_item')).join('') : `<div class="sub">${{t('empty_queue')}}</div>`;
  document.getElementById('playlists').innerHTML = (data.playlists || []).length ? data.playlists.map(i => itemHtml(i,'start_playlist')).join('') : `<div class="sub">${{t('empty_playlists')}}</div>`;
  document.getElementById('language').value = data.settings?.language || 'nl';
  document.getElementById('logLevel').value = data.settings?.log_level || 'INFO';
  document.getElementById('brightness').value = data.settings?.screen_brightness_percent || 100;
  document.getElementById('timeout').value = String(data.settings?.screen_timeout_seconds ?? 120);
  document.getElementById('about').innerHTML = Object.entries(data.about || {{}}).map(([k,v]) => `<div class="row"><span class="key">${{k}}</span><span class="value">${{v || '-'}}</span></div>`).join('');
  document.getElementById('diagnostics').innerHTML = (data.diagnostics || []).length ? data.diagnostics.map(diagnosticsHtml).join('') : `<div class="sub">${{t('no_diagnostics')}}</div>`;
  document.getElementById('logs').textContent = data.logs || '';
}}
async function refreshAll(showBusy=false) {{
  if (showBusy) setBusy('refreshButton', true, t('refreshing'));
  try {{
    render(await api('/api/portal/state?include=queue,playlists,logs'));
    scrollLogsToBottom();
    if (showBusy) toast(t('refreshed'));
  }}
  catch (err) {{ toast(`${{t('status_failed')}}: ${{err.message}}`); }}
  finally {{ if (showBusy) setBusy('refreshButton', false); }}
}}
async function refreshLogs(showBusy=false) {{
  if (showBusy) setBusy('logsRefreshButton', true, t('refreshing'));
  try {{
    document.getElementById('logs').textContent = (await api('/api/portal/state?include=logs')).logs || '';
    scrollLogsToBottom();
    if (showBusy) toast(t('logs_refreshed'));
  }}
  catch (err) {{ toast(`${{t('logs_failed')}}: ${{err.message}}`); }}
  finally {{ if (showBusy) setBusy('logsRefreshButton', false, t('refresh_logs')); }}
}}
async function copyLogs() {{
  const logs = document.getElementById('logs');
  const text = logs.textContent || '';
  const range = document.createRange();
  range.selectNodeContents(logs);
  const selection = window.getSelection();
  selection.removeAllRanges();
  selection.addRange(range);
  try {{
    if (navigator.clipboard && window.isSecureContext) {{
      await navigator.clipboard.writeText(text);
    }} else {{
      document.execCommand('copy');
    }}
    toast(t('copied'));
  }} catch (err) {{
    toast(t('copy_failed'));
  }}
}}
refreshAll();
gameReset();
setInterval(gameTick, 33);
setInterval(refreshAll, 15000);
</script>
</body>
</html>
"""
    return _minify_html(html).encode("utf-8")


def _minify_html(html: str) -> str:
    html = re.sub(r">\s+<", "><", html)
    html = re.sub(r"\s{2,}", " ", html)
    html = re.sub(r"\s*([{}:;,>])\s*", r"\1", html)
    html = re.sub(r"\s*([=])\s*", r"\1", html)
    return html.strip()
