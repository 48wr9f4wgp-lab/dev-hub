from pathlib import Path

p=Path('index.html')
s=p.read_text()

s=s.replace("LS_CACHE='devhub.cache.v12'", "LS_CACHE='devhub.cache.v13'", 1)

old_unset="""function unsetDevStatus(message='DEV_STATUS.json未設定'){
  return {phase:'状態未設定',checks:DEV_CHECKS.map(([key,label])=>({key,label,status:'none'})),next:'',note:message,source:'unset'};
}
"""
new_unset="""function unsetDevStatus(message='DEV_STATUS.json未設定'){
  return {phase:'状態未設定',checks:DEV_CHECKS.map(([key,label])=>({key,label,status:'none'})),next:'',note:message,source:'unset'};
}
function errorDevStatus(message='DEV_STATUS.json取得失敗'){
  return {phase:'状態取得失敗',checks:DEV_CHECKS.map(([key,label])=>({key,label,status:'none'})),next:'',note:message,source:'error'};
}
"""
if old_unset not in s: raise SystemExit('unsetDevStatus anchor not found')
s=s.replace(old_unset,new_unset,1)

old_load="""async function loadDevStatus(repo,names){
  if(!names.some(n=>n.toLowerCase()==='dev_status.json'))return unsetDevStatus();
  try{
    const f=await api(`https://api.github.com/repos/${OWNER}/${encodeURIComponent(repo.name)}/contents/DEV_STATUS.json?ref=${encodeURIComponent(repo.default_branch)}`);
    return explicitDevStatus(JSON.parse(decode64(f.content||'')));
  }catch(e){return unsetDevStatus('DEV_STATUS.json読込失敗');}
}
"""
new_load="""async function loadDevStatus(repo,names,root=[]){
  const item=Array.isArray(root)?root.find(x=>String(x?.name||'').toLowerCase()==='dev_status.json'):null;
  if(!item&&!names.some(n=>n.toLowerCase()==='dev_status.json'))return unsetDevStatus();
  if(!repo.private&&item?.download_url){
    const ctl=new AbortController(),timer=setTimeout(()=>ctl.abort(),5000);
    try{
      const r=await fetch(item.download_url,{signal:ctl.signal,cache:'no-store'});
      if(!r.ok)throw new Error(`raw ${r.status}`);
      return explicitDevStatus(JSON.parse(await r.text()));
    }catch(e){
      // Public repos normally use raw.githubusercontent.com so DEV_STATUS does not consume API quota.
    }finally{clearTimeout(timer)}
  }
  try{
    const f=await api(`https://api.github.com/repos/${OWNER}/${encodeURIComponent(repo.name)}/contents/DEV_STATUS.json?ref=${encodeURIComponent(repo.default_branch)}`);
    return explicitDevStatus(JSON.parse(decode64(f.content||'')));
  }catch(e){return errorDevStatus(e?.message||'DEV_STATUS.json読込失敗');}
}
"""
if old_load not in s: raise SystemExit('loadDevStatus anchor not found')
s=s.replace(old_load,new_load,1)

