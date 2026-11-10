"""31 새 원화의 반대손/커프만 채택하고 기존 새 전신·권총·발을 보존한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
def main():
 out=D/'hand31_joint_probe_v1';out.mkdir(exist_ok=False);bpath=D/'fourth_contacts_probe_v1/before_031.png';npath=D/'hand31_registered_full_v1/before_031.png';old=np.array(Image.open(bpath));src=np.array(Image.open(npath));verts=[(7,-4),(10,-4),(11,-3),(12,-2),(13,-1),(17,-1),(17,2),(13,2),(13,5),(8,5),(7,2)];mi=Image.new('L',(384,384));ImageDraw.Draw(mi).polygon([(x+160,y+160)for x,y in verts],fill=1);mask=np.array(mi,bool);new=old.copy();new[mask]=src[mask];need(np.array_equal(new[~mask],old[~mask]),'Outside exact');need(label(new>0,np.ones((3,3)))[1]==1,'Connected');need(int(np.nonzero(new)[0].max())==int(np.nonzero(old)[0].max()),'Sole');need(np.array_equal(new[:150],old[:150]),'Head');Image.fromarray(new).save(out/'before_031.png');Image.fromarray(mask.astype(np.uint8)*255).save(out/'semantic_mask.png')
 a=Archive((D.parent/'ultimate_wall_repaint/packed_wall_candidate_v1/PL02_U.ARC').read_bytes());helper.grid([('31 trailing hand only',[('accepted idle',a.composite(0,15)[0]),('previous new candidate',a.rgba(old,16)),('new source full / not adopted',a.rgba(src,16)),('hand-only candidate',a.rgba(new,16))])],out/'comparison.png',8)
 write(out/'registration.json',{'ref':31,'base':bpath.relative_to(ROOT).as_posix(),'base_sha256':digest(bpath),'new_source':npath.relative_to(ROOT).as_posix(),'new_source_sha256':digest(npath),'source_generated_sha256':digest(D/'hand31_v1/generated.png'),'region_vertices_world':verts,'changed_pixels':int(np.count_nonzero(old!=new)),'outside_semantic_region_exact':True,'head_legs_shoes_front_hand_canonical_gun_exact':True,'source_registered_pixels_only':True,'native_sha256':sha(new.tobytes()),'runtime_verified':False,'native_packed':False,'scope':'새31 반대손의 수평 막대를 새 원화의 주먹/커프로 교정. 같은 원화의 국소 배경 머리끝도 손 아래에서 복원하며 다른 전신은 기존 새 후보 그대로다.'})
 p=D/'hand31_v1/generation.json';q=json.loads(p.read_text('utf8'));q['input_images']={str(f.relative_to(ROOT)):digest(f)for f in(D/'before_fourth_v1/generated.png',D/'inputs_fourth_v1/old_before_targets.png')};q['prompt_note']='prompt_hand31_v1.txt 전체를 실제 builtin prompt로 전달. 원화 다른3셀은 채택하지 않았고31 국소만 사용.';write(p,q);print(json.dumps({'changed':int(np.count_nonzero(old!=new)),'png_sha256':digest(out/'before_031.png')}))
if __name__=='__main__':main()
