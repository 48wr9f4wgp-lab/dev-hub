from pathlib import Path
p=Path('index.html')
s=p.read_text()
s=s.replace("const status=(ok,warn=False)=>", "const status=(ok,warn=false)=>")
s=s.replace("add('QA配布');", "add('品質確認用配布');")
s=s.replace("add('PWA');", "add('ホーム画面対応');")
p.write_text(s)
print('follow-up Japanese wording/runtime cleanup applied')
