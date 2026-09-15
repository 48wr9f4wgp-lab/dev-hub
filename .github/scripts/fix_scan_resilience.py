from pathlib import Path
import re

p=Path('index.html')
s=p.read_text()

s=s.replace("const LS_META='devhub.meta.v2', LS_TOKEN='devhub.token.v1', LS_CACHE='devhub.cache.v13', LS_REPOS='devhub.repos.v1';",
            "const LS_META='devhub.meta.v2', LS_TOKEN='devhub.token.v1', LS_CACHE='devhub.cache.v14', LS_REPOS='devhub.repos.v1';")

needle="""const ROLE_OVERRIDE={
"""
insert="""const TECH_OVERRIDE={
  'Logistics-Boss':'godot','farm-loop':'godot','-grid-bloom':'godot','machi-loop':'godot',
  'fish-target':'web','tackle-fit':'web','tide-dash':'web','dev-hub':'web','-velvet-pwa':'web',
  'motorsport-hub':'scriptable','combat-hub':'scriptable','club-pulse':'scriptable',
  '-scrap-planet-qa':'other','48wr9f4wgp-lab-tide-dash':'other'
};
const ROLE_OVERRIDE={
"""
if needle not in s: raise SystemExit('ROLE_OVERRIDE anchor missing')
s=s.replace(needle,insert,1)

old_load=re.search(r"async function loadRepos\(\)\{.*?\}\nfunction rootKey",s,re.S)
if not old_load: raise SystemExit('loadRepos block missing')
new_load="""async function loadRepos(){
  msg.className='loading';msg.innerHTML='<span class=\"spinner\"></span><br>GitHubから読み込み中…';cards.innerHTML='';
  const cached=Array.isArray(repoCache)?repoCache.filter(r=>r&&!r.archived):[];
  if(cached.length){
    state.repos=cached;
    for(const r of cached){const c=cachedScanFor(r);if(c)state.scans[r.name]=c}
    msg.style.display='none';render();queueScans(cached);
  }
  try{
    const token=localStorage.getItem(LS_TOKEN);let repos;
    if(token){const all=await api('https://api.github.com/user/repos?per_page=100&sort=pushed&affiliation=owner',8000);repos=all.filter(r=>r.owner?.login===OWNER)}
    else{repos=await api(`https://api.github.com/users/${OWNER}/repos?per_page=100&sort=pushed&type=owner`,8000)}
    state.repos=repos.filter(r=>!r.archived);repoCache=state.repos;saveJSON(LS_REPOS,repoCache);
    for(const r of state.repos){if(!state.scans[r.name]){const c=cachedScanFor(r);if(c)state.scans[r.name]=c}}
    msg.style.display='none';render();queueScans(state.repos);
  }catch(e){
    if(cached.length){msg.style.display='none';queueScans(cached);return}
    msg.style.display='block';msg.className='error';msg.textContent='読み込み失敗: '+e.message;
  }
}
function rootKey"""
s=s[:old_load.start()]+new_load+s[old_load.end():]

s=s.replace("function rootKey(repo){return `${repo.name}|${repo.pushed_at||repo.updated_at}`}\n",
"""function rootKey(repo){return `${repo.name}|${repo.pushed_at||repo.updated_at}`}
function cachedScanFor(repo){
  const direct=cache[rootKey(repo)]?.data;if(direct)return direct;
  let best=null,bestAt=0;const prefix=repo.name+'|';
  for(const [key,val] of Object.entries(cache)){if(key.startsWith(prefix)&&val?.data&&Number(val.at||0)>bestAt){best=val.data;bestAt=Number(val.at||0)}}
  return best;
}
""",1)

pat=r"async function loadDevStatus\(repo,names,root=\[\]\)\{.*?\n\}\nfunction maturityChipHTML"
m=re.search(pat,s,re.S)
if not m: raise SystemExit('loadDevStatus block missing')
replacement="""async function loadDevStatus(repo){
  if(!repo.private){
    const branch=String(repo.default_branch||'main').split('/').map(encodeURIComponent).join('/');
    const rawUrl=`https://raw.githubusercontent.com/${encodeURIComponent(OWNER)}/${encodeURIComponent(repo.name)}/${branch}/DEV_STATUS.json`;
    const ctl=new AbortController(),timer=setTimeout(()=>ctl.abort(),5000);
    try{
      const r=await fetch(rawUrl,{signal:ctl.signal,cache:'no-store'});
      if(r.status===404)return unsetDevStatus();
      if(!r.ok)throw new Error(`raw ${r.status}`);
      return explicitDevStatus(JSON.parse(await r.text()));
    }catch(e){return errorDevStatus(e?.name==='AbortError'?'状態ファイル取得タイムアウト':(e?.message||'DEV_STATUS.json読込失敗'))}
    finally{clearTimeout(timer)}
  }
  try{
    const f=await api(`https://api.github.com/repos/${OWNER}/${encodeURIComponent(repo.name)}/contents/DEV_STATUS.json?ref=${encodeURIComponent(repo.default_branch||'main')}`);
    return explicitDevStatus(JSON.parse(decode64(f.content||'')));
  }catch(e){if(/404/.test(String(e?.message||'')))return unsetDevStatus();return errorDevStatus(e?.message||'DEV_STATUS.json読込失敗')}
}
function maturityChipHTML"""
s=s[:m.start()]+replacement+s[m.end():]

