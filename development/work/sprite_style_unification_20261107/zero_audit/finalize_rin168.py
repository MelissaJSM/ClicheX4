"""통합 전 검토 후보168을 동결한다. 실제 게임/사용자 수용은 별도다."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[2];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.build_sprite_style_unification import check_static_body
from scripts.overhaul_sprites_audit import render
R=D/'rin_extension';P=R/'prepared_saber_followup03';V=R/'saber168_review';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
def dump(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
assert not(P/'FROZEN.json').exists();expected='ef8a0364f520a70b17ed995e509e5985b19bae618444200ec25cf9016341b5d8'
proofs={k:R/f for k,f in [('independent','final168_readback_audit.json'),('native','rin168_components_native_checks.json'),('guard','rin168_guard_checks.json')]}
checks={k:json.loads(p.read_text('utf8'))for k,p in proofs.items()};q=json.loads((P/'proposal.json').read_text('utf8'));plan=json.loads((R/'rin168_components.json').read_text('utf8'));browser=json.loads((V/'browser_verification.json').read_text('utf8'));assert all(j['passed']for j in checks.values())and browser['passed'];assert sha(P/'PL01_U.ARC')==q['after_sha256']==checks['independent']['candidate_sha256']==expected
base=read_disc(ROOT/plan['source_bin'],('PL01_U.ARC',))[0]['PL01_U.ARC'];static=check_static_body(base,(P/'PL01_U.ARC').read_bytes(),q['static_body_patch']);dump(R/'rin168_static_binding_check.json',{'passed':True,'candidate_sha256':expected,'baseline':plan['source_bin'],'result':static})
m=json.loads((V/'manifest.json').read_text('utf8'));paths=[V/name for name in m['sheets']]+[P/f'{form}_readback_{n:02}.png'for form in('normal','black')for n in(0,1)]
old=(R/'prepared_air_saber02/PL01_U.ARC').read_bytes();new=(P/'PL01_U.ARC').read_bytes();anchors=[]
for n in(229,230,232,234):
 r={'ref':n}
 for label,arc in [('old',old),('new',new)]:
  a=render(arc,0,0,n)[0];ys,xs=np.where(a>0);y=int(ys.max());r[label]={'bottom_y':y-160,'bottom_x_cells':[int(x)-160 for x in np.flatnonzero(a[y])],'bounds':[int(xs.min())-160,int(ys.min())-160,int(xs.max()+1)-160,int(ys.max()+1)-160]}
 assert r['old']['bottom_y']==r['new']['bottom_y'];anchors.append(r)
visual={'sheets':[{'path':rel(p),'sha256':sha(p),'actually_viewed':True}for p in paths],
 'observations':['실제 패킹 일반·레드4장, 원순서 스트립8장, 원검기 합성2장을 직접 열람했다.229/230/232/234와 같은몸체b1_132에서 머릿결·눈·커프·앞치마·부츠 세부가 개선됐다.',
 '생성된 전신의 수평 이동을229/230/232/234 각각+1/+6/+2/+6px 정합했다.229는 발바닥 일괄정합으로 위로 뜬 목·양손을2px 되돌리고 새부츠 하단만2px 위로 등록했다. 새 옷을 과거 몸이나 머리로 덮지 않았다.',
 '네 키의 원래 최저 발끝 y를 보존했다.지상 검격231/233/235의 기존 검기 마스크를 새몸과 함께 보았고 손/커프 부근의 새 큰 틈은 보이지 않는다.이는 정적 동원점 접점 비교이며 게임의 동적 객체 위치·가림 검증과 다르다.',
 '229와b1_132는 이전부터 전신 표시가 완전동일함을 검증한 뒤 같은 새 원화를 등록했다. 빙열참/회전 진입의 원표도 별도 스트립으로 보았으며 다음133..137·161..175의 옛 세부 단순화는 후속 작업으로 남긴다.',
 '지상236/238/240/242/244/246은 여전히 미제작 범위다. 전수 미술 통일이나 실제 플레이 수용 완료로 기록하지 않는다.'],
 'floor_anchor_checks':anchors,'limitations':m['limitations'],'browser_verification':rel(V/'browser_verification.json'),'browser_scope':'오프라인82표 위치·정수4배·JS오류 없음. 연속 영상 육안 및 실제 게임 미실행.',
 'root_registered_art_review_pending':False,'root_final_packed_review_pending':True,'root_registered_review_source':'부모 /root의 saber_followup03_registered_v1 네 행 직접 열람 및 방향 수용 메시지','user_accepted':False,'runtime_verified':False}
vp=V/'visual_review.json';dump(vp,visual)
audit=checks['independent'];audit.update(visual_review=rel(vp),visual_review_sha256=sha(vp),visual_review_pending=False,root_final_packed_review_pending=True,static_binding_proof=rel(R/'rin168_static_binding_check.json'));dump(proofs['independent'],audit)
q.update(source_bin=plan['source_bin'],source_bin_sha256=plan['source_sha256'],integration_baseline_arc_sha256=plan['resources']['PL01_U.ARC']['before'],incremental_parent_arc_sha256=q['source_arc_sha256'],independent_report=rel(proofs['independent']),native_report=rel(proofs['native']),guard_report=rel(proofs['guard']),visual_report=rel(vp),ready_for_checkpoint_integration=False,frozen_candidate=True,root_art_review_pending=True,full_art_unification_complete=False,scope='공중검격 마지막229·지상230/232/234와정확같은몸b1_132까지5참조.이전163·검기·지원몸체·부분VRAM·정적몸체 보존.독립 reader·원MIPS·거부·자체 정적미술 검토통과. root 최종패킹 검토 및 실제 플레이/사용자 수용은 별도.');dump(P/'proposal.json',q)
lp=R/'progress_ledger.json';ledger=json.loads(lp.read_text('utf8'));assert ledger['prepared_count']==163;(R/'progress_ledger163_snapshot.json').write_bytes(lp.read_bytes());ledger['new_art_prepared_refs']=sorted(set(ledger['new_art_prepared_refs'])|set(q['new_art_refs']));assert len(ledger['new_art_prepared_refs'])==168;ledger['remaining_refs_in_original_audit']=[r for r in ledger['remaining_refs_in_original_audit']if r not in q['new_art_refs']];ledger.update(current_arc=str(P/'PL01_U.ARC'),current_sha256=expected,prepared_count=168,latest_scope=q['scope'],latest_proof='final168_readback_audit.json',latest_native='rin168_components_native_checks.json',next_page=None,next_page_scope='지상검격236/238/240/242/244/246, 이후 빙열참·공중회전 등 전수장부의 미완료동작을 보완한다.');dump(lp,ledger)
f={'candidate':rel(P/'PL01_U.ARC'),'candidate_sha256':expected,'proposal_sha256':sha(P/'proposal.json'),'source_bin_sha256':plan['source_sha256'],'integration_baseline_arc_sha256':plan['resources']['PL01_U.ARC']['before'],'incremental_parent_sha256':q['source_arc_sha256'],'static_recipe_sha256':sha(P/'static_effects.json'),'proofs':{k:{'path':rel(p),'sha256':sha(p)}for k,p in proofs.items()},'visual_review_sha256':sha(vp),'anchor_registration_sha256':sha(R/'saber_followup03_registered_v1/registration.json'),'cumulative_main_refs':168,'incremental_main_refs':5,'shared_support_refs_preserved':6,'shared_entire_consumed_tiles_preserved':32,'bank0_slack':2884,'bank1_slack':7242,'hidden_global_cleanup':False,'root_art_review_pending':True,'user_accepted':False,'runtime_verified':False};dump(P/'FROZEN.json',f);print(json.dumps(f))
