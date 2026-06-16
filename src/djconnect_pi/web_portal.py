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
    reset_pairing_confirm:'Opnieuw koppelen?', reboot_confirm:'Apparaat herstarten?', shutdown_confirm:'Apparaat uitschakelen?'
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
    reset_pairing_confirm:'Reset pairing?', reboot_confirm:'Restart device?', shutdown_confirm:'Shut down device?'
  }}
}};
function currentLanguage() {{ return (state.settings && state.settings.language) || document.getElementById('language')?.value || 'nl'; }}
function t(key) {{ const lang = currentLanguage(); return (I18N[lang] && I18N[lang][key]) || I18N.nl[key] || key; }}
function translateStatic() {{
  document.documentElement.lang = currentLanguage();
  for (const el of document.querySelectorAll('[data-i18n]')) el.textContent = t(el.dataset.i18n);
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
  const uri = item.uri || title;
  const encoded = encodeURIComponent(uri);
  return `<div class="item" role="button" tabindex="0" onclick="playMedia('${{command}}','${{encoded}}')">${{art}}<div><div class="item-title">${{title}}</div><div class="item-sub">${{sub}}</div></div><button class="play" onclick="event.stopPropagation();playMedia('${{command}}','${{encoded}}')">▶</button></div>`;
}}
function playMedia(command, encodedUri) {{
  const uri = decodeURIComponent(encodedUri);
  cmd(command, {{value:uri, uri:uri, context_uri:uri}});
}}
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