pat=r"async function scanRepo\(repo\)\{.*?\n\}\nasync function queueScans\(\)\{.*?\}\n"
m=re.search(pat,s,re.S)
if not m: raise SystemExit('scanRepo/queueScans block missing')
replacement="""async function scanRepo(repo){
  const k=rootKey(repo),previous=state.scans[repo.name]||cachedScanFor(repo);
  const maturity=await loadDevStatus(repo);
  if(previous){state.scans[repo.name]={...previous,maturity};render()}
  if(cache[k]&&Date.now()-cache[k].at<12*3600*1000){
    const data={...cache[k].data,maturity};state.scans[repo.name]=data;cache[k]={at:Date.now(),data};saveJSON(LS_CACHE,cache);render();return;
  }
  try{
    const root=await api(`https://api.github.com/repos/${OWNER}/${encodeURIComponent(repo.name)}/contents/?ref=${encodeURIComponent(repo.default_branch)}`);
    const names=Array.isArray(root)?root.map(x=>x.name):[];
    const dirs=Array.isArray(root)?root.filter(x=>x.type==='dir').map(x=>x.name+'/'):[];
    const lower=names.map(x=>x.toLowerCase());
    let tech=TECH_OVERRIDE[repo.name]||'other';
    if(lower.includes('project.godot'))tech='godot';
    else if(lower.includes('package.json')||lower.includes('index.html')||lower.some(x=>x.includes('manifest'))||lower.some(x=>x.includes('service-worker')))tech='web';
    let autoDesc=repo.description||previous?.autoDesc||'';
    if(names.some(n=>/^readme/i.test(n))&&(!autoDesc||!isJapanese(autoDesc))){try{const rd=await api(`https://api.github.com/repos/${OWNER}/${encodeURIComponent(repo.name)}/readme?ref=${encodeURIComponent(repo.default_branch)}`);const summary=readmeSummary(decode64(rd.content||''));if(summary&&(isJapanese(summary)||!autoDesc))autoDesc=summary}catch{}}
    let kind=inferKind(repo.name,tech,autoDesc),primary=pickPrimary(tech,names,dirs);
    if(tech==='other'||kind==='widget'||dirs.some(d=>/^(godot|game|web|app|src|payload)\/$/i.test(d))){try{const tree=await api(`https://api.github.com/repos/${OWNER}/${encodeURIComponent(repo.name)}/git/trees/${encodeURIComponent(repo.default_branch)}?recursive=1`);const paths=(tree.tree||[]).filter(x=>x.type==='blob').map(x=>x.path);cache['tree|'+k]={at:Date.now(),data:{paths}};const nestedTech=techFromPaths(paths,kind,autoDesc);if(nestedTech!=='other')tech=nestedTech;kind=inferKind(repo.name,tech,autoDesc);const nestedPrimary=pickPrimaryFromPaths(tech,paths);if(nestedPrimary.length)primary=nestedPrimary}catch{}}
    if(tech==='other'&&kind==='widget')tech='scriptable';
    const role=inferRole(repo.name,kind,autoDesc);
    const data={tech,kind,role,primary:primary.slice(0,5),autoDesc,maturity};
    state.scans[repo.name]=data;cache[k]={at:Date.now(),data};saveJSON(LS_CACHE,cache);render();
  }catch(e){
    const kind=previous?.kind||KIND_OVERRIDE[repo.name]||'other';
    const tech=previous?.tech||TECH_OVERRIDE[repo.name]||(kind==='widget'?'scriptable':'unknown');
    state.scans[repo.name]={tech,kind,role:previous?.role||inferRole(repo.name,kind,repo.description||''),primary:previous?.primary||[],autoDesc:previous?.autoDesc||repo.description||'',maturity,error:e.message};render();
  }
}
let scanQueueRunning=false;
async function queueScans(repos=state.repos){
  if(scanQueueRunning)return;scanQueueRunning=true;
  try{const arr=[...repos];const workers=Array.from({length:2},async()=>{while(arr.length){const r=arr.shift();await scanRepo(r)}});await Promise.all(workers)}
  finally{scanQueueRunning=false}
}
"""
s=s[:m.start()]+replacement+s[m.end():]

s=s.replace("const m=getMeta(name),sc=state.scans[name]||{tech:'unknown',kind:","const m=getMeta(name),sc=state.scans[name]||{tech:TECH_OVERRIDE[name]||'unknown',kind:")
s=s.replace("state.scans[r.name]||{tech:'unknown',kind:","state.scans[r.name]||{tech:TECH_OVERRIDE[r.name]||'unknown',kind:")

# Guard against accidental incomplete patch.
required=["devhub.cache.v14","const TECH_OVERRIDE=","function cachedScanFor(repo)","async function loadDevStatus(repo)","let scanQueueRunning=false","raw.githubusercontent.com"]
for x in required:
    if x not in s: raise SystemExit('missing '+x)

p.write_text(s)
print('patched',len(s))
