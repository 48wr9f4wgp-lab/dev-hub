from pathlib import Path
import re

p = Path('index.html')
s = p.read_text()

# 1) UI: role filter + product/support sections.
s = s.replace(
'''    <div class="filter-row"><div class="filter-title">種類</div><div class="choices" id="kindChoices"></div></div>''',
'''    <div class="filter-row"><div class="filter-title">役割</div><div class="choices" id="roleChoices"></div></div>\n    <div class="filter-row"><div class="filter-title">種類</div><div class="choices" id="kindChoices"></div></div>''')

s = s.replace(
'''  <div class="sectionhead"><h2 id="mainListTitle">アプリ一覧</h2><span class="count" id="resultCount"></span></div>\n  <div id="message" class="loading"><span class="spinner"></span><br>GitHubから読み込み中…</div>\n  <section class="cards" id="cards"></section>''',
'''  <div class="sectionhead" id="productHead"><h2 id="mainListTitle">プロダクト</h2><span class="count" id="resultCount"></span></div>\n  <div id="message" class="loading"><span class="spinner"></span><br>GitHubから読み込み中…</div>\n  <section class="cards" id="cards"></section>\n  <section id="supportWrap" hidden>\n    <div class="sectionhead"><h2>開発基盤 / QA</h2><span class="count" id="supportCount"></span></div>\n    <section class="cards" id="supportCards"></section>\n  </section>''')

s = s.replace(
'''自動取得：リポジトリ、更新日、技術、種類、構成、README。手動管理：進捗、次の作業、メモ、ピン留め。''',
'''自動取得：リポジトリ、更新日、役割、種類、技術、構成、README。手動管理：進捗、次の作業、メモ、ピン留め。''')

# 2) Cache/state/labels.
s = s.replace("const LS_META='devhub.meta.v2', LS_TOKEN='devhub.token.v1', LS_CACHE='devhub.cache.v6';",
              "const LS_META='devhub.meta.v2', LS_TOKEN='devhub.token.v1', LS_CACHE='devhub.cache.v7';")
s = s.replace("const state={repos:[],scans:{},kind:'all',tech:'all',status:'all',vis:'all',q:'',active:null};",
              "const state={repos:[],scans:{},role:'all',kind:'all',tech:'all',status:'all',vis:'all',q:'',active:null};")
s = s.replace("const $=s=>document.querySelector(s);const cards=$('#cards'),pinnedCards=$('#pinnedCards'),msg=$('#message');",
              "const $=s=>document.querySelector(s);const cards=$('#cards'),supportCards=$('#supportCards'),pinnedCards=$('#pinnedCards'),msg=$('#message');")
s = s.replace("const techLabels={godot:'Godot',web:'Web / PWA',other:'その他',unknown:'確認中'};",
              "const techLabels={godot:'Godot',web:'Web / PWA',scriptable:'Scriptable',other:'その他',unknown:'確認中'};")
s = s.replace("const kindLabels={game:'ゲーム',tool:'ツール',widget:'ウィジェット',platform:'基盤',qa:'配布 / QA',other:'その他'};",
              "const kindLabels={game:'ゲーム',tool:'ツール',widget:'ウィジェット',platform:'基盤',qa:'配布 / QA',other:'その他'};\nconst roleLabels={product:'プロダクト',support:'開発基盤 / QA'};")

# 3) Explicit role overrides for known repos. Unknown repos fall back to heuristics.
anchor = "const KIND_OVERRIDE={\n  'farm-loop':'game','-grid-bloom':'game','machi-loop':'game','Logistics-Boss':'game',\n  'fish-target':'tool','tackle-fit':'tool','tide-dash':'tool','dev-hub':'tool',\n  'motorsport-hub':'widget','combat-hub':'widget','club-pulse':'widget',\n  '-velvet-pwa':'platform','-scrap-planet-qa':'qa','48wr9f4wgp-lab-tide-dash':'qa'\n};"
if anchor not in s:
    raise SystemExit('KIND_OVERRIDE block not found')
