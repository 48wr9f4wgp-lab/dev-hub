from pathlib import Path

p=Path('index.html')
s=p.read_text()

s=s.replace("LS_CACHE='devhub.cache.v10'", "LS_CACHE='devhub.cache.v11'", 1)

old_css=".stat{display:flex;align-items:center;gap:5px;flex:0 0 auto;border:1px solid var(--border);background:var(--surface);border-radius:999px;padding:5px 9px}.num{font-size:12px;font-weight:900}.label{font-size:10px;color:var(--muted)}"
new_css=".stat{display:flex;align-items:center;gap:5px;flex:0 0 auto;border:1px solid var(--border);background:var(--surface);border-radius:999px;padding:5px 9px}.stat.attention{border-color:#92400e;background:#451a03}.stat.attention .num,.stat.attention .label{color:#fde68a}.num{font-size:12px;font-weight:900}.label{font-size:10px;color:var(--muted)}"
if old_css not in s: raise SystemExit('stats CSS anchor not found')
s=s.replace(old_css,new_css,1)

old_meta=".updated{font-size:10px;line-height:1.3;color:var(--muted);white-space:nowrap}.pinbtn"
new_meta=".updated{font-size:10px;line-height:1.3;color:var(--muted);white-space:nowrap}.attention-badge{border:1px solid #92400e;background:#451a03;color:#fde68a;border-radius:999px;padding:2px 6px;font-size:9px;line-height:1.2;font-weight:900;white-space:nowrap}.pinbtn"
if old_meta not in s: raise SystemExit('cardmeta CSS anchor not found')
s=s.replace(old_meta,new_meta,1)

old_fn="function qualityIcon(status){return status==='ok'?'✅':status==='warn'?'⚠️':status==='na'?'対象外':'—'}"
new_fn="function qualityIcon(status){return status==='ok'?'✅':status==='warn'?'⚠️':status==='na'?'対象外':'—'}\nfunction attentionCount(sc){const m=sc?.maturity;if(m?.source!=='explicit')return 0;return (m.checks||[]).filter(x=>x.status==='warn').length}\nfunction attentionBadgeHTML(sc){const n=attentionCount(sc);return n?`<span class=\"attention-badge\">要確認 ${n}</span>`:''}"
if old_fn not in s: raise SystemExit('qualityIcon anchor not found')
s=s.replace(old_fn,new_fn,1)

old_stats="const vals=[['Repo',rs.length],['プロダクト',productCount],['補助',supportCount],['今週更新',rs.filter(r=>new Date(r.pushed_at||r.updated_at).getTime()>=sevenDays).length],['完了',rs.filter(r=>getMeta(r.name).status==='complete').length]];if(rs.some(r=>r.private))vals.splice(3,0,['非公開',rs.filter(r=>r.private).length]);$('#stats').innerHTML=vals.map(([l,n])=>`<div class=\"stat\"><span class=\"num\">${n}</span><span class=\"label\">${l}</span></div>`).join('')}"
new_stats="const vals=[['Repo',rs.length],['プロダクト',productCount],['補助',supportCount],['今週更新',rs.filter(r=>new Date(r.pushed_at||r.updated_at).getTime()>=sevenDays).length],['要確認',rs.filter(r=>attentionCount(state.scans[r.name])>0).length],['完了',rs.filter(r=>getMeta(r.name).status==='complete').length]];if(rs.some(r=>r.private))vals.splice(3,0,['非公開',rs.filter(r=>r.private).length]);$('#stats').innerHTML=vals.map(([l,n])=>`<div class=\"stat ${l==='要確認'&&n?'attention':''}\"><span class=\"num\">${n}</span><span class=\"label\">${l}</span></div>`).join('')}"
if old_stats not in s: raise SystemExit('stats function anchor not found')
s=s.replace(old_stats,new_stats,1)

old_sort="const sr=statusRank(getMeta(a.name).status)-statusRank(getMeta(b.name).status);if(sr)return sr;return new Date(b.pushed_at||b.updated_at)-new Date(a.pushed_at||a.updated_at)})}"
new_sort="const sr=statusRank(getMeta(a.name).status)-statusRank(getMeta(b.name).status);if(sr)return sr;const ar=attentionCount(state.scans[b.name])-attentionCount(state.scans[a.name]);if(ar)return ar;return new Date(b.pushed_at||b.updated_at)-new Date(a.pushed_at||a.updated_at)})}"
if old_sort not in s: raise SystemExit('sort anchor not found')
s=s.replace(old_sort,new_sort,1)

old_card="<div class=\"cardmeta\"><span class=\"updated\">${ago(r.pushed_at||r.updated_at)}</span><button class=\"pinbtn ${m.pinned?'on':''}"
new_card="<div class=\"cardmeta\">${attentionBadgeHTML(sc)}<span class=\"updated\">${ago(r.pushed_at||r.updated_at)}</span><button class=\"pinbtn ${m.pinned?'on':''}"
if old_card not in s: raise SystemExit('card meta anchor not found')
s=s.replace(old_card,new_card,1)

p.write_text(s)
print('attention priority patch applied')
