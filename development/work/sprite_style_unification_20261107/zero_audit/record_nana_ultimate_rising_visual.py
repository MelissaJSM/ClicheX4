"""Record the three actually opened v4 boards and a local indexed check."""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3]
H=ROOT/'work/sprite_style_unification_20261107/nana_audit/rising_repaint'
S=H/'ultimate_costume_pair_probe_v4'
O=Path(__file__).parent/'nana_ultimate_rising_visual01';O.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
registration=json.loads((S/'registration.json').read_text(encoding='utf8'))
r=next(f for f in registration['frames'] if f['ref']==100)
bp=ROOT/r['before_path'];dp=ROOT/r['after_donor_path'];npth=S/'after_100.png'
before=np.array(Image.open(bp));donor=np.array(Image.open(dp));new=np.array(Image.open(npth))
points=[]
for x,y in [(5,-10),(6,-10),(7,-9),(8,-8),(9,-7)]:
    row={'world':[x,y],'before':int(before[160+y,160+x]),'after_donor':int(donor[160+y,160+x]),'composite_v4':int(new[160+y,160+x])}
    assert row['before']==row['composite_v4']==9 and row['after_donor']!=9
    points.append(row)
paths=[S/f'comparison_{n}.png' for n in (1,2,3)]
out={'scope':'후보 v4 비교3판을 view_image로 직접 열람한 정적 미술 의견. 기술 전수/MIPS/실기나 사용자 수용 아님.','actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in paths],
 'findings':[{'ref':100,'status':'수정 필요 후보 전달','observation':'맨팔 합성의 반대팔 바깥 윗선에 밝은 분홍 재킷 소매띠가 남아 보인다. donor 피부/머리 경계값 대신 before9가 유지된5셀을 확인했다.','points':points,'recommendation':'해당 원화의 맨팔/머리 경계 의미영역을 다시 확인. 전체 머리/몸체 복제나 임의 단색 채움은 요구하지 않는다.'},
 {'refs':[101,102,103,104,231],'status':'이3판에서 추가 확정 큰 단절 없음','observation':'101 복부 재킷끝은 제거되어 수영복/벨트가 읽힌다.102/231 목·팔과104 팔/손 연결에서 새 큰 절단은 찾지 못했다. 완성형 패킹·부분 의상 판정은 별도다.'}],
 'source_hashes':{p.relative_to(ROOT).as_posix():sha(p) for p in [S/'registration.json',bp,dp,npth]},'game_or_art_modified':False,'new_art_generated':False,'packed_candidate_reviewed':False,'runtime_verified':False}
(O/'report.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'report':str(O/'report.json'),'sha256':sha(O/'report.json')},ensure_ascii=False))
S5=H/'ultimate_costume_pair_probe_v5'
paths5=[S5/'comparison_1.png',H/'ultimate_ground_feet_probe_v1/comparison.png']
v5=np.array(Image.open(S5/'after_100.png'))
upper=[]
for x,y in [(2,-12),(3,-12),(2,-11),(4,-11),(5,-11)]:
    upper.append({'world':[x,y],'before':int(before[160+y,160+x]),'donor':int(donor[160+y,160+x]),'v5':int(v5[160+y,160+x])})
delta={'scope':'v5 소매/231접지 두 국소판 직접 열람. 전체 기술검사·실기 아님.',
 'actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in paths5],
 'v4_report':{'path':(O/'report.json').relative_to(ROOT).as_posix(),'sha256':sha(O/'report.json')},
 'findings':['100의 먼저 지적한5셀 밝은 선은 줄었지만 어깨 시작쪽 상단 잔여가 분홍/흰 옷깃처럼 읽힌다. 추가5셀의 원화 피부12 대비 옛9/10 잔류를 담당자에게 전달했다. 목/머리 소유를 먼저 구분하고 맨팔 외곽 전체를 이어 추적하도록 권고했다.','231 신발 하단+1y는 이 판에서 발목/종아리 새 단절 없이 바닥과 이어져 보인다. 실제 움직임/발 미끄러짐의 런타임 판정은 아니다.'],
 'upper_arm_samples':upper,'game_or_art_modified':False,'runtime_verified':False}
(O/'v5_delta.json').write_text(json.dumps(delta,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
S6=H/'ultimate_costume_pair_probe_v6'
v6=np.array(Image.open(S6/'after_100.png'))
assert all(v6[160+y,160+x]==donor[160+y,160+x] for x,y in [(2,-12),(3,-12),(2,-11),(4,-11),(5,-11)])
paths6=[S6/'comparison_1.png',H/'ultimate_neck_audit_v1/source_neck.png']
resolution={'scope':'v6 비교1 및 생성 원화 목 확대2판을 view_image로 실제 열람. 후보 미술 방향 의견이며 최종ARC/실기 검증은 아님.',
 'actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in paths6],
 'v4_findings_report_sha256':sha(O/'report.json'),'v5_findings_report_sha256':sha(O/'v5_delta.json'),
 'finding_100':'흰 옷깃·밝은 분홍 윗소매가 사라지고 원화의 검정 상의끈/피부 어깨로 읽힌다. 얼굴 아래 목 경계와 어깨 시작도 원화 후폼과 이어져 보이며 이판에서 새 확정 틈·머리 절단을 찾지 못했다.',
 'additional_samples_match_donor':5,'after_100_sha256':sha(S6/'after_100.png'),
 'recommendation':'정적 미술 방향상 패킹 검토 진행 가능. 최종35목표층/ARC/원효과 독립 검사는 별도.',
 'game_or_art_modified':False,'packed_candidate_verified':False,'runtime_verified':False,'user_accepted':False}
(O/'v6_resolution.json').write_text(json.dumps(resolution,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'v6_resolution_sha256':sha(O/'v6_resolution.json')},ensure_ascii=False))