s = s.replace(anchor, anchor + "\nconst ROLE_OVERRIDE={\n  'dev-hub':'support','-velvet-pwa':'support','-scrap-planet-qa':'support','48wr9f4wgp-lab-tide-dash':'support'\n};")

# 4) Tech chip styling.
s = s.replace(".chip.web{border-color:#15803d;color:#86efac;background:#052e16}",
              ".chip.web{border-color:#15803d;color:#86efac;background:#052e16}.chip.scriptable{border-color:#0369a1;color:#bae6fd;background:#082f49}")

# 5) Inference helpers.
old_infer = "function inferKind(name,tech,desc=''){if(KIND_OVERRIDE[name])return KIND_OVERRIDE[name];const t=`${name} ${desc}`.toLowerCase();if(/\\bqa\\b|hosting|public build|verified build/.test(t))return'qa';if(/widget|scriptable/.test(t))return'widget';if(tech==='godot'||/game|simulator|simulation|puzzle/.test(t))return'game';if(/platform|framework|common base|基盤/.test(t))return'platform';if(tech==='web')return'tool';return'other'}"
new_infer = old_infer + "\nfunction inferRole(name,kind,desc=''){if(ROLE_OVERRIDE[name])return ROLE_OVERRIDE[name];const t=`${name} ${desc}`.toLowerCase();if(kind==='qa'||kind==='platform'||/\\bqa\\b|hosting|host repo|public build|verified build|distribution|deploy|common base|framework|基盤/.test(t))return'support';return'product'}"
if old_infer not in s:
    raise SystemExit('inferKind not found')
s = s.replace(old_infer, new_infer)

# 6) Recursive path-based tech/primary detection for nested projects.
marker = "function isImportantPath(p,tech){"
helpers = r'''function techFromPaths(paths,kindHint='other',desc=''){
  const low=paths.map(p=>p.toLowerCase());
  if(low.some(p=>p==='project.godot'||p.endsWith('/project.godot')))return'godot';
  if(low.some(p=>/(^|\/)(package\.json|index\.html|manifest\.webmanifest|manifest\.json|service-worker\.js)$/.test(p)))return'web';
  if(kindHint==='widget'||/scriptable/i.test(desc||''))return'scriptable';
  return'other';
}
function pickPrimaryFromPaths(tech,paths){
  const dirs=new Set();for(const p of paths){const parts=p.split('/');for(let i=1;i<parts.length;i++)dirs.add(parts.slice(0,i).join('/')+'/')}
  const files=new Set(paths);const all=[...files,...dirs];
  const rank=x=>{const low=x.toLowerCase();let n=0;if(tech==='godot'){if(low.endsWith('project.godot'))n+=150;if(low.endsWith('main.tscn'))n+=140;if(/(^|\/)scenes\/$/.test(low))n+=105;if(/(^|\/)scripts\/$/.test(low))n+=100;if(/(^|\/)assets\/$/.test(low))n+=90;if(/(^|\/)addons\/$/.test(low))n+=70;if(/(^|\/)tests\/$/.test(low))n+=60}else if(tech==='web'){if(low.endsWith('index.html'))n+=150;if(low.endsWith('package.json'))n+=140;if(/(^|\/)src\/$/.test(low))n+=120;if(/(^|\/)app\/$/.test(low))n+=110;if(/(^|\/)components\/$/.test(low))n+=100;if(/(^|\/)public\/$/.test(low))n+=90;if(/manifest\.(webmanifest|json)$/.test(low))n+=85;if(/(^|\/)scripts\/$/.test(low))n+=75}else if(tech==='scriptable'){if(/\.js$/.test(low))n+=100;if(/(^|\/)(src|scripts|widgets)\/$/.test(low))n+=90;if(/(^|\/)(data|config)\/$/.test(low))n+=70}else{if(/(^|\/)(src|app|scripts|payload|data|public|assets|components|lib|server|client)\/$/.test(low))n+=80}if(x.startsWith('.github/')||/^\.github\/$/.test(x)||/README|LICENSE|CHANGELOG/i.test(x))n-=200;return n};
  return all.map(x=>[x,rank(x)]).filter(([,n])=>n>0).sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0])).map(([x])=>x).filter((x,i,a)=>a.indexOf(x)===i).slice(0,5);
}
'''
if marker not in s:
    raise SystemExit('isImportantPath marker not found')
