from pathlib import Path
import re

p=Path('index.html')
s=p.read_text()

s=s.replace("['7日以内',rs.filter(r=>new Date(r.pushed_at||r.updated_at).getTime()>=sevenDays).length]", "['今週更新',rs.filter(r=>new Date(r.pushed_at||r.updated_at).getTime()>=sevenDays).length]")

css='''
    .detailhero h2{margin:5px 0 2px;font-size:23px}.overview{font-size:13px;line-height:1.65;color:#d9e2ec;margin:10px 0 12px}.detailfacts{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-top:12px}.fact{background:#0d151d;border:1px solid var(--border);border-radius:10px;padding:9px 10px;min-width:0}.fact span{display:block;font-size:9px;color:var(--muted);font-weight:800;margin-bottom:2px}.fact b{display:block;font-size:12px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.progresshead{display:flex;justify-content:space-between;align-items:center;gap:10px}.progressvalue{font-size:12px;font-weight:900;color:#cbd5e1}.progressbar{height:8px;border-radius:999px;background:#0d151d;border:1px solid var(--border);overflow:hidden;margin:9px 0 12px}.progressfill{height:100%;background:linear-gradient(90deg,#0891b2,#22d3ee);border-radius:999px}.nowlist{display:grid;gap:7px}.nowitem{padding:9px 10px;border:1px solid var(--border);border-radius:10px;background:#0d151d}.nowitem span{display:block;font-size:9px;color:var(--muted);font-weight:800;margin-bottom:3px}.nowitem b{display:block;font-size:12px;line-height:1.5}.manage{padding:0}.manage summary{cursor:pointer;list-style:none;padding:14px;font-size:14px;font-weight:850;display:flex;justify-content:space-between;align-items:center}.manage summary::-webkit-details-marker{display:none}.manage summary:after{content:'＋';color:var(--muted);font-size:17px}.manage[open] summary:after{content:'−'}.managebody{padding:0 14px 14px;border-top:1px solid var(--border)}
'''
if '.detailfacts{' not in s:
    s=s.replace('    dialog{width:min(92vw,560px);', css+'    dialog{width:min(92vw,560px);')

