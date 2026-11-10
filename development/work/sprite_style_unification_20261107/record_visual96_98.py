from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,paths,findings,limits,**extra):
 p=W/f'root_review_checkpoint{n}.json';assert not p.exists()
 data={'root_actually_viewed':[{'path':(W/q).relative_to(ROOT).as_posix(),'sha256':sha(W/q)} for q in paths], 'findings':findings,'limits':limits,'final_user_accepted':False,**extra}
 p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8');print(p.name,sha(p))
save(96,['shibuki_audit/ultimate_ladder_shot_sequence01/'+n for n in ('before_ordered_contacts.png','after_ordered_contacts.png')]+['shibuki_audit/ultimate_ladder_endpoint_review02/feet_00.png','shibuki_audit/ultimate_ladder_endpoint_review02/feet_01.png'],
 ['사다리 사격92/93 순서2판과 발 위치2판을 직접 열람했다. 반동시 총구 이동과 손-무기 연결, 두 의상 사이 다리 공통 표현에 추가 확정 분리는 보이지 않았다.','원위치와 비교해143/149/151/154 발끝1픽셀,183은2픽셀 높은 차이는 남는다. 몸 전체 축척/원점을 변경한 결과로 단정하지 않으며 발목의 원화 차이로 기록한다.'],
 ['원155의 몸통 반동을 전부 복원한 것은 아니다. 기본형에서 수용한149 몸체 공유 정책이며,93 외부 시간은 미리보기 가정이 포함된다.','이 기록은 정지 순서도 검토다. 실제 게임의 사다리 가로대 접촉/전체 재생/실기는 별도다.'],candidate_arc_sha256='03a675626035b93ad2e2feef8dd643365ed8a3e1a61a1eb02a476063e2c55e8a')
base='nana_audit/ultimate_hurt_repaint/'
save(97,[base+f'effect_probe_v1/comparison_{i}.png' for i in (1,2,3)]+[base+'aura_contact_probe_v2/comparison.png']+[base+f'packed_hurt_diagnostic_v1/readback_{i}.png' for i in range(1,6)],
 ['효과3판/오라 재등록1판/최종 패킹 재추출5판을 직접 열람했다. 새 머릿결·소매·피부 명암이 대기 기준에 더 가까우며 두 의상에 추가 확정 절단은 찾지 못했다.','107/108의 기존 획득 후 표시에서 빠졌던 효과를 획득 전에서 분리한 번개로 맞추며,235/236 외부 효과는 새 귀와 머리/다리에 겹치지 않게 원래 조각 단위로 이동했다.'],
 ['원래 숨겨진 효과 전체를 추정 복원한 것은 아니다. 확인 가능한 외부 조각만 보존·정합했다.','실제 게임 피해 유형/반복/방향 검사는 아직 미실행이며 원MIPS/독립검사도 별도다.'],candidate_arc_sha256='c9e68442829a7f149ae86317c88172e27dbce545e454687b98310fad28ef83a5')
save(98,['root_nana_ladder/first_registered01/comparison_1.png','root_nana_ladder/first_registered01/comparison_2.png'],
 ['나나 기본/포스143/146 새4표시의 전체 고정셀 등록을 직접 열람했다. 평평한 뒷머리에 분할된 머릿결과 명암이 생겼고 포스 베일 주름이 기준 대기와 연결된다.','등록상 발끝이 기존보다1픽셀 낮고 포스143 올린 손이1픽셀 높다. 원화를 옛 그림으로 덮지 않고 접점만 후속 검토한다.'],
 ['새 원화 후보4표시이며 ARC 패킹/전체 사다리 동작/실기 미완료다.'])
