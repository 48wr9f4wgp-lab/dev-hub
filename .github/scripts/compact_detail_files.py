from pathlib import Path
import re

p = Path('index.html')
s = p.read_text()

css = '''
    .folderchips{display:flex;flex-wrap:wrap;gap:5px;margin-top:12px}.folderchip{border:1px solid var(--border);background:#0d151d;border-radius:999px;padding:4px 8px;font-size:10px;color:#cbd5e1}.importantfiles{display:grid;gap:5px;margin-top:7px}.morefiles{margin-top:8px;border:1px solid var(--border);border-radius:10px;background:#0d151d;overflow:hidden}.morefiles summary{cursor:pointer;list-style:none;padding:9px 10px;font-size:11px;font-weight:800;color:#cbd5e1}.morefiles summary::-webkit-details-marker{display:none}.morefiles summary:after{content:'＋';float:right;color:var(--muted)}.morefiles[open] summary:after{content:'−'}.morefiles .filelist{max-height:320px;padding:0 8px 8px}
'''
if '.folderchips{' not in s:
    s = s.replace('    dialog{width:min(92vw,560px);', css + '    dialog{width:min(92vw,560px);')

helper = r'''function detailFiles(paths,tech){
  const relevant=paths.filter(p=>isImportantPath(p,tech));
  const folders=[...new Set(relevant.filter(p=>p.includes('/')).map(p=>p.split('/')[0]))].slice(0,8);
  const score=p=>{let n=0;const low=p.toLowerCase();if(/(^|\/)(main\.tscn|project\.godot|export_presets\.cfg|index\.html|package\.json|manifest(\.webmanifest|\.json)?|service-worker\.js)$/.test(low))n+=120;if(!p.includes('/'))n+=35;if(/\.(gd|js|ts|tsx|jsx|py|swift|kt|java|cs|cpp|go|rs)$/i.test(p))n+=25;if(/(^|\/)(main|app|index|game|controller|manager|service|core)[^/]*\./i.test(p))n+=20;if(/test|spec|fixture|mock/i.test(p))n-=25;if(/assets?\//i.test(p)&&!/icon|logo/i.test(p))n-=8;return n};
  const important=[...relevant].sort((a,b)=>score(b)-score(a)||a.localeCompare(b)).slice(0,6);
  return {relevant:relevant.slice(0,70),folders,important};
}
'''
if 'function detailFiles(paths,tech)' not in s:
    marker = 'async function renderDetail(name,fetchTree=true)'
    s = s.replace(marker, helper + marker)

old = "const sums=summaryFor(d.paths,sc.tech);const relevant=d.paths.filter(p=>isImportantPath(p,sc.tech)).slice(0,70);$('#deepStructure').className='';$('#deepStructure').innerHTML=`<div class=\"summarygrid\" style=\"margin-top:12px\">${sums.map(([l,n])=>`<div class=\"mini\"><b>${n}</b><span>${l}</span></div>`).join('')}</div><h3 style=\"margin-top:16px\">主要ファイル</h3><div class=\"filelist\">${relevant.map(p=>`<div class=\"file mono\">${escapeHtml(p)}</div>`).join('')||'<div class=\"small\">表示対象のファイルがありません。</div>'}</div>`"
new = "const sums=summaryFor(d.paths,sc.tech);const df=detailFiles(d.paths,sc.tech);$('#deepStructure').className='';$('#deepStructure').innerHTML=`<div class=\"summarygrid\" style=\"margin-top:12px\">${sums.map(([l,n])=>`<div class=\"mini\"><b>${n}</b><span>${l}</span></div>`).join('')}</div>${df.folders.length?`<h3 style=\"margin-top:16px\">主要フォルダ</h3><div class=\"folderchips\">${df.folders.map(f=>`<span class=\"folderchip mono\">${escapeHtml(f)}/</span>`).join('')}</div>`:''}<h3 style=\"margin-top:16px\">重要ファイル</h3><div class=\"importantfiles\">${df.important.map(p=>`<div class=\"file mono\">${escapeHtml(p)}</div>`).join('')||'<div class=\"small\">表示対象のファイルがありません。</div>'}</div>${df.relevant.length>df.important.length?`<details class=\"morefiles\"><summary>すべて見る（${df.relevant.length}件）</summary><div class=\"filelist\">${df.relevant.map(p=>`<div class=\"file mono\">${escapeHtml(p)}</div>`).join('')}</div></details>`:''}`"
if old not in s:
    raise SystemExit('detail file rendering block not found')
s = s.replace(old, new, 1)

p.write_text(s)
