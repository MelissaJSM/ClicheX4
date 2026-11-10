"""실제 열람한 최종 재추출2판·원순서5판의 한정된 정적 의견을 기록한다."""
from pathlib import Path
import sys,json
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import digest,write,need
def main():
 p=D/'packed_special_candidate_v1';out=p/'producer_visual_review.json';need(not out.exists(),'새 검토 기록');sheets=[p/f'readback_{i}.png'for i in(1,2)]+[D/f'native_cycle_v1/timeline_{n}.png'for n in(95,96,97,104,105)]
 write(out,{'candidate_sha256':digest(p/'PL02_U.ARC'),'actually_viewed':[{'path':s.relative_to(ROOT).as_posix(),'sha256':digest(s)}for s in sheets],'findings':['최종95/96의 새머리·재킷 주름/맨팔·접힌 다리와 바닥이 등록 후보와 이어진다. 전후폼 새손·사선권총의 추가확정 단절은 보이지 않았다.','최종98/99의 손 피부와 정본권총 그립이 이어지며 초기의 떠있는 총/손 진단은 남지 않았다. 전후 의상에서 새머리·다리와 손목을 공유한다.','원표95/96은 이전동결138/139에서 이번95/96으로 연결되고,104/105는 이전동결97·81에서 이번98/99로 이어진다. 이번에는 두X+1쌍을 새양폼 공통으로 유지한다.','원표97은96 단일 종료참조다. 실제 복제체 caller·게임효과를 실행한 검토로 세지 않는다.'],'limits':['정지 순서판을 직접 열람한 미술 의견이며 인간의 실제60Hz게임 관찰이 아니다.','95는 실제 새 사선총이며98만85 정본20texel X−3/Y+1의 모듈위치정책이다. 새 발사점 MIPS추적을 한 것으로 확대하지 않는다.','독립 reader·루트 최종수용·실기는 각각 별도 증거다.'],'runtime_verified':False});print(json.dumps({'sha256':digest(out),'sheets':len(sheets)}))
if __name__=='__main__':main()
