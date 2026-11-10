from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
bind=lambda p:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
D=W/'nana_hurt_partial_review02';m=read(D/'manifest.json')
assert len(m['frames'])==128 and len(m['pages'])==4
for p in m['pages']:assert sha(ROOT/p['path'])==p['sha256']
records={83:{'root_actually_viewed':m['pages'],'source_manifest':bind(D/'manifest.json'),
 'findings':['패킹된 f823 진단 ARC의106/110/233/234×16마스크×팔2유형128RGBA를 직접 추출했다. 팔1/2가 정확히 같아64고유표시4판으로 배열하고 전부 직접 열람했다.',
 '이번 정적 전조합 판에서 새 목·허리·무릎 접점의 확정 절단이나 별도 고립파츠는 찾지 못했다. 새 몸체의 머리·의상 상세 묘사가 부분파츠 조합에도 남아 있다.'],
 'limits':['235/236의 오라는 포함하지 않았다. 최종 오라 수정 ARC에서4몸체128RGBA 동일성 재검증이 필요하다.',
 '정적4판 검토이며 실제 모든 부분착용 피격 전수 플레이나 사용자 최종 수용은 아니다.']},
 84:{'root_actually_viewed':[bind(W/'nana_audit/hurt_repaint/aura_contact_probe_v2/comparison.png')],
 'source_manifest':bind(W/'nana_audit/hurt_repaint/aura_contact_probe_v2/manifest.json'),
 'findings':['모자·뒤머리를 덮던235/236 오라를 새 몸 외곽에 맞춰 국소 정합한 비교판을 직접 열람했다. 원래 빛 조각 모양과 새 몸체의 상세 묘사가 구별된다.',
 '최대 간격6→8px 증가는 이번 정적판에서 과도하게 떨어진 효과로 보이지 않았다. 몸체를 유지한 채 최종 패킹·원순서 재생 검토로 진행한다.'],
 'limits':['원순서 깜빡임·실제 피격에서의 인상은 아직 확인하지 않았다. 최종 채택 또는 전체 수용을 뜻하지 않는다.']}}
for number,r in records.items():
 r['final_user_accepted']=False;p=W/f'root_review_checkpoint{number}.json';assert not p.exists();p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(number,sha(p))
