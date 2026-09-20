// COURTSIDE v0.2
// Scriptable NBA favorite-team widget.
// Widget parameter: NBA team abbreviation, e.g. LAL, GSW, BOS.

const DEFAULT_TEAM = "LAL";
const TEAM = String(args.widgetParameter || DEFAULT_TEAM).trim().toUpperCase();

const TEAM_IDS = {
  ATL:"1", BOS:"2", NOP:"3", CHI:"4", CLE:"5", DAL:"6", DEN:"7", DET:"8",
  GSW:"9", HOU:"10", IND:"11", LAC:"12", LAL:"13", MIA:"14", MIL:"15",
  MIN:"16", BKN:"17", NYK:"18", ORL:"19", PHI:"20", PHX:"21", POR:"22",
  SAC:"23", SAS:"24", OKC:"25", UTA:"26", WAS:"27", TOR:"28", MEM:"29",
  CHA:"30"
};

if (!TEAM_IDS[TEAM]) {
  const w = errorWidget("COURTSIDE", `Unknown team: ${TEAM}`);
  Script.setWidget(w);
  if (!config.runsInWidget) await w.presentMedium();
  Script.complete();
  return;
}

const TEAM_ID = TEAM_IDS[TEAM];
const SEASON = nbaSeasonYear(new Date());
const BASE = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba";

const model = await loadModel();
const widget = await buildWidget(model);

Script.setWidget(widget);

if (!config.runsInWidget) {
  const family = config.widgetFamily || "medium";
  if (family === "small") await widget.presentSmall();
  else if (family === "large") await widget.presentLarge();
  else if (family === "accessoryRectangular") await widget.presentAccessoryRectangular();
  else if (family === "accessoryInline") await widget.presentAccessoryInline();
  else if (family === "accessoryCircular") await widget.presentAccessoryCircular();
  else await widget.presentMedium();
}

Script.complete();

function nbaSeasonYear(d) {
  const y = d.getFullYear();
  return d.getMonth() >= 6 ? y + 1 : y;
}

async function loadModel() {
  const cache = readCache();
  try {
    const [teamJson, pre, reg, post] = await Promise.all([
      getJSON(`${BASE}/teams/${TEAM_ID}`),
      getJSON(`${BASE}/teams/${TEAM_ID}/schedule?season=${SEASON}&seasontype=1`),
      getJSON(`${BASE}/teams/${TEAM_ID}/schedule?season=${SEASON}&seasontype=2`),
      getJSON(`${BASE}/teams/${TEAM_ID}/schedule?season=${SEASON}&seasontype=3`)
    ]);

    const team = teamJson?.team || {};
    const all = [...(pre?.events || []), ...(reg?.events || []), ...(post?.events || [])];
    const seen = new Set();

    const events = all
      .filter(e => {
        if (!e?.id || seen.has(e.id)) return false;
        seen.add(e.id);
        return true;
      })
      .map(normalizeEvent)
      .filter(Boolean)
      .sort((a,b) => a.date - b.date);

    const now = new Date();
    const live = events.find(e => e.state === "in") || null;
    const upcoming = events.find(e =>
      !e.completed &&
      e.state !== "in" &&
      e.date >= new Date(now.getTime() - 3 * 60 * 60 * 1000)
    ) || null;

    const completed = events.filter(e => e.completed).sort((a,b) => b.date - a.date);
    const last = completed[0] || null;

    const regularCompleted = events.filter(e => e.completed && e.seasonType === 2);
    const wins = regularCompleted.filter(e => e.result === "W").length;
    const losses = regularCompleted.filter(e => e.result === "L").length;
    const last5 = [...regularCompleted].sort((a,b) => b.date - a.date).slice(0,5).reverse();

    const out = {
      team: {
        abbr: TEAM,
        id: TEAM_ID,
        displayName: team.displayName || TEAM,
        shortName: team.shortDisplayName || team.name || TEAM,
        color: validHex(team.color) || fallbackColor(TEAM),
        logo: team.logos?.[0]?.href || logoURL(TEAM)
      },
      live,
      upcoming,
      last,
      last5,
      record: { wins, losses },
      fetchedAt: Date.now()
    };

    writeCache(out);
    return out;
  } catch (e) {
    if (cache) {
      cache.fromCache = true;
      return cache;
    }

    return {
      error: String(e),
      team: {
        abbr: TEAM,
        displayName: TEAM,
        shortName: TEAM,
        color: fallbackColor(TEAM),
        logo: logoURL(TEAM)
      }
    };
  }
}

