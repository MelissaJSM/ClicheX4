from pathlib import Path
import hashlib,json
D=Path(__file__).parent/'nana_ultimate_rising7_independent01'
p=D/'report.json';r=json.loads(p.read_text('utf8'))
for row in r['new_readback_sheets']:
    q=Path(__file__).resolve().parents[3]/row['path']
    assert hashlib.sha256(q.read_bytes()).hexdigest()==row['sha256']
r['readback_actually_viewed']=True
r['visual_review']={
 'reviewer':'hud_checkpoint',
 'method':'view_image로 독립 재추출 readback_00/01/02 세 판 실제 열람',
 'observations':[
  '대기와 나란히 본 새 머릿결·재킷·맨팔·다리 명암은 이전보다 상세하다.',
  '100 후폼의 옛 밝은 소매와 목 주변 재킷 흔적은 제거되어 검은 상의끈·피부와 이어진다.',
  '103/104 오른쪽 위로 든 팔과 권총, 231/232 발목·신발 접지에 새로 확정할 단절은 이 판에서 발견하지 못했다.'
 ],
 'limits':['독립 정적 판독이며 실제 불꽃 시간표·게임 혼합·사용자 수용 증거가 아니다.','원화 전체 재양자화 재현은 제작자 증거와 구분한다.']
}
p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(hashlib.sha256(p.read_bytes()).hexdigest())
