"""후속 나나 라이징 원화에 사용할 원US 손/효과 접점의 정적 대조."""
from pathlib import Path
import sys,json
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;ROOT=D.parents[2]
sys.path[:0]=[str(ROOT),str(D/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
def main():
 proof=ROOT/'work/sprite_style_unification_20261107/shibuki_audit/rising_runtime_followup01/report.json';p=json.loads(proof.read_text('utf8'));need(p['source_us_bin_sha256']=='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b','US evidence')
 paths=[D/'dash_repaint/packed_dash_candidate_v1/PL00_U.ARC',D/'ultimate_wall_repaint/packed_wall_candidate_v1/PL02_U.ARC'];expected=['cbe6996784a901363abab2d93c81dca49ade8574ac0d5c378af398651f2f6cfa','e151044c37b5a59016f10d8c4d9637ffd4e192563f03c6a76df528383cfb4031'];arcs=[]
 for s,h in zip(paths,expected):need(digest(s)==h,'Frozen');arcs.append(Archive(s.read_bytes()))
 out=D/'rising_contact_review_v1';out.mkdir(exist_ok=False);rows=[];records=[]
 box=[2,-32,10,-25]
 for form,a,mask in(('base',arcs[0],0),('fourth',arcs[0],15),('ultimate_before',arcs[1],15),('ultimate_after',arcs[1],0)):
  images=[a.composite(n,mask)[0]for n in(0,103,104)];guide=images[2].copy();dr=ImageDraw.Draw(guide);dr.rectangle((box[0]+159,box[1]+159,box[2]+160,box[3]+160),outline=(0,170,190,255),width=1)
  rows.append((form+' / static only',[('accepted idle',images[0]),('current prep 103',images[1]),('current firing 104',images[2]),('US fist location overlay',guide)]));records.append({'form':form,'arc_sha256':sha(a.data),'refs':{str(n):sha(im.tobytes())for n,im in zip((0,103,104),images)}})
 helper.grid(rows,out/'comparison.png',6)
 write(out/'manifest.json',{'actual_nana_runtime':False,'original_us_evidence_file':str(proof.relative_to(ROOT)),'original_us_evidence_sha256':digest(proof),'original_us104_fist_bbox_world':box,'native_effect_initializers_from_root_report':p['native_initializers'],'frames':records,'scope':'현재 나나 정적표시와 원US손범위 대조. 청록선은 원효과의 실제그림이아닌 손범위가이드. 나나의새실기/독립CPU실행으로세지않는다. 지상231/232와공중103/104의손/효과를동일시하지않음.','new_art_generated':False});print(out)
if __name__=='__main__':main()