function normalizeEvent(event) {
  try {
    const comp = event.competitions?.[0];
    if (!comp) return null;

    const competitors = comp.competitors || [];
    const mine = competitors.find(c => c.team?.abbreviation?.toUpperCase() === TEAM);
    const opp = competitors.find(c => c !== mine);
    if (!mine || !opp) return null;

    const status = comp.status || event.status || {};
    const state = status.type?.state || (status.type?.completed ? "post" : "pre");
    const completed = Boolean(status.type?.completed || state === "post");
    const teamScore = Number(mine.score || 0);
    const oppScore = Number(opp.score || 0);

    return {
      id: String(event.id || ""),
      date: new Date(comp.date || event.date),
      state,
      completed,
      period: Number(status.period || 0),
      clock: status.displayClock || "",
      statusText: status.type?.shortDetail || status.type?.detail || "",
      seasonType: Number(event.season?.type || 0),
      homeAway: mine.homeAway || "",
      opponent: {
        abbr: opp.team?.abbreviation || "OPP",
        name: opp.team?.shortDisplayName || opp.team?.name || "Opponent",
        logo: opp.team?.logo || logoURL(opp.team?.abbreviation || "")
      },
      teamScore,
      oppScore,
      result: completed
        ? (teamScore > oppScore ? "W" : teamScore < oppScore ? "L" : "T")
        : null
    };
  } catch (_) {
    return null;
  }
}

async function getJSON(url) {
  const req = new Request(url);
  req.timeoutInterval = 12;
  req.headers = { "Accept":"application/json", "User-Agent":"Mozilla/5.0" };
  return await req.loadJSON();
}

function cachePath() {
  const fm = FileManager.local();
  return fm.joinPath(fm.documentsDirectory(), `courtside_${TEAM.toLowerCase()}_cache.json`);
}

function readCache() {
  try {
    const fm = FileManager.local();
    const p = cachePath();
    if (!fm.fileExists(p)) return null;

    const x = JSON.parse(fm.readString(p));
    for (const k of ["live","upcoming","last"]) {
      if (x?.[k]?.date) x[k].date = new Date(x[k].date);
    }
    if (Array.isArray(x?.last5)) {
      x.last5.forEach(g => {
        if (g?.date) g.date = new Date(g.date);
      });
    }
    return x;
  } catch (_) {
    return null;
  }
}

function writeCache(x) {
  try {
    FileManager.local().writeString(cachePath(), JSON.stringify(x));
  } catch (_) {}
}

async function getImage(url, key) {
  if (!url) return null;
  const fm = FileManager.local();
  const p = fm.joinPath(fm.documentsDirectory(), `courtside_${key}.png`);

  try {
    if (fm.fileExists(p)) return fm.readImage(p);
    const req = new Request(url);
    req.timeoutInterval = 10;
    const img = await req.loadImage();
    fm.writeImage(p, img);
    return img;
  } catch (_) {
    return fm.fileExists(p) ? fm.readImage(p) : null;
  }
}

function phase(m) {
  if (m.live) {
    if (m.live.seasonType === 1) return "preseason";
    if (m.live.seasonType === 3) return "playoffs";
    return "regular";
  }
  if (m.upcoming?.seasonType === 1) return "preseason";
  if (m.upcoming?.seasonType === 3 || m.last?.seasonType === 3) return "playoffs";
  if (m.upcoming?.seasonType === 2 || m.last?.seasonType === 2) return "regular";
  return "offseason";
}

