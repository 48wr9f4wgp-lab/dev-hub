from pathlib import Path

p = Path('index.html')
s = p.read_text()

# Force a fresh scan schema so old cached scan objects without maturity are not reused.
s = s.replace("LS_CACHE='devhub.cache.v7'", "LS_CACHE='devhub.cache.v8'")

# Compact maturity UI styles.
if '.maturity-chip{' not in s:
    anchor = "    .empty,.loading,.error{"
    css = """    .maturity-chip{border-color:#0e7490;color:#a5f3fc;background:#083344}.maturity-breakdown{display:grid;gap:5px;margin:0 0 12px}.maturity-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:8px;align-items:center;font-size:10px;color:#cbd5e1}.maturity-row span:last-child{font-variant-numeric:tabular-nums;color:var(--muted)}.maturity-row.earned span:last-child{color:#67e8f9}.maturity-note{font-size:9px;color:var(--muted);margin:-5px 0 10px}\n"""
    if anchor not in s:
        raise SystemExit('css anchor not found')
    s = s.replace(anchor, css + anchor, 1)

# Automatic maturity model. It uses only repository evidence; it does not claim gameplay quality.
if 'function maturityFromPaths(' not in s:
    anchor = 'async function scanRepo(repo)'
    fn = r'''function maturityStage(score){if(score>=90)return'Release Ready';if(score>=80)return'Release Candidate';if(score>=65)return'QA';if(score>=50)return'Polish';if(score>=30)return'Functional Build';if(score>=15)return'Vertical Slice';return'Context Lock'}
function maturityFromPaths(paths,tech,kind,role,desc=''){
  const low=(paths||[]).map(p=>p.toLowerCase()),has=re=>low.some(p=>re.test(p)),count=re=>low.filter(p=>re.test(p)).length;
  const code=count(/\.(gd|js|ts|tsx|jsx|py|swift|kt|java|cs|cpp|go|rs)$/),scene=count(/\.tscn$/),tests=count(/(^|\/)(tests?|specs?|e2e|qa)(\/|\.)|(_test|\.test|\.spec)\./),assets=count(/(^|\/)(assets?|art|audio|sfx|music|vfx|ui|styles?|components?)(\/|\.)/);
  const items=[];let score=0;const add=(label,weight,earned)=>{earned=Math.max(0,Math.min(weight,Math.round(earned)));score+=earned;items.push({label,weight,earned})};
  const entry=tech==='godot'?has(/(^|\/)project\.godot$/)&&has(/\.tscn$/):tech==='web'?has(/(^|\/)index\.html$|(^|\/)package\.json$/):tech==='scriptable'?code>0:code>0||has(/(^|\/)payload\//);
  const docs=has(/(^|\/)(gdd|design|docs?|specs?|adr|roadmap|product|planning)(\/|\.)|readme\.md$/)||/gdd|core loop|vertical slice|仕様|設計|企画/i.test(desc||'');
  add('企画 / GDD',10,docs?10:0);
  add('Vertical Slice',15,entry?(code>=3||scene>=1?15:8):0);
  add('Functional Build',15,entry&&((tech==='godot'&&code>=5)||(tech!=='godot'&&code>=3))?15:entry?8:0);
  add('UI/UX・Art/Game Feel',10,assets>=3||has(/(^|\/)(theme|fonts?|icons?|shaders?)(\/|\.)/)?10:assets>0?5:0);
  const stateEvidence=has(/save|progression|progress|persistence|profile|inventory|storage|localstorage|cache|settings|state|config|(^|\/)data(\/|\.)/);
  add('Save / Progression',10,stateEvidence?10:0);
  add('Analytics',10,has(/analytics|telemetry|metrics|tracking|event[_-]?schema|observability/)?10:0);
  const hasWorkflow=has(/(^|\/)\.github\/workflows\/.+\.ya?ml$/),hasTests=tests>0;
  add('Test / Build',10,hasWorkflow&&hasTests?10:(hasWorkflow||hasTests)?5:0);
  const qaEvidence=has(/performance|perf|benchmark|profil|regression|e2e|device[_-]?test|safari|qa(\/|\.)/);
  add('Performance / QA',10,qaEvidence?10:hasTests?4:0);
  const releaseEvidence=tech==='godot'?has(/export_presets\.cfg|(^|\/)(build|dist|release|web)(\/|\.)/):has(/manifest\.(webmanifest|json)$|service-worker|(^|\/)(dist|build|release)(\/|\.)|pages\.ya?ml|deploy/);
  add('Release',10,releaseEvidence?10:0);
  score=Math.max(0,Math.min(100,score));
  return {score,stage:maturityStage(score),items,source:'repository-evidence'};
}
function maturityChipHTML(sc){const m=sc?.maturity;if(!m||!Number.isFinite(m.score))return'';return `<span class="chip maturity-chip">${m.score}% · ${escapeHtml(m.stage)}</span>`}
function maturityBreakdownHTML(m){if(!m?.items?.length)return'<div class="maturity-note">GitHub上の実装証跡を解析中です。</div>';return `<div class="maturity-note">GitHub上で確認できる実装証跡から自動算出。面白さ・品質そのものを保証する数値ではありません。</div><div class="maturity-breakdown">${m.items.map(x=>`<div class="maturity-row ${x.earned?'earned':''}"><span>${escapeHtml(x.label)}</span><span>${x.earned}/${x.weight}</span></div>`).join('')}</div>`}
'''
    if anchor not in s:
        raise SystemExit('scanRepo anchor not found')
    s = s.replace(anchor, fn + anchor, 1)

