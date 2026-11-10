from pathlib import Path
import sys,json,hashlib
import pack_settle
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];out=D/'packed_settle01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'));ind=W/'zero_audit/nana_base_settle87_92_independent01';review=W/'root_review_checkpoint138.json'
assert not(out/'FROZEN.json').exists();assert sha(review)=='b8832490d86f21e4a46b5efb3a0b9b7e793da21551272e0f4b87a48e1e069261'
for p in [out/'report.json',out/'reproduction.json',D/'settle_components_native_checks.json',D/'native_sequence01/browser_verification.json',ind/'report.json']:assert read(p)['passed'],p
assert sha(ind/'report.json')=='ab899d91a95b290b8afa5bcd9fcf9afe4e278c40d6b9de15bcc3c8b2f675dcd6';assert read(ind/'report.json')['candidate_sha256']==sha(out/'PL00_U.ARC')
lock=read(ind/'READER_INPUT_LOCK.json');assert sha(ind/'READER_INPUT_LOCK.json')=='e5fc34fb8d85b9ba91947ac61d42337792be3ba1049e454c42f2d9dd1d3fd6ba'
for name,digest in lock['input_files'].items():assert sha(ROOT/name)==digest,name
for name in ('reader','report','visual'):
 row=lock[name];assert sha(ROOT/row['path'])==row['sha256'],name
assert sha(W/'zero_audit/nana_base_settle2_independent01/report.json')=='bc5269ec1e23fb2823b254303da1a83b4b21724d33fa48c989c1e060d621489c'
assert sha(W/'zero_audit/nana_base_settle2_independent01/visual_review.json')=='f6c67b2270092bdd06ad7a5c23aa563296b6a5f72df39c813792f0eee5ae6951'
paths=set(D.glob('*.py'))
for mod in list(sys.modules.values()):
 s=getattr(mod,'__file__',None)
 if s:
  p=Path(s).resolve()
  if p.suffix=='.py'and p.is_relative_to(ROOT)and '/work/tools/'not in p.as_posix():paths.add(p)
for name in ('inputs01','art01','registered01','joint_targets02'):paths.update(p for p in(D/name).rglob('*')if p.is_file())
bound=lambda p:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)};write=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
write(out/'INPUT_FROZEN.json',{'scope':'새87/92 네 의상셀. 새손·얼굴공유와 같은행 다리등록, joint02 베일소유. 92의 떠있던1셀을 가진joint01은 최종입력 제외.','files':[bound(p)for p in sorted(paths)]})
proposal={'resource':'PL00_U.ARC','path':(out/'PL00_U.ARC').relative_to(ROOT).as_posix(),'before':read(out/'report.json')['before'],'after':sha(out/'PL00_U.ARC'),'refs':[87,92],'new_authored_body_refs':[87,92],'derived_refs':[],'forms':['base','fourth_arm1','fourth_arm2','partial_masks'],'preserved':['홍채·몸체전체높이·발 높이·비대상 몸체·팔레트·EXE·원시간표·판정·음향·사용자 저장'],'runtime_verified':False,'user_accepted':False}
write(out/'proposal.json',proposal)
proof=[out/'PL00_U.ARC',out/'report.json',out/'reproduction.json',out/'INPUT_FROZEN.json',out/'proposal.json',D/'settle_components.json',D/'settle_components_native_checks.json',D/'native_sequence01/report.json',D/'native_sequence01/browser_verification.json',ind/'report.json',ind/'visual.json',ind/'READER_INPUT_LOCK.json',review]
write(out/'FROZEN.json',{'frozen':True,'character':'nana','candidate_sha256':proposal['after'],'parent_arc_sha256':proposal['before'],'refs':proposal['refs'],'files':[bound(p)for p in proof],'source_lock_sha256':sha(out/'INPUT_FROZEN.json'),'status':'새 몸체4셀·10층. 재현1/거부7·원MIPS/GPU·64부분조합·독립/루트시각·원표5/23스텝/1250canvas 통과. 실기발동과 선택1..8사본은 별도, 전체 미술 완료 아님.','runtime_verified':False,'final_user_accepted':False})
print(json.dumps({'inputs':len(paths),'freeze_sha256':sha(out/'FROZEN.json'),'arc':proposal['after']}))
