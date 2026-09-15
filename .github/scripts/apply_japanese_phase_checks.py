from pathlib import Path

p=Path('index.html')
s=p.read_text()

# Force a fresh repository analysis for the new phase/check model.
s=s.replace("LS_CACHE='devhub.cache.v8'", "LS_CACHE='devhub.cache.v9'")

# Japanese-first labels for non-product jargon.
s=s.replace("web:'Web / PWA'", "web:'Web'")
s=s.replace("qa:'配布 / QA'", "qa:'配布 / 品質確認'")
s=s.replace("support:'開発基盤 / QA'", "support:'開発基盤 / 品質確認'")
s=s.replace("['support','開発基盤/QA']", "['support','開発基盤/品質確認']")
s=s.replace("['qa','配布/QA']", "['qa','配布/品質確認']")
s=s.replace("<div class=\"filter-title\">進捗</div>", "<div class=\"filter-title\">状態</div>")
s=s.replace("現在はVertical Slice段階。", "現在は中核部分の試作段階。")

old_css="""    .maturity-chip{border-color:#0e7490;color:#a5f3fc;background:#083344}.maturity-breakdown{display:grid;gap:5px;margin:0 0 12px}.maturity-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px;align-items:center;font-size:10px;color:#cbd5e1}.maturity-row span:last-child{font-variant-numeric:tabular-nums;color:var(--muted)}.maturity-row.earned span:last-child{color:#67e8f9}.maturity-note{font-size:9px;color:var(--muted);margin:-5px 0 10px}
"""
new_css="""    .maturity-chip{border-color:#0e7490;color:#a5f3fc;background:#083344}.qualityline{display:flex;flex-wrap:wrap;gap:4px 8px;margin-top:7px;font-size:9px;color:#cbd5e1}.quality-item{white-space:nowrap}.phasebanner{margin:9px 0 10px;padding:9px 10px;border:1px solid #155e75;border-radius:10px;background:#083344;color:#a5f3fc;font-size:13px;font-weight:900}.maturity-breakdown{display:grid;gap:6px;margin:0 0 12px}.maturity-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px;align-items:center;padding:7px 8px;border:1px solid var(--border);border-radius:8px;background:#0d151d;font-size:10px;color:#cbd5e1}.quality-status{font-weight:900}.quality-status.ok{color:#86efac}.quality-status.warn{color:#fde68a}.quality-status.none{color:#64748b}.maturity-note{font-size:9px;line-height:1.5;color:var(--muted);margin:0 0 9px}
"""
if old_css not in s:
    raise SystemExit('maturity css anchor not found')
s=s.replace(old_css,new_css,1)