new_chunk=r'''async function renderDetail(name,fetchTree=true){
  const repo=state.repos.find(r=>r.name===name);if(!repo)return;
  const m=getMeta(name),sc=state.scans[name]||{tech:'unknown',kind:KIND_OVERRIDE[name]||'other',autoDesc:repo.description||'',primary:[]};
  const desc=displayDesc(repo,sc)||'説明未設定';
  const progress=Math.max(0,Math.min(100,Number(m.progress)||0));
  const tech=techLabels[sc.tech]||'確認中',kind=kindLabels[sc.kind]||'その他';
  $('#drawerTitle').textContent=displayName(name);
  const detail=$('#detail');
  const nowItems=[m.objective?`<div class="nowitem"><span>現在の目的</span><b>${escapeHtml(m.objective)}</b></div>`:'',m.next?`<div class="nowitem"><span>次にやること</span><b>${escapeHtml(m.next)}</b></div>`:'',m.memo?`<div class="nowitem"><span>メモ</span><b>${escapeHtml(m.memo)}</b></div>`:''].join('');
  detail.innerHTML=`<div class="panel detailhero"><div class="eyebrow">${escapeHtml(kind)} · ${escapeHtml(tech)}</div><h2>${escapeHtml(displayName(name))}</h2><div class="repoid mono" style="max-width:none">${escapeHtml(name)}</div><div class="overview">${escapeHtml(desc)}</div><div class="chips"><button class="chip ${m.pinned?'done':''}" id="detailPin">${m.pinned?'★ ピン留め中':'☆ ピン留め'}</button><span class="chip ${repo.private?'private':''}">${repo.private?'非公開':'公開'}</span><span class="chip ${chipClassStatus(m.status)}">${statusLabels[m.status]}</span></div><div class="detailfacts"><div class="fact"><span>技術</span><b>${escapeHtml(tech)}</b></div><div class="fact"><span>種類</span><b>${escapeHtml(kind)}</b></div><div class="fact"><span>ブランチ</span><b class="mono">${escapeHtml(repo.default_branch||'main')}</b></div><div class="fact"><span>更新</span><b>${escapeHtml(ago(repo.pushed_at||repo.updated_at))}</b></div></div></div><div class="panel"><div class="progresshead"><h3 style="margin:0">現在</h3><div class="progressvalue">${statusLabels[m.status]} · ${progress}%</div></div><div class="progressbar"><div class="progressfill" style="width:${progress}%"></div></div>${nowItems?`<div class="nowlist">${nowItems}</div>`:'<div class="small">目的・次の作業・メモはまだ設定されていません。</div>'}</div><div class="panel" id="structurePanel"><h3>技術・構成</h3><div class="paths mono" style="white-space:normal">${sc.primary.length?escapeHtml(sc.primary.join(' / ')):'主要構成を取得中…'}</div><div id="deepStructure" class="loading" style="display:${fetchTree?'block':'none'}">詳細構成を読み込み中…</div></div><div class="panel"><h3>リンク</h3><div class="buttons"><a class="action primary" target="_blank" rel="noopener" href="${repo.html_url}">GitHubを開く</a>${repo.homepage?`<a class="action" target="_blank" rel="noopener" href="${escapeHtml(repo.homepage)}">公開版を開く</a>`:''}</div></div>${editorHTML(name,m,desc)}`;
  $('#detailPin').onclick=()=>togglePin(name);bindEditor(name);
  if(fetchTree){try{const d=await detailScan(repo);if(state.active!==name)return;const sums=summaryFor(d.paths,sc.tech);const relevant=d.paths.filter(p=>isImportantPath(p,sc.tech)).slice(0,70);$('#deepStructure').className='';$('#deepStructure').innerHTML=`<div class="summarygrid" style="margin-top:12px">${sums.map(([l,n])=>`<div class="mini"><b>${n}</b><span>${l}</span></div>`).join('')}</div><h3 style="margin-top:16px">主要ファイル</h3><div class="filelist">${relevant.map(p=>`<div class="file mono">${escapeHtml(p)}</div>`).join('')||'<div class="small">表示対象のファイルがありません。</div>'}</div>`}catch(e){if($('#deepStructure')){$('#deepStructure').className='error';$('#deepStructure').textContent='詳細構成を取得できません: '+e.message}}}
}
function editorHTML(name,m,autoDesc){return `<details class="panel manage"><summary>管理情報を編集</summary><div class="managebody"><div class="field"><label>ひとこと説明</label><textarea id="fDesc" placeholder="このアプリは何をするもの？">${escapeHtml(m.description||autoDesc||'')}</textarea></div><div class="field"><label>進捗状態</label><div class="statusgrid" id="statusGrid">${Object.entries(statusLabels).map(([v,l])=>`<button class="statusbtn ${m.status===v?'active':''}" data-s="${v}">${l}</button>`).join('')}</div></div><div class="field"><label>進捗 <span id="progressVal">${m.progress}%</span></label><input class="range" id="fProgress" type="range" min="0" max="100" step="5" value="${m.progress}"></div><div class="field"><label>現在の目的</label><input id="fObjective" value="${escapeHtml(m.objective)}" placeholder="今どこを作っている？"></div><div class="field"><label>次にやること</label><input id="fNext" value="${escapeHtml(m.next)}" placeholder="次の一手を1つだけ"></div><div class="field"><label>メモ</label><textarea id="fMemo" placeholder="覚えておきたいこと">${escapeHtml(m.memo)}</textarea></div><div class="savehint">進捗・メモ・ピンはこの端末に自動保存。種類・技術・構成・更新日はGitHubから自動取得します。</div></div></details>`}
'''
pattern=r"async function renderDetail\(name,fetchTree=true\)\{.*?\nfunction bindEditor"
if not re.search(pattern,s,flags=re.S):
    raise SystemExit('detail block not found')
s=re.sub(pattern,new_chunk+'function bindEditor',s,count=1,flags=re.S)

p.write_text(s)