# Reuse recursive tree data when scanRepo already fetched it.
old = "const paths=(tree.tree||[]).filter(x=>x.type==='blob').map(x=>x.path);const nestedTech=techFromPaths(paths,kind,autoDesc);"
new = "const paths=(tree.tree||[]).filter(x=>x.type==='blob').map(x=>x.path);cache['tree|'+k]={at:Date.now(),data:{paths}};const nestedTech=techFromPaths(paths,kind,autoDesc);"
if old in s:
    s = s.replace(old, new, 1)

# Calculate maturity for every repo using the recursive tree; cache the same tree for detail view.
old = "if(tech==='other'&&kind==='widget')tech='scriptable';const role=inferRole(repo.name,kind,autoDesc);const data={tech,kind,role,primary:primary.slice(0,5),autoDesc};"
new = "if(tech==='other'&&kind==='widget')tech='scriptable';const role=inferRole(repo.name,kind,autoDesc);let maturity=null;try{const tk='tree|'+k;let paths=cache[tk]?.data?.paths;if(!Array.isArray(paths)){const tree=await api(`https://api.github.com/repos/${OWNER}/${encodeURIComponent(repo.name)}/git/trees/${encodeURIComponent(repo.default_branch)}?recursive=1`);paths=(tree.tree||[]).filter(x=>x.type==='blob').map(x=>x.path);cache[tk]={at:Date.now(),data:{paths}}}maturity=maturityFromPaths(paths,tech,kind,role,autoDesc)}catch{}const data={tech,kind,role,primary:primary.slice(0,5),autoDesc,maturity};"
if old not in s:
    raise SystemExit('scanRepo data anchor not found')
s = s.replace(old, new, 1)

# Add automatic maturity to every list card.
old = "${visChip}${statusChip}</div>${structureHtml}"
new = "${visChip}${statusChip}${maturityChipHTML(sc)}</div>${structureHtml}"
if old not in s:
    raise SystemExit('card chips anchor not found')
s = s.replace(old, new, 1)

# Detail view uses automatic maturity instead of the old manual percentage.
old = "const progress=Math.max(0,Math.min(100,Number(m.progress)||0));"
new = "const maturity=sc.maturity||{score:0,stage:'解析中',items:[]};const progress=Math.max(0,Math.min(100,Number(maturity.score)||0));"
if old not in s:
    raise SystemExit('detail progress anchor not found')
s = s.replace(old, new, 1)

old = "<div class=\"progressvalue\">${statusLabels[m.status]} · ${progress}%</div>"
new = "<div class=\"progressvalue\">自動成熟度 ${progress}% · ${escapeHtml(maturity.stage)}</div>"
if old not in s:
    raise SystemExit('detail progress label anchor not found')
s = s.replace(old, new, 1)

old = "</div>${nowItems?`<div class=\"nowlist\">${nowItems}</div>`:'<div class=\"small\">目的・次の作業・メモはまだ設定されていません。</div>'}</div><div class=\"panel\" id=\"structurePanel\">"
new = "</div>${maturityBreakdownHTML(maturity)}${nowItems?`<div class=\"nowlist\">${nowItems}</div>`:'<div class=\"small\">目的・次の作業・メモはまだ設定されていません。</div>'}</div><div class=\"panel\" id=\"structurePanel\">"
if old not in s:
    raise SystemExit('detail breakdown anchor not found')
s = s.replace(old, new, 1)

# Remove manual progress slider. Status/notes stay manually editable.
old = "<div class=\"field\"><label>進捗 <span id=\"progressVal\">${m.progress}%</span></label><input class=\"range\" id=\"fProgress\" type=\"range\" min=\"0\" max=\"100\" step=\"5\" value=\"${m.progress}\"></div>"
s = s.replace(old, '', 1)

old = "const save=()=>setMeta(name,{description:$('#fDesc').value,progress:Number($('#fProgress').value),objective:$('#fObjective').value,next:$('#fNext').value,memo:$('#fMemo').value});"
new = "const save=()=>setMeta(name,{description:$('#fDesc').value,objective:$('#fObjective').value,next:$('#fNext').value,memo:$('#fMemo').value});"
if old not in s:
    raise SystemExit('editor save anchor not found')
s = s.replace(old, new, 1)

s = s.replace("$('#fProgress').oninput=e=>{$('#progressVal').textContent=e.target.value+'%'};$('#fProgress').onchange=save;", "", 1)
s = s.replace("進捗・メモ・ピンはこの端末に自動保存。役割・種類・技術・構成・更新日はGitHubから自動取得します。", "説明・状態・目的・次の作業・メモ・ピンはこの端末に保存。成熟度・役割・種類・技術・構成・更新日はGitHubから自動取得します。", 1)

p.write_text(s)
print('auto maturity patched')