s = s.replace(marker, helpers + marker, 1)

# Add Scriptable path handling.
s = s.replace("if(tech==='web')return /\\.html$|\\.(js|ts|tsx|jsx|css)$|manifest|service.worker|package\\.json|^src\\/|^app\\/|^components\\/|^public\\/|^scripts\\/|^data\\//i.test(p);return",
              "if(tech==='web')return /\\.html$|\\.(js|ts|tsx|jsx|css)$|manifest|service.worker|package\\.json|^src\\/|^app\\/|^components\\/|^public\\/|^scripts\\/|^data\\//i.test(p);if(tech==='scriptable')return /\\.(js|ts|json)$|^src\\/|^scripts\\/|^widgets\\/|^data\\/|^config\\//i.test(p);return")

# 7) Replace scanRepo with nested-aware version.
scan_re = re.compile(r"async function scanRepo\(repo\)\{.*?\nasync function queueScans", re.S)
m = scan_re.search(s)
if not m:
    raise SystemExit('scanRepo block not found')
new_scan = r'''async function scanRepo(repo){const k=rootKey(repo);if(cache[k]&&Date.now()-cache[k].at<12*3600*1000){state.scans[repo.name]=cache[k].data;render();return}try{const root=await api(`https://api.github.com/repos/${OWNER}/${encodeURIComponent(repo.name)}/contents/?ref=${encodeURIComponent(repo.default_branch)}`);const names=Array.isArray(root)?root.map(x=>x.name):[];const dirs=Array.isArray(root)?root.filter(x=>x.type==='dir').map(x=>x.name+'/'):[];const lower=names.map(x=>x.toLowerCase());let tech='other';if(lower.includes('project.godot'))tech='godot';else if(lower.includes('package.json')||lower.includes('index.html')||lower.some(x=>x.includes('manifest'))||lower.some(x=>x.includes('service-worker')))tech='web';let autoDesc=repo.description||'';if(names.some(n=>/^readme/i.test(n))&&(!autoDesc||!isJapanese(autoDesc))){try{const rd=await api(`https://api.github.com/repos/${OWNER}/${encodeURIComponent(repo.name)}/readme?ref=${encodeURIComponent(repo.default_branch)}`);const summary=readmeSummary(decode64(rd.content||''));if(summary&&(isJapanese(summary)||!autoDesc))autoDesc=summary}catch{}}let kind=inferKind(repo.name,tech,autoDesc);let primary=pickPrimary(tech,names,dirs);if(tech==='other'||kind==='widget'||dirs.some(d=>/^(godot|game|web|app|src|payload)\/$/i.test(d))){try{const tree=await api(`https://api.github.com/repos/${OWNER}/${encodeURIComponent(repo.name)}/git/trees/${encodeURIComponent(repo.default_branch)}?recursive=1`);const paths=(tree.tree||[]).filter(x=>x.type==='blob').map(x=>x.path);const nestedTech=techFromPaths(paths,kind,autoDesc);if(nestedTech!=='other')tech=nestedTech;kind=inferKind(repo.name,tech,autoDesc);const nestedPrimary=pickPrimaryFromPaths(tech,paths);if(nestedPrimary.length)primary=nestedPrimary}catch{}}if(tech==='other'&&kind==='widget')tech='scriptable';const role=inferRole(repo.name,kind,autoDesc);const data={tech,kind,role,primary:primary.slice(0,5),autoDesc};state.scans[repo.name]=data;cache[k]={at:Date.now(),data};saveJSON(LS_CACHE,cache);render()}catch(e){const kind=KIND_OVERRIDE[repo.name]||'other';state.scans[repo.name]={tech:kind==='widget'?'scriptable':'unknown',kind,role:inferRole(repo.name,kind,repo.description||''),primary:[],autoDesc:repo.description||'',error:e.message};render()}}
async function queueScans'''
s = s[:m.start()] + new_scan + s[m.end():]

