from pathlib import Path

p=Path('index.html')
s=p.read_text()

s=s.replace("LS_CACHE='devhub.cache.v9'", "LS_CACHE='devhub.cache.v10'")
s=s.replace("自動取得：リポジトリ、更新日、役割、種類、技術、構成、README。手動管理：進捗、次の作業、メモ、ピン留め。", "自動取得：リポジトリ、更新日、役割、種類、技術、構成、README、DEV_STATUS.json。手動管理：状態、次の作業、メモ、ピン留め。")

start=s.index('function maturityStage(')
end=s.index('async function queueScans()',start)
new_block=r'''const DEV_PHASES=['企画確認中','企画確定','中核部分の試作','主要機能実装','見た目・操作感の改善','品質確認','公開前最終版','公開可能'];
const DEV_CHECKS=[
  ['boot','起動確認'],['test','自動テスト'],['device','実機確認'],['save','保存'],
  ['analytics','分析計測'],['performance','性能確認'],['release','公開準備']
];
function normalizeCheck(v){
  if(v===true||v==='ok'||v==='verified'||v==='confirmed'||v==='pass')return'ok';
  if(v==='warn'||v==='partial'||v==='checking'||v==='in-progress')return'warn';
  return'none';
}
function unsetDevStatus(message='DEV_STATUS.json未設定'){
  return {phase:'状態未設定',checks:DEV_CHECKS.map(([key,label])=>({key,label,status:'none'})),next:'',note:message,source:'unset'};
}
function explicitDevStatus(raw){
  if(!raw||typeof raw!=='object')return unsetDevStatus('DEV_STATUS.jsonを読み取れません');
  const phase=DEV_PHASES.includes(raw.phase)?raw.phase:'状態未設定';
  const src=raw.checks&&typeof raw.checks==='object'?raw.checks:{};
  return {phase,checks:DEV_CHECKS.map(([key,label])=>({key,label,status:normalizeCheck(src[key])})),next:String(raw.next||''),note:String(raw.note||''),updated_at:String(raw.updated_at||''),source:'explicit'};
}
async function loadDevStatus(repo,names){
  if(!names.some(n=>n.toLowerCase()==='dev_status.json'))return unsetDevStatus();
  try{
    const f=await api(`https://api.github.com/repos/${OWNER}/${encodeURIComponent(repo.name)}/contents/DEV_STATUS.json?ref=${encodeURIComponent(repo.default_branch)}`);
    return explicitDevStatus(JSON.parse(decode64(f.content||'')));
  }catch(e){return unsetDevStatus('DEV_STATUS.json読込失敗');}
}
function maturityChipHTML(sc){const m=sc?.maturity;if(!m?.phase)return'';return `<span class="chip maturity-chip">${escapeHtml(m.phase)}</span>`}
function qualityIcon(status){return status==='ok'?'✅':status==='warn'?'⚠️':'—'}
function qualityLineHTML(sc){const m=sc?.maturity;if(!m)return'';if(m.source!=='explicit')return `<div class="qualityline"><span class="quality-item">状態ファイル未設定</span></div>`;const shown=(m.checks||[]).slice(0,5);return `<div class="qualityline">${shown.map(x=>`<span class="quality-item">${escapeHtml(x.label)} ${qualityIcon(x.status)}</span>`).join('')}</div>`}
function maturityBreakdownHTML(m){if(!m||m.source!=='explicit')return'<div class="maturity-note">このRepoにはDEV_STATUS.jsonがまだありません。推測でフェーズ判定はしません。</div>';const note=m.note?`<div class="maturity-note">${escapeHtml(m.note)}</div>`:'';return `<div class="maturity-note">✅ 確認済み　⚠️ 確認中 / 一部確認　— 未確認</div>${note}<div class="maturity-breakdown">${(m.checks||[]).map(x=>`<div class="maturity-row"><span>${escapeHtml(x.label)}</span><span class="quality-status ${x.status}">${qualityIcon(x.status)}</span></div>`).join('')}</div>`}
async function scanRepo(repo){
  const k=rootKey(repo);
  if(cache[k]&&Date.now()-cache[k].at<12*3600*1000){state.scans[repo.name]=cache[k].data;render();return}
  try{
    const root=await api(`https://api.github.com/repos/${OWNER}/${encodeURIComponent(repo.name)}/contents/?ref=${encodeURIComponent(repo.default_branch)}`);
    const names=Array.isArray(root)?root.map(x=>x.name):[];
    const dirs=Array.isArray(root)?root.filter(x=>x.type==='dir').map(x=>x.name+'/'):[];
    const lower=names.map(x=>x.toLowerCase());
    let tech='other';
    if(lower.includes('project.godot'))tech='godot';
    else if(lower.includes('package.json')||lower.includes('index.html')||lower.some(x=>x.includes('manifest'))||lower.some(x=>x.includes('service-worker')))tech='web';
    let autoDesc=repo.description||'';
    if(names.some(n=>/^readme/i.test(n))&&(!autoDesc||!isJapanese(autoDesc))){try{const rd=await api(`https://api.github.com/repos/${OWNER}/${encodeURIComponent(repo.name)}/readme?ref=${encodeURIComponent(repo.default_branch)}`);const summary=readmeSummary(decode64(rd.content||''));if(summary&&(isJapanese(summary)||!autoDesc))autoDesc=summary}catch{}}
    let kind=inferKind(repo.name,tech,autoDesc),primary=pickPrimary(tech,names,dirs);
    if(tech==='other'||kind==='widget'||dirs.some(d=>/^(godot|game|web|app|src|payload)\/$/i.test(d))){try{const tree=await api(`https://api.github.com/repos/${OWNER}/${encodeURIComponent(repo.name)}/git/trees/${encodeURIComponent(repo.default_branch)}?recursive=1`);const paths=(tree.tree||[]).filter(x=>x.type==='blob').map(x=>x.path);cache['tree|'+k]={at:Date.now(),data:{paths}};const nestedTech=techFromPaths(paths,kind,autoDesc);if(nestedTech!=='other')tech=nestedTech;kind=inferKind(repo.name,tech,autoDesc);const nestedPrimary=pickPrimaryFromPaths(tech,paths);if(nestedPrimary.length)primary=nestedPrimary}catch{}}
    if(tech==='other'&&kind==='widget')tech='scriptable';
    const role=inferRole(repo.name,kind,autoDesc);
    const maturity=await loadDevStatus(repo,names);
    const data={tech,kind,role,primary:primary.slice(0,5),autoDesc,maturity};
    state.scans[repo.name]=data;cache[k]={at:Date.now(),data};saveJSON(LS_CACHE,cache);render();
  }catch(e){const kind=KIND_OVERRIDE[repo.name]||'other';state.scans[repo.name]={tech:kind==='widget'?'scriptable':'unknown',kind,role:inferRole(repo.name,kind,repo.description||''),primary:[],autoDesc:repo.description||'',maturity:unsetDevStatus('Repo情報を取得できません'),error:e.message};render()}
}
'''
s=s[:start]+new_block+s[end:]

