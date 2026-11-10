from pathlib import Path
import sys,json,hashlib
import pack_vehicle
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];out=D/'packed_vehicle03'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'));ind=W/'zero_audit/nana_base_vehicle13_independent01';native=W/'zero_audit/nana_vehicle_composition_native01/report.json';review=W/'root_review_checkpoint132.json'
assert not(out/'FROZEN.json').exists();assert sha(review)=='ef8e478b578b3fb53f84a1be8c26c5304360fa17c8c49e6d37bb3938be43ae8a'
for p in [out/'report.json',out/'reproduction.json',D/'vehicle_components_native_checks.json',D/'native_sequence01/browser_verification.json',ind/'report_clarified.json',native]:assert read(p)['passed'],p
assert sha(ind/'report_clarified.json')=='c9053b41fd2441a2f323d6f1ccb86dc7b2dc37c08ba9a1703f8883e25256e482';assert read(ind/'report_clarified.json')['candidate_sha256']==sha(out/'PL00_U.ARC')
assert sha(native)=='4bd59dcb6c8c422690982f7161b5591ae7dae3a26a4a2d47fc05f98d518d925f'
paths=set(D.glob('*.py'))
for mod in list(sys.modules.values()):
 s=getattr(mod,'__file__',None)
 if s:
  p=Path(s).resolve()
  if p.suffix=='.py'and p.is_relative_to(ROOT)and '/work/tools/'not in p.as_posix():paths.add(p)
for name in ('inputs_a01','inputs_b01','art_a01','art_b01','registered_a01','registered_b01','joint_targets03'):paths.update(p for p in(D/name).rglob('*')if p.is_file())
bound=lambda p:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)};write=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
write(out/'INPUT_FROZEN.json',{'scope':'새 네 몸체 두 의상, 실제 원Y별칭9, joint03 연결 소유. 재현 진입점 pack_vehicle.build; 초기 탐색/생성 스크립트는 이력이다.','files':[bound(p)for p in sorted(paths)]})
proposal={'resource':'PL00_U.ARC','path':(out/'PL00_U.ARC').relative_to(ROOT).as_posix(),'before':read(out/'report.json')['before'],'after':sha(out/'PL00_U.ARC'),'refs':list(range(162,175)),'new_authored_body_refs':[162,166,170,174],'derived_refs':[163,164,165,167,168,169,171,172,173],'forms':['base','fourth_arm1','fourth_arm2','partial_masks'],'internal_record_storage':read(out/'report.json')['internal_record_storage'],'preserved':['그래픽은행 절대경계·비대상 몸체·팔레트·EXE·원시간표·판정·음향·사용자 저장'],'runtime_verified':False,'user_accepted':False}
write(out/'proposal.json',proposal)
proof=[out/'PL00_U.ARC',out/'report.json',out/'reproduction.json',out/'INPUT_FROZEN.json',out/'proposal.json',D/'vehicle_components.json',D/'vehicle_components_native_checks.json',D/'native_sequence01/report.json',D/'native_sequence01/browser_verification.json',ind/'report.json',ind/'report_clarified.json',ind/'visual_review.json',native,review]
write(out/'FROZEN.json',{'frozen':True,'character':'nana','candidate_sha256':proposal['after'],'parent_arc_sha256':proposal['before'],'refs':proposal['refs'],'files':[bound(p)for p in proof],'source_lock_sha256':sha(out/'INPUT_FROZEN.json'),'status':'새 몸체8셀·Y파생9참조. 재현2/거부7, 원MIPS/GPU·416부분조합·독립/루트시각·원표65..76/39스텝/1944canvas 통과. 내부head bank40B 추가는 body bank미참조tail40B 회수이며27nonzero, 0패딩이 아니다. 원loader/animation decoder26회·원composition lookup1896회 검증. 실제 차량 탑승은 별도.','runtime_verified':False,'final_user_accepted':False})
print(json.dumps({'inputs':len(paths),'freeze_sha256':sha(out/'FROZEN.json'),'arc':proposal['after']}))