function phaseLabel(m) {
  const p = phase(m);
  if (p === "preseason") return "PRESEASON";
  if (p === "regular") return "REGULAR SEASON";
  if (p === "playoffs") return "PLAYOFFS";
  return "OFFSEASON";
}

function countdown(date) {
  if (!date) return "";
  const now = new Date();
  const target = new Date(date);
  const a = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const b = new Date(target.getFullYear(), target.getMonth(), target.getDate());
  const days = Math.round((b - a) / 86400000);

  if (days === 0) {
    const mins = Math.max(0, Math.round((target - now) / 60000));
    if (mins < 60) return `あと${mins}分`;
    return `あと${Math.max(1, Math.floor(mins/60))}時間`;
  }
  if (days === 1) return "明日";
  return days > 1 ? `あと${days}日` : "";
}

function liveStatus(g) {
  if (!g) return "";
  if (g.period <= 0) return g.statusText || "LIVE";
  return `Q${g.period} ${g.clock || ""}`.trim();
}

function formText(m) {
  return (m.last5 || []).map(g => g.result || "-").join(" ");
}

async function buildWidget(m) {
  if (m.error) return errorWidget("COURTSIDE", "データ取得に失敗しました");

  const family = config.widgetFamily || "medium";
  if (family === "accessoryInline") return lockInline(m);
  if (family === "accessoryCircular") return lockCircular(m);
  if (family === "accessoryRectangular") return lockRect(m);

  const w = new ListWidget();
  w.setPadding(14,14,14,14);

  const grad = new LinearGradient();
  grad.locations = [0,1];
  grad.colors = [new Color(m.team.color,0.98), new Color("070911",1)];
  w.backgroundGradient = grad;

  // iOS decides the actual refresh time.
  w.refreshAfterDate = new Date(Date.now() + (m.live ? 5 : 30) * 60 * 1000);

  if (family === "small") await smallWidget(w,m);
  else if (family === "large") await largeWidget(w,m);
  else await mediumWidget(w,m);

  return w;
}

async function header(parent,m,compact=false) {
  const row = parent.addStack();
  row.centerAlignContent();

  const img = await getImage(m.team.logo, `${m.team.abbr.toLowerCase()}_logo`);
  if (img) {
    const logo = row.addImage(img);
    logo.imageSize = compact ? new Size(28,28) : new Size(34,34);
  }

  row.addSpacer(8);

  const col = row.addStack();
  col.layoutVertically();
  addText(col,m.team.shortName,compact ? 15 : 17,"bold","FFFFFF");

  if (!compact && phase(m) !== "preseason") {
    addText(col,`${m.record.wins}-${m.record.losses}`,11,"medium","FFFFFF",0.72);
  }

  row.addSpacer();

  if (m.live) {
    const b = row.addStack();
    b.setPadding(4,7,4,7);
    b.cornerRadius = 8;
    b.backgroundColor = new Color("FF3B30");
    addText(b,"LIVE",9,"bold","FFFFFF");
  }
}

async function smallWidget(w,m) {
  await header(w,m,true);
  w.addSpacer(8);
  addText(w,phaseLabel(m),8,"bold","FFFFFF",0.48);
  w.addSpacer(3);

  const g = m.live || m.upcoming || m.last;
  if (!g) {
    addText(w,"日程未発表",16,"bold","FFFFFF");
  } else if (m.live) {
    addText(w,`${m.team.abbr} ${g.teamScore}-${g.oppScore}`,20,"bold","FFFFFF");
    addText(w,`vs ${g.opponent.abbr}`,11,"medium","FFFFFF",0.7);
    addText(w,liveStatus(g),11,"medium","FFFFFF",0.82);
  } else if (m.upcoming) {
    addText(w,`vs ${g.opponent.abbr}`,23,"bold","FFFFFF");
    addText(w,formatGameDate(g.date),11,"medium","FFFFFF",0.9);
    if (phase(m) === "preseason") {
      addText(w,countdown(g.date),12,"bold","FFFFFF",0.9);
    } else {
      addText(w,g.homeAway === "away" ? "AWAY" : "HOME",9,"medium","FFFFFF",0.62);
    }
  } else {
    addText(w,`${g.result} ${g.teamScore}-${g.oppScore}`,21,"bold",g.result === "W" ? "34C759" : "FF453A");
    addText(w,`vs ${g.opponent.abbr}`,11,"medium","FFFFFF",0.72);
  }

  w.addSpacer();
  footer(w,m);
}

