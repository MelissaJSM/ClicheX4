from pathlib import Path
import json,hashlib
D=Path(__file__).parent;ROOT=D.parents[2];O=D/'nana_legacy_timeline_review01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
mp=O/'manifest.json';m=json.loads(mp.read_text('utf8'))
for p,h in m['source_files'].items():assert sha(ROOT/p)==h,p
groups={
 'nana_dash12/air_left':['공중 상승→왼쪽 공중대시→하강/착지→대기 연결을 확인했다.','13.250~14.250초, 효과가 몸을 가리는 표본은 몸 전체 판정에 쓰지 않았다.'],
 'nana_dash12/fire_right':['오른쪽 대시 사격·총구 섬광·잔상→서서 사격 회복→대기를 확인했다.','17.000~18.125초. 당시 RN12 포스 원화이며 후속 원화의 실기를 의미하지 않는다.'],
 'nana_dash12/fire_left':['왼쪽 대시 사격과 회복을 확인했다. 총구 섬광/배경 효과에 가린 구간을 제외한 표본에서 추가 확정 신체 절단은 찾지 못했다.','22.000~23.125초.'],
 'nana_ultimate01/right_jump_fire':['오른쪽 점프사격 후 착지/대기 구간이며111/112캡처가 동일 WebP111을 쓰는 병합을 실제 확인했다.','6.719~7.469초. 이 두 판만으로 앞선 점프 전체를 새로 검증하지 않는다.'],
 'nana_ultimate01/left_jump_fire':['왼쪽 점프와 사격→하강/착지→대기 흐름을 확인했다.','9.984~11.484초. 당시 RN9 Ultimate 후폼 원화이다.'],
 'nana_ultimate01/dash':['오른쪽 지상대시·잔상·회복→대기를 확인했다.','12.000~12.750초. 뒤쪽 효과 가림을 고려해 보이는 몸체만 검토했다.'],
 'nana_ultimate01/charge':['일반탄·충전 입자/팔레트 깜박임→차지 발사·반동→대기 연결을 확인했다.','15.000~17.187초. 발사 효과가 몸/총을 덮는 표본은 접점의 완전한 육안 증거가 아니다.']}
review=[]
for p in m['pages']:
 key='/'.join(Path(p['path']).parts[-2:]);group=key.rsplit('_',1)[0]
 note=groups[group];p['actual_viewed']=True
 review.append({'path':p['path'],'sha256':p['sha256'],'actually_viewed':True,'findings':note,'new_confirmed_graphics_defect_found':False})
m['visual_review_pending']=False
mp.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n','utf8')
r={'scope':'시간 매핑이 어긋난 과거 비교판16장의 교정 후 실제 열람. 최신 아트/자원 검증이나 전체완료 판정 아님.','manifest_sha256':sha(mp),'pages':review,'pages_actually_viewed':16,'selected_crops':116,'legacy_vs_corrected_different_crops':108,'conclusion':'시간/사진 연결 오류를 교정했다. 이 선택 표본에서 추가 확정 몸체 절단/그래픽 누락을 찾지 못했다. 당시 RN12/RN9의 의상·색·체형만 보여주며 이후 재작화의 미술 또는 실기 통과를 대신하지 않는다.','limits':['기존 RAM/GPU 결과는 영상 seek와 독립이며 재실행하거나 변경하지 않았다.','이전 영상의 재해독/열람이다. 새 에뮬레이터 부팅·키입력·카드 접근은 없다.','기존16판·영상·evidence·watch·기존동결을 모두 해시로 재대조해 불변 확인했다.','16판의 표본 사이 미촬영 시간과 효과 가림 내부는 전수 검토한 것이 아니다.'],'protected_source_files_exact':len(m['source_files']),'old_files_unchanged':True,'new_runtime':False}
(O/'visual_review.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'manifest_sha256':sha(mp),'visual_sha256':sha(O/'visual_review.json'),'protected':len(m['source_files'])}))
