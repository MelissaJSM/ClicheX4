from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
out=W/'root_review_checkpoint125.json';assert not out.exists()
paths=[D/'joint_targets01'/f'comparison_{i}.png' for i in range(1,5)]+[D/'packed_arrival01'/f'readback_{i}.png' for i in range(1,4)]+[D/'native_sequence01'/f'{form}_id2_ordered.png' for form in ('base','fourth')]
r={'root_actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in paths],'candidate_sha256':sha(D/'packed_arrival01/PL00_U.ARC'),'refs':[130,131,133,134,135,136,137],'findings':['新133/135/136/137은 대기와 같은 얼굴·머리카락·옷 주름 분리가 살아있으며 원래 무릎 굽힘·기립 높이 흐름이 유지된다.','포스의 새 베일·의상을 동일한 몸체 포즈에 대응시켰다. 기존133..137의 아머층은 비어있었음을 데이터에서 확인했다.','130/131/134의 원래 효과에 새133의 실루엣과 몸체를 연결했다.136/137의 번개 위치·픽셀은 그대로이며132의 기존 효과를 보존했다.','기본·포스 원표2의18단계를 정지 순서판으로 보았고, 추가 확정 분리·전환 크기 급변·테두리 유실을 찾지 못했다.'],'limits':['135의 모자 꼭지1px 및133 끝발1px은 새 그림 차이로 기록했으며 통째 크기 변환은 하지 않았다.','직접 본 것은 비교판과 정지 순서판9장이다. 연속 동영상 시청·실제 게임 테스트가 아니다.','모든 캐릭터 및 모든 모션의 미술 완료가 아니다.'],'runtime_verified':False,'final_user_accepted':False}
r['findings'][0]=r['findings'][0].replace('新','새')
out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(out))