# 8) Stats: distinguish total repos, product repos and support repos.
stats_re = re.compile(r"function stats\(\)\{.*?\}\nfunction chipClassStatus", re.S)
m = stats_re.search(s)
if not m:
    raise SystemExit('stats block not found')
new_stats = r'''function stats(){const rs=state.repos;const sevenDays=Date.now()-7*86400000;const productCount=rs.filter(r=>(state.scans[r.name]?.role||inferRole(r.name,KIND_OVERRIDE[r.name]||'other',r.description||''))==='product').length;const supportCount=rs.length-productCount;const vals=[['Repo',rs.length],['プロダクト',productCount],['補助',supportCount],['今週更新',rs.filter(r=>new Date(r.pushed_at||r.updated_at).getTime()>=sevenDays).length],['完了',rs.filter(r=>getMeta(r.name).status==='complete').length]];if(rs.some(r=>r.private))vals.splice(3,0,['非公開',rs.filter(r=>r.private).length]);$('#stats').innerHTML=vals.map(([l,n])=>`<div class="stat"><span class="num">${n}</span><span class="label">${l}</span></div>`).join('')}
function chipClassStatus'''
s = s[:m.start()] + new_stats + s[m.end():]

# 9) Filtering includes role.
s = s.replace("const m=getMeta(r.name),sc=state.scans[r.name]||{tech:'unknown',kind:KIND_OVERRIDE[r.name]||'other',autoDesc:r.description||''};",
              "const m=getMeta(r.name),sc=state.scans[r.name]||{tech:'unknown',kind:KIND_OVERRIDE[r.name]||'other',role:inferRole(r.name,KIND_OVERRIDE[r.name]||'other',r.description||''),autoDesc:r.description||''};")
s = s.replace("&&(state.kind==='all'||sc.kind===state.kind)&&(state.tech==='all'||sc.tech===state.tech)",
              "&&(state.role==='all'||sc.role===state.role)&&(state.kind==='all'||sc.kind===state.kind)&&(state.tech==='all'||sc.tech===state.tech)")

# 10) Chips are always two separate axes: kind + tech.
s = s.replace("function techShort(t){return t==='godot'?'Godot':t==='web'?'Web':''}",
              "function techShort(t){return t==='godot'?'Godot':t==='web'?'Web':t==='scriptable'?'Scriptable':t==='other'?'その他':'確認中'}\nfunction techChipClass(t){return t==='godot'?'godot':t==='web'?'web':t==='scriptable'?'scriptable':''}")
card_re = re.compile(r"function cardHTML\(r\)\{.*?\}\nfunction activeFilterCount", re.S)
m = card_re.search(s)
if not m:
    raise SystemExit('cardHTML block not found')
