from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
groups=[(88,[W/'nana_audit/ultimate_hurt_repaint/first_registered_v1'/f'comparison_{i}.png' for i in (1,2)],
 ['Ultimate 피격106/110 전후 4표시의 원화 등록 비교2판을 직접 열람했다. 이전 단색 뒤머리에 머릿결 명암이 생겼으며 새 외곽이 대기와 가까워졌다. 얼굴·머리 묘사를 유지하면서 손발 접점과 전후 의상 공통층을 이어서 검사한다.'],
 ['초기 등록 후보이며 최종 패킹·게임 적용·사용자 수용이 아니다.']),
 (89,[W/'shibuki_audit/ultimate_ladder_contacts01'/f'{form}_poses_{i:02}.png' for form in ('before','after') for i in (0,1)],
 ['사다리12참조 전후의 공통 몸체4판을 직접 열람했다. 뒤통수 안경 반복은 보이지 않고 재킷/수영복과 머릿결의 방향이 일치한다. 151 낮은 팔 수정이 들어간 후보에서 추가 확정 분리점을 찾지 못했다.'],
 ['손발의 실제 사다리 접점, 아직 없는 사격150/155, 원래 순서의 연속재생·패킹·실기는 별도 확인 대상이다.'])]
for n,paths,findings,limits in groups:
 p=W/f'root_review_checkpoint{n}.json';assert not p.exists()
 data={'root_actually_viewed':[{'path':q.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in paths],
 'findings':findings,'limits':limits,'final_user_accepted':False}
 p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8')
 print(n,hashlib.sha256(p.read_bytes()).hexdigest())
