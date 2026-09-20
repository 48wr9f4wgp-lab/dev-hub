// 俺専用ダッシュボード v1.5-github
// Remote main for Scriptable loader.
// IMPORTANT: Script.complete() は loader 側で呼ぶ。

const VERSION = "1.5-github";

const CFG = {
  fallbackCity:"伊勢崎", fallbackLat:36.31, fallbackLon:139.20,
  maxEvents:3, maxTasks:3,
  universityLookAheadDays:180, universityMaxItems:3,
  lifestyleLookAheadDays:45,
  anniversaryMonth:9, anniversaryDay:28,
  refreshMinutes:15
};

const UNIVERSITY_KEYWORDS = [
  "放送大学","シン・ビートルズ de 英文法","社会調査の基礎","社会学概論",
  "イノベーション・マネジメント","雇用社会と法","マーケティング",
  "現代の内部監査","情報社会のユニバーサルデザイン",
  "情報化社会におけるメディア教育","宇宙の誕生と進化"
];
const DEADLINE_KEYWORDS = ["締切","〆切","期限","払込期限","納入期限","提出期限","申込期限","申請期限","回答期限","最終日","必着"];
const START_KEYWORDS = ["開始","提出開始","受付開始","申込開始","申請開始","試験開始","公開開始"];
const END_KEYWORDS = ["終了","提出終了","受付終了","申込終了","申請終了"];
const PERIOD_KEYWORDS = ["期間","提出期間","受付期間","試験期間","申込期間"];
const SCHEDULE_KEYWORDS = ["試験日","単位認定試験","面接授業","試験"];

const C = {
  text:new Color("#0F172A"), sub:new Color("#64748B"),
  blue:new Color("#2563EB"), green:new Color("#16A34A"),
  orange:new Color("#EA580C"), red:new Color("#DC2626"),
  purple:new Color("#7C3AED"), gray:new Color("#94A3B8"),
  card:new Color("#FFFFFF",0.82), weakCard:new Color("#FFFFFF",0.64)
};

const LIFESTYLE = {
  fishing:{title:"釣り",icon:"fish.fill",color:C.blue,keywords:["釣り","釣行","アジング","サビキ","泳がせ","遠投カゴ","ぶっ込み","ショアジギ","ジギング","伊豆釣行","堤防釣り","磯釣り"]},
  garden:{title:"菜園",icon:"leaf.fill",color:C.green,keywords:["菜園","家庭菜園","水やり","追肥","植え替え","播種","種まき","収穫","摘心","受粉","ズッキーニ","ナス","バジル","ほうれん草","ラディッシュ","レモン","ブルーベリー","パイナップル","タラの芽"]},
  workout:{title:"筋トレ",icon:"dumbbell.fill",color:C.purple,keywords:["筋トレ","トレーニング","胸トレ","背中トレ","脚トレ","肩トレ","腕トレ","ジム","ベンチプレス","スクワット","デッドリフト"]}
};

function icon(stack,name,color,size=12){const sf=SFSymbol.named(name);sf.applyFont(Font.systemFont(size));const i=stack.addImage(sf.image);i.imageSize=new Size(size,size);i.tintColor=color;return i;}
function normalize(v){return v?String(v).replace(/\s+/g," ").trim():"";}
function shorten(v,n){v=normalize(v);return v.length<=n?v:v.slice(0,n-1)+"…";}
function any(text,keys){text=normalize(text);return keys.some(k=>text.includes(k));}
function fmtTime(d,allDay=false){if(allDay)return "終日";const f=new DateFormatter();f.dateFormat="HH:mm";return f.string(d);}
function fmtDate(d){const f=new DateFormatter();f.locale="ja_JP";f.dateFormat="M/d";return f.string(d);}
function todayText(){const f=new DateFormatter();f.locale="ja_JP";f.dateFormat="M月d日 EEE";return f.string(new Date());}
function dayStart(d){return new Date(d.getFullYear(),d.getMonth(),d.getDate());}
function addDays(d,n){const x=new Date(d);x.setDate(x.getDate()+n);return x;}
function daysBetween(a,b){return Math.round((dayStart(b)-dayStart(a))/86400000);}
function relativeDay(d){const n=daysBetween(new Date(),d);if(n<0)return Math.abs(n)+"日超過";if(n===0)return "今日";if(n===1)return "明日";return "あと"+n+"日";}
function realEventEnd(e){const d=new Date(e.endDate);if(e.isAllDay)d.setMilliseconds(d.getMilliseconds()-1);return d;}
function calName(x){return x.calendar&&x.calendar.title?normalize(x.calendar.title):"";}
function mkCard(p){const c=p.addStack();c.layoutVertically();c.backgroundColor=C.card;c.cornerRadius=14;c.setPadding(9,10,9,10);return c;}
function section(p,symbol,title,color){const r=p.addStack();r.centerAlignContent();icon(r,symbol,color,11);r.addSpacer(5);const t=r.addText(title);t.font=Font.boldSystemFont(11);t.textColor=C.text;return r;}

