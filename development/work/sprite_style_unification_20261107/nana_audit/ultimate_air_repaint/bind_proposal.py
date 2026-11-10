"""원활성 BIN의 실제 PL02 해시를 검증하여 통합용 before와 작업부모를 구분한다."""
from pathlib import Path
import sys,json
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import sha,digest,write,need
from scripts.export_sprite_playback import read_disc
def main():
 out=D/'packed_air_candidate_v1';source=ROOT/'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin';expected='f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720'
 need(digest(source)==expected,'Original active parent BIN');old=read_disc(source,['PL02_U.ARC'])['PL02_U.ARC'];need(sha(old)=='4564d66c4e8559454f4cc434e78194d3ac89f42b4db5877925755c818153a1fa','Original active parent resource')
 p=json.loads((out/'proposal.json').read_text('utf8'));p['baseline_sha256']=expected;p['baseline']=source.relative_to(ROOT).as_posix();p['files']['PL02_U.ARC']['working_parent_before']=p['parent_arc_sha256'];p['files']['PL02_U.ARC']['before']=sha(old);write(out/'proposal.json',p)
 write(out/'baseline_binding.json',{'passed':True,'baseline_bin':source.relative_to(ROOT).as_posix(),'baseline_bin_sha256':expected,'baseline_arc_sha256':sha(old),'working_parent_arc_sha256':p['parent_arc_sha256'],'candidate_arc_sha256':digest(out/'PL02_U.ARC'),'scope':'기존 원화복원·노바 머리 동기화가 들어간 작업부모 bced 위에 새 공중22를 누적했다. 원활성4564와 작업부모를 혼동하지 않는다. BIN은 읽기만 했다.'})
 print(json.dumps(p))
if __name__=='__main__':main()
