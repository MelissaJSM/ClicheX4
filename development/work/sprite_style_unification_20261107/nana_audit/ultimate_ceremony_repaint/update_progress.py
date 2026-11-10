"""현재 등장 제작 상태와 미채택 원화를 실제 근거에 연결한다."""
from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def rec(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def main():
    runtime=ROOT/'work/sprite_style_unification_20261107/runtime/nana_ultimate_hurt19_summary.json';r=json.loads(runtime.read_text('utf8'))
    m={'parent_arc':rec(N/'ultimate_hurt_repaint/packed_hurt_candidate_v1/PL02_U.ARC'),'parent_frozen':rec(N/'ultimate_hurt_repaint/packed_hurt_candidate_v1/FROZEN.json'),'parent_runtime':rec(runtime),'parent_runtime_scope':{'forms':['ultimate_after'],'refs':r['verified_new_references'],'actual_captures':r['actual_captures'],'root_viewed_boards':r['root_viewed_boards'],'scope':'루트 RN19 실기.앞폼/106..114/부분전조합 실기까지 확대하지 않음.'},
       'production':{'candidate_body_keys':[133,135,136,137],'forms':['ultimate_before','ultimate_after'],'source_pages':[rec(D/'first_v1/generation.json'),rec(D/'second_v1/generation.json')],'fixed_registrations':[rec(D/'first_registered_v2/registration.json'),rec(D/'second_registered_v1/registration.json')],'semantic_candidate':rec(D/'costume_pair_probe_v3/manifest.json'),'effect_probe':rec(D/'effect_probe_v1/manifest.json'),'limitations':['133 전체+1y 눈정합은 바닥+1y여서 미채택.원점 고정 원화 사용.','135 원 감긴눈→새 열린눈은 준비동작의 표현 변경으로 기록,루트 정적 방향검토와 최종원순서 분리.','133/135 재킷 경계6셀은 실제 새원화 점유.124~.347 검정표본을 등록한 미술후보.임의 색채움/맨팔 알파클립 없음.','136/137 원효과46px씩 원위치 재합성,새 몸과겹침12/12 및32/27픽셀.관통 여부 최종원순서검토 전.','각 자세의 사랑이/손 소유를 역사 원화와 별도 대조 중.정본무기 정합은 미완료.']},
       'rejected_source':{'ref':138,'source':rec(D/'settle_v1/generation.json'),'registration':rec(D/'settle_registered_v1/registration.json'),'decision':'미채택: 위로 든 권총을 긴 귀로 오인한 입력해석 때문에 팔을 낮춘 그림 생성.발바닥/단일연결 검사 통과가 미술수용을 뜻하지 않는다.','correction_input':rec(D/'raised138_inputs_v1/manifest.json'),'new_correction_source':None},
       'relationship_proofs':[rec(ROOT/'work/sprite_style_unification_20261107/zero_audit/nana_ultimate_ceremony_sources01/report.json'),rec(ROOT/'work/sprite_style_unification_20261107/zero_audit/nana_ultimate_ceremony_sources02/coordinate_report.json'),rec(ROOT/'work/sprite_style_unification_20261107/zero_audit/nana_ultimate_ceremony_sources03/report.json')],
       'linked_scope':{'new_bodies':[133,135,136,137,138],'linked_body_or_silhouette':[130,131,134,139,141],'preserve':[132,140,142,156,157,158],'remaining_later':[204,205,206,207],'policy':'138→139는 역사 수용Nana의 y−1 관계,원US동일그림이라 주장하지 않는다.141은idle0와원먼지로 복귀 연동,130은 원shell가림 유지.156..158은 현재상세/효과 출처 확인 후 이번새몸제작에서 보존 검토.'},
       'native_prepared_arc':None,'game_files_written':False,'all_nana_style_complete':False,'all_four_characters_complete':False}
    if (D/'raised138_v1/generation.json').exists():
        m['rejected_source']['new_correction_source']=rec(D/'raised138_v1/generation.json')
        m['raised138_local_candidate']=rec(D/'raised138_local_probe_v1/manifest.json')
        m['raised138_stage']='교정 원화와 의미영역 국소등록 완료.새 얼굴/다리/반대팔은 보존하고 위로 든 사랑이/팔 복원.원손/정본총 및 공통층 정합 미완료.'
    m['actual_viewed_current_sheets']=[rec(D/p)for p in('second_registered_v1/comparison_1.png','second_registered_v1/comparison_2.png','semantic_grids_v1/grid_133.png','semantic_grids_v1/grid_135.png','semantic_grids_v1/grid_136.png','semantic_grids_v1/grid_137.png','costume_pair_probe_v1/comparison_1.png','costume_pair_probe_v1/comparison_2.png','costume_pair_probe_v2/comparison_1.png','costume_pair_probe_v3/comparison_1.png','costume_pair_probe_v3/comparison_2.png','settle_registered_v1/comparison.png','effect_probe_v1/comparison_1.png','effect_probe_v1/comparison_2.png','raised138_registered_v1/comparison.png','raised138_local_probe_v1/comparison.png')]
    m['production']['candidate_body_keys']=[133,135,136,137,138]
    m['production']['limitations']=[
      '133 전체+1y 눈정합은 바닥+1y여서 미채택. 원점 고정 원화 사용.',
      '135 감긴눈→열린눈은 준비동작 표현 변경. 정적 방향검토와 최종원순서 구분.',
      '136/137 역사 흰선46px는 총구 효과가 아니며 원좌표 보존.',
      '직접 선행133/135/136/137 원화에서 사랑이가 누락됐음을 역사대조로 확인. 새 손 국소 원화와 정본85의20texel/8px 총열로 복원. 옛 검정 손 전체를 권총으로 복사하지 않음.',
      '138 최초 낮춘팔 원화는 미채택. 국소 raised138 새팔을 통해 위로 든 권총 자세로 복귀.',
      '138 하체 밝은 면/윤곽 손실 확인 후 새 종아리 국소 원화42e56f28로 보완. 대상외·신발/권총 exact; 최종 ARC/원순서는 후속.']
    m['pistol_sources']=[rec(D/f'pistol_hands_{g}_v1/generation.json')for g in('a','b')]
    m['canonical_weapon_candidate']=rec(D/'canonical_cases_probe_v2/manifest.json')
    m['canonical_weapon_v1_rejected']='총과 손이 분리된 첫 정합은 미채택. v2 새손 기준으로 변경.'
    m['common_hands_candidate']=rec(D/'common_hands_probe_v1/manifest.json')
    m['raised138_stage']='위로 든 새 팔·정본 권총·양폼 공통부 등록 완료. 가는 종아리는 다음 국소 원화로 보완.'
    m['settle_body_audit']=rec(D/'settle_body_audit_v1/report.json')
    m['settle_legs_source']=rec(D/'settle_legs_v1/generation.json')
    m['settle_legs_candidate']=rec(D/'settle_legs_registered_v1/manifest.json')
    m['linked_target_candidate']=rec(D/'arrival_targets_probe_v2/manifest.json')
    m['packing_memory_probe']=rec(D/'packing_probe_v1/verification.json')
    m['packing_stage']='10참조50층의 메모리 패킹/512raw·1140층/320대상RGBA 통과, 아직 ARC 파일 미작성.131/132만 저장스트림 분리하며132decodedraw/표시/조립 불변.'
    m['relationship_proofs'] += [rec(ROOT/'work/sprite_style_unification_20261107/zero_audit'/p)for p in('nana_ultimate_ceremony_pistol_sources01/report.json','nana_arrival141_dust01/report.json')]
    m['actual_viewed_current_sheets'] += [rec(D/p)for p in('canonical_cases_probe_v2/comparison_1.png','canonical_cases_probe_v2/comparison_2.png','canonical_cases_probe_v2/comparison_3.png','common_hands_probe_v1/comparison_1.png','common_hands_probe_v1/comparison_2.png','common_hands_probe_v1/comparison_3.png','settle_body_audit_v1/before_comparison.png','settle_body_audit_v1/after_comparison.png','settle_legs_inputs_v1/lower_body_comparison.png','settle_legs_registered_v1/comparison.png')]
    ladder=ROOT/'work/sprite_style_unification_20261107/root_nana_ladder/packed_ladder07/FROZEN.json'
    if ladder.exists():m['other_owner_basic_fourth_ladder']={'frozen':rec(ladder),'scope':'루트 소유. 새8몸체×2+새사격2팔×2+반전4×2의14참조. RN20 통합/기술검증은루트보고,실기미실행. 내Ultimate등장제작수와혼합안함.'}
    frozen=D/'packed_arrival_candidate_v1/FROZEN.json'
    if frozen.exists():
        m['native_prepared_arc']=rec(frozen.parent/'PL02_U.ARC');m['frozen']=rec(frozen)
        m['packing_stage']='등장10 최종 동결. 50층/7296RGBA/원MIPS/GPU/독립320부분/별도프로세스 재현8거부/114canvas 및 root107·110 실제열람 완료. 게임 통합/실기는 루트 후속.'
        m['production']['limitations']=[
          '133 원점 고정 원화 사용, 전체+1y 후보 미채택.',
          '135 감긴눈→열린눈은 준비동작 표현 변경이며 원순서 정적판으로 검토.',
          '136/137 흰선46px씩 역사 원좌표 보존. 총구 효과로 해석하지 않음.',
          '133/135/136/137 누락 권총은 최초 원화 자세+새손+정본85로 복원.',
          '138 낮춘팔 후보와 성긴 종아리 후보는 미채택. 위로 든 새팔·고정권총·42e56f28 국소하체를 최종 사용.',
          '131/132 저장스트림 분리에도132 raw/count/조립/표시 보존. 실제 게임 이벤트는 별도.']
        m['raised138_stage']='위로 든 새팔·정본권총·양폼 공통부 및 종아리 국소 보완을 최종 ARC에 반영해 동결.'
        m['validation']=[rec(p)for p in(frozen.parent/'verification.json',frozen.parent/'source_reconstruction.json',frozen.parent/'reproduction.json',D/'native_components_v1_native_checks.json',D/'native_cycle_v1/verification.json')]
    (D/'production_status.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({'path':str(D/'production_status.json'),'sha256':sha(D/'production_status.json')}))
if __name__=='__main__':main()
