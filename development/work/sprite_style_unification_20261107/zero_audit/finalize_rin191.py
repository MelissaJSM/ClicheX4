"""빙열참11 후보의 검수 범위를 기록한다. 실제 플레이 수용과 구분한다."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
D=Path(__file__).resolve().parent;ROOT=D.parents[2];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.build_sprite_style_unification import check_static_body
from scripts.overhaul_sprites_audit import render
R=D/'rin_extension';P=R/'prepared_ice01';V=R/'ice191_review';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
def dump(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
assert not(P/'FROZEN.json').exists();expected='70b483ba78dedefa9c4af45c9b4c5fe4fb8ef915290a4c92c1dd5dea6b0b01d8'
proofs={k:R/f for k,f in [('independent','final191_readback_audit.json'),('native','rin191_components_native_checks.json'),('guard','rin191_guard_checks.json')]}
checks={k:json.loads(p.read_text('utf8'))for k,p in proofs.items()};q=json.loads((P/'proposal.json').read_text('utf8'));plan=json.loads((R/'rin191_components.json').read_text('utf8'));browser=json.loads((V/'browser_verification.json').read_text('utf8'))
assert all(j['passed']for j in checks.values())and browser['passed'];assert sha(P/'PL01_U.ARC')==q['after_sha256']==checks['independent']['candidate_sha256']==expected
base=read_disc(ROOT/plan['source_bin'],('PL01_U.ARC',))[0]['PL01_U.ARC'];static=check_static_body(base,(P/'PL01_U.ARC').read_bytes(),q['static_body_patch']);dump(R/'rin191_static_binding_check.json',{'passed':True,'candidate_sha256':expected,'baseline':plan['source_bin'],'result':static})
m=json.loads((V/'manifest.json').read_text('utf8'));paths=[V/name for name in m['sheets']]+[P/f'{form}_readback_{n:02}.png'for form in('normal','black')for n in(0,1,2)]
old=(R/'prepared_saber_followup05_v2/PL01_U.ARC').read_bytes();new=(P/'PL01_U.ARC').read_bytes();anchors=[]
for n in(133,135,138,139):
 row={'ref':n}
 for label,arc in [('old',old),('new',new)]:
  a=render(arc,1,5,n)[0];ys,xs=np.where(a>0);y=int(ys.max());row[label]={'bottom_y':y-160,'bottom_x_cells':[int(x)-160 for x in np.flatnonzero(a[y])],'bounds':[int(xs.min())-160,int(ys.min())-160,int(xs.max()+1)-160,int(ys.max()+1)-160]}
 assert row['old']['bottom_y']==row['new']['bottom_y'];anchors.append(row)
visual={'sheets':[{'path':rel(p),'sha256':sha(p),'actually_viewed':True}for p in paths],
 'observations':['패킹 일반·레드6장 및 원표97/98 순서의 일반·레드 스트립4장을 실제 열람했다.',
 '133/135의 머릿결·작은 청록 눈·들린 커프와 치마 주름이 선명해졌다.138/139의 머리와 앞치마 경계·부츠 음영도 기존 새 지상 검격과 이어진다. 옛 머리나 몸을 덮지 않았다.',
 '135/139의 전신 x+2,133/135 새 장갑/도구 y+1,138 새 구두 x−1로 접점을 정합했다. 실제 원화 청록18/20표본을133/135 눈 한 셀로 살렸다. 네 키의 원래 최저 발끝 y는 동일하다.',
 '133의 정확 y−1 사본134/136/137 및139의 동일 사본140..143을 함께 바꿨다. 공중 반복133..137와 착지138→139..143→98/95/87 회복 구간에서 새 몸체와 선행 수용 몸체 사이 뚜렷한 단절을 발견하지 못했다.',
 '빙열참 무기 객체의 별도 파츠/VRAM과 실제 이동·타격은 재현하지 않았다. 이번 비교는 몸체 원표97/98이다.144 및 공중회전 등 남은 장부는 계속 보완한다.'],
 'floor_anchor_checks':anchors,'limitations':m['limitations'],'browser_verification':rel(V/'browser_verification.json'),'browser_scope':'오프라인42표 위치·정수4배·JS오류 없음. 연속 영상 육안 및 실제 게임 미실행.',
 'root_registered_art_review_pending':True,'root_final_packed_review_pending':True,'user_accepted':False,'runtime_verified':False}
vp=V/'visual_review.json';dump(vp,visual)
audit=checks['independent'];audit.update(visual_review=rel(vp),visual_review_sha256=sha(vp),visual_review_pending=False,root_final_packed_review_pending=True,static_binding_proof=rel(R/'rin191_static_binding_check.json'));dump(proofs['independent'],audit)
q.update(source_bin=plan['source_bin'],source_bin_sha256=plan['source_sha256'],integration_baseline_arc_sha256=plan['resources']['PL01_U.ARC']['before'],incremental_parent_arc_sha256=q['source_arc_sha256'],independent_report=rel(proofs['independent']),native_report=rel(proofs['native']),guard_report=rel(proofs['guard']),visual_report=rel(vp),ready_for_checkpoint_integration=False,frozen_candidate=True,root_art_review_pending=True,full_art_unification_complete=False,scope='빙열참133/135/138/139 새4원화와 정확 동일·평행 사본7까지11참조. 이전180·지원132의 소비12타일·부분VRAM8·정적몸체 보존. 독립reader·원MIPS·8거부·자체 정적미술 통과. 루트 미술 및 실제빙열참/사용자 수용 별도.');dump(P/'proposal.json',q)
lp=R/'progress_ledger.json';ledger=json.loads(lp.read_text('utf8'));assert ledger['prepared_count']==180;(R/'progress_ledger180_snapshot.json').write_bytes(lp.read_bytes());ledger['new_art_prepared_refs']=sorted(set(ledger['new_art_prepared_refs'])|set(q['new_art_refs']));assert len(ledger['new_art_prepared_refs'])==191;ledger['remaining_refs_in_original_audit']=[r for r in ledger['remaining_refs_in_original_audit']if r not in q['new_art_refs']]
ledger['limitations']=[s for s in ledger['limitations']if '52참조 전체'not in s and '남은263'not in s]+['새 원화 누적191의 전수 실제 플레이와 사용자 최종 수용은 미확인이다. 단계별 root 정적미술 검토는 외부 기록으로 구분한다.','원래 장부315에는 중복·대기·일부 효과 오분류가 있어 남은 참조 수는 필요한 새 그림 수가 아니다.']
ledger.update(current_arc=str(P/'PL01_U.ARC'),current_sha256=expected,prepared_count=191,latest_scope=q['scope'],latest_proof='final191_readback_audit.json',latest_native='rin191_components_native_checks.json',next_page=None,next_page_scope='빙열참144 별도 자세와 회전161/163/167/171 대표, 이후 전수장부 잔여를 보완한다.');dump(lp,ledger)
f={'candidate':rel(P/'PL01_U.ARC'),'candidate_sha256':expected,'proposal_sha256':sha(P/'proposal.json'),'source_bin_sha256':plan['source_sha256'],'integration_baseline_arc_sha256':plan['resources']['PL01_U.ARC']['before'],'incremental_parent_sha256':q['source_arc_sha256'],'static_recipe_sha256':sha(P/'static_effects.json'),'proofs':{k:{'path':rel(p),'sha256':sha(p)}for k,p in proofs.items()},'visual_review_sha256':sha(vp),'anchor_registration_sha256':sha(R/'ice_registered_v1/registration.json'),'cumulative_main_refs':191,'incremental_main_refs':11,'body_refs':11,'shared_support_refs_preserved':1,'shared_entire_consumed_tiles_preserved':12,'bank0_slack':2766,'bank1_slack':6816,'hidden_global_cleanup':False,'root_art_review_pending':True,'user_accepted':False,'runtime_verified':False};dump(P/'FROZEN.json',f);print(json.dumps(f))
