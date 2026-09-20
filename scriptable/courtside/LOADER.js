// COURTSIDE Loader v1.0
// One-time Scriptable loader. Future COURTSIDE updates are fetched from GitHub.

const SOURCE = "https://raw.githubusercontent.com/48wr9f4wgp-lab/dev-hub/main/scriptable/courtside/COURTSIDE.js";
const CACHE_FILE = "COURTSIDE_remote_cache.js";

const fm = FileManager.local();
const cachePath = fm.joinPath(fm.documentsDirectory(), CACHE_FILE);

let code = null;

try {
  const req = new Request(SOURCE + "?t=" + Date.now());
  req.timeoutInterval = 12;
  req.headers = { "Cache-Control": "no-cache" };

  const downloaded = await req.loadString();

  if (!downloaded.includes("// COURTSIDE") || !downloaded.includes("Script.setWidget")) {
    throw new Error("Invalid remote script");
  }

  code = downloaded;
  fm.writeString(cachePath, downloaded);
} catch (e) {
  if (fm.fileExists(cachePath)) {
    code = fm.readString(cachePath);
  } else {
    const w = new ListWidget();
    w.backgroundColor = new Color("1C1C1E");
    w.setPadding(14,14,14,14);

    const title = w.addText("COURTSIDE");
    title.font = Font.boldSystemFont(16);
    title.textColor = Color.white();

    w.addSpacer(8);

    const body = w.addText("GitHubからコードを取得できませんでした。通信後に再実行してください。");
    body.font = Font.systemFont(11);
    body.textColor = new Color("FFFFFF",0.75);

    Script.setWidget(w);
    if (!config.runsInWidget) await w.presentMedium();
    Script.complete();
    return;
  }
}

try {
  const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor;
  await new AsyncFunction(code)();
} catch (e) {
  const w = new ListWidget();
  w.backgroundColor = new Color("1C1C1E");
  w.setPadding(14,14,14,14);

  const title = w.addText("COURTSIDE ERROR");
  title.font = Font.boldSystemFont(15);
  title.textColor = Color.white();

  w.addSpacer(8);

  const body = w.addText(String(e));
  body.font = Font.systemFont(9);
  body.textColor = new Color("FFFFFF",0.75);

  Script.setWidget(w);
  if (!config.runsInWidget) await w.presentMedium();
  Script.complete();
}
