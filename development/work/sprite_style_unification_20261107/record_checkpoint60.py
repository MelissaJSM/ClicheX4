from pathlib import Path
import sys,json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
sha=lambda b:hashlib.sha256(b).hexdigest()
D=W/'nana_audit/remaining_review_v1';m=json.loads((D/'manifest.json').read_text('utf8'))
game=ROOT/'out/ver_rin_nana/sprite_style_unification_20261107_v15/rin_nana.bin'
assert sha(game.read_bytes())=='66b808fc2f37a93eefd915ab7199934bbed62dcef4500ee087b75daa80324989'
arcs={k:Archive(v) for k,v in read_disc(game,('PL00_U.ARC','PL02_U.ARC'))[0].items()}
forms={'base':('PL00_U.ARC',0),'fourth':('PL00_U.ARC',15),'ultimate_before':('PL02_U.ARC',15),'ultimate_after':('PL02_U.ARC',0)}
refs={0,106,108,120,124,233,143,146,150,153,183,133,135,137,141,142,156,161,204,206,207};checks=[]
for r in m['frames']:
 if r['ref'] not in refs:continue
 key,mask=forms[r['form']];im,_=arcs[key].composite(r['ref'],mask,2);current=sha(im.tobytes());assert current==r['rgba_sha256'],(r['form'],r['ref'])
 checks.append({'form':r['form'],'ref':r['ref'],'current_rgba_sha256':current})
pages=[D/(n+'.png') for n in ['focus_hurt_low','focus_ladder','focus_arrival','focus_victory']]
report={'root_actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())} for p in pages],'current_disc_sha256':sha(game.read_bytes()),'focused_references_match_current_bin':checks,
 'findings':['나나 기본 피격106/108과 사다리143/146/150의 후면 머리/소매는 대기보다 큰 단색 면으로 줄어들어 잔여 세부 묘사 수정 대상이다.','등장133/135/137의 굵은 외곽, 승리204/206/207의 머리/소매 세부 차이를 후속 묶음으로 확인했다.','포스와 Ultimate 전의 등장 일부가 기본/수영복으로 보이는 정적 차이는 확인했으나 원작 전환층 정책이 있으므로 새 런타임 결함으로 확정하지 않는다.'],
 'limits':['직접 열람한 것은 집중4판이며84참조×폼 해시 대조는 미술 전수 열람과 다르다.','광선161·복귀대기141/142는 의도된 효과/기준 그림을 보존한다.','이 기록은 기존 분류의 재확인과 현재BIN 연결이며 새 원화나 최종 수용이 아니다.']}
p=W/'root_review_checkpoint60.json';assert not p.exists();p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'matched':len(checks),'sha256':sha(p.read_bytes())}))
