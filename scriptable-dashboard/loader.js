// 俺専用ダッシュボード Loader v1.0
// このスクリプトだけをScriptableに残す。
// GitHub上のmain.jsを毎回取得し、失敗時は前回成功版へフォールバックする。

const REMOTE = "https://raw.githubusercontent.com/48wr9f4wgp-lab/dev-hub/main/scriptable-dashboard/main.js";
const fm = FileManager.local();
const dir = fm.joinPath(fm.documentsDirectory(), "ore-dashboard-loader");
const cachePath = fm.joinPath(dir, "main.lastgood.js");

if (!fm.fileExists(dir)) fm.createDirectory(dir, true);

const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor;

async function runCode(code) {
  const fn = new AsyncFunction(code);
  await fn();
}

function errorWidget(title, detail) {
  const w = new ListWidget();
  w.setPadding(16,16,16,16);
  const t = w.addText(title);
  t.font = Font.boldSystemFont(14);
  t.textColor = new Color("#DC2626");
  w.addSpacer(6);
  const d = w.addText(detail);
  d.font = Font.systemFont(10);
  d.textColor = new Color("#64748B");
  return w;
}

let remoteError = null;

try {
  const req = new Request(REMOTE + "?ts=" + Date.now());
  req.timeoutInterval = 12;
  const code = await req.loadString();

  // 構文エラーならここで弾く
  new AsyncFunction(code);

  // 実行に成功したものだけ last-good として保存
  await runCode(code);
  fm.writeString(cachePath, code);

} catch (e) {
  remoteError = e;

  if (fm.fileExists(cachePath)) {
    try {
      await runCode(fm.readString(cachePath));
    } catch (cacheError) {
      const w = errorWidget(
        "ダッシュボード起動失敗",
        "GitHub版と前回成功版の両方でエラー\n" + String(cacheError)
      );
      if (config.runsInWidget) Script.setWidget(w);
      else await w.presentLarge();
    }
  } else {
    const w = errorWidget(
      "初回取得に失敗",
      "GitHubへ接続できません。通信状態を確認して再実行してください。\n" + String(remoteError)
    );
    if (config.runsInWidget) Script.setWidget(w);
    else await w.presentLarge();
  }
}

Script.complete();
