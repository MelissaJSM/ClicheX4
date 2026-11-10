"""실제로 열람한 재추출/원순서 정적판만 기록한다."""
from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];P=D/'packed_vehicle_candidate_v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=P/'producer_visual_review.json';assert not out.exists();paths=[P/f'readback_{i}.png'for i in range(1,6)]+[D/f'native_cycle_v1/timeline_{i}.png'for i in range(65,77)]
 r={'candidate_sha256':sha(P/'PL02_U.ARC'),'actually_viewed_files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}for p in paths],'observations':['새4자세에서 머릿결·재킷/맨팔·접힌 다리 음영이 대기 세부와 이어진다.','162/166 굽힌 무릎과 손/손목,170 앞팔과 발목,174 두 신발에 새로운 확정 절단을 찾지 못했다.','Y상하별칭에서 동일몸체의 원점만 이동하여 머리/사지 크기가 별도로 변하지 않는다.','166/170 팔 뒤의 작은 분홍은 실제후폼 donor 표본을 보존했다. 색만 보고 소매를 지우지 않았다.'],'limits':['17파일 정적 실제열람이며 인간 실시간 게임 관찰은 아니다.','78canvas/원표12 재생검사는 별도 기계검사.','차량 배경·손잡이·페달과 실제게임 접점은 미검증.','원US Y별칭을 새양폼 정책으로 적용했으며 옛후폼의 개별등록 차이까지 exact 복원한 것이 아니다.'],'runtime_verified':False,'all_nana_style_complete':False};out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'sheets':len(paths),'sha256':sha(out)}))
if __name__=='__main__':main()
