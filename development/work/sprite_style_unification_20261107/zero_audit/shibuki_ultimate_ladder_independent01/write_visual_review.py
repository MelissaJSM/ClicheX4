from pathlib import Path
import json,hashlib
O=Path(__file__).resolve().parent
ROOT=O.parents[3]
H=O.parents[1]/'shibuki_audit'
P=H/'prepared_ultimate_ladder01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paths=[P/f'{form}_readback_{n:02}.png' for form in ('before','after')for n in range(3)]
review={
 'scope':'실제 패킹 재추출6판, 전후14자세씩28표시를 view_image로 열람했다. 원점 고정 정지판의 미술 의견이며 실기·움직임 접점 전체의 수용을 뜻하지 않는다.',
 'candidate_sha256':sha(P/'PL02_U.ARC'),
 'independent_report_sha256':sha(O/'report.json'),
 'viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}for p in paths],
 'observations':[
  '144/145·146/147 후두부의 내부 밝고 어두운 머릿결이 구분되고, 재킷 소매와 맨팔 구분이 유지된다.',
  '143·148/149 측면 얼굴과 머리, 허리에서 접힌 다리로 이어지는 선에 새로 확인되는 단절을 찾지 못했다.',
  '150/155 두 총열과 팔은 각각 손목에 붙어 보이며, 재킷/맨팔에서도 같은 발사부위가 유지된다.',
  '151/152 낮은 쪽 팔과 153/154/183 사다리 끝 동작은 머리·소매/맨팔·하체가 이어진다. 이 정지판만으로 사다리 칸과 발끝의 실제 접촉 성공을 판정하지 않았다.'
 ],
 'new_confirmed_art_defects':[],
 'limitations':[
  '155는 수용149의 몸체+반동팔을 사용하는 신규 정책으로 원US155 전신 반동의 동일 복원이 아니다.',
  '일부 발끝이 원래보다1~2px 높은 기존 명시사항은 미술 정지판과 기술검사만으로 실제 접점 해소라고 하지 않는다.',
  '원순서92/93 영상/게임 화면은 이 열람 목록에 포함하지 않았다.'
 ],
 'user_final_accepted':False,'runtime_verified':False,
 'root_separate_review':{'path':'work/sprite_style_unification_20261107/root_review_checkpoint94.json','sha256':sha(ROOT/'work/sprite_style_unification_20261107/root_review_checkpoint94.json')}
}
(O/'visual_review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n','utf8')
print(sha(O/'visual_review.json'))
