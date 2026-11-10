"""사다리 보류와 독립인 Ultimate89/97의 네 전신 원화 입력."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need
def main():
 p=N/'ultimate_ladder_repaint/packed_first7_diagnostic_v1/PL02_U.ARC';need(digest(p)=='dcaf1343747fabeab3054c59fc384c3bbd598209eccb6c5a37ac84c1d340d339','동결부모');a=Archive(p.read_bytes())
 bp=N.parent/'root_nana_standing/packed_standing03/PL00_U.ARC';need(digest(bp)=='87cc15efefedd475e0de972587995ad351d3ded1bd38a5c5096d5a3ab441748e','포즈참고');b=Archive(bp.read_bytes())
 out=D/'a_inputs_v1';out.mkdir(exist_ok=False);refs=[89,97];crop=(112,112,208,208);target=Image.new('RGBA',(1536,1536));style=target.copy();pose=Image.new('RGBA',(1536,768));frames=[]
 for row,(form,mask)in enumerate((('before',15),('after',0))):
  for col,n in enumerate(refs):
   im=a.composite(n,mask)[0];target.alpha_composite(im.crop(crop).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768));alpha=np.array(im)[:,:,3];alpha[112:208,112:208]=0;need(not alpha.any(),'고정입력창')
   ref=0 if col==0 else 85;style.alpha_composite(a.composite(ref,mask)[0].crop(crop).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
   frames.append({'ref':n,'form':form,'mask':mask,'cell':row*2+col,'source_rgba_sha256':sha(im.tobytes())})
 for col,n in enumerate(refs):pose.alpha_composite(b.composite(n)[0].crop(crop).resize((768,768),Image.Resampling.NEAREST),(col*768,0))
 target.save(out/'targets.png');style.save(out/'style.png');pose.save(out/'accepted_pose_reference.png')
 prompt='''Use case: style-transfer. Refine four neutral full-body adult heroine sprites for a PS1 Mega Man X4 game mod, in an exact1536x1536 transparent 2x2 sheet. Each768cell represents96x96 native game pixels enlarged8x.
Image1 is the EDIT TARGET. Top row is Nana's accepted pink jacket costume; bottom row is her accepted black sleeveless athletic costume with pink waistband. Image2 is STYLE ONLY: accepted idle on the left and detailed standing shot85 on the right, with the same costume rows. Preserve each outfit's existing coverage, green shoes, long pink hair, rabbit-ear hair accessory and green eyes. Do not transfer the idle gesture. Image3 is POSE DETAIL ONLY: the already refined black-dress version of the same89/97 joints and gun direction. Do not copy its black dress, beret or boots.
LEFT column89: wide planted standing stance, pistol arm raised diagonally up-left, short pink/black Sarang pistol pointed diagonally upward-left, other arm low beside the torso. RIGHT column97: standing preparation stance, both arms bent close in front of chest and face, pistol in the hand near the face. Preserve the distinct gun orientation and exact hand/wrist/elbow/shoulder centers of each column. Keep the same eye position, head size, waist, knee angles, toe positions and foot baseline. Both rows depict the same body and joint placement in different clothes.
Improve the large flat pink rear-hair block into separate layered pink locks with burgundy shadows and small highlights, matching Image2. Improve jacket folds, cuff edges and selective skin/leg shading. Keep crisp connected wrist/ankle contours; do not thicken everything with black outlines. Retain the small pistol's size and grip-to-hand connection. No new weapon design, oversized gun or extra arm. The bottom row has uncovered arms and the black outfit shown in Image2; do not carry pink jacket sleeve blocks into those arms. Do not alter the anatomy, body proportions, silhouette volume or outfit coverage.
Retain transparent padding and all positions in each cell. No bounding-box fitting, recentering, body scaling, sprite cropping, added effect, beam, ladder, text, label, grid, shadow, background or halo. Output exactly four complete sprites with genuine transparency and game-sized pixel clusters.'''
 (out/'prompt.txt').write_text(prompt,'utf8');write(out/'manifest.json',{'parent_arc':p.relative_to(ROOT).as_posix(),'parent_arc_sha256':digest(p),'pose_reference_arc':bp.relative_to(ROOT).as_posix(),'pose_reference_sha256':digest(bp),'refs':refs,'columns':2,'rows':2,'native_cell':[96,96],'world_crop':[-48,-48,48,48],'frames':frames,'files':[{'path':(out/f).relative_to(ROOT).as_posix(),'sha256':digest(out/f)}for f in('targets.png','style.png','accepted_pose_reference.png','prompt.txt')],'scope':'別개 Ultimate89/97 특수기 새원화. 보류된 사다리 참조와 무관하며 그 자료를 사용하지 않는다.','native_packed':False,'runtime_verified':False})
 print(out)
if __name__=='__main__':main()
