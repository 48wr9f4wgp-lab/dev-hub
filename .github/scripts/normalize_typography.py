from pathlib import Path

p = Path('index.html')
s = p.read_text()

# Stop iOS Safari text inflation and make the list typography deterministic.
s = s.replace(
    '*{box-sizing:border-box}html{background:var(--bg)}body{margin:0;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Hiragino Sans","Yu Gothic UI",Meiryo,sans-serif;line-height:1.42}',
    '*{box-sizing:border-box}html{background:var(--bg);-webkit-text-size-adjust:100%;text-size-adjust:100%}body{margin:0;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Hiragino Sans","Yu Gothic UI",Meiryo,sans-serif;line-height:1.42;-webkit-text-size-adjust:100%;text-size-adjust:100%}'
)

# List hierarchy: title > description > metadata. Keep all cards consistent on iPhone.
s = s.replace(
    '.name{font-size:16px;font-weight:850;overflow-wrap:anywhere}',
    '.name{font-size:16px;line-height:1.2;font-weight:850;overflow-wrap:anywhere}'
)
s = s.replace(
    '.desc{font-size:12.5px;line-height:1.45;margin:6px 0 7px;color:#d9e2ec;display:-webkit-box;-webkit-line-clamp:1;-webkit-box-orient:vertical;overflow:hidden}',
    '.desc{font-size:12px;line-height:1.45;margin:6px 0 7px;color:#d9e2ec;display:-webkit-box;-webkit-line-clamp:1;-webkit-box-orient:vertical;overflow:hidden;overflow-wrap:anywhere;min-width:0}'
)
s = s.replace(
    '.chip{border:1px solid var(--border);border-radius:999px;padding:2px 7px;font-size:10px;font-weight:800;color:var(--muted)}',
    '.chip{border:1px solid var(--border);border-radius:999px;padding:2px 7px;font-size:10px;line-height:1.25;font-weight:800;color:var(--muted)}'
)
s = s.replace(
    '.paths{font-size:10.5px;color:#c5d1dc;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0}',
    '.paths{font-size:10px;line-height:1.35;color:#c5d1dc;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;min-width:0}'
)
s = s.replace(
    '.kicker{font-size:9px;font-weight:900;color:var(--muted);white-space:nowrap}',
    '.kicker{font-size:9px;line-height:1.35;font-weight:900;color:var(--muted);white-space:nowrap}'
)
s = s.replace(
    '.updated{font-size:10px;color:var(--muted);white-space:nowrap}',
    '.updated{font-size:10px;line-height:1.3;color:var(--muted);white-space:nowrap}'
)
s = s.replace(
    '.sectionhead h2{font-size:16px;margin:0}',
    '.sectionhead h2{font-size:16px;line-height:1.2;margin:0}'
)

# Desktop can breathe slightly more, but still follows the same hierarchy.
s = s.replace('@media(min-width:500px){.desc{-webkit-line-clamp:2}}@media(min-width:640px){',
              '@media(min-width:500px){.desc{-webkit-line-clamp:2}}@media(min-width:640px){')
s = s.replace('.card{padding:14px}.desc{font-size:13px}', '.card{padding:14px}.desc{font-size:12.5px}')

p.write_text(s)
