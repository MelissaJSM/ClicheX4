"""후속 검격4를 검토 후보로 동결. 실제 플레이 수용과 구분한다."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
D=Path(__file__).resolve().parent;ROOT=D.parents[2];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.build_sprite_style_unification import check_static_body
from scripts.overhaul_sprites_audit import render
R=D/'rin_extension';P=R/'prepared_saber_followup05_v2';V=R/'saber180_review';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
def dump(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
assert not(P/'FROZEN.json').exists();expected='0f6665a4cca930edf7e90351b8a8ac044b23326b19836eaa52d473b1b2390941'
proofs={k:R/f for k,f in [('independent','final180_readback_audit.json'),('native','rin180_components_native_checks.json'),('guard','rin180_guard_checks.json')]}
checks={k:json.loads(p.read_text('utf8'))for k,p in proofs.items()};q=json.loads((P/'proposal.json').read_text('utf8'));plan=json.loads((R/'rin180_components.json').read_text('utf8'));browser=json.loads((V/'browser_verification.json').read_text('utf8'))
assert all(j['passed']for j in checks.values())and browser['passed'];assert sha(P/'PL01_U.ARC')==q['after_sha256']==checks['independent']['candidate_sha256']==expected
base=read_disc(ROOT/plan['source_bin'],('PL01_U.ARC',))[0]['PL01_U.ARC'];static=check_static_body(base,(P/'PL01_U.ARC').read_bytes(),q['static_body_patch']);dump(R/'rin180_static_binding_check.json',{'passed':True,'candidate_sha256':expected,'baseline':plan['source_bin'],'result':static})
m=json.loads((V/'manifest.json').read_text('utf8'));paths=[V/name for name in m['sheets']]+[P/f'{form}_readback_{n:02}.png'for form in('normal','black')for n in(0,1)]
old=(R/'prepared_saber_followup04/PL01_U.ARC').read_bytes();new=(P/'PL01_U.ARC').read_bytes();anchors=[]
for n in(244,246):
 r={'ref':n}
 for label,arc in [('old',old),('new',new)]:
  a=render(arc,0,0,n)[0];ys,xs=np.where(a>0);y=int(ys.max());r[label]={'bottom_y':y-160,'bottom_x_cells':[int(x)-160 for x in np.flatnonzero(a[y])],'bounds':[int(xs.min())-160,int(ys.min())-160,int(xs.max()+1)-160,int(ys.max()+1)-160]}
 assert r['old']['bottom_y']==r['new']['bottom_y'];anchors.append(r)
visual={'sheets':[{'path':rel(p),'sha256':sha(p),'actually_viewed':True}for p in paths],
 'observations':['실제 패킹 일반·레드4장, 원순서 스트립10장, 원검기 합성2장을 직접 열람했다. 최종본의 스트립8장+검기2장은 앞선179 검토본에서 실제 열람한 이미지와 파일 바이트가 같고, 바뀐 섬광 포함 스트립2장은 최종본으로 다시 열람했다.',
 '244/246의 머릿결·커프·가슴 리본·앞치마·부츠 상세가 이전 새 검격과 이어진다. 전신 좌표는 최초 등록 그대로 보존했고246에서 원화의 실제 청록29샘플이 대응한 눈1도트를 복원했다. 옛 몸이나 임의 색 덮기는 없다.',
 '246과 전신이 같던 b1_87/95/96/98/99도 같은 새 몸체로 확장했다. 부모 b1_88이87의 알파에4방향1px흰테두리를 두는 섬광임을 정확 재현한 뒤 새87로 동기화했다. 이를 빠뜨렸던179 첫패킹은 미채택이다.',
 '두 키의 원래 최저 발끝 y를 유지했고245 잔여 검기와 새244의 손 접점도 정적 동원점에서 확인했다. 원표92 전체 및95/96/98/101의 동일 자세 사용 구간을 비교했다. 빙열참·회전의 아직 단순한 몸체와 준비86 등은 후속이며 전수 완성/실기 수용 주장은 하지 않는다.'],
 'floor_anchor_checks':anchors,'limitations':m['limitations'],'browser_verification':rel(V/'browser_verification.json'),'browser_scope':'오프라인228표 위치·정수4배·JS오류 없음. 연속 영상 육안 및 실제 게임 미실행.',
 'reused_byte_exact_visual_proof':rel(V/'reused_visual_proof.json'),'root_registered_art_review_pending':True,'root_final_packed_review_pending':True,'user_accepted':False,'runtime_verified':False}
vp=V/'visual_review.json';dump(vp,visual)
audit=checks['independent'];audit.update(visual_review=rel(vp),visual_review_sha256=sha(vp),visual_review_pending=False,root_final_packed_review_pending=True,static_binding_proof=rel(R/'rin180_static_binding_check.json'));dump(proofs['independent'],audit)
q.update(source_bin=plan['source_bin'],source_bin_sha256=plan['source_sha256'],integration_baseline_arc_sha256=plan['resources']['PL01_U.ARC']['before'],incremental_parent_arc_sha256=q['source_arc_sha256'],independent_report=rel(proofs['independent']),native_report=rel(proofs['native']),guard_report=rel(proofs['guard']),visual_report=rel(vp),ready_for_checkpoint_integration=False,frozen_candidate=True,root_art_review_pending=True,full_art_unification_complete=False,scope='지상검격244/246 새2원화와정확동일5사본, 원규칙흰섬광88까지8참조. 이전172·지원6참조소비21타일·부분VRAM·정적몸체 보존. 독립reader·원MIPS·9거부·자체정적미술 통과. root미술 및실기/사용자수용 별도.');dump(P/'proposal.json',q)
lp=R/'progress_ledger.json';ledger=json.loads(lp.read_text('utf8'));assert ledger['prepared_count']==172;(R/'progress_ledger172_snapshot.json').write_bytes(lp.read_bytes());ledger['new_art_prepared_refs']=sorted(set(ledger['new_art_prepared_refs'])|set(q['new_art_refs']));assert len(ledger['new_art_prepared_refs'])==180;ledger['remaining_refs_in_original_audit']=[r for r in ledger['remaining_refs_in_original_audit']if r not in q['new_art_refs']];ledger.update(current_arc=str(P/'PL01_U.ARC'),current_sha256=expected,prepared_count=180,latest_scope=q['scope'],latest_proof='final180_readback_audit.json',latest_native='rin180_components_native_checks.json',next_page=None,next_page_scope='지상검격244/246, 이후 빙열참·공중회전 등 전수장부의 미완료동작 보완.');dump(lp,ledger)
f={'candidate':rel(P/'PL01_U.ARC'),'candidate_sha256':expected,'proposal_sha256':sha(P/'proposal.json'),'source_bin_sha256':plan['source_sha256'],'integration_baseline_arc_sha256':plan['resources']['PL01_U.ARC']['before'],'incremental_parent_sha256':q['source_arc_sha256'],'static_recipe_sha256':sha(P/'static_effects.json'),'proofs':{k:{'path':rel(p),'sha256':sha(p)}for k,p in proofs.items()},'visual_review_sha256':sha(vp),'anchor_registration_sha256':sha(R/'saber_followup05_registered_v1/registration.json'),'cumulative_main_refs':180,'incremental_main_refs':8,'body_refs':7,'derived_flash_refs':1,'shared_support_refs_preserved':6,'shared_entire_consumed_tiles_preserved':21,'bank0_slack':2766,'bank1_slack':7328,'hidden_global_cleanup':False,'root_art_review_pending':True,'user_accepted':False,'runtime_verified':False};dump(P/'FROZEN.json',f);print(json.dumps(f))
