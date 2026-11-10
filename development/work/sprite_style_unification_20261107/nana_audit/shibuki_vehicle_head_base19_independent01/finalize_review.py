"""실제 열람한 최종 재추출판 기록과 불변 입력 잠금. 새 게임 실행 없음."""
from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent
ROOT=O.parents[3]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()
rp=O/'report.json'
r=json.loads(rp.read_text(encoding='utf-8'))
assert r['passed'] and len(r['readback_sheets'])==6
for p,h in r['inputs'].items():
    assert sha(ROOT/p)==h,p
for s in r['readback_sheets']:
    assert sha(ROOT/s['path'])==s['sha256'],s['path']
vp=O/'visual_review.json'
lp=O/'READER_LOCK.json'
assert not vp.exists() and not lp.exists()
review={
 'candidate_sha256':r['candidate_sha256'],
 'technical_report':{'path':rel(rp),'sha256':sha(rp)},
 'actually_viewed':True,
 'viewed_files':r['readback_sheets'],
 'observations':[
  '기본형 19개의 실제 재추출을 부모와 1배·5배로 비교했다. 넓었던 연보라 머리 내부가 어두운 가닥과 밝은 면으로 분리되며 외곽 부피와 금색 홍채 위치가 유지된다.',
  '포스 19개의 검보라·금색 옆장식은 공통 얼굴을 가리지 않고 머리 옆 경계에 이어진다. 이 정적판에서 장식이 별도 떠 있는 조각이나 눈을 덮는 새 결함은 찾지 못했다.',
  '184와196의 각16부분 조합판을 실제 열람했다. 머리 비트의 장식 전환 외에 얼굴 크기·홍채·외곽이 튀거나 비어 보이는 추가 확정 문제는 찾지 못했다.',
  '기존 부모19동형의 평행이동 관계를 보존한 결과이다. 원US 고유 각도 복원이나 실제 조종석 합성 검토로 확대하지 않는다.'
 ],
 'limitations':[
  '이번 실제 열람은 최종 ARC 자체 재추출 6파일이다. 앞선 생성 원화 2셀 출처 열람·재양자화 abc7753c와 구분한다.',
  '608부분은 수치 전수 검사이고 실제 부분판 열람은184·196 각16표시이다.',
  '원MIPS19는 기존 후보/decoded 해시를 결속했으며 새 원MIPS·원표·게임 실기를 실행하지 않았다.'
 ]
}
vp.write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
files={rel(p):sha(p)for p in(O/'reader.py',Path(__file__),rp,vp)}
files.update({s['path']:s['sha256']for s in r['readback_sheets']})
lock={'passed':True,'candidate_sha256':r['candidate_sha256'],'parent_sha256':r['parent_sha256'],
      'inputs':r['inputs'],'evidence':files,
      'source_and_resource_modified':False,'new_MIPS_or_game_execution':False}
lp.write_text(json.dumps(lock,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'report':sha(rp),'visual':sha(vp),'lock':sha(lp),'head5_overlaps':len(r['record_storage']['actual_head5_partial_overlaps']),
                 'relocated_non_target':r['record_storage']['non_target_relocated_count'],'target_external':r['record_storage']['target_records_shared_with_external'],
                 'ref198':r['ref198']},ensure_ascii=False))
