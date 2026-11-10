"""Ultimate 사다리 마지막154/183의 네 전신 원화 입력."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need
def main():
 p=N/'ultimate_return_repaint/packed_return_candidate_v1/PL02_U.ARC';need(digest(p)=='493bf2706aae33b64c4ffe70be1576a7ed63b0a4f62c54e89ca5876131392e29','동결부모');a=Archive(p.read_bytes());bp=N.parent/'root_nana_ladder/packed_ladder07/PL00_U.ARC';b=Archive(bp.read_bytes());out=D/'c_inputs_v1';out.mkdir(exist_ok=True);need(not(out/'manifest.json').exists(),'완성입력 덮기거부');refs=[154,183];crop=(128,132,192,196);stylecrop=(128,124,192,188);target=Image.new('RGBA',(1024,1024));base=Image.new('RGBA',(1024,512));style=Image.new('RGBA',(1024,1024));frames=[]
 for row,(form,mask)in enumerate((('before',15),('after',0))):
  for col,n in enumerate(refs):
   im=a.composite(n,mask)[0];target.alpha_composite(im.crop(crop).resize((512,512),Image.Resampling.NEAREST),(col*512,row*512));alpha=np.array(im)[:,:,3];alpha[crop[1]:crop[3],crop[0]:crop[2]]=0;need(not alpha.any(),'고정입력창');frames.append({'ref':n,'form':form,'mask':mask,'cell':row*2+col,'source_rgba_sha256':sha(im.tobytes())})
  style.alpha_composite(a.composite(0,mask)[0].crop(stylecrop).resize((512,512),Image.Resampling.NEAREST),(0,row*512));z=np.array(Image.open(D/'a_arm_registered_v1'/f'{form}_146_indices.png'));style.alpha_composite(a.rgba(z,16 if mask else 0).crop(stylecrop).resize((512,512),Image.Resampling.NEAREST),(512,row*512))
 for col,n in enumerate(refs):base.alpha_composite(b.composite(n)[0].crop(crop).resize((512,512),Image.Resampling.NEAREST),(col*512,0))
 target.save(out/'targets.png');style.save(out/'style.png');base.save(out/'accepted_base_pose_reference.png')
 prompt='''Use case: style-transfer. Four neutral full-body adult heroine game sprites on an exact1024x1024 transparent canvas,2columns by2rows. Each512cell represents64x64 native game pixels.
Image1 is the edit target. Column1 is154, a side-view forward-leaning climb-over transition with both arms reaching forward and bent legs trailing back. Column2 is183, a back-view rung hold with two hands spread to opposite sides and one folded knee. Preserve those exact gestures, every hand/foot center, knee bend, floor level, head orientation and body scale. Never add front eyes or a face to the back-facing183.
TOP ROW is the accepted pink jacket costume with its gray/white lower clothing. BOTTOM ROW is the accepted black sleeveless top and BLACK lower costume with the narrow PINK waistband; use Image2 bottom-left idle as the outfit authority. The old target contains pale clothing and pink sleeve artifacts: do not carry those into the bottom-row arms or black hip garment. Keep coverage and body contour unchanged; do not expose additional skin or alter anatomy. Bottom arms remain bare from shoulder to black wrist cuff.
Image2 is style only: accepted idle in its left column, our new back-view climbing146 in its right column. Match the detailed pink hair locks, burgundy shadow clusters, green footwear and selective skin shadows. Image3 is an accepted basic-costume version of these SAME poses for joint direction and back-hair movement only, never copy its black dress or tall boots.
Improve flat hair, jacket folds and cuffs to the style quality without simplifying the silhouette, widening the head or lengthening limbs. Preserve the separate knees, ankle-to-shoe connection and raised/low hand heights. No gun, extra limb, effect, ladder, label, border, cast shadow, gradient backdrop or halo. Output only four complete sprites with genuine transparency, fixed layout and clean native-sized pixel clusters.'''
 (out/'prompt.txt').write_text(prompt,'utf8');write(out/'manifest.json',{'parent_arc':p.relative_to(ROOT).as_posix(),'parent_arc_sha256':digest(p),'base_pose_reference_arc':bp.relative_to(ROOT).as_posix(),'base_pose_reference_arc_sha256':digest(bp),'refs':refs,'columns':2,'rows':2,'frames':frames,'native_cell':[64,64],'world_crop':[-32,-28,32,36],'render_scale':8,'files':[{'path':(out/f).relative_to(ROOT).as_posix(),'sha256':digest(out/f)}for f in('targets.png','style.png','accepted_base_pose_reference.png','prompt.txt')],'native_packed':False,'runtime_verified':False});print(out)
if __name__=='__main__':main()
