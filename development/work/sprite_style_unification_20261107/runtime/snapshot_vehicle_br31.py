from pathlib import Path
import json, struct, sys, subprocess, hashlib
R=Path(__file__).resolve().parent; ROOT=R.parents[2]
sys.path.insert(0,str(ROOT))
from scripts.observe_sprite_consistency_runtime import ReadOnlyProcess, identify, PLAYER
from scripts.audit_sprite_consistency_coverage import read_assets
S=ROOT/'work/ver_buki_riko/emulator_sessions/20261108T014333879732Z'
rec=json.loads((S/'session.local.json').read_text('utf8'))
check=json.loads(subprocess.check_output([sys.executable,str(R/'read_menu_br31.py'),'--session',str(S),'--pid',str(rec['pid']),'--ram-base','19537440'],text=True,encoding='utf8'))
assert check['passed'] and check['engine']['stage']==4 and check['engine']['area']==1
assert check['engine']['armor']==15 and check['engine']['ultimate_black']==0
game=ROOT/'out/ver_buki_riko/sprite_style_unification_20261107_v31/shibuki_riko.bin'
assets,_=read_assets(game,['PL00_U.ARC','PL01_U.ARC','PL02_U.ARC'])
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(assets['PL00_U.ARC'])=='8b4cc387a59c5cc04b365bac7bc31cacfca79a02054e891e90049e2943b53397'
p=ReadOnlyProcess(rec)
try: ram=p.read(19537440,2097152)
finally:p.close()
found=identify(ram,assets); active=[r for r in found if r[4]]
assert len(active)==1 and active[0][0]=='PL00_U.ARC'
n,es,addresses,candidates,matched=active[0]
assert 184<=ram[PLAYER+0x47]<=203 and ram[PLAYER+0x47]!=198
data={'passed':True,'session':S.relative_to(ROOT).as_posix(),'bin_sha256':rec['bin_sha256'],
 'check':check,'ram_sha256':sha(ram),'archive':n,'archive_sha256':sha(assets[n]),
 'complete_resident_entries':{str(t):{'offset':addresses[t],'size':len(es[t]),'sha256':sha(es[t]),'exact':True} for t in es},
 'active_bank_pointers':matched,'player_animation':ram[PLAYER+0x17],'player_frame':ram[PLAYER+0x47],
 'memory_written':False,'F1_F3_sent':False,
 'limits':['일시정지 시점 상주 그래픽/조립/팔레트 항목 및 활성 포인터의 동일성 검사. 매60Hz VRAM/GPU 전수 추적은 아님.']}
dest=R/'br31_vehicle_resident01.json'; assert not dest.exists()
dest.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'frame':data['player_frame'],'entries':len(es),'sha256':sha(dest.read_bytes())}))
