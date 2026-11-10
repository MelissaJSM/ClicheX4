"""Ultimate 사다리 첫3고유자세×전후6 원화 입력.기존손발 원점을 고정한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need
def main():
 p=N/'ultimate_return_repaint/packed_return_candidate_v1/PL02_U.ARC';need(digest(p)=='493bf2706aae33b64c4ffe70be1576a7ed63b0a4f62c54e89ca5876131392e29','최신동결');a=Archive(p.read_bytes());bp=N.parent/'root_nana_ladder/packed_ladder07/PL00_U.ARC';need(digest(bp)=='509cc9785cb5eb3dca9f7a8a3fd1d3ea334887a98d3834b9f327266b3c6bbdce','기본형동결');b=Archive(bp.read_bytes())
 out=D/'a_inputs_v1';out.mkdir(exist_ok=False);refs=[143,144,146];crop=(128,124,192,188);target=Image.new('RGBA',(1536,1024));style=Image.new('RGBA',(1536,1024));base=Image.new('RGBA',(1536,512));frames=[]
 for row,(form,mask)in enumerate((('before',15),('after',0))):
  for col,n in enumerate(refs):
   im=a.composite(n,mask)[0];target.alpha_composite(im.crop(crop).resize((512,512),Image.Resampling.NEAREST),(col*512,row*512));y,x=np.nonzero(np.array(im)[:,:,3]);need(x.min()>=crop[0]and y.min()>=crop[1]and x.max()<crop[2]and y.max()<crop[3],'전신입력범위')
   frames.append({'ref':n,'form':form,'mask':mask,'cell':row*3+col,'world_bbox':[int(x.min()-160),int(y.min()-160),int(x.max()-159),int(y.max()-159)],'source_rgba_sha256':sha(im.tobytes())})
  for col,n in enumerate((0,79,61)):style.alpha_composite(a.composite(n,mask)[0].crop(crop).resize((512,512),Image.Resampling.NEAREST),(col*512,row*512))
 for col,n in enumerate(refs):base.alpha_composite(b.composite(n)[0].crop(crop).resize((512,512),Image.Resampling.NEAREST),(col*512,0))
 target.save(out/'targets.png');style.save(out/'style.png');base.save(out/'accepted_base_pose_reference.png')
 prompt='''Use case: style-transfer. Neutral full-body adult heroine game-sprite cleanup, six sprites on an exact1536x1024 transparent canvas,3columns by2rows. Image1 is the ONLY edit target and gives the exact positions, pose and clothing. Each512x512cell represents64x64 native game pixels.
TOP ROW left-to-right: ladder143,144,146 in the established pink jacket outfit. BOTTOM ROW: the same three poses in the established black-and-pink sleeveless costume. Preserve the clothing coverage and designs exactly as shown; do not mix the two outfits or add shorts. This is technical sprite work, neutral climbing poses.
Improve the broad flat pink back-hair into distinct lock clusters and readable shadow planes. Match the accepted sprite detail, face/head size, jacket folds, cuff seams, green footwear and selective skin shadows in Image2. Image2 columns are idle, dash, wall poses and is STYLE ONLY; do not copy those poses.
Image3 is an accepted basic-costume version of the SAME three climbing gestures for back-hair rhythm and limb orientation only. Do not copy its black dress or tall boots into the Ultimate outfits.
Keep ALL target hand grips, wrist/elbow/shoulder positions, knees, ankles, toes and leg length.143 has a side/three-quarter climbing transition with its existing visible face direction.144 and146 are BACK-VIEW climbing poses: show the back of the head and hair, never add front-facing eyes or face on the back. Keep the short animal ears and rear hairstyle consistent with the input. Do not turn the character around, swap the supporting hands, straighten the bent knees or move the rung contacts.
No change to scale, placement, silhouette width, foot size or native joint anchors. Preserve the modest game-sprite proportions; no anatomy emphasis. Improve hair, cloth and leg shading with clean native-sized pixel clusters, not smooth gradients or high-resolution tiny linework. Keep the arms/torso and knees/boots distinctly connected. No extra weapon, limb, effect, ladder, background or border. Output only the exact six complete sprites with genuine transparent background and no halo, shadow, text or labels.'''
 (out/'prompt.txt').write_text(prompt,'utf8');write(out/'manifest.json',{'parent_arc':p.relative_to(ROOT).as_posix(),'parent_arc_sha256':digest(p),'base_pose_reference_arc':bp.relative_to(ROOT).as_posix(),'base_pose_reference_arc_sha256':digest(bp),'refs':refs,'frames':frames,'native_cell':[64,64],'world_crop':[-32,-36,32,28],'render_scale':8,'files':[{'path':(out/f).relative_to(ROOT).as_posix(),'sha256':digest(out/f)}for f in('targets.png','style.png','accepted_base_pose_reference.png','prompt.txt')],'scope':'Ultimate 사다리1431441463고유몸체×전후2의상 첫페이지 입력.반전/사격/공통층은 후속.아직생성/패킹/실기없음.','native_packed':False,'runtime_verified':False});print(out)
if __name__=='__main__':main()
