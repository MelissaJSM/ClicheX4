"""새 호버 몸체와 기존 사격 좌표를 분리한 새팔 입력."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need
def main():
 p=N/'ultimate_vehicle_repaint/packed_vehicle_candidate_v1/PL02_U.ARC';a=Archive(p.read_bytes());Y,X=np.indices((384,384));Y-=160;X-=160
 for page,refs in [('a',[222,224,226,228]),('b',[230])]:
  out=D/f'shot_{page}_inputs_v1';out.mkdir(exist_ok=False);side=1536 if len(refs)>1 else 768;cell=768;boards={k:Image.new('RGBA',(side,side))for k in('new_bodies','old_firing_pose','barrel_positions')};proof=[]
  for i,n in enumerate(refs):
   src=D/f'canonical_cases_probe_v3/body_{n-1:03}_indices.png';new=np.array(Image.open(src));old=a.layer(n)[0];yy,xx=np.nonzero(old);mx=int(xx.min())-160;ys=np.nonzero(old[:,mx+160])[0]-160;top,bottom=int(ys.min()),int(ys.max());guard=(X>=mx)&(X<mx+8)&(Y>=top-1)&(Y<=bottom+4);bar=np.where(guard,old,0).astype(np.uint8);place=(i%2*cell,i//2*cell)if len(refs)>1 else(0,0)
   ims={'new_bodies':a.rgba(new),'old_firing_pose':a.composite(n,15)[0],'barrel_positions':a.rgba(bar)}
   for name,im in ims.items():boards[name].alpha_composite(im.crop((112,112,208,208)).resize((cell,cell),Image.Resampling.NEAREST),place)
   Image.fromarray(bar).save(out/f'old_barrel_window_{n}.png');proof.append({'ref':n,'body_ref':n-1,'cell':i,'body_source':src.relative_to(ROOT).as_posix(),'body_source_sha256':digest(src),'old_muzzle_column':mx,'old_muzzle_rows':[top,bottom],'old_gun_window':[mx,top-1,mx+8,bottom+5],'window_sha256':sha(bar.tobytes()),'window_semantic_classification_pending':True})
  for name,im in boards.items():im.save(out/f'{name}.png')
  layout='four corresponding sprites in exactly the same2x2 cells of the full square canvas'if len(refs)>1 else'exactly one sprite in the same full square canvas'
  prompt=f'''Edit the FIRST image, a transparent sheet of adult Nana action-game sprites. Return {layout}. FIRST image is the new detailed body master to preserve. SECOND image shows each corresponding original firing pose, only as an arm-angle and weapon-position guide. THIRD image isolates the original pistol target windows in the same canvas coordinates. Keep the full canvas and margins, exact native96x96 cell coordinate system, character scale, eye/face, rabbit-ear accessories, pink hair curls, torso, black-and-pink outfit, opposite arm, legs, gray propulsion shoes and foot endpoints from FIRST image.
Change ONLY the front arm currently holding the pistol near the chest into the corresponding horizontal left-facing firing arm from SECOND. Replace that existing bent arm and its held pistol; do not add a third arm, duplicate fist or second gun. Attach the new upper arm naturally at the SAME shoulder on the FIRST-image torso, with the elbow, forearm, wrist and fingers extending to the fixed THIRD-image pistol location. Keep the precise original muzzle endpoint, compact pink-and-black pistol size, horizontal direction and hand grip from SECOND/THIRD. The other arm (raised above/behind the head on the first two poses, lowered on the others) remains untouched. Do not paint a pink sleeve, straight dark chest bar, extra skin hand, new props, jet flames or muzzle effects. Preserve subtle tan skin midtone and shadow clusters around elbow and wrist, so the arm has a clear fine lower shadow contour and compact thickness consistent with the master legs and accepted body. The outfit and coverage stay exactly as supplied. Neutral full-body side-view gameplay artwork, no anatomical emphasis.
Use crisp deliberate square pixel-art clusters at the master detail level, no smooth painting, blur, body scaling, stretched torso or enlarged hands. Transparent RGBA background, no text, lines, labels, grids, shadows or extra figures. Only the original front arm changes into its shooting pose; all remaining body details and coordinate origins stay fixed.'''
  if len(refs)==1:prompt=prompt.replace('The other arm (raised above/behind the head on the first two poses, lowered on the others) remains untouched.','The other lowered arm remains exactly as in FIRST image.')
  (out/'prompt.txt').write_text(prompt,'utf8');write(out/'manifest.json',{'parent_arc':p.relative_to(ROOT).as_posix(),'parent_arc_sha256':digest(p),'frames':proof,'native_cell':[96,96],'input_cell':[768,768],'output_scope':'새 사격팔 원화 입력. 총구의 현재 표시 좌표는 추출값이며 원US 발사 초기화 검사와 별개. 신발 국소 정합·층·패킹은 후속.','files':[{'path':q.relative_to(ROOT).as_posix(),'sha256':digest(q)}for q in sorted(out.iterdir())if q.is_file()],'native_packed':False,'runtime_verified':False})
 print('shot a4+b1 inputs saved')
if __name__=='__main__':main()
