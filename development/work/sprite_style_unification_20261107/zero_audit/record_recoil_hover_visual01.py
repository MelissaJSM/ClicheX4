"""실제로 열람한 6판만 기록. 그림/자원 변경과 기술 통과 주장은 하지 않는다."""
from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent;ROOT=D.parents[2];W=D.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(folder,paths,observations,limits):
 o=D/folder;o.mkdir(exist_ok=False)
 r={'scope':'요청된 중간 등록판의 정적 미술 읽기','actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}for p in paths],'observations':observations,'limitations':limits,'art_or_resource_modified':False,'technical_audit_executed':False,'runtime_verified':False,'user_accepted':False,'overall_complete':False}
 p=o/'review.json';p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(folder,sha(p))
H=W/'shibuki_audit/ultimate_standing_followthrough_common03'
save('shibuki_ultimate_recoil90_boundary_visual01',[H/n for n in('before_comparison.png','after_comparison.png','partial_090.png')],[
 '90의 높은 손에서 팔꿈치·어깨로 내려가는 굴곡이 두 의상에서 이어진다. 후보의 보라 외곽이 따로 떠 있는 조각이나 새로운 주먹처럼 읽히는 확정 결함은 이 세 판에서 찾지 못했다.',
 '재킷 소매의 어두운 가장자리와 맨팔의 아래 그늘을 공통 외곽에 둔 방향은 정적으로 납득된다. 단, 두 셀의 실제 색인15↔31 동색 및 donor 출처는 제작자 설명이며 이번 미술 읽기로 재검증한 수치는 아니다.',
 '부분16표시 판에서 재킷/맨팔 전환 때문에 팔꿈치가 끊기거나 새로운 긴 소매 잔재가 생기는 현상은 보이지 않는다. 손·총과 목/어깨 연결은 유지되어 보인다.'
],['정적 세 판의 관찰이다. 새 ARC·GPU·원순서·실기 통과를 의미하지 않는다.','90/91 전체 범위나 사용자 최종수용 판단으로 확대하지 않는다.'])
N=W/'nana_audit/ultimate_hover_repaint/shot_joint_probe_v1'
save('nana_ultimate_hover_shots_visual01',[N/f'comparison_{i}.png'for i in(1,2,3)],[
 '222/224의 사격팔이 새 어깨에서 수평으로 이어지고 위로 든 반대팔과 구분된다. 새 머리·목 아래에서 추가 팔이나 명백한 절단은 보이지 않는다.',
 '226/228의 팔은 밝은 윗면과 어두운 아랫면이 읽히며 손목에서 권총으로 이어진다. 원 그림의 검정 커프처럼 보이던 긴 띠보다 맨팔 의미가 선명하다. 228은 밝은 팔 면이 단순하지만 이 비교판만으로 추가 재작화가 필요한 확정 결함으로 보지는 않는다.',
 '230의 접힌 무릎와 사격팔은 분리되고 어깨/가슴의 검정 경계가 이어진다. 총 아래 어두운 손목 부분이 가장 두껍게 읽히므로 원 8열 창에 포함된 손과 새 피부손의 경계를 최종 출처 검사에서 유지하면 좋겠다. 현재 판에서 총이 손 밖에 떠 보이는 확정 결함은 찾지 못했다.'
],['정적 세 판에 표시된 다섯 중간 사격 자세만 열람했다.','8열 원총구의 바이트 보존, 팔 마스크/피부30셀 재구성, 새 ARC·게임 실기는 이번 검토 범위가 아니다.'])