async function mediumWidget(w,m) {
  await header(w,m);
  w.addSpacer(9);

  if (m.live) {
    addText(w,phaseLabel(m),8,"bold","FFFFFF",0.48);
    w.addSpacer(4);

    const row = w.addStack();

    const a = row.addStack();
    a.layoutVertically();
    addText(a,m.team.abbr,11,"bold","FFFFFF",0.62);
    addText(a,String(m.live.teamScore),30,"bold","FFFFFF");

    row.addSpacer();

    const mid = row.addStack();
    mid.layoutVertically();
    const badge = mid.addStack();
    badge.setPadding(3,7,3,7);
    badge.cornerRadius = 7;
    badge.backgroundColor = new Color("FF3B30");
    addText(badge,"LIVE",9,"bold","FFFFFF");
    mid.addSpacer(4);
    addText(mid,liveStatus(m.live),10,"medium","FFFFFF",0.72);

    row.addSpacer();

    const b = row.addStack();
    b.layoutVertically();
    addText(b,m.live.opponent.abbr,11,"bold","FFFFFF",0.62);
    addText(b,String(m.live.oppScore),30,"bold","FFFFFF");

    w.addSpacer();
    footer(w,m);
    return;
  }

  const body = w.addStack();
  body.spacing = 12;

  const left = body.addStack();
  left.layoutVertically();
  addText(left,phaseLabel(m),8,"bold","FFFFFF",0.48);
  left.addSpacer(2);

  if (m.upcoming) {
    addText(left,"次の試合",10,"bold","FFFFFF",0.68);
    addText(left,`vs ${m.upcoming.opponent.abbr}`,27,"bold","FFFFFF");
    addText(left,formatGameDate(m.upcoming.date),12,"medium","FFFFFF",0.9);
    addText(left,m.upcoming.homeAway === "away" ? "AWAY" : "HOME",9,"medium","FFFFFF",0.6);
  } else {
    addText(left,"次戦",10,"bold","FFFFFF",0.68);
    addText(left,"日程未発表",16,"bold","FFFFFF");
  }

  body.addSpacer();

  const right = body.addStack();
  right.layoutVertically();

  if (phase(m) === "preseason" && m.upcoming) {
    const oppImg = await getImage(m.upcoming.opponent.logo,`opp_${m.upcoming.opponent.abbr.toLowerCase()}`);
    if (oppImg) {
      const lr = right.addStack();
      lr.centerAlignContent();
      const logo = lr.addImage(oppImg);
      logo.imageSize = new Size(42,42);
      lr.addSpacer();
    }
    right.addSpacer(3);
    addText(right,countdown(m.upcoming.date),19,"bold","FFFFFF");
    addText(right,`vs ${m.upcoming.opponent.abbr}`,9,"medium","FFFFFF",0.62);
  } else {
    addText(right,"SEASON",8,"bold","FFFFFF",0.5);
    addText(right,`${m.record.wins}-${m.record.losses}`,21,"bold","FFFFFF");

    if (m.last) {
      right.addSpacer(5);
      addText(right,"LAST",8,"bold","FFFFFF",0.5);
      addText(
        right,
        `${m.last.result} ${m.last.teamScore}-${m.last.oppScore}`,
        14,
        "bold",
        m.last.result === "W" ? "34C759" : "FF453A"
      );
      addText(right,`vs ${m.last.opponent.abbr}`,9,"medium","FFFFFF",0.62);
    }

    const f = formText(m);
    if (f) {
      right.addSpacer(4);
      addText(right,`FORM ${f}`,8,"medium","FFFFFF",0.58);
    }
  }

  w.addSpacer();
  footer(w,m);
}

