from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;O=D/'nana_rising7_independent01'
p=O/'report.json';r=json.loads(p.read_text('utf8'))
r['readback_actually_viewed']=True
r['visual_review']={'reviewer':'hud_checkpoint','actual_candidate_readback_sheets':r['new_readback_sheets'],
 'partial_source_sheets':[{'path':str((q:=D.parent/'nana_audit/rising_repaint/joint_layers_probe_v2'/f'partial_{i}.png').relative_to(ROOT)),'sha256':hashlib.sha256(q.read_bytes()).hexdigest()}for i in range(1,4)],
 'findings':['실제 후보 ARC를 다시 읽어 만든3판에서7참조의 기본/포스와 대기를 같은4배율로 비교했다. 머릿결·소매/옷깃·치맛단의 새 명암이 기존 단순면보다 세분화되었다.',
 '103/104는 오른쪽 위로 든 손과8px권총이 이어지며, 구형 반대손 발사 자세를 유지한 것이 아니다. 손목이나 어깨의 새 확정 절단을 찾지 못했다.',
 '101/102/231 포스 다리의 그늘쪽 외곽과 구두색이 남는다. 짧게 접힌100 다리와104의 길게 펴진 다리는 서로 다른 자세이며 이번 판에서 새로운 마른 절단은 찾지 못했다.',
 '부분3판의 head/body/arm/leg/body+leg 조합을 직접 보았다. 큰 뒤베일 leg8 및 머리 연결 head5라는 기존 배분이 남으므로 leg 단독에도 뒤베일이 보인다. 이것을 새 원화의 미지정 잔재로 해석하지 않았다.',
 '231/232는 원래5층 표시가 정확히 같았고 새표시도 같다. 후보의 두 압축주소는 별도이며 디코드raw만같다. 같은stream별칭이라고 보고하지 않는다.'],
 'limits':['실제 불꽃 시간표·전투·좌우 전환 실기를 새로 수행하지 않았다.','224부분 전부는 픽셀검사이며 육안 열람은 명시한 대표30조합이다.','Root 최종미술 판단과 사용자수용은 이독립보고와별도다.']}
p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8')
print(hashlib.sha256(p.read_bytes()).hexdigest())