async function getPosition(){
  try{
    Location.setAccuracyToThreeKilometers();
    const loc=await Location.current();
    let city=CFG.fallbackCity;
    try{const p=await Location.reverseGeocode(loc.latitude,loc.longitude,"ja_JP");if(p&&p[0])city=p[0].locality||p[0].subLocality||city;}catch(_){}
    return {ok:true,city,lat:loc.latitude,lon:loc.longitude};
  }catch(_){return {ok:false,city:CFG.fallbackCity,lat:CFG.fallbackLat,lon:CFG.fallbackLon};}
}

async function getWeather(pos){
  try{
    const u="https://api.open-meteo.com/v1/forecast?latitude="+pos.lat+"&longitude="+pos.lon+"&current=temperature_2m,weather_code&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max&timezone=auto&forecast_days=1";
    const r=new Request(u);r.timeoutInterval=10;const j=await r.loadJSON();
    return {ok:true,temp:Math.round(j.current.temperature_2m),code:j.current.weather_code,max:Math.round(j.daily.temperature_2m_max[0]),min:Math.round(j.daily.temperature_2m_min[0]),rain:Math.round(j.daily.precipitation_probability_max[0])};
  }catch(_){return {ok:false,temp:null,code:-1,max:null,min:null,rain:null};}
}

function weatherInfo(code){
  if(code===0)return ["快晴","sun.max.fill"];
  if([1,2].includes(code))return ["晴れ","cloud.sun.fill"];
  if(code===3)return ["くもり","cloud.fill"];
  if([45,48].includes(code))return ["霧","cloud.fog.fill"];
  if([51,53,55,56,57].includes(code))return ["霧雨","cloud.drizzle.fill"];
  if([61,63,65,66,67,80,81,82].includes(code))return ["雨","cloud.rain.fill"];
  if([71,73,75,77,85,86].includes(code))return ["雪","cloud.snow.fill"];
  if([95,96,99].includes(code))return ["雷雨","cloud.bolt.rain.fill"];
  return ["不明","questionmark.circle.fill"];
}

async function getEvents(){
  try{
    const now=new Date();const list=await CalendarEvent.today();
    const items=list.filter(e=>e.isAllDay||e.endDate>now).sort((a,b)=>{if(a.isAllDay&&!b.isAllDay)return -1;if(!a.isAllDay&&b.isAllDay)return 1;return a.startDate-b.startDate;}).slice(0,CFG.maxEvents);
    return {ok:true,items};
  }catch(_){return {ok:false,items:[]};}
}

async function getTasks(){
  try{return {ok:true,items:(await Reminder.incompleteDueToday()).slice(0,CFG.maxTasks)};}
  catch(_){return {ok:false,items:[]};}
}

function isUniversity(text,calendarTitle){return any(text,UNIVERSITY_KEYWORDS)||any(calendarTitle,UNIVERSITY_KEYWORDS);}