async function largeWidget(w,m) {
  await header(w,m);
  w.addSpacer(10);
  addText(w,phaseLabel(m),8,"bold","FFFFFF",0.48);
  w.addSpacer(4);

  if (m.live) {
    addText(w,`${m.team.abbr} ${m.live.teamScore} - ${m.live.oppScore} ${m.live.opponent.abbr}`,27,"bold","FFFFFF");
    addText(w,liveStatus(m.live),12,"medium","FFFFFF",0.78);
  } else if (m.upcoming) {
    const next = w.addStack();

    const info = next.addStack();
    info.layoutVertically();
    addText(info,"次の試合",10,"bold","FFFFFF",0.68);
    addText(info,`${m.team.abbr} vs ${m.upcoming.opponent.abbr}`,24,"bold","FFFFFF");
    addText(info,`${formatGameDate(m.upcoming.date)} · ${m.upcoming.homeAway === "away" ? "AWAY" : "HOME"}`,12,"medium","FFFFFF",0.84);

    next.addSpacer();

    const img = await getImage(m.upcoming.opponent.logo,`large_${m.upcoming.opponent.abbr.toLowerCase()}`);
    if (img) {
      const logo = next.addImage(img);
      logo.imageSize = new Size(56,56);
    }

    if (phase(m) === "preseason") {
      w.addSpacer(7);
      addText(w,countdown(m.upcoming.date),18,"bold","FFFFFF",0.92);
    }
  } else {
    addText(w,"日程未発表",18,"bold","FFFFFF");
  }

  w.addSpacer(14);

  if (phase(m) === "preseason") {
    addText(w,"PRESEASON MODE",9,"bold","FFFFFF",0.58);
    addText(w,"開幕後は戦績・直近結果・FORMへ自動切替",12,"medium","FFFFFF",0.78);
  } else {
    const row = w.addStack();

    const left = row.addStack();
    left.layoutVertically();
    addText(left,"直近の試合",9,"bold","FFFFFF",0.58);

    if (m.last) {
      addText(left,`${m.last.result} ${m.last.teamScore}-${m.last.oppScore}`,20,"bold",m.last.result === "W" ? "34C759" : "FF453A");
      addText(left,`vs ${m.last.opponent.abbr}`,10,"medium","FFFFFF",0.68);
    } else {
      addText(left,"まだ試合なし",12,"medium","FFFFFF",0.72);
    }

    row.addSpacer();

    const right = row.addStack();
    right.layoutVertically();
    addText(right,"SEASON",9,"bold","FFFFFF",0.58);
    addText(right,`${m.record.wins}-${m.record.losses}`,22,"bold","FFFFFF");

    w.addSpacer(14);
    addText(w,"直近5試合",9,"bold","FFFFFF",0.58);
    w.addSpacer(6);

    const form = w.addStack();
    form.spacing = 7;

    if (m.last5?.length) {
      for (const g of m.last5) {
        const pill = form.addStack();
        pill.setPadding(5,8,5,8);
        pill.cornerRadius = 8;
        pill.backgroundColor = new Color(g.result === "W" ? "34C759" : "FF453A",0.9);
        addText(pill,g.result,11,"bold","FFFFFF");
      }
    } else {
      addText(form,"試合データ待ち",12,"medium","FFFFFF",0.72);
    }
  }

  w.addSpacer();
  footer(w,m);
}

function lockInline(m) {
  const w = new ListWidget();
  w.addAccessoryWidgetBackground = true;
  if (m.live) {
    w.addText(`${m.team.abbr} ${m.live.teamScore}-${m.live.oppScore} ${m.live.opponent.abbr} ${liveStatus(m.live)}`);
  } else if (m.upcoming) {
    const lead = phase(m) === "preseason" ? countdown(m.upcoming.date) : formatGameDate(m.upcoming.date);
    w.addText(`${m.team.abbr} vs ${m.upcoming.opponent.abbr} ${lead}`);
  } else {
    w.addText(`${m.team.abbr} 日程未発表`);
  }
  return w;
}

