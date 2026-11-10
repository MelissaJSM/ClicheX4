from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
items=[(78,'nana_audit/hurt_repaint/extra_registered_v1',['comparison_1.png','comparison_2.png'],
 ['기본/포스233·234의 머리결·소매·베일 추가 묘사2판을 직접 확인했다. 초기 방향은 대기 기준의 재질 분할을 유지한다.'],
 ['234 발끝1행 및 포스233 머리 기준점 정합은 제작자가 후속 조사 중이다. 별도235·236 피격 오라와 실제 재생은 아직 검토하지 않았다.']),
 (79,'shibuki_audit/ultimate_ladder_native03',['before_comparison.png','after_comparison.png'],
 ['143/144/146×전후 의상2판을 직접 보았다. 앞모습과 뒷모습의 구별을 유지하고 새 머리결·등/소매·다리 묘사가 기존 단색 영역보다 대기 기준에 가까워졌다.',
  '144/146 뒷머리에 선글라스 앞면을 그렸던 오류를 국소 교정한 판이며, 현재 뒤통수에서 앞면 안경 반복은 보이지 않는다.'],
 ['패킹 전 초기3키포즈 검토다. 손발 접점·파트 공유·나머지 사다리 자세와 실제 동작 검증은 남아 있다.'])]
for number,directory,names,findings,limits in items:
 pages=[W/directory/n for n in names]
 r={'root_actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in pages],
 'findings':findings,'limits':limits,'final_user_accepted':False}
 p=W/f'root_review_checkpoint{number}.json';assert not p.exists();p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(number,sha(p))