async function getUniversityItems(){
  const out={reminderOK:false,calendarOK:false,items:[]};
  try{
    const rs=await Reminder.allIncomplete();out.reminderOK=true;
    for(const r of rs){
      if(!r.dueDate)continue;
      const title=normalize(r.title), notes=normalize(r.notes), combined=title+" "+notes;
      if(!isUniversity(combined,calName(r)))continue;
      let kind=null,color=C.blue;
      if(any(combined,START_KEYWORDS)){kind="開始";color=C.purple;}
      else if(any(combined,END_KEYWORDS)){kind="終了";color=C.orange;}
      else if(any(combined,DEADLINE_KEYWORDS)){kind="期限";color=C.red;}
      else if(any(combined,SCHEDULE_KEYWORDS)){kind="予定";color=C.blue;}
      if(kind)out.items.push({title,date:r.dueDate,kind,color});
    }
  }catch(_){}
  try{
    const now=new Date(), endSearch=addDays(now,CFG.universityLookAheadDays);
    const es=await CalendarEvent.between(now,endSearch);out.calendarOK=true;
    for(const e of es){
      const title=normalize(e.title), notes=normalize(e.notes), combined=title+" "+notes;
      if(!isUniversity(combined,calName(e)))continue;
      const start=new Date(e.startDate), end=realEventEnd(e), sd=dayStart(start), ed=dayStart(end);
      const periodLike=ed>sd||any(combined,PERIOD_KEYWORDS);
      if(periodLike){
        out.items.push({title,date:start,kind:"開始",color:C.purple});
        if(ed.getTime()!==sd.getTime())out.items.push({title,date:end,kind:"終了",color:C.orange});
        continue;
      }
      let kind=null,color=C.blue;
      if(any(combined,START_KEYWORDS)){kind="開始";color=C.purple;}
      else if(any(combined,END_KEYWORDS)){kind="終了";color=C.orange;}
      else if(any(combined,DEADLINE_KEYWORDS)){kind="期限";color=C.red;}
      else if(any(combined,SCHEDULE_KEYWORDS)){kind="予定";color=C.blue;}
      if(kind)out.items.push({title,date:start,kind,color});
    }
  }catch(_){}
  const seen=new Set();
  out.items=out.items.sort((a,b)=>a.date-b.date).filter(x=>{const k=x.title+"|"+x.kind+"|"+dayStart(x.date).getTime();if(seen.has(k))return false;seen.add(k);return true;}).slice(0,CFG.universityMaxItems);
  return out;
}

async function getLifestyleSources(){
  const r={calendarOK:false,reminderOK:false,calendarItems:[],reminderItems:[]};
  const now=new Date(),end=addDays(now,CFG.lifestyleLookAheadDays);
  try{r.calendarItems=await CalendarEvent.between(now,end);r.calendarOK=true;}catch(_){}
  try{r.reminderItems=await Reminder.allIncomplete();r.reminderOK=true;}catch(_){}
  return r;
}

function nextLifestyle(src,cat){
  const a=[],now=new Date(),end=addDays(now,CFG.lifestyleLookAheadDays);
  if(src.calendarOK)for(const e of src.calendarItems){const title=normalize(e.title),combined=title+" "+normalize(e.notes);if(any(combined,cat.keywords)||any(calName(e),cat.keywords))a.push({title,date:new Date(e.startDate)});}
  if(src.reminderOK)for(const r of src.reminderItems){if(!r.dueDate)continue;const d=new Date(r.dueDate);if(d<dayStart(now)||d>end)continue;const title=normalize(r.title),combined=title+" "+normalize(r.notes);if(any(combined,cat.keywords)||any(calName(r),cat.keywords))a.push({title,date:d});}
  a.sort((x,y)=>x.date-y.date);return a[0]||null;
}

function anniversary(){
  const n=new Date();let t=new Date(n.getFullYear(),CFG.anniversaryMonth-1,CFG.anniversaryDay);
  if(dayStart(t)<dayStart(n))t=new Date(n.getFullYear()+1,CFG.anniversaryMonth-1,CFG.anniversaryDay);
  return {date:t,days:daysBetween(n,t)};
}

const fetchedAt=new Date();
const position=await getPosition();
const [W,eventsData,tasksData,universityData,lifestyleSources]=await Promise.all([getWeather(position),getEvents(),getTasks(),getUniversityItems(),getLifestyleSources()]);
const life={sourcesOK:lifestyleSources.calendarOK||lifestyleSources.reminderOK,fishing:nextLifestyle(lifestyleSources,LIFESTYLE.fishing),garden:nextLifestyle(lifestyleSources,LIFESTYLE.garden),workout:nextLifestyle(lifestyleSources,LIFESTYLE.workout)};
const ann=anniversary();
const [weatherName,weatherIcon]=weatherInfo(W.code);

