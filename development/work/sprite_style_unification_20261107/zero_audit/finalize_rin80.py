"""Freeze the five remaining rear poses, preserving the prior Rin75 checkpoint."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
D=Path(__file__).parent;sys.path.insert(0,str(D));R=D/'rin_extension'
import pack_rin_rear_continuation2 as wrapper
c=wrapper.core;e=c.engine;P=c.OUT;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not(P/'FROZEN.json').exists()
arc=c.P.read_bytes();targets=c.targets(arc);e.PARENT=c.P;e.PARENT_SHA=c.SHA;e.KEYS={k:(0,0,0)for k in targets};e.get_targets=c.targets;e.pack_frame=c.pack
rejected=[]
for case in('wrong_parent','missing_art','changed_authored_pixel','index16','wrong_alias'):
 a=arc;t={k:v.copy()for k,v in targets.items()}
 if case=='wrong_parent':a=bytes([arc[0]^1])+arc[1:]
 elif case=='missing_art':del t[0,191]
 elif case=='changed_authored_pixel':t[0,194][160,150]^=1
 elif case=='index16':t[0,192][160,150]=16
 else:t[0,196]=t[0,191].copy()
 try:e.build(a,t)
 except ValueError as exc:rejected.append({'case':case,'error':str(exc)})
 else:raise AssertionError('Unsafe input accepted')
audit_path=R/'final80_readback_audit.json';audit=json.loads(audit_path.read_text('utf8'));native_path=R/'rin80_components_native_checks.json';native=json.loads(native_path.read_text('utf8'))
assert audit['passed']and native['passed']and sha(P/'PL01_U.ARC')==audit['candidate_sha256']=='a565e55fb422764432b03fe60d53430fcd5ede2aa95829a655a9c22bcc902c4d'
boxes={191:[154,113,163,121],192:[149,133,160,141],194:[166,114,176,121],195:[147,125,158,133]};anchors=[]
for n,(x0,y0,x1,y1)in boxes.items():
 before=e.native.render(arc,0,0,n)[0];after=targets[0,n];row={'ref':n,'glove_roi':[x0,y0,x1,y1]};points=[]
 for label,ar in [('before',before),('after',after)]:
  y,x=np.nonzero(np.isin(ar[y0:y1,x0:x1],range(7,12)));center=[float(x.mean()+x0),float(y.mean()+y0)];points.append(center)
  yy,xx=np.nonzero(ar);row[label]={'glove_bright_area_center':center,'floor_y':int(yy.max()),'floor_x':xx[yy==yy.max()].tolist()}
 row['glove_center_delta']=list(np.array(points[1])-points[0]);assert np.max(np.abs(row['glove_center_delta']))<0.6
 assert row['before']['floor_y']==row['after']['floor_y'];anchors.append(row)
anchor_path=R/'rear80_anchor_review.json';anchor_path.write_text(json.dumps({'source_generated':str((c.ART.parent/'generated.png').relative_to(c.ROOT)),'source_generated_sha256':sha(c.ART.parent/'generated.png'),'scale_from_native_registration':json.loads((c.ART/'registration.json').read_text('utf8'))['scale'],'source_old_head_or_body_pixels_copied':0,'whole_body_translation':[0,0],'geometric_warping':False,'observations':anchors,'scope':'장갑의 명암면 중심은 실제 엔진 접점 좌표가 아니며 원화 위치 차이를 점검하는 보조치다.194 바닥 폭은1px 증가했지만 바닥 높이와 발목 연결은 유지된다.','runtime_verified':False},ensure_ascii=False,indent=2)+'\n','utf8')
seen=[{'path':str((P/f'{form}_readback_{i:02}.png').relative_to(c.ROOT)),'sha256':sha(P/f'{form}_readback_{i:02}.png'),'actually_viewed':True}for form in('normal','black')for i in range(2)]
visual={'sheets':seen,'scope':'패킹 ARC에서 재추출한 일반·레드 5참조와 대기 비교4장을 직접 열람했다.','observations':['191은 높게 올라간 자세와 양손 연결을 유지하며 머리 층과 치마 명암이 추가됐다.','192의 몸 기울기·무릎 굽힘,194의 양팔 방향과 두 다리가 분리되어 보인다. 새 종아리가 선처럼 가늘거나 잘려 보이는 결함은 발견하지 못했다.','195/196은 같은 새 그림으로 표시되며 뒤로 접힌 무릎·등 주름·머릿결이 이어진다.','레드에서도 내부 명암 구분이 유지된다. 정적 비교이며 연속 실기 전이를 모두 검사한 결과는 아니다.'],'root_final_packed_review_pending':True,'user_accepted':False,'runtime_verified':False}
vp=R/'rear80_visual_review.json';vp.write_text(json.dumps(visual,ensure_ascii=False,indent=2)+'\n','utf8')
audit.update({'visual_review_pending':False,'visual_review':str(vp.relative_to(c.ROOT)),'visual_review_sha256':sha(vp),'anchor_review':str(anchor_path.relative_to(c.ROOT)),'anchor_review_sha256':sha(anchor_path),'limitations':['후면5참조를 추가한 누적80이며 전동작 미술통일·실기·사용자 수용 완료가 아니다.','전신 이동과 옛 머리 덮기 없이 새 원화를 고정 셀에서 등록했다. 장갑 명암면 중심 차이는0.6px 미만이며 발끝 높이는 원래와 같다.','부분VRAM42..49·bank1전체·정적23/24와 모든 비대상 동작은 그대로다. 실제 게임에서 모든 전이를 확인한 것은 아니다.']})
audit_path.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n','utf8')
guard=R/'rin80_guard_checks.json';guard.write_text(json.dumps({'passed':True,'rejections':rejected,'reproducible_twice':True},ensure_ascii=False,indent=2)+'\n','utf8')
j=json.loads((P/'proposal.json').read_text('utf8'));j.update({'independent_report':str(audit_path.relative_to(c.ROOT)),'native_report':str(native_path.relative_to(c.ROOT)),'visual_report':str(vp.relative_to(c.ROOT)),'anchor_report':str(anchor_path.relative_to(c.ROOT)),'guard_report':str(guard.relative_to(c.ROOT)),'ready_for_checkpoint_integration':True,'full_art_unification_complete':False,'root_final_packed_review_pending':True,'limitations':audit['limitations'],'hidden_global_cleanup':False});j['verification']['independent_incremental_counts']=audit['incremental_counts'];(P/'proposal.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
lp=R/'progress_ledger.json';l=json.loads(lp.read_text('utf8'));assert l['prepared_count']==75;(R/'progress_ledger75_snapshot.json').write_bytes(lp.read_bytes());l['new_art_prepared_refs']=sorted(set(l['new_art_prepared_refs'])|set(j['new_art_refs']));assert len(l['new_art_prepared_refs'])==80
l['remaining_refs_in_original_audit']=[r for r in l['remaining_refs_in_original_audit']if r not in j['new_art_refs']];l.update(current_arc=str(P/'PL01_U.ARC'),current_sha256=sha(P/'PL01_U.ARC'),prepared_count=80,latest_scope=j['scope'],latest_proof='final80_readback_audit.json',latest_native='rin80_components_native_checks.json',next_page=None,next_page_scope='다음 후보는 용염인 후면148/150/152/154. 원화/입력은 아직 준비 전이며 선택과 팔·검기 접점 검토가 필요하다.');lp.write_text(json.dumps(l,ensure_ascii=False,indent=2)+'\n','utf8')
frozen={'candidate':j['resource'],'candidate_sha256':j['after_sha256'],'proposal_sha256':sha(P/'proposal.json'),'independent_sha256':sha(audit_path),'native_sha256':sha(native_path),'static_recipe_sha256':sha(P/'static_effects.json'),'guard_sha256':sha(guard),'visual_review_sha256':sha(vp),'anchor_review_sha256':sha(anchor_path),'cumulative_main_refs':80,'incremental_main_refs':5,'bank0_slack':4660,'root_final_packed_review_pending':True,'user_accepted':False,'runtime_verified':False};(P/'FROZEN.json').write_text(json.dumps(frozen,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(frozen))
