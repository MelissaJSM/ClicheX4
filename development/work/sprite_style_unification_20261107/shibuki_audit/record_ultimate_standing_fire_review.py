"""고정 준비본의 실제 열람 및 별도 원순서 증거를 추가한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write

def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}

def main():
    d=H/'prepared_standing_fire_ultimate01';s=H/'ultimate_standing_fire_sequence01'
    need(sha((d/'PL02_U.ARC').read_bytes())=='1f271aeaee7c65a938a6a09116bc8b2317f7f138465f563d4c6cc1f3704ee1ad','고정 후보 변경')
    target=d/'author_visual_review.json';need(not target.exists(),'새 열람 기록 필요')
    complete=[d/f'{form}_readback_{i:02}.png'for form in('before','after')for i in range(3)]
    partial=[d/f'partial_{ref:03}.png'for ref in range(85,93)]
    ordered=[s/f'{form}_id{seq}_ordered.png'for form in('before','after')for seq in(88,91)]
    write(target,{'candidate':ev(d/'PL02_U.ARC'),'actually_viewed':[ev(p)for p in complete+partial+ordered],
        'counts':{'complete_plates':6,'partial_plates':8,'ordered_plates':4},
        'observations':['재킷과 획득 후 각각의 실제 대기와 새 머릿결·고글·발 높이를 비교했다. 큰 체격 도약이나 새 확정 단절을 찾지 못했다.',
            '90의 높은 팔 아래 공통 보라 외곽은 소매 가장자리/맨팔 그늘로 이어지고 추가 손처럼 읽히는 조각은 찾지 못했다.',
            '16부분 조합을 나열한 8판에서 획득 후 팔 위 흰 소매 잔재나 몸통/손목의 새 확정 분리는 찾지 못했다.',
            '88의 83픽셀 효과가 새89의 왼쪽 1픽셀 이동 몸체 위에 있고, 91표의 상향→대각→수평 팔과 복귀92 순서를 원점 기준 정적판으로 확인했다.'],
        'limits':['정적판 실제 열람이며 연속 동영상을 실제 시청했다고 주장하지 않는다.',
            '브라우저 재생은 원표 호출수와 60호출/초 가정이다. 실제 외부 상태·탄환 객체·공격 판정·실기는 이 검사 범위가 아니다.',
            '대기 자체를 재작화하지 않았고, 새85/90/91의 발 모양은 기본형에서 수용한 새 자세 정책을 따른다. 전체 폼 미술 완료가 아니다.'],
        'runtime_verified':False,'continuous_video_actually_watched':False})
    native=H/'ultimate_standing_fire_components_native_checks.json';browser=s/'browser_verification.json'
    need(json.loads(native.read_text('utf8'))['passed'] and json.loads(browser.read_text('utf8'))['passed'],'검사 미통과')
    write(d/'post_lock_evidence.json',{'candidate':ev(d/'PL02_U.ARC'),'prepared_lock':ev(d/'PREPARED_LOCK.json'),
        'source_lock':ev(d/'INPUT_LOCK.json'),'native':ev(native),'sequence':ev(s/'report.json'),'browser':ev(browser),
        'author_visual_review':ev(target),'independent_pending':True,'root_final_evidence_pending':True,
        'locked_assets_modified':False,'new_gameplay_execution':False})
    q=json.loads((H/'fullform_ledger32.json').read_text('utf8'))
    q['selection_standing8_prepared'].update(frozen=True,frozen_record=ev(H/'prepared_selection_standing01/FROZEN.json'),independent_pending=False,v4_guard_root_pending=False,
        integration_status='루트의 BR24 통합 보고는 별도 전체범위표10에 있음. 이 장부 작성에서는 새 BIN 재독출/실기를 수행하지 않음.')
    pending={'refs':list(range(85,93)),'forms':['ultimate_before','ultimate_after'],'candidate':ev(d/'PL02_U.ARC'),
        'proposal':ev(d/'proposal.json'),'lock':ev(d/'PREPARED_LOCK.json'),'source_lock':ev(d/'INPUT_LOCK.json'),
        'source_manifest':ev(H/'ultimate_standing_fire_targets01/manifest.json'),'post_lock_evidence':ev(d/'post_lock_evidence.json'),
        'frozen':False,'integrated':False,'independent_pending':True,'root_final_pending':True,'runtime_verified':False,
        'status':'7고유자세14원화와 88효과 파생을 합친 8참조40층 준비본. 재현3/거부17·원MIPS·256부분·원표23단계/594폼canvas 통과. 독립/루트 최종기록 대기.',
        'source_policy':'새 원화·현재 수용 기본형 자세를 유지한다.88은 원US 효과 전체타일2의12→6 및 현재83좌표와 대조한 뒤 새89 x−1에 합성. 옛Ultimate88의198셀 몸 차이를 효과로 복사하지 않는다.'}
    q['ultimate_standing_fire8_prepared_scope']=pending;q['next_generation']=pending
    for r in q['references']:
        if r['form'].startswith('ultimate')and 85<=r['ref']<=92:r['in_progress_unapplied_art']=pending
    q['pending_related_old_frames']=[135];q['full_art_unification_complete']=False
    q['next_groups_after_standing_fire']={'next_read_only_and_input_preparation':'4폼 체이서162..174의 실제 관절·별칭·몸체4키 확인 후 기본/포스 첫 소량 원화.',
        'also_remaining':['4폼 노바/호버213..230: 실제 body/effect/mask15 규칙 분리','차량 머리184..203: 198빈참조·장식 식별성 조건부검토','Ultimate135 도구 거부 편집은 재시도 없이 부모 보호'],
        'review_basis':ev(H.parent/'root_review_checkpoint72.json')}
    need(not(H/'fullform_ledger33.json').exists(),'새 장부 필요');write(H/'fullform_ledger33.json',q)
    keys=json.loads((H/'unique_art_keys32.json').read_text('utf8'));keys.update(source_ledger=ev(H/'fullform_ledger33.json'),next_unfrozen_art=pending,selection_copy_candidate=q['selection_standing8_prepared'])
    keys['counts_scope_note']='동결 고유키 수는 이전32와 동일. 이번16표시는 아직 준비본이므로 동결 완료 수에 더하지 않음.'
    write(H/'unique_art_keys33.json',keys)
    print(json.dumps({'visual':ev(target),'post_lock':ev(d/'post_lock_evidence.json'),'ledger':ev(H/'fullform_ledger33.json')}))

if __name__=='__main__':main()
