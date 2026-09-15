from pathlib import Path

p = Path('index.html')
s = p.read_text()

old = "const LS_META='devhub.meta.v2', LS_TOKEN='devhub.token.v1', LS_CACHE='devhub.cache.v7';"
new = "const LS_META='devhub.meta.v2', LS_TOKEN='devhub.token.v1', LS_CACHE='devhub.cache.v7', LS_REPOS='devhub.repos.v1';"
if old not in s:
    raise SystemExit('storage constants anchor not found')
s = s.replace(old, new, 1)

old = "let meta=loadJSON(LS_META,{}),cache=loadJSON(LS_CACHE,{});"
new = "let meta=loadJSON(LS_META,{}),cache=loadJSON(LS_CACHE,{}),repoCache=loadJSON(LS_REPOS,[]);"
if old not in s:
    raise SystemExit('cache anchor not found')
s = s.replace(old, new, 1)

old = "async function api(url){const r=await fetch(url,{headers:headers()});if(!r.ok){let m=`GitHub API ${r.status}`;try{const j=await r.json();m=j.message||m}catch{}throw new Error(m)}return r.json()}"
new = "async function api(url,timeoutMs=8000){const ctl=new AbortController(),timer=setTimeout(()=>ctl.abort(),timeoutMs);try{const r=await fetch(url,{headers:headers(),signal:ctl.signal,cache:'no-store'});if(!r.ok){let m=`GitHub API ${r.status}`;try{const j=await r.json();m=j.message||m}catch{}throw new Error(m)}return await r.json()}catch(e){if(e?.name==='AbortError')throw new Error('GitHub応答タイムアウト');throw e}finally{clearTimeout(timer)}}"
if old not in s:
    raise SystemExit('api anchor not found')
s = s.replace(old, new, 1)

old = "async function loadRepos(){msg.className='loading';msg.innerHTML='<span class=\"spinner\"></span><br>GitHubから読み込み中…';cards.innerHTML='';try{const token=localStorage.getItem(LS_TOKEN);let repos;if(token){const all=await api('https://api.github.com/user/repos?per_page=100&sort=pushed&affiliation=owner');repos=all.filter(r=>r.owner?.login===OWNER)}else{repos=await api(`https://api.github.com/users/${OWNER}/repos?per_page=100&sort=pushed&type=owner`)}state.repos=repos.filter(r=>!r.archived);msg.style.display='none';render();queueScans()}catch(e){msg.style.display='block';msg.className='error';msg.textContent='読み込み失敗: '+e.message}}"
new = "async function loadRepos(){msg.className='loading';msg.innerHTML='<span class=\"spinner\"></span><br>GitHubから読み込み中…';cards.innerHTML='';const cached=Array.isArray(repoCache)?repoCache.filter(r=>r&&!r.archived):[];if(cached.length){state.repos=cached;for(const r of cached){const c=cache[rootKey(r)];if(c?.data)state.scans[r.name]=c.data}msg.style.display='none';render()}try{const token=localStorage.getItem(LS_TOKEN);let repos;if(token){const all=await api('https://api.github.com/user/repos?per_page=100&sort=pushed&affiliation=owner',8000);repos=all.filter(r=>r.owner?.login===OWNER)}else{repos=await api(`https://api.github.com/users/${OWNER}/repos?per_page=100&sort=pushed&type=owner`,8000)}state.repos=repos.filter(r=>!r.archived);repoCache=state.repos;saveJSON(LS_REPOS,repoCache);msg.style.display='none';render();queueScans()}catch(e){if(cached.length){msg.style.display='none';return}msg.style.display='block';msg.className='error';msg.textContent='読み込み失敗: '+e.message}}"
if old not in s:
    raise SystemExit('loadRepos anchor not found')
s = s.replace(old, new, 1)

p.write_text(s)
print('loading resilience patched')
