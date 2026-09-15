from pathlib import Path

p = Path('index.html')
s = p.read_text()

# Add a neutral technology chip for static/QA distribution repositories.
old_css = ".chip.hold{border-color:#92400e;color:#fde68a;background:#451a03}"
new_css = old_css + ".chip.static{border-color:#475569;color:#cbd5e1;background:#0f172a}"
if old_css not in s:
    raise SystemExit('chip css anchor not found')
s = s.replace(old_css, new_css, 1)

# Replace raw file-path structure summaries with human-readable semantic summaries.
old_compact = "function compactPrimary(sc){if(!sc.primary?.length)return'構成を確認中…';const shown=sc.primary.slice(0,3);return shown.join(' / ')+(sc.primary.length>3?` +${sc.primary.length-3}`:'')}"
new_compact = r'''function structureSummary(sc){
  const ps=(sc.primary||[]).map(p=>p.toLowerCase());
  if(!ps.length)return'';
  const out=[];const add=x=>{if(x&&!out.includes(x))out.push(x)};
  const has=re=>ps.some(p=>re.test(p));
  if(sc.kind==='qa'){
    add('QA配布');
    if(has(/(^|\/)payload\/?$/))add('ペイロード');
    if(has(/index\.html|manifest|\.wasm$|\.pck$/))add('Webビルド');
  }else if(sc.tech==='godot'){
    add('Godot');
    if(has(/\.tscn$|(^|\/)scenes\/?$/))add('シーン');
    if(has(/\.gd$|(^|\/)(scripts|domain|ui|view|persistence)\/?$/))add('スクリプト');
    if(has(/(^|\/)(assets|art)\/?$/))add('素材');
    if(has(/(^|\/)tests?\/?$/))add('テスト');
  }else if(sc.tech==='web'){
    add('Web');
    if(has(/(^|\/)(src|app|components|public)\/?$|index\.html$/))add('UI');
    if(has(/(^|\/)scripts\/?$|\.(js|ts|tsx|jsx)$/|package\.json$/))add('スクリプト');
    if(has(/manifest\.(webmanifest|json)$|service-worker/))add('PWA');
    if(has(/(^|\/)data\/?$/))add('データ');
  }else if(sc.tech==='scriptable'){
    add('Scriptable');
    if(has(/widget|loader|\.js$|\.ts$/))add('ウィジェット');
    if(has(/(^|\/)(data|config)\/?$|\.json$/))add('データ');
  }else{
    if(has(/(^|\/)payload\/?$/))add('ペイロード');
    if(has(/(^|\/)src\/?$/))add('ソース');
    if(has(/(^|\/)scripts\/?$|\.(js|ts|py|gd)$/))add('スクリプト');
    if(has(/(^|\/)(assets|public|data)\/?$/))add('データ');
  }
  if(!out.length)return'';
  const shown=out.slice(0,3);return shown.join(' / ')+(out.length>3?` +${out.length-3}`:'');
}'''
if old_compact not in s:
    raise SystemExit('compactPrimary anchor not found')
s = s.replace(old_compact, new_compact, 1)

old_tech = "function techShort(t){return t==='godot'?'Godot':t==='web'?'Web':t==='scriptable'?'Scriptable':t==='other'?'その他':'確認中'}\nfunction techChipClass(t){return t==='godot'?'godot':t==='web'?'web':t==='scriptable'?'scriptable':''}"
new_tech = "function techShort(t,kind='other'){if(t==='other'&&kind==='qa')return'静的配布';return t==='godot'?'Godot':t==='web'?'Web':t==='scriptable'?'Scriptable':t==='other'?'その他':'確認中'}\nfunction techChipClass(t,kind='other'){if(t==='other'&&kind==='qa')return'static';return t==='godot'?'godot':t==='web'?'web':t==='scriptable'?'scriptable':''}"
if old_tech not in s:
    raise SystemExit('tech helpers anchor not found')
s = s.replace(old_tech, new_tech, 1)

# Card technology chip now knows the repository kind.
s = s.replace("const k=kindLabels[sc.kind]||'その他',ts=techShort(sc.tech);", "const k=kindLabels[sc.kind]||'その他',ts=techShort(sc.tech,sc.kind);", 1)
s = s.replace("const structureHtml=sc.primary?.length?`<div class=\"structure\"><span class=\"kicker\">構成</span><span class=\"paths mono\">${escapeHtml(compactPrimary(sc))}</span></div>`:'';", "const semanticStructure=structureSummary(sc);const structureHtml=semanticStructure?`<div class=\"structure\"><span class=\"kicker\">構成</span><span class=\"paths\">${escapeHtml(semanticStructure)}</span></div>`:'';", 1)
s = s.replace("${techChipClass(sc.tech)}", "${techChipClass(sc.tech,sc.kind)}", 1)

# Detail page uses the same semantic structure summary instead of raw paths.
old_detail = "<div class=\"paths mono\" style=\"white-space:normal\">${sc.primary.length?escapeHtml(sc.primary.join(' / ')):'主要構成を取得中…'}</div>"
new_detail = "<div class=\"paths\" style=\"white-space:normal\">${escapeHtml(structureSummary(sc)||'主要構成を取得中…')}</div>"
if old_detail not in s:
    raise SystemExit('detail structure anchor not found')
s = s.replace(old_detail, new_detail, 1)

p.write_text(s)
print('structure summary finalized')
