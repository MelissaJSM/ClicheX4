"""Read-only comparison of protected inputs and isolated test cards."""
from pathlib import Path
import argparse, hashlib, json, subprocess
W = Path(__file__).resolve().parent; ROOT = W.parents[1]
read = lambda p: json.loads(p.read_text('utf8'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''): h.update(b)
    return h.hexdigest()
p=argparse.ArgumentParser(); p.add_argument('checkpoint',type=int); p.add_argument('--previous',type=int,required=True); a=p.parse_args()
dest=W/f'protection_checkpoint{a.checkpoint}.json'; assert not dest.exists()
files={}
for name, old in read(W/'protection_before.json')['files'].items():
    f=ROOT/name; now={'size':f.stat().st_size,'sha256':sha(f)}
    assert now==old,name
    files[name]=now
cards=read(W/f'protection_checkpoint{a.previous}.json')['test_cards']
for c in cards: assert sha(ROOT/c['source'])==sha(ROOT/c['copy'])==c['sha256']
count=subprocess.check_output(['powershell','-NoProfile','-Command','(Get-Process epsxe* -ErrorAction SilentlyContinue | Measure-Object).Count'],text=True)
assert count.strip()=='0'
dest.write_text(json.dumps({'passed':True,'protected_files':len(files),'files':files,'test_cards':cards,'epsxe_process_count':0},ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'checkpoint':a.checkpoint,'protected_files':len(files),'test_cards':len(cards),'sha256':sha(dest)}))
