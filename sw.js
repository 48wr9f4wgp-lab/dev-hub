const CACHE='devhub-shell-v4';
const API_CACHE='devhub-api-v1';
const OWNER='48wr9f4wgp-lab';
const SHELL=['./','./index.html','./manifest.webmanifest','./icon.svg'];

const PUBLIC_FALLBACK=[
  'farm-loop','tide-dash','motorsport-hub','48wr9f4wgp-lab-tide-dash','tackle-fit','Logistics-Boss','machi-loop','dev-hub','-grid-bloom','-velvet-pwa','combat-hub','fish-target','club-pulse','-scrap-planet-qa'
].map(name=>({
  name,
  owner:{login:OWNER},
  private:false,
  archived:false,
  default_branch:'main',
  html_url:`https://github.com/${OWNER}/${name}`,
  homepage:'',
  description:null,
  pushed_at:null,
  updated_at:null
}));

const ROOT_HINTS={
  'farm-loop':['project.godot','scenes/','scripts/','DEV_STATUS.json'],
  '-grid-bloom':['project.godot','scenes/','scripts/','DEV_STATUS.json'],
  'machi-loop':['project.godot','scenes/','scripts/','DEV_STATUS.json'],
  'Logistics-Boss':['project.godot','scenes/','scripts/','assets/','DEV_STATUS.json'],
  'fish-target':['index.html','scripts/','src/','DEV_STATUS.json'],
  'tackle-fit':['index.html','src/','manifest.webmanifest','DEV_STATUS.json'],
  'tide-dash':['index.html','scripts/','manifest.webmanifest','DEV_STATUS.json'],
  'dev-hub':['index.html','manifest.webmanifest','sw.js','DEV_STATUS.json'],
  '-velvet-pwa':['index.html','src/','manifest.webmanifest','DEV_STATUS.json'],
  'motorsport-hub':['widget.js','data/','DEV_STATUS.json'],
  'combat-hub':['widget.js','data/','DEV_STATUS.json'],
  'club-pulse':['widget.js','data/','DEV_STATUS.json'],
  '-scrap-planet-qa':['payload/','index.html','DEV_STATUS.json'],
  '48wr9f4wgp-lab-tide-dash':['payload/','index.html','DEV_STATUS.json']
};

function jsonResponse(data,status=200){
  return new Response(JSON.stringify(data),{status,headers:{'Content-Type':'application/json; charset=utf-8','Cache-Control':'no-store'}});
}

function syntheticRoot(repo,branch='main'){
  const hints=ROOT_HINTS[repo];
  if(!hints)return null;
  return hints.map(name=>{
    const dir=name.endsWith('/');
    const clean=dir?name.slice(0,-1):name;
    return {
      name:clean,
      path:clean,
      type:dir?'dir':'file',
      download_url:dir?null:`https://raw.githubusercontent.com/${OWNER}/${repo}/${branch}/${clean}`
    };
  });
}

async function networkFirstApi(request,fallback){
  const cache=await caches.open(API_CACHE);
  try{
    const res=await fetch(request,{cache:'no-store'});
    if(!res.ok)throw new Error(`GitHub API ${res.status}`);
    await cache.put(request,res.clone());
    return res;
  }catch{
    const cached=await cache.match(request);
    if(cached)return cached;
    return jsonResponse(fallback());
  }
}

self.addEventListener('install',event=>{
  event.waitUntil(caches.open(CACHE).then(c=>c.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener('activate',event=>{
  event.waitUntil((async()=>{
    const keys=await caches.keys();
    await Promise.all(keys.filter(k=>![CACHE,API_CACHE].includes(k)).map(k=>caches.delete(k)));
    await self.clients.claim();

    // 新しいService Workerが有効になった直後、旧Workerで表示された「確認中」状態を
    // 1回だけ自動再読込して最新の取得ロジックへ切り替える。
    const clients=await self.clients.matchAll({type:'window',includeUncontrolled:true});
    await Promise.all(clients.map(client=>{
      try{
        const url=new URL(client.url);
        if(url.origin===self.location.origin&&url.pathname.startsWith(new URL(self.registration.scope).pathname)){
          return client.navigate(client.url);
        }
      }catch{}
      return Promise.resolve();
    }));
  })());
});

self.addEventListener('fetch',event=>{
  const url=new URL(event.request.url);

  // GitHub APIのレート制限で一覧解析が丸ごと止まらないようにする。
  if(event.request.method==='GET'&&url.hostname==='api.github.com'){
    if(url.pathname===`/users/${OWNER}/repos`){
      event.respondWith(networkFirstApi(event.request,()=>PUBLIC_FALLBACK));
      return;
    }

    const rootMatch=url.pathname.match(new RegExp(`^/repos/${OWNER}/([^/]+)/contents/?$`));
    if(rootMatch){
      const repo=decodeURIComponent(rootMatch[1]);
      const branch=url.searchParams.get('ref')||'main';
      const root=syntheticRoot(repo,branch);
      if(root){
        event.respondWith(Promise.resolve(jsonResponse(root)));
        return;
      }
    }
  }

  if(url.origin!==location.origin)return;

  // DEV HUBはGitHubの最新状態を見るのが主目的なので、画面遷移は常にネット優先・HTTPキャッシュ回避。
  if(event.request.mode==='navigate'){
    event.respondWith(
      fetch(event.request,{cache:'no-store'})
        .then(res=>{
          const copy=res.clone();
          caches.open(CACHE).then(c=>c.put('./index.html',copy));
          return res;
        })
        .catch(()=>caches.match('./index.html'))
    );
    return;
  }

  // manifest/iconも更新を優先し、失敗時だけキャッシュを使用。
  event.respondWith(
    fetch(event.request,{cache:'no-store'})
      .then(res=>{
        const copy=res.clone();
        caches.open(CACHE).then(c=>c.put(event.request,copy));
        return res;
      })
      .catch(()=>caches.match(event.request))
  );
});
