from pathlib import Path
p=Path('index.html')
s=p.read_text()
s=s.replace("if(v==='warn'||v==='partial'||v==='checking'||v==='in-progress')return'warn';\n  return'none';", "if(v==='warn'||v==='partial'||v==='checking'||v==='in-progress')return'warn';\n  if(v==='na'||v==='not-applicable'||v==='対象外')return'na';\n  return'none';")
s=s.replace("function qualityIcon(status){return status==='ok'?'✅':status==='warn'?'⚠️':'—'}", "function qualityIcon(status){return status==='ok'?'✅':status==='warn'?'⚠️':status==='na'?'対象外':'—'}")
s=s.replace("✅ 確認済み　⚠️ 確認中 / 一部確認　— 未確認", "✅ 確認済み　⚠️ 確認中 / 一部確認　— 未確認　対象外")
s=s.replace("${m.next?`<div class=\"nextline\"><b>次：</b>${escapeHtml(m.next)}</div>`:''}</article>", "${(m.next||sc.maturity?.next)?`<div class=\"nextline\"><b>次：</b>${escapeHtml(m.next||sc.maturity?.next)}</div>`:''}</article>")
p.write_text(s)
print('status applicability patch applied')