new_card = r'''function cardHTML(r){const m=getMeta(r.name),sc=state.scans[r.name]||{tech:'unknown',kind:KIND_OVERRIDE[r.name]||'other',role:inferRole(r.name,KIND_OVERRIDE[r.name]||'other',r.description||''),primary:[],autoDesc:r.description||''};const desc=displayDesc(r,sc);const visChip=r.private?'<span class="chip private">非公開</span>':'';const statusChip=m.status!=='not-started'?`<span class="chip ${chipClassStatus(m.status)}">${statusLabels[m.status]}</span>`:'';const k=kindLabels[sc.kind]||'その他',ts=techShort(sc.tech);const structureHtml=sc.primary?.length?`<div class="structure"><span class="kicker">構成</span><span class="paths mono">${escapeHtml(compactPrimary(sc))}</span></div>`:'';return `<article class="card ${m.pinned?'pinned':''}" data-repo="${escapeHtml(r.name)}"><div class="cardtop"><div class="name">${escapeHtml(displayName(r.name))}</div><div class="cardmeta"><span class="updated">${ago(r.pushed_at||r.updated_at)}</span><button class="pinbtn ${m.pinned?'on':''}" data-pin="${escapeHtml(r.name)}" aria-label="${m.pinned?'ピンを外す':'ピン留め'}">${m.pinned?'★':'☆'}</button></div></div><div class="desc ${desc?'':'missing'}">${escapeHtml(desc||'説明未設定 — タップして追加')}</div><div class="chips"><span class="chip ${sc.kind}">${escapeHtml(k)}</span><span class="chip ${techChipClass(sc.tech)}">${escapeHtml(ts)}</span>${visChip}${statusChip}</div>${structureHtml}${m.next?`<div class="nextline"><b>次：</b>${escapeHtml(m.next)}</div>`:''}</article>`}
function activeFilterCount'''
s = s[:m.start()] + new_card + s[m.end():]

s = s.replace("function activeFilterCount(){return Number(state.kind!=='all')+Number(state.tech!=='all')+Number(state.status!=='all')+Number(state.vis!=='all')}",
              "function activeFilterCount(){return Number(state.role!=='all')+Number(state.kind!=='all')+Number(state.tech!=='all')+Number(state.status!=='all')+Number(state.vis!=='all')}")

# 11) Render product/support sections.
render_re = re.compile(r"function render\(\)\{.*?\}\nfunction choiceGroup", re.S)
m = render_re.search(s)
if not m:
    raise SystemExit('render block not found')
new_render = r'''function render(){stats();const rs=filtered(),pinned=rs.filter(r=>getMeta(r.name).pinned),rest=rs.filter(r=>!getMeta(r.name).pinned);const products=rest.filter(r=>(state.scans[r.name]?.role||inferRole(r.name,KIND_OVERRIDE[r.name]||'other',r.description||''))==='product'),support=rest.filter(r=>(state.scans[r.name]?.role||inferRole(r.name,KIND_OVERRIDE[r.name]||'other',r.description||''))==='support');const wrap=$('#pinnedWrap');wrap.hidden=!pinned.length;$('#pinnedCount').textContent=pinned.length?`${pinned.length}件`:'';pinnedCards.innerHTML=pinned.map(cardHTML).join('');$('#mainListTitle').textContent='プロダクト';$('#resultCount').textContent=`${products.length}件`;cards.innerHTML=products.map(cardHTML).join('');$('#productHead').hidden=!products.length;const sw=$('#supportWrap');sw.hidden=!support.length;$('#supportCount').textContent=`${support.length}件`;supportCards.innerHTML=support.map(cardHTML).join('');if(!rs.length&&state.repos.length){$('#productHead').hidden=false;cards.innerHTML='<div class="empty">条件に合うリポジトリはありません。</div>'}bindCardEvents(cards);bindCardEvents(supportCards);bindCardEvents(pinnedCards);updateFilterUI()}
function choiceGroup'''
s = s[:m.start()] + new_render + s[m.end():]

# 12) Filter choices and reset.
s = s.replace("const KIND_ITEMS=[['all','すべて'],['game','ゲーム'],['tool','ツール'],['widget','ウィジェット'],['platform','基盤'],['qa','配布/QA'],['other','その他']];",
              "const ROLE_ITEMS=[['all','すべて'],['product','プロダクト'],['support','開発基盤/QA']];\nconst KIND_ITEMS=[['all','すべて'],['game','ゲーム'],['tool','ツール'],['widget','ウィジェット'],['platform','基盤'],['qa','配布/QA'],['other','その他']];")
s = s.replace("const TECH_ITEMS=[['all','すべて'],['godot','Godot'],['web','Web/PWA'],['other','その他']]",
              "const TECH_ITEMS=[['all','すべて'],['godot','Godot'],['web','Web/PWA'],['scriptable','Scriptable'],['other','その他']]")
