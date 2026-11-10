"""제안의 원활성/작업 부모 해시를 실제 파일과 직접 대조한다."""
from pathlib import Path
import sys,json
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import digest,sha,write,need
from scripts.export_sprite_playback import read_disc
def main():
 out=D/'packed_dash_candidate_v1';p=json.loads((out/'proposal.json').read_text('utf8'));source=ROOT/'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin';need(digest(source)==p['baseline_sha256'],'Original baseline BIN');data=read_disc(source,['PL02_U.ARC'])['PL02_U.ARC'];q=p['files']['PL02_U.ARC'];need(sha(data)==q['before'],'Original baseline resource');parent=D.parent/'ultimate_wall_repaint/packed_wall_candidate_v1/PL02_U.ARC';need(digest(parent)==q['working_parent_before']==p['parent_arc_sha256'],'Working frozen parent');candidate=ROOT/q['path'];need(candidate==out/'PL02_U.ARC'and digest(candidate)==q['after'],'Target resource');write(out/'baseline_binding.json',{'passed':True,'baseline':source.relative_to(ROOT).as_posix(),'baseline_sha256':p['baseline_sha256'],'original_active_resource_sha256':sha(data),'working_parent_sha256':digest(parent),'candidate_sha256':digest(candidate),'original_bytes_untouched':True,'active_pointers_or_user_saves_touched':False})
 print(digest(out/'baseline_binding.json'))
if __name__=='__main__':main()
