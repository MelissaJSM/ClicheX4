"""담당자가 실제 열람한 최종 재추출/부분/순서판 기록."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
out=H/'standing_fire_visual_review02.json';need(not out.exists(),'기존 검토 기록 보호')
paths=[H/'standing_fire_base_pack01'/f'{f}_readback_{i:02}.png'for f in('base','fourth')for i in range(3)]
paths += [H/'standing_fire_base_pack01'/f'partial_{n:03}.png'for n in range(85,93)]
paths += [H/'standing_fire_sequence01'/f'{f}_id{aid}_ordered.png'for f in('base','fourth')for aid in(88,91)]
write(out,{'candidate':ev(H/'prepared_standing_fire_base01/PL00_U.ARC'),'actual_viewed':[ev(p)for p in paths],
    'scope':'최종6재추출/8부분아머/4원순서 정적판18장 실제 열람. 연속 영상 또는 실기 검토 아님.',
    'observations':['85~92의 머릿결·옷깃·땋은부분·소매 및 신발 명암이 패킹 뒤에도 새 원화와 이어진다.',
        '기본/포스 완성 및16부분아머에서 추가 팔이나 명확한 새 목/손목/무릎 분리는 발견하지 못했다.',
        '88의 원래83픽셀 효과는 위로 들리는 팔/머리 앞에 남아 있으며 다음89에서 사라지는 원순서를 유지한다.',
        '87과92는 각각 내리는 팔/마무리로 별도 표현되고 idle0 통째 치환이 아니다.90/91은 다른 하체 자세를 유지한다.',
        '85 왼발1px 높이는 오른발 접지와 함께 root가 현후보 유지 방향을 수용했고90/91 신발폭도 현후보 유지. 이번 정적판은 새 물리 접점 검증이 아니다.'],
    'technical_evidence':[ev(H/'prepared_standing_fire_base01/verification.json'),ev(H/'standing_fire_components_native_checks.json'),ev(H/'standing_fire_sequence01/browser_verification.json')],
    'limits':['root 최종검토와 독립 static reader는 별도','선택UI1..8 새몸체 동기화 미완료','별도 탄환/실제게임 물리와 말미92 이후 외부상태는 오프라인 검토기 범위 밖','85/86은 원US 몸체391셀 차이의 완전복원 주장이 아니라 수용포즈 기준의 개별 새 원화'],
    'all_forms_complete':False,'runtime_verified':False,'art_reduced_for_storage':False})
print(json.dumps({'plates':len(paths),'sha256':sha(out.read_bytes())}))
