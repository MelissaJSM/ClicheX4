from pathlib import Path
import sys,json,hashlib
import pack_return
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];out=D/'packed_return03'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'));ind=W/'zero_audit/nana_base_return3_independent01';review=W/'root_review_checkpoint131.json'
assert not(out/'FROZEN.json').exists();assert sha(review)=='1156725def24cd35aca58842ae1b7f3d886bc5f8c61e1d6ebffc3e91ff070d80'
for p in [out/'report.json',out/'reproduction.json',D/'return_components_native_checks.json',D/'native_sequence01/browser_verification.json',ind/'report.json']:assert read(p)['passed'],p
assert sha(ind/'report.json')=='0c99eff7d4a47d5b8bcc8535680c93faa7a4f9432d250cb10ee04729c0143d54';assert read(ind/'report.json')['candidate_sha256']==sha(out/'PL00_U.ARC')
paths=set(D.glob('*.py'))
for mod in list(sys.modules.values()):
 s=getattr(mod,'__file__',None)
 if s:
  p=Path(s).resolve()
  if p.suffix=='.py'and p.is_relative_to(ROOT)and '/work/tools/'not in p.as_posix():paths.add(p)
for name in ('inputs01','art01','registered01','joint_targets03'):paths.update(p for p in(D/name).rglob('*')if p.is_file())
bound=lambda p:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)};write=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
write(out/'INPUT_FROZEN.json',{'scope':'새156 두 의상과157/158 파생, joint03 최종소유. 옛joint01 뜬7px와02 베일소유는 최종입력에서 제외.','files':[bound(p)for p in sorted(paths)]})
proposal={'resource':'PL00_U.ARC','path':(out/'PL00_U.ARC').relative_to(ROOT).as_posix(),'before':read(out/'report.json')['before'],'after':sha(out/'PL00_U.ARC'),'refs':[156,157,158],'new_authored_body_refs':[156],'derived_refs':[157,158],'forms':['base','fourth_arm1','fourth_arm2','partial_masks'],'preserved':['159/160 원효과·비대상 몸체·팔레트·EXE·원시간표·판정·음향·사용자 저장'],'runtime_verified':False,'user_accepted':False}
write(out/'proposal.json',proposal)
proof=[out/'PL00_U.ARC',out/'report.json',out/'reproduction.json',out/'INPUT_FROZEN.json',out/'proposal.json',D/'return_components.json',D/'return_components_native_checks.json',D/'native_sequence01/report.json',D/'native_sequence01/browser_verification.json',ind/'report.json',ind/'visual_review.json',review]
write(out/'FROZEN.json',{'frozen':True,'character':'nana','candidate_sha256':proposal['after'],'parent_arc_sha256':proposal['before'],'refs':proposal['refs'],'files':[bound(p)for p in proof],'source_lock_sha256':sha(out/'INPUT_FROZEN.json'),'status':'새 몸체2셀·귀환효과파생2참조. 재현2/거부7, 원MIPS/GPU·96부분조합·독립/루트시각·원표3/40/12스텝/724canvas 통과. 실기발동 별도, 전체 미술 완료 아님.','runtime_verified':False,'final_user_accepted':False})
print(json.dumps({'inputs':len(paths),'freeze_sha256':sha(out/'FROZEN.json'),'arc':proposal['after']}))
