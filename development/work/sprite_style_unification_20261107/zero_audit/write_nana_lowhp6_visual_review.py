from pathlib import Path
import hashlib,json
D=Path(__file__).parent;ROOT=D.parents[2];O=D/'nana_base_lowhp6_independent01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
r=json.loads((O/'report.json').read_text(encoding='utf8'))
for q in r['fresh_sheets']:assert sha(ROOT/q['path'])==q['sha256']
v={'candidate_sha256':r['candidate_sha256'],'independent_report':{'path':rel(O/'report.json'),'sha256':sha(O/'report.json')},
 'actually_viewed':r['fresh_sheets'],'scope':'패킹 자원에서 새로 추출한 전후2판24표시+부분3판30표시 정적 열람',
 'observations':[
 '기본형은 모자와 머릿결·소매·검정 부츠 내부 명암이 기존보다 구분되며, 기울어진 저체력 자세와 고정된 발바닥이 유지되어 보인다.',
 '포스는 긴 머리와 베일이 같은 호흡 위상으로 이어지고, 맨다리/신발의 경계가 분리돼 보인다. 동일행 출처로 정합한 다리에서 추가 확정 구멍이나 발목 단절을 찾지 못했다.',
 '부분 몸통/팔만 장착한 판에는 베일 아래 삼각형만 떠 있는 모습이 없다. 다리 장착 시 베일 윗부분부터 아랫부분까지 함께 나타나 머리 뒤와 연결되어 보인다. 베일 의미영역의 변경222texel이 모두legs8 소유인 독립 수치와 일치한다.',
 '120/121,122/123,124/125의 차이는각폼 한픽셀입이며 전신이 교체되거나 발이 이동하지 않는다. 최종3호흡의 아래5행 RGBA가 두폼 각각 동일함도 확인했다.',
 '새 권총/손은 이 저체력 자세에서 몸 가까이 연결되어 보이며 별도 떠 있는 무기 조각을 찾지 못했다. 실제 발사나 외부 탄환 접점을 시험한 것은 아니다.'
 ],
 'assessment':'정적 미술 및 실제 자원 보존 검사 범위에서 추가 확정 결함 없음. 부모 최종 검토와 별개인 독립 의견.',
 'limits':['새 게임 실행/동적 원표 재생은 하지 않았다.','생성 원화 전체 재양자화는 포함하지 않았다.','사용자 미술 수용이나 전체작업 완료로 간주하지 않는다.'],
 'producer_functions_called':False,'runtime_verified':False,'user_accepted':False}
p=O/'visual_review.json';p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'path':rel(p),'sha256':sha(p)},ensure_ascii=False))
