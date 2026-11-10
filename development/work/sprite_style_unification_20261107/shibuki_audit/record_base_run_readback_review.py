from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import sha,write,need
d=H/'base_run_complete_pack06';need(sha((d/'PL00_U.ARC').read_bytes())=='381d83fa2623d58a3302914196ffdd73bd8c972e27aa584380af05d819e688ce','Candidate changed')
files=[d/f'{form}_readback_{i:02}.png'for form in('base','fourth')for i in range(6)]
write(H/'base_run_readback_review01.json',{'candidate_sha256':sha((d/'PL00_U.ARC').read_bytes()),'reviewer':'overhaul_ui','actual_view_image_used':True,'sheets':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}for p in files],'form_displays_viewed':64,'observations':['ref1은 현재수용idle0와 동일. 새2팔 아래의 옛소매 잔여 없이 무릎·다리가 이어짐.','3..32의 머릿결·옷깃·소매/허리장식과 부츠명암이 패킹 전 등록판처럼 유지됨.','기본/포스 사격 짝의 총열은 원래위치에서 유지되고 별도세번째팔·목/손목/발목의 새확정공백은 발견하지 못함.','13/15/25/27의 기울고 좁은 실루엣은 수용한 보행원화의 발교차 자세이며 대기bbox와 다르다는 이유만으로오류판정하지 않음.'],'limits':['최종정적재추출12판 검토이며 실제게임/60Hz 연속전환 검증은 아직 별도.','1024부분조합의 픽셀일치는제작검사로통과했지만32개의16mask판을이열람기록에서모두봤다는뜻아님.','사용자최종수용/전체모션완료를의미하지않음.']})
print(sha((H/'base_run_readback_review01.json').read_bytes()))
