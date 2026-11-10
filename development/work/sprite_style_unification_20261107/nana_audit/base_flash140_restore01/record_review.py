"""제작자가 실제 열람한 최종140 재추출/부분/착지순서만 기록한다."""
from prepare_validation import *
def main():
 validate(P.read_bytes());p=D/'packed_flash_candidate_v1';dest=p/'producer_visual_review.json';need(not dest.exists(),'새 검토기록')
 findings={p/'readback.png':'기본형 실루엣과양옆46효과는동일하다. 새포스 섬광의 모자/뒤베일/하체가 현재포스 대기알파와이어지며 추가확정잘림을못찾았다.',p/'partial.png':'head/body/arm/leg부분과조합의 추가알파가 현부분대기 외곽을따른다. mask8의작은분리뒤베일은현idle부분에서도있는형상이며 새단절로계산하지않았다.',D/'native_cycle_v1/timeline_2_landing.png':'138/139의임시기본복에서140 event1로포스알파가복구되고141/142로이어지는정적전환을확인. 기본형은전후동일. 단색섬광이실제현재포스뒷머리/하체범위와이어진다.'}
 write(dest,{'actually_viewed':True,'candidate_sha256':FINAL,'parent_sha256':BEFORE,'views':[{'path':f.relative_to(ROOT).as_posix(),'sha256':digest(f),'actually_viewed':True,'finding':v}for f,v in findings.items()],'limits':['정지이미지3판을직접열람했으며브라우저기계재생은별도verification.json근거이다.','실제caller/게임입력/물리/변하는CLUT·실시간사람관찰은실행하지않았다.','원US140도아머빈층이므로현재의상추가149셀은승인된새의상실루엣정책이다.'],'runtime_verified':False});print(digest(dest))
if __name__=='__main__':main()
