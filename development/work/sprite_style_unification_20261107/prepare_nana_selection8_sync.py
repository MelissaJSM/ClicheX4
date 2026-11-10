"""Create an isolated Nana UI copy tool from the measured identity mapping."""
from pathlib import Path
import sys,json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
 d=W/'root_nana_selection8';assert not d.exists();d.mkdir()
 plan=json.loads((W/'staging_rn_v37.json').read_text('utf8'))
 source=ROOT/plan['source_bin'];assert sha(source.read_bytes())==plan['source_sha256']
 old=read_disc(source,('PL00_U.ARC',))[0]['PL00_U.ARC'];assert sha(old)==plan['resources']['PL00_U.ARC']['before']
 (d/'baseline_PL00_U.ARC').write_bytes(old)
 origin=json.loads((W/'nana_selection8_origins.json').read_text('utf8'))
 assert origin['source_sha256']==plan['source_sha256'] and origin['all_eight_exact']
 assert all(r['exact_matches']==[{'flip_x':False,'dx':0,'dy':0,'different_pixels':0}]for r in origin['rows'])
 src=W/'shibuki_audit/sync_standing_selection.py';s=src.read_text('utf8')
 a=s.index("UI=W/");b=s.index('\ndef decode',a)
 ui=plan['resources']['ST0E_U1.ARC'];new=plan['resources']['PL00_U.ARC']
 s=s[:a]+f"UI=ROOT/{ui['path']!r}\nOLD=H/'baseline_PL00_U.ARC'\nNEW=ROOT/{new['path']!r}\nHASHES={[ui['after'],sha(old),new['after']]!r}\nDY={{n:0 for n in range(1,9)}}\n"+s[b:]
 assert s.count('staging_br_v23.json')==1;s=s.replace('staging_br_v23.json','staging_rn_v37.json').replace('builder_v4_guard_pending','builder_v5_guard_pending')
 (d/'sync_standing_selection.py').write_text(s,'utf8')
 report={'template':{'path':src.relative_to(ROOT).as_posix(),'sha256':sha(src.read_bytes())},'baseline_sha256':sha(old),'measured_origins':origin,'new_game':new,'ui_parent':ui,'only_new_local_files':True}
 (d/'preparation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
 print(json.dumps({'directory':str(d),'baseline':sha(old)}))
if __name__=='__main__':main()
