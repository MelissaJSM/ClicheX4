from pathlib import Path
import sys,json,hashlib
import pack_arrival
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];out=D/'packed_arrival01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
ind=W/'zero_audit/nana_base_arrival7_independent01';review=W/'root_review_checkpoint125.json'
assert not(out/'FROZEN.json').exists()
assert sha(review)=='f6f5c8f2999453c5d1ccc9101b88f25caa9c05359b6dc1ac5ab6928ed550319f'
checks=[out/'report.json',out/'reproduction.json',D/'arrival_components_native_checks.json',D/'native_sequence01/browser_verification.json',ind/'report.json']
for p in checks:assert read(p)['passed'],p
assert read(ind/'report.json')['candidate_sha256']==sha(out/'PL00_U.ARC')
assert sha(ind/'report.json')=='be6dad6568f350ccb5ea69084afaebb256e8ffc69d79f4e2616d11c2c3034993'
paths=set(D.glob('*.py'))
for mod in list(sys.modules.values()):
 s=getattr(mod,'__file__',None)
 if s:
  p=Path(s).resolve()
  if p.suffix=='.py' and p.is_relative_to(ROOT) and '/work/tools/' not in p.as_posix():paths.add(p)
for name in ('inputs_a01','inputs_b01','art_a01','art_b01','registered_a01','registered_b01','body_targets02','joint_targets01'):
 paths.update(p for p in(D/name).rglob('*')if p.is_file())
bound=lambda p:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
write=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
write(out/'INPUT_FROZEN.json',{'scope':'새133/135/136/137 두 의상8셀, 새133에 연동한130/131/134 효과파생. 상단베일 머리5 소유02 및 공동3타일 head. 반려body_targets01 제외.','files':[bound(p)for p in sorted(paths)]})
proposal={'resource':'PL00_U.ARC','path':(out/'PL00_U.ARC').relative_to(ROOT).as_posix(),'before':read(out/'report.json')['before'],'after':sha(out/'PL00_U.ARC'),'refs':[130,131,133,134,135,136,137],'new_authored_body_refs':[133,135,136,137],'derived_refs':[130,131,134],'forms':['base','fourth_arm1','fourth_arm2','partial_masks'],'preserved':['132의 기존효과 raw·조립·표시','비대상 몸체·팔레트·EXE·시간표·발사체·판정·음향·저장'],'runtime_verified':False,'user_accepted':False}
write(out/'proposal.json',proposal)
proof=[out/'PL00_U.ARC',out/'report.json',out/'reproduction.json',out/'INPUT_FROZEN.json',out/'proposal.json',D/'arrival_components.json',D/'arrival_components_native_checks.json',D/'native_sequence01/report.json',D/'native_sequence01/browser_verification.json',ind/'report.json',ind/'visual_review.json',review]
write(out/'FROZEN.json',{'frozen':True,'character':'nana','candidate_sha256':proposal['after'],'parent_arc_sha256':proposal['before'],'refs':proposal['refs'],'files':[bound(p)for p in proof],'source_lock_sha256':sha(out/'INPUT_FROZEN.json'),'status':'새 몸체8셀·효과파생3참조. 재현2/거부7, 원MIPS/GPU·224부분조합·독립/루트시각·원표2/18스텝/402canvas 통과. 실기발동 별도, 전체 미술 완료 아님.','runtime_verified':False,'final_user_accepted':False})
print(json.dumps({'inputs':len(paths),'freeze_sha256':sha(out/'FROZEN.json'),'arc':proposal['after']}))
