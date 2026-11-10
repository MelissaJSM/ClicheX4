"""Ultimate 사다리 후속 고유3자세×전후 의상 입력을 별도 준비한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need
def main():
 p=N/'ultimate_return_repaint/packed_return_candidate_v1/PL02_U.ARC';need(digest(p)=='493bf2706aae33b64c4ffe70be1576a7ed63b0a4f62c54e89ca5876131392e29','최신Ultimate동결');a=Archive(p.read_bytes());bp=N.parent/'root_nana_ladder/packed_ladder07/PL00_U.ARC';need(digest(bp)=='509cc9785cb5eb3dca9f7a8a3fd1d3ea334887a98d3834b9f327266b3c6bbdce','기본형동결');b=Archive(bp.read_bytes())
 out=D/'b_inputs_v1';out.mkdir(exist_ok=False);refs=[149,151,153];crop=(128,124,192,188);target=Image.new('RGBA',(1536,1024));style=Image.new('RGBA',(1536,1024));base=Image.new('RGBA',(1536,512));frames=[];styles=[]
 for row,(form,mask)in enumerate((('before',15),('after',0))):
  for col,n in enumerate(refs):
   im=a.composite(n,mask)[0];target.alpha_composite(im.crop(crop).resize((512,512),Image.Resampling.NEAREST),(col*512,row*512));y,x=np.nonzero(np.array(im)[:,:,3]);need(x.min()>=crop[0]and y.min()>=crop[1]and x.max()<crop[2]and y.max()<crop[3],'전신입력범위');frames.append({'ref':n,'form':form,'mask':mask,'cell':row*3+col,'world_bbox':[int(x.min()-160),int(y.min()-160),int(x.max()-159),int(y.max()-159)],'source_rgba_sha256':sha(im.tobytes())})
  style.alpha_composite(a.composite(0,mask)[0].crop(crop).resize((512,512),Image.Resampling.NEAREST),(0,row*512))
  for col,n in((1,144),(2,146)):
   src=D/'a_arm_registered_v1'/f'{form}_{n}_indices.png';z=np.array(Image.open(src));style.alpha_composite(a.rgba(z,16 if mask else 0).crop(crop).resize((512,512),Image.Resampling.NEAREST),(col*512,row*512));styles.append({'form':form,'ref':n,'path':src.relative_to(ROOT).as_posix(),'sha256':digest(src)})
 for col,n in enumerate(refs):base.alpha_composite(b.composite(n)[0].crop(crop).resize((512,512),Image.Resampling.NEAREST),(col*512,0))
 target.save(out/'targets.png');style.save(out/'style.png');base.save(out/'accepted_base_pose_reference.png')
 prompt='''Use case: style-transfer. Neutral full-body adult heroine game-sprite cleanup. Exactly1536x1024 transparent canvas,3columns by2rows; each512x512cell equals64x64 native pixels.
Image1 is the edit target. TOP ROW left to right: ladder149,151,153 in the established pink jacket outfit. BOTTOM ROW: the same three gestures in the established black-and-pink sleeveless costume. Maintain the same modest outfit coverage and style as Image2. Bottom row has bare arms from shoulder to black hand cuff, with no pink jacket sleeves or white sleeve-edge bands. Do not copy any old pink sleeve artifacts from Image1 bottom row.
Image2 is clothing/hair/skin style reference only: accepted idle in column1, new back-view climbing144/146 in columns2/3. Match its head size, layered pink locks, short ears, distinct burgundy hair shadows, jacket folds and bare-arm shading. Do not substitute its poses. Image3 shows the already accepted basic-costume versions of the exact149/151/153 gestures: use it for actual hand-grip direction, wrist/elbow alignment and back-hair rhythm only, never copy its black dress or tall boots.
Keep the exact hand-grip centers, wrist/elbow/shoulder, two distinct feet, knee bends and floor positions from Image1. These are back/three-quarter climbing movements; preserve each view direction. Where the head faces away, show layered back-hair and ears with no front-facing eyes or face. Do not add a second face or mirror the hands. Do not straighten the crouched climbing leg or shorten the shin.
Improve broad flat hair and fabric areas with coherent native-size pixel clusters and selective shadows. Keep readable one-pixel shadow-side skin edges and wrist/ankle connections, no uniform thick black outlines. No overall scaling, changed silhouette width, moved body origin, enlarged head, longer limbs, extra gun, effect, ladder or object. Output six complete neutral game sprites, transparent background, no halo, labels, text, border or cast shadow.'''
 (out/'prompt.txt').write_text(prompt,'utf8');write(out/'manifest.json',{'parent_arc':p.relative_to(ROOT).as_posix(),'parent_arc_sha256':digest(p),'base_pose_reference_arc':bp.relative_to(ROOT).as_posix(),'base_pose_reference_arc_sha256':digest(bp),'refs':refs,'frames':frames,'style_sources':styles,'native_cell':[64,64],'world_crop':[-32,-36,32,28],'render_scale':8,'files':[{'path':(out/f).relative_to(ROOT).as_posix(),'sha256':digest(out/f)}for f in('targets.png','style.png','accepted_base_pose_reference.png','prompt.txt')],'scope':'Ultimate 사다리1491511533고유몸체×전후2의상 후속페이지 입력. 기존후폼 분홍소매는 보존대상이 아니며 대기/새144146 맨팔로 교정한다.','native_packed':False,'runtime_verified':False});print(out)
if __name__=='__main__':main()
