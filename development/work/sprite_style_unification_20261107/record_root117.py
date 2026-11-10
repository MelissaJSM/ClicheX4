from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'root_nana_standing';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paths=[D/'packed_standing03/readback_1.png',D/'joint_layers06/partial_1.png',D/'joint_layers06/partial_2.png']
paths += [D/'native_sequence01'/f'{form}_id{aid}_ordered.png' for aid in (91,104,105) for form in ('base','fourth')]
out=W/'root_review_checkpoint117.json';assert not out.exists()
result={'root_actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in paths],
 'arc_sha256':sha(D/'packed_standing03/PL00_U.ARC'),
 'findings':['재추출1판, 부분파츠2판, 원표91/104/105 두 의상6판을 직접 열람했다. 새89/97의 머릿결·소매·베일 윤곽과 발 위치를 대기 및 전후 자세에 대조했다.',
 '97 몸통만 입었을 때 남던 베일2픽셀을 leg8 소유로 이동해 검은 점을 없앴다. 전체 그림은 유지했고 최종 부분파츠 판에서 추가 확정 분리점을 찾지 못했다.',
 '88은89의 원래X-1 관계와 기존83개 광선 픽셀을 보존했다. 효과를 별도 타일로 공유 저장하여 몸체 디테일을 줄이지 않았다.',
 '원표91의86/90/91은 부모 그림이다.90/91의 머리와 옷 세부는 후속 전수 잔여 검토에 남긴다. 새89/97 검사 성공을 인접 자세 전체 재작화 완료로 확대하지 않는다.'],
 'runtime_verified':False,'continuous_animation_actually_watched_by_model':False,'all_character_art_complete':False,'final_user_accepted':False}
out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(out))
