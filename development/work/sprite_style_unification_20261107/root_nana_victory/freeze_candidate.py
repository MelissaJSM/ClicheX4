from pathlib import Path
import sys,json,hashlib
import pack_victory
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];out=D/'packed_victory02'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
ind=W/'zero_audit/nana_base_victory4_independent01';review=W/'root_review_checkpoint129.json'
assert not(out/'FROZEN.json').exists();assert sha(review)=='3478a104bbb1045c3e9ca0d06741bce6204d0eb665c763090ce56f6848618e2c'
for p in [out/'report.json',out/'reproduction.json',D/'victory_components_native_checks.json',D/'native_sequence01/browser_verification.json',ind/'report.json']:assert read(p)['passed'],p
assert sha(ind/'report.json')=='ecdd70532a316932432295222d414364d369d61ed85b6ead29f437bcc58819a5';assert read(ind/'report.json')['candidate_sha256']==sha(out/'PL00_U.ARC')
paths=set(D.glob('*.py'))
for mod in list(sys.modules.values()):
 s=getattr(mod,'__file__',None)
 if s:
  p=Path(s).resolve()
  if p.suffix=='.py'and p.is_relative_to(ROOT)and '/work/tools/'not in p.as_posix():paths.add(p)
for name in ('inputs_a01','inputs_b01','inputs_206_03','art_a01','art_b01','art_206_03','registered_a01','registered_b01','registered_206_03','joint_targets01'):
 paths.update(p for p in(D/name).rglob('*')if p.is_file())
bound=lambda p:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
write=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
write(out/'INPUT_FROZEN.json',{'scope':'204/205 A,206 세 번째 원화,207 B01 y−5. 206 B01/B02 및207 B02 미채택. 고정384캔버스에서 새 머리와 의상 디테일 보존.','files':[bound(p)for p in sorted(paths)]})
proposal={'resource':'PL00_U.ARC','path':(out/'PL00_U.ARC').relative_to(ROOT).as_posix(),'before':read(out/'report.json')['before'],'after':sha(out/'PL00_U.ARC'),'refs':[204,205,206,207],'new_authored_body_refs':[204,205,206,207],'forms':['base','fourth_arm1','fourth_arm2','partial_masks'],'preserved':['비대상 몸체·원팔레트·EXE·시간표·판정·음향·사용자 저장'],'runtime_verified':False,'user_accepted':False}
write(out/'proposal.json',proposal)
proof=[out/'PL00_U.ARC',out/'report.json',out/'reproduction.json',out/'INPUT_FROZEN.json',out/'proposal.json',D/'victory_components.json',D/'victory_components_native_checks.json',D/'native_sequence01/report.json',D/'native_sequence01/browser_verification.json',ind/'report.json',ind/'visual_review.json',review]
write(out/'FROZEN.json',{'frozen':True,'character':'nana','candidate_sha256':proposal['after'],'parent_arc_sha256':proposal['before'],'refs':proposal['refs'],'files':[bound(p)for p in proof],'source_lock_sha256':sha(out/'INPUT_FROZEN.json'),'status':'승리 새8셀. 재현2/거부7, 원MIPS/GPU·128부분조합·독립/루트시각·원표39/6스텝/322canvas 통과. 실기발동 별도, 전체 미술 완료 아님.','runtime_verified':False,'final_user_accepted':False})
print(json.dumps({'inputs':len(paths),'freeze_sha256':sha(out/'FROZEN.json'),'arc':proposal['after']}))
