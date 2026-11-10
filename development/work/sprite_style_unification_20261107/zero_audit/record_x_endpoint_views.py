from pathlib import Path
import hashlib,json
D=Path(__file__).parent
O=D/'x_endpoint_supplement01'
p=O/'report.json';r=json.loads(p.read_text('utf-8'))
observations={
 'shibuki':'HQ12의 긴 머리·귀·소매·다리 내부선과 출발9의 굽힌 무릎 연결이 보인다. 대화8은 의상/장식 변형 및 입열림을 유지한 큰 별도 일러스트다. 작은 잔기 얼굴은 별도 단순화 디자인으로 게임플레이 머리보다 적은 정보가 있으나 이 차이만으로 결함 판정하지 않았다. 이번 정적8범주 내 새 확정 절단/팔레트 혼입은 찾지 못했다.',
 'nana':'HQ12는 검정 의상의 안쪽 회색선·소매·머릿결이 있고 대기/대화/출발 자세가 같은 큰 크기 체계로 이어진다. 대화8은 기본형 얼굴의 닫힌입/열린입 공유설계이며 Ultimate별도옷을 새로 그린 것으로 세지 않는다. 잔기는 눈/얼굴이 읽히는 독립 작은 디자인이다. 이번 정적판에서 새 확정 목/다리 절단은 찾지 못했다.'}
for project in r['projects'].values():
    for s in project['sheets']:
        q=D.parents[2]/s['path']
        assert hashlib.sha256(q.read_bytes()).hexdigest()==s['sha256']
        s['actually_viewed']=True;s['viewer']='hud_checkpoint view_image'
    project['actual_visual_review_this_extraction']=True
    project['visual_observation']=observations[project['character']]
    project['decision']='기존 별도 디자인 보존 방향의 정적 의견. 최종 루트 미술 판단 대기이며 전수 실기/사용자 수용 아님.'
r['actually_viewed_sheets']=8
r['new_confirmed_art_defects']=[]
p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(hashlib.sha256(p.read_bytes()).hexdigest())