const w=new ListWidget();
w.setPadding(12,14,9,14);
const bg=new LinearGradient();bg.colors=[new Color("#D8ECFF"),new Color("#EEF7FF"),new Color("#FFFFFF")];bg.locations=[0,0.55,1];w.backgroundGradient=bg;

// HEADER
const header=w.addStack();header.centerAlignContent();
const left=header.addStack();left.layoutVertically();
let t=left.addText(position.city);t.font=Font.boldSystemFont(16);t.textColor=C.blue;
t=left.addText(todayText());t.font=Font.systemFont(9);t.textColor=C.sub;
header.addSpacer();
if(W.ok){
  t=header.addText(W.temp+"°");t.font=Font.boldSystemFont(26);t.textColor=C.text;header.addSpacer(6);
  t=header.addText(weatherName);t.font=Font.semiboldSystemFont(10);t.textColor=C.sub;header.addSpacer(6);
  icon(header,weatherIcon,C.blue,22);
}else{t=header.addText("天気取得失敗");t.font=Font.semiboldSystemFont(10);t.textColor=C.red;}
w.addSpacer(7);

// ROW1
const row1=w.addStack();row1.spacing=8;
const eventCard=mkCard(row1);eventCard.size=new Size(164,96);section(eventCard,"calendar","今日の予定",C.blue);eventCard.addSpacer(5);
if(!eventsData.ok){t=eventCard.addText("取得失敗");t.font=Font.systemFont(9);t.textColor=C.red;}
else if(!eventsData.items.length){t=eventCard.addText("この後の予定なし");t.font=Font.systemFont(9);t.textColor=C.sub;}
else eventsData.items.forEach((e,i)=>{const l=eventCard.addStack();l.centerAlignContent();let x=l.addText(fmtTime(e.startDate,e.isAllDay));x.font=Font.semiboldSystemFont(9);x.textColor=C.blue;l.addSpacer(5);x=l.addText(shorten(e.title,18));x.font=Font.systemFont(9);x.textColor=C.text;x.lineLimit=1;if(i<eventsData.items.length-1)eventCard.addSpacer(3);});

const taskCard=mkCard(row1);taskCard.size=new Size(136,96);section(taskCard,"checkmark.circle.fill","やること",C.green);taskCard.addSpacer(5);
if(!tasksData.ok){t=taskCard.addText("取得失敗");t.font=Font.systemFont(9);t.textColor=C.red;}
else if(!tasksData.items.length){t=taskCard.addText("今日のタスクなし");t.font=Font.systemFont(9);t.textColor=C.sub;}
else tasksData.items.forEach((r,i)=>{const l=taskCard.addStack();l.centerAlignContent();icon(l,"circle",r.isOverdue?C.red:C.green,8);l.addSpacer(5);const x=l.addText(shorten(r.title,16));x.font=Font.systemFont(9);x.textColor=C.text;x.lineLimit=1;if(i<tasksData.items.length-1)taskCard.addSpacer(3);});
w.addSpacer(6);

// ROW2
const row2=w.addStack();row2.spacing=8;
const family=mkCard(row2);family.size=new Size(105,100);section(family,"person.2.fill","家族",C.orange);family.addSpacer(4);
t=family.addText("結婚記念日");t.font=Font.systemFont(9);t.textColor=C.sub;
t=family.addText(ann.days===0?"今日 ♥":"あと"+ann.days+"日");t.font=Font.boldSystemFont(19);t.textColor=C.text;
t=family.addText(fmtDate(ann.date));t.font=Font.systemFont(8);t.textColor=C.sub;

const uni=mkCard(row2);uni.size=new Size(195,100);const uh=section(uni,"graduationcap.fill","放送大学",C.purple);uh.addSpacer();
t=uh.addText((universityData.reminderOK||universityData.calendarOK)?"自動":"取得失敗");t.font=Font.systemFont(8);t.textColor=(universityData.reminderOK||universityData.calendarOK)?C.green:C.red;uni.addSpacer(4);
if(!universityData.items.length){t=uni.addText("検出イベントなし");t.font=Font.systemFont(9);t.textColor=C.sub;}
else universityData.items.forEach((it,i)=>{const l=uni.addStack();l.centerAlignContent();let x=l.addText(it.kind);x.font=Font.boldSystemFont(8);x.textColor=it.color;l.addSpacer(4);x=l.addText(relativeDay(it.date));x.font=Font.boldSystemFont(9);x.textColor=it.color;l.addSpacer(4);x=l.addText(fmtDate(it.date));x.font=Font.systemFont(8);x.textColor=C.sub;l.addSpacer(4);x=l.addText(shorten(it.title,11));x.font=Font.systemFont(8);x.textColor=C.text;x.lineLimit=1;if(i<universityData.items.length-1)uni.addSpacer(3);});
w.addSpacer(6);