start=s.index('function maturityStage(')
end=s.index('async function scanRepo',start)
new_funcs=r'''function maturityStage(e){
  if(e.releaseReady)return'公開可能';
  if(e.release&&e.testStrong&&(e.device||e.qa))return'公開前最終版';
  if(e.functional&&(e.testStrong||e.qa))return'品質確認';
  if(e.functional&&e.polish)return'見た目・操作感の改善';
  if(e.functional)return'主要機能実装';
  if(e.entry)return'中核部分の試作';
  if(e.docs)return'企画確定';
  return'企画確認中';
}
function maturityFromPaths(paths,tech,kind,role,desc=''){
  const low=(paths||[]).map(p=>p.toLowerCase()),has=re=>low.some(p=>re.test(p)),count=re=>low.filter(p=>re.test(p)).length;
  const code=count(/\.(gd|js|ts|tsx|jsx|py|swift|kt|java|cs|cpp|go|rs)$/),scene=count(/\.tscn$/),assets=count(/(^|\/)(assets?|art|audio|sfx|music|vfx|ui|styles?|components?)(\/|\.)/);
  const entry=tech==='godot'?has(/(^|\/)project\.godot$/)&&has(/\.tscn$/):tech==='web'?has(/(^|\/)(index\.html|package\.json)$/):tech==='scriptable'?code>0:code>0||has(/(^|\/)payload\//);
  const docs=has(/(^|\/)(gdd|design|docs?|specs?|adr|roadmap|product|planning)(\/|\.)|readme\.md$/)||/core loop|仕様|設計|企画/i.test(desc||'');
  const functional=entry&&((tech==='godot'&&code>=5)||(tech!=='godot'&&code>=3));
  const polish=assets>=3||has(/(^|\/)(theme|fonts?|icons?|shaders?)(\/|\.)/);
  const save=has(/save|progression|progress|persistence|profile|inventory|storage|localstorage|(^|\/)state(\/|\.)|(^|\/)data(\/|\.)/);
  const analytics=has(/analytics|telemetry|metrics|tracking|event[_-]?schema|observability/);
  const workflow=has(/(^|\/)\.github\/workflows\/.+\.ya?ml$/),testFiles=has(/(^|\/)(tests?|specs?|e2e)(\/|\.)|(_test|\.test|\.spec)\./),testStrong=workflow&&testFiles;
  const device=has(/device[_-]?test|real[_-]?device|実機|iphone|ipad|ios|android|safari|chrome[_-]?mobile|browser[_-]?verify/);
  const qa=has(/(^|\/)qa(\/|\.)|regression|acceptance|checklist|verification|verified/);
  const perf=has(/performance|perf[_-]|benchmark|profil|fps|memory[_-]?test|load[_-]?test/);
  const release=tech==='godot'?has(/export_presets\.cfg|(^|\/)(build|dist|release|web)(\/|\.)/):has(/manifest\.(webmanifest|json)$|service-worker|(^|\/)(dist|build|release)(\/|\.)|pages\.ya?ml|deploy/);
  const releaseReady=has(/release[_-]?ready|qa[_-]?pass|rc[_-]?pass|release[_-]?checklist.*(done|pass)|公開可能/);
  const status=(ok,warn=False)=>ok?'ok':warn?'warn':'none';
  const checks=[
    {key:'boot',label:'起動構成',status:status(entry,code>0),note:'起動に必要な構成が見つかるか'},
    {key:'test',label:'自動テスト',status:status(testStrong,workflow||testFiles),note:'テストと自動実行の証拠'},
    {key:'device',label:'実機確認',status:status(device,qa),note:'スマホ・ブラウザ等での確認記録'},
    {key:'save',label:'保存',status:status(save,false),note:'保存・状態保持の実装証拠'},
    {key:'analytics',label:'分析計測',status:status(analytics,false),note:'利用状況を計測する実装証拠'},
    {key:'performance',label:'性能確認',status:status(perf,qa),note:'性能測定・回帰確認の証拠'},
    {key:'release',label:'公開準備',status:status(release,false),note:'配布・公開設定の証拠'}
  ];
  const phase=maturityStage({docs,entry,functional,polish,testStrong,device,qa,release,releaseReady});
  return {phase,checks,source:'repository-evidence'};
}
function maturityChipHTML(sc){const m=sc?.maturity;if(!m?.phase)return'';return `<span class="chip maturity-chip">${escapeHtml(m.phase)}</span>`}
function qualityIcon(status){return status==='ok'?'✅':status==='warn'?'⚠️':'—'}
function qualityLineHTML(sc){const checks=sc?.maturity?.checks;if(!checks?.length)return'';const shown=checks.slice(0,5);return `<div class="qualityline">${shown.map(x=>`<span class="quality-item">${escapeHtml(x.label)} ${qualityIcon(x.status)}</span>`).join('')}</div>`}
function maturityBreakdownHTML(m){if(!m?.checks?.length)return'<div class="maturity-note">GitHub上の確認材料を解析中です。</div>';return `<div class="maturity-note">✅ 確認材料あり　⚠️ 一部のみ　— 確認できず。GitHub上の証拠を見ているため、実動作の成功そのものは保証しません。</div><div class="maturity-breakdown">${m.checks.map(x=>`<div class="maturity-row"><span>${escapeHtml(x.label)}</span><span class="quality-status ${x.status}">${qualityIcon(x.status)}</span></div>`).join('')}</div>`}
'''
s=s[:start]+new_funcs+s[end:]

old='${visChip}${statusChip}${maturityChipHTML(sc)}</div>${structureHtml}'
new='${visChip}${statusChip}${maturityChipHTML(sc)}</div>${qualityLineHTML(sc)}${structureHtml}'
if old not in s:
    raise SystemExit('card maturity anchor not found')
s=s.replace(old,new,1)

old="const maturity=sc.maturity||{score:0,stage:'解析中',items:[]};const progress=Math.max(0,Math.min(100,Number(maturity.score)||0));"
new="const maturity=sc.maturity||{phase:'解析中',checks:[]};"
if old not in s:
    raise SystemExit('detail maturity variable anchor not found')
s=s.replace(old,new,1)

old='''<div class="panel"><div class="progresshead"><h3 style="margin:0">現在</h3><div class="progressvalue">自動成熟度 ${progress}% · ${escapeHtml(maturity.stage)}</div></div><div class="progressbar"><div class="progressfill" style="width:${progress}%"></div></div>${maturityBreakdownHTML(maturity)}'''
new='''<div class="panel"><div class="progresshead"><h3 style="margin:0">現在</h3><div class="progressvalue">開発フェーズ</div></div><div class="phasebanner">${escapeHtml(maturity.phase)}</div>${maturityBreakdownHTML(maturity)}'''
if old not in s:
    raise SystemExit('detail maturity panel anchor not found')
s=s.replace(old,new,1)

s=s.replace('成熟度・役割・種類・技術・構成・更新日はGitHubから自動取得します。','開発フェーズ・品質チェック・役割・種類・技術・構成・更新日はGitHubから自動取得します。')

p.write_text(s)
print('japanese phase and quality checks patched')