s = s.replace("choiceGroup($('#kindChoices'),KIND_ITEMS,'kind');",
              "choiceGroup($('#roleChoices'),ROLE_ITEMS,'role');\nchoiceGroup($('#kindChoices'),KIND_ITEMS,'kind');", 1)
s = s.replace("$('#resetFilters').onclick=()=>{state.kind=state.tech=state.status=state.vis='all';choiceGroup($('#kindChoices'),KIND_ITEMS,'kind');",
              "$('#resetFilters').onclick=()=>{state.role=state.kind=state.tech=state.status=state.vis='all';choiceGroup($('#roleChoices'),ROLE_ITEMS,'role');choiceGroup($('#kindChoices'),KIND_ITEMS,'kind');")

# 13) Detail: expose all three axes including role.
s = s.replace("const m=getMeta(name),sc=state.scans[name]||{tech:'unknown',kind:KIND_OVERRIDE[name]||'other',autoDesc:repo.description||'',primary:[]};",
              "const m=getMeta(name),sc=state.scans[name]||{tech:'unknown',kind:KIND_OVERRIDE[name]||'other',role:inferRole(name,KIND_OVERRIDE[name]||'other',repo.description||''),autoDesc:repo.description||'',primary:[]};")
s = s.replace("const tech=techLabels[sc.tech]||'確認中',kind=kindLabels[sc.kind]||'その他';",
              "const tech=techLabels[sc.tech]||'確認中',kind=kindLabels[sc.kind]||'その他',role=roleLabels[sc.role]||'プロダクト';")
s = s.replace("<div class=\"panel detailhero\"><div class=\"eyebrow\">${escapeHtml(kind)} · ${escapeHtml(tech)}</div>",
              "<div class=\"panel detailhero\"><div class=\"eyebrow\">${escapeHtml(role)} · ${escapeHtml(kind)} · ${escapeHtml(tech)}</div>")
s = s.replace("<div class=\"detailfacts\"><div class=\"fact\"><span>技術</span><b>${escapeHtml(tech)}</b></div><div class=\"fact\"><span>種類</span><b>${escapeHtml(kind)}</b></div><div class=\"fact\"><span>ブランチ</span>",
              "<div class=\"detailfacts\"><div class=\"fact\"><span>役割</span><b>${escapeHtml(role)}</b></div><div class=\"fact\"><span>種類</span><b>${escapeHtml(kind)}</b></div><div class=\"fact\"><span>技術</span><b>${escapeHtml(tech)}</b></div><div class=\"fact\"><span>ブランチ</span>")
s = s.replace("進捗・メモ・ピンはこの端末に自動保存。種類・技術・構成・更新日はGitHubから自動取得します。",
              "進捗・メモ・ピンはこの端末に自動保存。役割・種類・技術・構成・更新日はGitHubから自動取得します。")

# 14) Scriptable summary in detail.
s = s.replace("if(tech==='web')return[['HTML',countExt('.html')],['JS/TS',countExt('.js')+countExt('.ts')+countExt('.tsx')],['CSS',countExt('.css')],['フォルダ',folders.size]];return",
              "if(tech==='web')return[['HTML',countExt('.html')],['JS/TS',countExt('.js')+countExt('.ts')+countExt('.tsx')],['CSS',countExt('.css')],['フォルダ',folders.size]];if(tech==='scriptable')return[['JS/TS',countExt('.js')+countExt('.ts')],['JSON',countExt('.json')],['ファイル',paths.length],['フォルダ',folders.size]];return")

# Basic acceptance checks.
checks = [
    'id="roleChoices"', 'id="supportCards"', "scriptable:'Scriptable'", 'function inferRole(',
    'function techFromPaths(', 'function pickPrimaryFromPaths(', "role:'all'", "ROLE_ITEMS",
    "<span class=\"chip ${sc.kind}\">", '開発基盤 / QA'
]
missing = [x for x in checks if x not in s]
if missing:
    raise SystemExit('missing after patch: ' + repr(missing))

p.write_text(s)
print('patched index.html')
