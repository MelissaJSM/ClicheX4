"""Confirm three viewed older detail boards still describe RN18 body pixels."""
from pathlib import Path
import sys,json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
sha=lambda b:hashlib.sha256(b).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
old=W/'nana_audit/remaining_review_v1';m=read(old/'manifest.json');plan=read(W/'staging_rn_v18.json')
disc=ROOT/plan['output']/'rin_nana.bin';assert sha(disc.read_bytes())=='0f40463b883e00a7e3acf268fd45052b905d0454440d8c5436ce24fe80f58c95'
assets,_=read_disc(disc,('PL00_U.ARC','PL02_U.ARC'));arcs={n:Archive(b) for n,b in assets.items()}
lookup={(r['form'],r['ref']):r for r in m['frames']}
groups={'focus_ladder.png':[0,143,146,150,153,183],'focus_arrival.png':[0,133,135,137,141,142],'focus_victory.png':[0,156,161,204,206,207]}
checks=[];art=[]
for name,refs in groups.items():
 p=old/name;matches=[r for r in m['sheets'] if Path(r['path']).name==name];assert len(matches)==1 and sha(p.read_bytes())==matches[0]['sha256']
 art.append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())})
 for form in ('base','fourth','ultimate_before','ultimate_after'):
  archive='PL02_U.ARC' if form.startswith('ultimate') else 'PL00_U.ARC';mask=15 if form in ('fourth','ultimate_before') else 0
  for ref in refs:
   im,_=arcs[archive].composite(ref,mask,2);before=lookup[form,ref]['rgba_sha256'];now=sha(im.tobytes())
   checks.append({'sheet':name,'form':form,'ref':ref,'current_rgba_sha256':now,'exact_to_viewed_older_sheet':now==before})
assert all(r['exact_to_viewed_older_sheet'] for r in checks)
record={'root_actually_viewed':art,'current_bin':disc.relative_to(ROOT).as_posix(),'current_bin_sha256':sha(disc.read_bytes()),
 'actual_disc_assets':{n:sha(b) for n,b in assets.items()},'current_reextraction_checks':checks,
 'findings':['사다리 기본143/146/150의 단색 분홍 뒤머리와 승리204/206/207 소매의 검은 덩어리는 대기보다 세부 표현이 적어 후속 재작화 우선 후보로 유지한다.',
 '등장133/135/137의 현재 포스 표시가 기본형 의상과 같아 보인다. 이 판만으로 누락을 확정하지 않고 원파츠/로딩 정책을 추가 조사한다. Ultimate 전폼 재킷의 대비도 점검 대상이다.'],
 'limits':['선택한72표시가 현재 BIN과 같은지 확인한 미술 검토다. 해당모션 실기/나머지 모든참조 품질 통과를 뜻하지 않는다.','원본/기준대기/현재 게임자산은 변경하지 않았다.'],
 'final_user_accepted':False}
p=W/'root_review_checkpoint93.json';assert not p.exists();p.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'root93':sha(p.read_bytes()),'exact_current_displays':len(checks)}))
