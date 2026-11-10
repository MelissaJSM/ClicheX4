"""통합 원활성4564와 이번 작업부모122c를 실제 파일로 구분한다."""
from pathlib import Path
import sys,json
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import sha,digest,write,need
from scripts.export_sprite_playback import read_disc
def main():
 out=D/'packed_wall_candidate_v1';src=ROOT/'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin';expected='f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720';need(digest(src)==expected,'Original baseline');old=read_disc(src,['PL02_U.ARC'])['PL02_U.ARC'];need(sha(old)=='4564d66c4e8559454f4cc434e78194d3ac89f42b4db5877925755c818153a1fa','Original ARC')
 p=json.loads((out/'proposal.json').read_text('utf8'));need(p['parent_arc_sha256']=='122c92c29fd0599772e18ac5ed3f918c8f0d40703fe08c396e4ccbdbb92f2c18','Working parent');need(p['files']['PL02_U.ARC']['before']==sha(old),'Before');p['baseline']=src.relative_to(ROOT).as_posix();write(out/'proposal.json',p)
 write(out/'baseline_binding.json',{'passed':True,'baseline_bin':src.relative_to(ROOT).as_posix(),'baseline_bin_sha256':expected,'baseline_arc_sha256':sha(old),'working_parent_arc_sha256':p['parent_arc_sha256'],'candidate_arc_sha256':digest(out/'PL02_U.ARC'),'scope':'원활성4564에서 머리복원·노바동기화·공중22를 포함한 작업부모122c 위에 벽12를 누적. BIN/포인터 쓰기 없음.'});print('Baseline verified')
if __name__=='__main__':main()