// ROW3 lifestyle
const lifeCard=mkCard(w);lifeCard.setPadding(7,9,7,9);const lh=section(lifeCard,"leaf.fill","暮らし・趣味",C.green);lh.addSpacer();
t=lh.addText(life.sourcesOK?"自動":"取得失敗");t.font=Font.systemFont(8);t.textColor=life.sourcesOK?C.green:C.red;lifeCard.addSpacer(5);
const lr=lifeCard.addStack();lr.spacing=7;
function lifeCol(cat,item,extra){
  const c=lr.addStack();c.layoutVertically();c.size=new Size(94,48);
  const h=c.addStack();h.centerAlignContent();icon(h,cat.icon,cat.color,10);h.addSpacer(4);let x=h.addText(cat.title);x.font=Font.boldSystemFont(9);x.textColor=C.text;c.addSpacer(3);
  if(!life.sourcesOK){x=c.addText("取得失敗");x.font=Font.systemFont(8);x.textColor=C.red;}
  else if(!item){x=c.addText("予定なし");x.font=Font.systemFont(8);x.textColor=C.sub;}
  else{x=c.addText(relativeDay(item.date)+" "+fmtDate(item.date));x.font=Font.semiboldSystemFont(8);x.textColor=cat.color;x=c.addText(shorten(item.title,12));x.font=Font.systemFont(8);x.textColor=C.text;x.lineLimit=1;}
  if(extra){x=c.addText(extra);x.font=Font.systemFont(7);x.textColor=C.gray;}
}
lifeCol(LIFESTYLE.fishing,life.fishing,"潮汐 未接続");lifeCol(LIFESTYLE.garden,life.garden);lifeCol(LIFESTYLE.workout,life.workout);
w.addSpacer(6);

// ROW4 full width placeholders
const row4=w.addStack();row4.spacing=8;
function wideCard(iconName,title,color){
  const c=row4.addStack();c.layoutVertically();c.backgroundColor=C.weakCard;c.cornerRadius=12;c.setPadding(7,9,7,9);c.size=new Size(150,47);
  const h=c.addStack();h.centerAlignContent();icon(h,iconName,color,10);h.addSpacer(5);let x=h.addText(title);x.font=Font.boldSystemFont(9);x.textColor=C.text;h.addSpacer();x=h.addText("未接続");x.font=Font.systemFont(8);x.textColor=C.gray;c.addSpacer(3);x=c.addText("データソース未設定");x.font=Font.systemFont(7);x.textColor=C.gray;
}
wideCard("chart.line.uptrend.xyaxis","資産",C.green);wideCard("newspaper.fill","ニュース",C.blue);

w.addSpacer();
const footer=w.addStack();footer.centerAlignContent();
const ok=W.ok&&eventsData.ok&&tasksData.ok&&(universityData.reminderOK||universityData.calendarOK)&&life.sourcesOK;
t=footer.addText("●");t.font=Font.systemFont(7);t.textColor=ok?C.green:C.orange;footer.addSpacer(4);
t=footer.addText("最終取得");t.font=Font.systemFont(8);t.textColor=C.sub;footer.addSpacer(4);
const rel=footer.addDate(fetchedAt);rel.applyRelativeStyle();rel.font=Font.systemFont(8);rel.textColor=C.sub;
footer.addSpacer();t=footer.addText("v"+VERSION);t.font=Font.systemFont(7);t.textColor=C.gray;footer.addSpacer(6);
t=footer.addText(position.ok?"現在地":"位置情報:予備地点");t.font=Font.systemFont(8);t.textColor=position.ok?C.sub:C.orange;

w.refreshAfterDate=new Date(Date.now()+CFG.refreshMinutes*60*1000);
if(config.runsInWidget) Script.setWidget(w); else await w.presentLarge();