old_quality="""function qualityLineHTML(sc){const m=sc?.maturity;if(!m)return'';if(m.source!=='explicit')return `<div class=\"qualityline\"><span class=\"quality-item\">状態ファイル未設定</span></div>`;const shown=(m.checks||[]).slice(0,5);return `<div class=\"qualityline\">${shown.map(x=>`<span class=\"quality-item\">${escapeHtml(x.label)} ${qualityIcon(x.status)}</span>`).join('')}</div>`}
function maturityBreakdownHTML(m){if(!m||m.source!=='explicit')return'<div class=\"maturity-note\">このRepoにはDEV_STATUS.jsonがまだありません。推測でフェーズ判定はしません。</div>';const note=m.note?`<div class=\"maturity-note\">${escapeHtml(m.note)}</div>`:'';return `<div class=\"maturity-note\">✅ 確認済み　⚠️ 確認中 / 一部確認　— 未確認　対象外</div>${note}<div class=\"maturity-breakdown\">${(m.checks||[]).map(x=>`<div class=\"maturity-row\"><span>${escapeHtml(x.label)}</span><span class=\"quality-status ${x.status}\">${qualityIcon(x.status)}</span></div>`).join('')}</div>`}
"""
new_quality="""function qualityLineHTML(sc){const m=sc?.maturity;if(!m)return'';if(m.source==='error')return `<div class=\"qualityline\"><span class=\"quality-item\">状態ファイル取得失敗</span></div>`;if(m.source!=='explicit')return `<div class=\"qualityline\"><span class=\"quality-item\">状態ファイル未設定</span></div>`;const shown=(m.checks||[]).slice(0,5);return `<div class=\"qualityline\">${shown.map(x=>`<span class=\"quality-item\">${escapeHtml(x.label)} ${qualityIcon(x.status)}</span>`).join('')}</div>`}
function maturityBreakdownHTML(m){if(m?.source==='error')return `<div class=\"maturity-note\">DEV_STATUS.jsonは存在しますが取得できませんでした。${escapeHtml(m.note||'')}</div>`;if(!m||m.source!=='explicit')return'<div class=\"maturity-note\">このRepoにはDEV_STATUS.jsonがまだありません。推測でフェーズ判定はしません。</div>';const note=m.note?`<div class=\"maturity-note\">${escapeHtml(m.note)}</div>`:'';return `<div class=\"maturity-note\">✅ 確認済み　⚠️ 確認中 / 一部確認　— 未確認　対象外</div>${note}<div class=\"maturity-breakdown\">${(m.checks||[]).map(x=>`<div class=\"maturity-row\"><span>${escapeHtml(x.label)}</span><span class=\"quality-status ${x.status}\">${qualityIcon(x.status)}</span></div>`).join('')}</div>`}
"""
if old_quality not in s: raise SystemExit('quality helpers anchor not found')
s=s.replace(old_quality,new_quality,1)

old_auto="""    let autoDesc=repo.description||'';
    if(names.some(n=>/^readme/i.test(n))&&(!autoDesc||!isJapanese(autoDesc))){try{const rd=await api(`https://api.github.com/repos/${OWNER}/${encodeURIComponent(repo.name)}/readme?ref=${encodeURIComponent(repo.default_branch)}`);const summary=readmeSummary(decode64(rd.content||''));if(summary&&(isJapanese(summary)||!autoDesc))autoDesc=summary}catch{}}
    let kind=inferKind(repo.name,tech,autoDesc),primary=pickPrimary(tech,names,dirs);
"""
new_auto="""    const maturity=await loadDevStatus(repo,names,root);
    let autoDesc=repo.description||'';
    if(names.some(n=>/^readme/i.test(n))&&(!autoDesc||!isJapanese(autoDesc))){try{const rd=await api(`https://api.github.com/repos/${OWNER}/${encodeURIComponent(repo.name)}/readme?ref=${encodeURIComponent(repo.default_branch)}`);const summary=readmeSummary(decode64(rd.content||''));if(summary&&(isJapanese(summary)||!autoDesc))autoDesc=summary}catch{}}
    let kind=inferKind(repo.name,tech,autoDesc),primary=pickPrimary(tech,names,dirs);
"""
if old_auto not in s: raise SystemExit('scan maturity insertion anchor not found')
s=s.replace(old_auto,new_auto,1)

old_late="""    const role=inferRole(repo.name,kind,autoDesc);
    const maturity=await loadDevStatus(repo,names);
    const data={tech,kind,role,primary:primary.slice(0,5),autoDesc,maturity};
"""
new_late="""    const role=inferRole(repo.name,kind,autoDesc);
    const data={tech,kind,role,primary:primary.slice(0,5),autoDesc,maturity};
"""
if old_late not in s: raise SystemExit('late maturity anchor not found')
s=s.replace(old_late,new_late,1)

p.write_text(s)
print('status loading resilience patch applied')