function lockCircular(m) {
  const w = new ListWidget();
  w.addAccessoryWidgetBackground = true;
  const t = w.addText(
    m.live
      ? `${m.live.teamScore}\n${m.live.oppScore}`
      : m.upcoming && phase(m) === "preseason"
        ? countdown(m.upcoming.date).replace("あと","")
        : m.team.abbr
  );
  t.font = Font.boldSystemFont(15);
  t.centerAlignText();
  return w;
}

function lockRect(m) {
  const w = new ListWidget();
  w.addAccessoryWidgetBackground = true;

  const t = w.addText(m.team.shortName);
  t.font = Font.boldSystemFont(12);

  const g = m.live || m.upcoming || m.last;
  const s = w.addText(
    m.live
      ? `${m.team.abbr} ${g.teamScore}-${g.oppScore} ${g.opponent.abbr} ${liveStatus(g)}`
      : m.upcoming
        ? `次戦 vs ${g.opponent.abbr} ${phase(m) === "preseason" ? countdown(g.date) : formatGameDate(g.date)}`
        : m.last
          ? `直近 ${g.result} ${g.teamScore}-${g.oppScore}`
          : "日程未発表"
  );
  s.font = Font.mediumSystemFont(11);
  return w;
}

function addText(parent,text,size,weight="regular",hex="FFFFFF",opacity=1) {
  const t = parent.addText(String(text));
  if (weight === "bold") t.font = Font.boldSystemFont(size);
  else if (weight === "semibold") t.font = Font.semiboldSystemFont(size);
  else if (weight === "medium") t.font = Font.mediumSystemFont(size);
  else t.font = Font.systemFont(size);
  t.textColor = new Color(hex,opacity);
  t.lineLimit = 1;
  return t;
}

function footer(w,m) {
  const t = w.addText(`${m.fromCache ? "CACHE" : "UPDATED"} ${formatTime(new Date(m.fetchedAt || Date.now()))}`);
  t.font = Font.mediumSystemFont(7);
  t.textColor = new Color("FFFFFF",0.28);
}

function formatGameDate(d) {
  const f = new DateFormatter();
  f.locale = "ja_JP";
  f.dateFormat = "M/d (E) H:mm";
  return f.string(new Date(d));
}

function formatTime(d) {
  const f = new DateFormatter();
  f.locale = "ja_JP";
  f.dateFormat = "H:mm";
  return f.string(new Date(d));
}

function validHex(v) {
  if (!v) return null;
  const h = String(v).replace("#","").toUpperCase();
  return /^[0-9A-F]{6}$/.test(h) ? h : null;
}

function logoURL(abbr) {
  return `https://a.espncdn.com/i/teamlogos/nba/500/${String(abbr).toLowerCase()}.png`;
}

function fallbackColor(abbr) {
  const colors = {
    LAL:"552583", GSW:"1D428A", BOS:"007A33", NYK:"006BB6", MIA:"98002E",
    CHI:"CE1141", PHX:"1D1160", DAL:"00538C", DEN:"0E2240", MIL:"00471B",
    CLE:"860038", OKC:"007AC1", PHI:"006BB6", BKN:"000000", LAC:"C8102E",
    SAC:"5A2D81", SAS:"000000", HOU:"CE1141", MIN:"0C2340", MEM:"5D76A9",
    NOP:"0C2340", ATL:"E03A3E", CHA:"1D1160", DET:"C8102E", IND:"002D62",
    ORL:"0077C0", POR:"E03A3E", TOR:"CE1141", UTA:"002B5C", WAS:"002B5C"
  };
  return colors[abbr] || "1C1C1E";
}

function errorWidget(title,body) {
  const w = new ListWidget();
  w.backgroundColor = new Color("1C1C1E");
  w.setPadding(14,14,14,14);

  const a = w.addText(title);
  a.font = Font.boldSystemFont(16);
  a.textColor = Color.white();

  w.addSpacer(8);

  const b = w.addText(body);
  b.font = Font.systemFont(11);
  b.textColor = new Color("FFFFFF",0.75);
  return w;
}
