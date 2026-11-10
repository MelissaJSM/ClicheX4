"""후속 검격4를 검토 후보로 동결. 실제 플레이 수용과 구분한다."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
D=Path(__file__).resolve().parent;ROOT=D.parents[2];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.build_sprite_style_unification import check_static_body
from scripts.overhaul_sprites_audit import render
R=D/'rin_extension';P=R/'prepared_saber_followup04';V=R/'saber172_review';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
def dump(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
assert not(P/'FROZEN.json').exists();expected='8bfbf74ea8b14478d5b34906bbedf0e73d7a17689031c804545fb0a4ebac9c54'
proofs={k:R/f for k,f in [('independent','final172_readback_audit.json'),('native','rin172_components_native_checks.json'),('guard','rin172_guard_checks.json')]}
checks={k:json.loads(p.read_text('utf8'))for k,p in proofs.items()};q=json.loads((P/'proposal.json').read_text('utf8'));plan=json.loads((R/'rin172_components.json').read_text('utf8'));browser=json.loads((V/'browser_verification.json').read_text('utf8'))
assert all(j['passed']for j in checks.values())and browser['passed'];assert sha(P/'PL01_U.ARC')==q['after_sha256']==checks['independent']['candidate_sha256']==expected
base=read_disc(ROOT/plan['source_bin'],('PL01_U.ARC',))[0]['PL01_U.ARC'];static=check_static_body(base,(P/'PL01_U.ARC').read_bytes(),q['static_body_patch']);dump(R/'rin172_static_binding_check.json',{'passed':True,'candidate_sha256':expected,'baseline':plan['source_bin'],'result':static})
m=json.loads((V/'manifest.json').read_text('utf8'));paths=[V/name for name in m['sheets']]+[P/f'{form}_readback_00.png'for form in('normal','black')]
old=(R/'prepared_saber_followup03/PL01_U.ARC').read_bytes();new=(P/'PL01_U.ARC').read_bytes();anchors=[]
for n in(236,238,240,242):
 r={'ref':n}
 for label,arc in [('old',old),('new',new)]:
  a=render(arc,0,0,n)[0];ys,xs=np.where(a>0);y=int(ys.max());r[label]={'bottom_y':y-160,'bottom_x_cells':[int(x)-160 for x in np.flatnonzero(a[y])],'bounds':[int(xs.min())-160,int(ys.min())-160,int(xs.max()+1)-160,int(ys.max()+1)-160]}
 assert r['old']['bottom_y']==r['new']['bottom_y'];anchors.append(r)
visual={'sheets':[{'path':rel(p),'sha256':sha(p),'actually_viewed':True}for p in paths],
 'observations':['실제 패킹 일반·레드2장, 원순서 스트립2장, 원검기 합성2장을 직접 열람했다.236/238/240/242의 머릿결·커프·앞치마·부츠 내부 명암이 새 대기 및 앞선 검격과 가까워졌다.',
 '238/240/242는 새 원화 전신을 x+2/+1/+3px 정합했다.236의 앞 손·커프는 y−1, 뒤 손목·커프는 x+1/y−1 강체 정합했다. 원화의 목·몸통은 보존했고 옛 몸체나 임의 색은 덮지 않았다.',
 '네 자세의 원래 최저 발끝 y를 보존했다. 원검기237/239/241/243을 같은 원점에서 합성해 손/커프와 새로운 큰 틈이 생기지 않는 것을 확인했다. 동적 무기 객체의 위치·CLUT·가림을 재현한 검사는 아니다.',
 '원표92에서230/232/234의 이전 새 자세와236..242를 함께 비교했다. 마무리244/246은 구형 상세가 남아 다음 제작 대상으로 유지한다. 전수 미술 통일 또는 실제 플레이 수용 완료가 아니다.'],
 'floor_anchor_checks':anchors,'limitations':m['limitations'],'browser_verification':rel(V/'browser_verification.json'),'browser_scope':'오프라인20표 위치·정수4배·JS오류 없음. 연속 영상 육안 및 실제 게임 미실행.',
 'root_registered_art_review_pending':False,'root_final_packed_review_pending':True,'root_registered_review_source':'부모 /root가 followup04_registered_v1 일반 비교를 실제 열람하고 세부 및 손접점 방향 수용. checkpoint21 기록.','user_accepted':False,'runtime_verified':False}
vp=V/'visual_review.json';dump(vp,visual)
audit=checks['independent'];audit.update(visual_review=rel(vp),visual_review_sha256=sha(vp),visual_review_pending=False,root_final_packed_review_pending=True,static_binding_proof=rel(R/'rin172_static_binding_check.json'));dump(proofs['independent'],audit)
q.update(source_bin=plan['source_bin'],source_bin_sha256=plan['source_sha256'],integration_baseline_arc_sha256=plan['resources']['PL01_U.ARC']['before'],incremental_parent_arc_sha256=q['source_arc_sha256'],independent_report=rel(proofs['independent']),native_report=rel(proofs['native']),guard_report=rel(proofs['guard']),visual_report=rel(vp),ready_for_checkpoint_integration=False,frozen_candidate=True,root_art_review_pending=True,full_art_unification_complete=False,scope='지상검격236/238/240/242 새4원화. 이전168·검기4참조의소비40타일·부분VRAM·정적몸체 보존. 독립 reader·원MIPS·거부·자체 정적미술 검토통과. root 최종패킹 검토 및 실제 플레이/사용자 수용 별도.');dump(P/'proposal.json',q)
lp=R/'progress_ledger.json';ledger=json.loads(lp.read_text('utf8'));assert ledger['prepared_count']==168;(R/'progress_ledger168_snapshot.json').write_bytes(lp.read_bytes());ledger['new_art_prepared_refs']=sorted(set(ledger['new_art_prepared_refs'])|set(q['new_art_refs']));assert len(ledger['new_art_prepared_refs'])==172;ledger['remaining_refs_in_original_audit']=[r for r in ledger['remaining_refs_in_original_audit']if r not in q['new_art_refs']];ledger.update(current_arc=str(P/'PL01_U.ARC'),current_sha256=expected,prepared_count=172,latest_scope=q['scope'],latest_proof='final172_readback_audit.json',latest_native='rin172_components_native_checks.json',next_page=None,next_page_scope='지상검격244/246, 이후 빙열참·공중회전 등 전수장부의 미완료동작 보완.');dump(lp,ledger)
f={'candidate':rel(P/'PL01_U.ARC'),'candidate_sha256':expected,'proposal_sha256':sha(P/'proposal.json'),'source_bin_sha256':plan['source_sha256'],'integration_baseline_arc_sha256':plan['resources']['PL01_U.ARC']['before'],'incremental_parent_sha256':q['source_arc_sha256'],'static_recipe_sha256':sha(P/'static_effects.json'),'proofs':{k:{'path':rel(p),'sha256':sha(p)}for k,p in proofs.items()},'visual_review_sha256':sha(vp),'anchor_registration_sha256':sha(R/'saber_followup04_registered_v1/registration.json'),'cumulative_main_refs':172,'incremental_main_refs':4,'shared_support_refs_preserved':4,'shared_entire_consumed_tiles_preserved':40,'bank0_slack':2842,'bank1_slack':7242,'hidden_global_cleanup':False,'root_art_review_pending':True,'user_accepted':False,'runtime_verified':False};dump(P/'FROZEN.json',f);print(json.dumps(f))
