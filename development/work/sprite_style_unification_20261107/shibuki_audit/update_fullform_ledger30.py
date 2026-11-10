"""서서사격8의 고정은행 준비/원MIPS와 Ultimate 국소 미완료를 구별한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
need(not(H/'fullform_ledger30.json').exists(),'새 장부 필요')
q=json.loads((H/'fullform_ledger29.json').read_text('utf8'));keys=json.loads((H/'unique_art_keys29.json').read_text('utf8'))
v=json.loads((H/'prepared_standing_fire_base01/verification.json').read_text('utf8'))
n=q['next_generation'];n.update(status='기본/포스85..92 새40층과 기존18참조 순열을 고정은행에 수납. 재현3회/변조15거부, 변경26 원MIPS/GPU와 독립508directory 원MIPS 통과. 독립static/루트최종검토·동결/선택사본1..8 동기화/통합·실기 별도 대기.',arc_written=True,frozen=False,all_visual_review_complete=False,author_actual_final_plates=18,graphics_bank0_remaining_bytes=68,graphics_directory_changed=False,storage_only_refs=v['storage_only_refs'],storage_full_inverse_texels_exact=True,
    candidate=ev(H/'prepared_standing_fire_base01/PL00_U.ARC'),proposal=ev(H/'prepared_standing_fire_base01/proposal.json'),prepared_lock=ev(H/'prepared_standing_fire_base01/PREPARED_LOCK.json'),
    evidence=[ev(H/p)for p in ['standing_fire_locked01/LOCK.json','prepared_standing_fire_base01/verification.json','standing_fire_components_native_checks.json','standing_fire_visual_review02.json','standing_fire_sequence01/report.json','standing_fire_sequence01/browser_verification.json']]+[ev(H.parent/'zero_audit/shibuki_standing_fire_directory_native01/report.json')],
    ultimate85_92='85/89 새4원화 고정등록. 후폼 두 앞팔 흰소매 잔재 확인, 국소 첫편집89는 세로소매잔존/팔하강으로 미채택.89 정확팔영역 가이드 재교정 진행.86/87/90/91/92 원화 미완료.',
    ultimate_source_evidence=[ev(H/p)for p in ['ultimate_standing_fire_inputs01/generation_receipt.json','ultimate_standing_fire_native01/report.json','ultimate_standing_fire_sleeves01/generation_receipt.json','ultimate_standing_fire_sleeves_inspection01/report.json','ultimate_standing89_arm02/input.json']],
    selection_followup='기본/Ultimate85..92 마감 후 최신BR22 UI ea216의1..8 사본을 futurev4 최소범위로 동기화. 기존v2/v3동결/다른선택참조 보존. root helper와 조율, 아직수행안함.')
q['priority_next'][0]['why']=n['status']
for r in q['references']:
    if r['ref']in range(85,93)and r['form']in('base','fourth'):r['in_progress_unapplied_art']=n
q['full_art_unification_complete']=False;write(H/'fullform_ledger30.json',q)
keys.update(scope='BR22에 통합된 동결PL00fdba/PL0226fd 기준.85..92 준비본4fe717은 독립static/루트수용/동결 전이므로 완성집계에 넣지 않음.',source_ledger=ev(H/'fullform_ledger30.json'),next_unfrozen_art=n)
write(H/'unique_art_keys30.json',keys);print(json.dumps({'ledger':ev(H/'fullform_ledger30.json'),'keys':ev(H/'unique_art_keys30.json')}))
