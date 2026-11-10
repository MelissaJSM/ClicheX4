"""고유 탑승4자세의 전후 의상 입력을 원점 고정으로 준비한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need
def main():
 p=N/'ultimate_recoil_repaint/packed_recoil_candidate_v1/PL02_U.ARC';need(digest(p)=='ce61617f541fd59a5a3ab0b26bba6ce88cc7740bf5f9d4719c9acb129783c8d0','동결 부모');a=Archive(p.read_bytes());crop=(112,112,208,208)
 for label,refs in(('a',(162,166)),('b',(170,174))):
  out=D/f'{label}_inputs_v1';out.mkdir(exist_ok=False);target=Image.new('RGBA',(1536,1536));style=target.copy();frames=[]
  for row,(form,mask)in enumerate((('before',15),('after',0))):
   for col,n in enumerate(refs):
    im=a.composite(n,mask)[0];alpha=np.array(im)[:,:,3];alpha[112:208,112:208]=0;need(not alpha.any(),'입력창 절단');target.alpha_composite(im.crop(crop).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768));style.alpha_composite(a.composite(0 if col==0 else 33,mask)[0].crop(crop).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768));frames.append({'ref':n,'form':form,'mask':mask,'cell':row*2+col,'original_rgba_sha256':sha(im.tobytes())})
  target.save(out/'targets.png');style.save(out/'style.png')
  prompt='''Edit the FIRST transparent 2 by 2 gameplay sprite sheet. The SECOND sheet is a STYLE and CLOTHING reference only, not output poses. Repaint exactly the four existing riding sprites with the crisp detailed pixel-art treatment of the reference, preserving their fixed cell locations. Native cell is 96x96 enlarged 8x, overall1536x1536; retain blank margins and native world origins, no tight crops or scaling individual figures.
These are neutral side-view action-game animations of Nana sitting on an invisible hoverbike, leaning left toward the handlebar. Preserve the first sheet's distinct riding poses, exact head and eye positions, torso tilt, shoulder height, front fingertip, seated hip, folded knees, ankles and feet. Show only the character, no vehicle, environment, shadows or effects. Hands retain the handlebar grip, no added pistol or new props. The two costumes in each column share exactly the same pose and anatomy.
Top row: the reference's short pink jacket with clear collar, front opening, cuffs and fabric folds over the existing black-and-pink outfit. Bottom row: the same reference black-and-pink outfit with bare arms, its original narrow pink waist detail and dark torso design. Preserve the reference design without inventing shorts, white trousers or extra sleeves. Small green ankle accents and dark small shoes remain consistent. Keep the ears, pink curled hair and green eyes. Give large flat hair areas the reference's separated darker strands, pink intermediate clusters and short bright highlights; retain the original hair mass, volume and trailing direction. Use thin varied shadow edges and clear elbow, knee and ankle transitions, with highlights and darker skin shading like the reference. Maintain the compact game-sprite body size and original bent leg lengths; do not elongate torso, legs or arms. No smoothing, gradient airbrush, blurry single-color blobs, thick continuous black outlines, enlarged head, extra hands or hidden limbs. Transparent RGBA background, no labels, grid, text or additional sprites. Only four output sprites in the same cells.'''
  (out/'prompt.txt').write_text(prompt,'utf8');write(out/'manifest.json',{'parent_arc':p.relative_to(ROOT).as_posix(),'parent_arc_sha256':digest(p),'parent_frozen':True,'source_keys':list(refs),'native_cell':[96,96],'world_crop':[-48,-48,48,48],'frames':frames,'files':[{'path':(out/f).relative_to(ROOT).as_posix(),'sha256':digest(out/f)}for f in('targets.png','style.png','prompt.txt')],'scope':'탑승고유자세 신규상세 입력. 기존사다리 보류자료를 사용하지 않는다. 후속9별명은 원층관계조사 후 별도 연결.','native_packed':False,'runtime_verified':False})
 print('two fixed-origin riding pages prepared')
if __name__=='__main__':main()