old="  const nowItems=[m.objective?`<div class=\"nowitem\"><span>現在の目的</span><b>${escapeHtml(m.objective)}</b></div>`:'',m.next?`<div class=\"nowitem\"><span>次にやること</span><b>${escapeHtml(m.next)}</b></div>`:'',m.memo?`<div class=\"nowitem\"><span>メモ</span><b>${escapeHtml(m.memo)}</b></div>`:''].join('');"
new="  const statusNext=m.next||maturity.next||'';\n  const nowItems=[m.objective?`<div class=\"nowitem\"><span>現在の目的</span><b>${escapeHtml(m.objective)}</b></div>`:'',statusNext?`<div class=\"nowitem\"><span>次にやること</span><b>${escapeHtml(statusNext)}</b></div>`:'',m.memo?`<div class=\"nowitem\"><span>メモ</span><b>${escapeHtml(m.memo)}</b></div>`:''].join('');"
if old not in s: raise SystemExit('nowItems anchor not found')
s=s.replace(old,new,1)

s=s.replace('開発フェーズ・品質チェック・役割・種類・技術・構成・更新日はGitHubから自動取得します。','開発フェーズ・品質チェックは各RepoのDEV_STATUS.jsonを正本として表示します。役割・種類・技術・構成・更新日はGitHubから自動取得します。')

p.write_text(s)
print('explicit DEV_STATUS integration patched')
