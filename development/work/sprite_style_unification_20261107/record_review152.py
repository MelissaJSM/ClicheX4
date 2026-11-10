from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];H=W/'shibuki_audit';out=W/'root_review_checkpoint152.json';assert not out.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
cp=H/'prepared_nova_strike_base01/PL00_U.ARC';assert sha(cp).startswith('36d4d029')
files=[H/f'nova_strike_base_pack01/{n}.png'for n in('base_readback','fourth_readback','partial_217','partial_220')]
files += [H/f'nova_strike_base_sequence01/{form}_{n}.png'for form in('base','fourth')for n in('preparation_order','strike_order')]
r={'checkpoint':152,'candidate_sha256':sha(cp),'actually_viewed_files':[{'path':f.relative_to(ROOT).as_posix(),'sha256':sha(f),'actually_viewed':True}for f in files],'observations':['새217 몸체의 머리카락/귀/리본/허리/부츠를 대기와 직접 비교했다. 넓은단색영역의 상세가개선됐으며 포스의 검보라·금색부츠가 대기복장과 이어진다.','217 및원효과를뒤에둔220의16부분조합2판을 직접 열람했고 추가확정 팔/허리/발 절단을 찾지 못했다.','기본mask0/포스15를 유지한 준비·돌진 원순서4판을 직접 열람했다. 이전새213..216→새217→기존218/219효과→새220 사이 큰체형도약을 찾지 못했다.'],'limits':['원효과의 단색가림·점멸은 유지하며 새218/219 몸체를 그린 것으로 세지 않는다.','실제PL00노바의 발동가능성·전체60Hz·공용GPU큐 극한상태는 미검증이다. 후보의31본체+7파츠는 원코드 별도검사 대상이다.','2개새몸+부츠국소donor에서217/220을 파생한 것이며4개고유몸체 원화로 세지 않는다.'],'root_static_art_direction_accepted':True,'runtime_verified':False,'whole_project_complete':False}
out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'candidate':sha(cp),'review':sha(out),'viewed':len(files)}))
