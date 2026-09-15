from pathlib import Path

p=Path('index.html')
s=p.read_text()

s=s.replace("LS_CACHE='devhub.cache.v11'", "LS_CACHE='devhub.cache.v12'", 1)

old_css=".stat{display:flex;align-items:center;gap:5px;flex:0 0 auto;border:1px solid var(--border);background:var(--surface);border-radius:999px;padding:5px 9px}.stat.attention{border-color:#92400e;background:#451a03}.stat.attention .num,.stat.attention .label{color:#fde68a}.num{font-size:12px;font-weight:900}.label{font-size:10px;color:var(--muted)}"
new_css=".stat{display:flex;align-items:center;gap:5px;flex:0 0 auto;border:1px solid var(--border);background:var(--surface);border-radius:999px;padding:5px 9px}.stat.attention{border-color:#92400e;background:#451a03}.stat.attention .num,.stat.attention .label{color:#fde68a}.stat.critical{border-color:#be123c;background:#4c0519}.stat.critical .num,.stat.critical .label{color:#fecdd3}.num{font-size:12px;font-weight:900}.label{font-size:10px;color:var(--muted)}"
if old_css not in s: raise SystemExit('stats css anchor not found')
s=s.replace(old_css,new_css,1)

old_badge=".attention-badge{border:1px solid #92400e;background:#451a03;color:#fde68a;border-radius:999px;padding:2px 6px;font-size:9px;line-height:1.2;font-weight:900;white-space:nowrap}.pinbtn"
new_badge=".attention-badge{border:1px solid #92400e;background:#451a03;color:#fde68a;border-radius:999px;padding:2px 6px;font-size:9px;line-height:1.2;font-weight:900;white-space:nowrap}.attention-badge.critical{border-color:#be123c;background:#4c0519;color:#fecdd3}.pinbtn"
if old_badge not in s: raise SystemExit('badge css anchor not found')
s=s.replace(old_badge,new_badge,1)

old_fn='''function qualityIcon(status){return status==='ok'?'✅':status==='warn'?'⚠️':status==='na'?'対象外':'—'}
function attentionCount(sc){const m=sc?.maturity;if(m?.source!=='explicit')return 0;return (m.checks||[]).filter(x=>x.status==='warn').length}
function attentionBadgeHTML(sc){const n=attentionCount(sc);return n?`<span class="attention-badge">要確認 ${n}</span>`:''}'''
new_fn='''function qualityIcon(status){return status==='ok'?'✅':status==='warn'?'⚠️':status==='na'?'対象外':'—'}
function reviewPriority(sc){const m=sc?.maturity;if(m?.source!=='explicit')return {level:0,count:0,critical:0,normal:0};const warns=(m.checks||[]).filter(x=>x.status==='warn');const critical=warns.filter(x=>x.key==='boot'||x.key==='device').length;const normal=warns.length-critical;return {level:critical?2:normal?1:0,count:warns.length,critical,normal}}
function attentionCount(sc){return reviewPriority(sc).count}
function attentionBadgeHTML(sc){const p=reviewPriority(sc);if(!p.count)return'';return `<span class="attention-badge ${p.level===2?'critical':''}" title="${p.level===2?'最優先':'要確認'}">⚠️${p.count}</span>`}'''
if old_fn not in s: raise SystemExit('attention functions anchor not found')
s=s.replace(old_fn,new_fn,1)

old_stats="const vals=[['Repo',rs.length],['プロダクト',productCount],['補助',supportCount],['今週更新',rs.filter(r=>new Date(r.pushed_at||r.updated_at).getTime()>=sevenDays).length],['要確認',rs.filter(r=>attentionCount(state.scans[r.name])>0).length],['完了',rs.filter(r=>getMeta(r.name).status==='complete').length]];if(rs.some(r=>r.private))vals.splice(3,0,['非公開',rs.filter(r=>r.private).length]);$('#stats').innerHTML=vals.map(([l,n])=>`<div class=\"stat ${l==='要確認'&&n?'attention':''}\"><span class=\"num\">${n}</span><span class=\"label\">${l}</span></div>`).join('')}"
new_stats="const vals=[['Repo',rs.length],['プロダクト',productCount],['補助',supportCount],['今週更新',rs.filter(r=>new Date(r.pushed_at||r.updated_at).getTime()>=sevenDays).length],['最優先',rs.filter(r=>reviewPriority(state.scans[r.name]).level===2).length],['要確認',rs.filter(r=>reviewPriority(state.scans[r.name]).level===1).length],['完了',rs.filter(r=>getMeta(r.name).status==='complete').length]];if(rs.some(r=>r.private))vals.splice(3,0,['非公開',rs.filter(r=>r.private).length]);$('#stats').innerHTML=vals.map(([l,n])=>`<div class=\"stat ${l==='最優先'&&n?'critical':l==='要確認'&&n?'attention':''}\"><span class=\"num\">${n}</span><span class=\"label\">${l}</span></div>`).join('')}"
if old_stats not in s: raise SystemExit('stats function anchor not found')
s=s.replace(old_stats,new_stats,1)

old_sort="const sr=statusRank(getMeta(a.name).status)-statusRank(getMeta(b.name).status);if(sr)return sr;const ar=attentionCount(state.scans[b.name])-attentionCount(state.scans[a.name]);if(ar)return ar;return new Date(b.pushed_at||b.updated_at)-new Date(a.pushed_at||a.updated_at)})}"
new_sort="const ap=reviewPriority(state.scans[a.name]),bp=reviewPriority(state.scans[b.name]);const pr=bp.level-ap.level;if(pr)return pr;const cr=bp.critical-ap.critical;if(cr)return cr;const ar=bp.count-ap.count;if(ar)return ar;const sr=statusRank(getMeta(a.name).status)-statusRank(getMeta(b.name).status);if(sr)return sr;return new Date(b.pushed_at||b.updated_at)-new Date(a.pushed_at||a.updated_at)})}"
if old_sort not in s: raise SystemExit('sort anchor not found')
s=s.replace(old_sort,new_sort,1)

p.write_text(s)
print('refined attention priority applied')
