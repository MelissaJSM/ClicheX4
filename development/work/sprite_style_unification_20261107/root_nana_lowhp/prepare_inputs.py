"""Inspect current low-HP native frames and prepare a fixed-cell art edit."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive,page
from scripts.prepare_shibuki_ultimate_production import records
sha=lambda b:hashlib.sha256(b).hexdigest()
def main():
 source=W/'root_nana_ladder/packed_ladder07/PL00_U.ARC';data=source.read_bytes();assert sha(data)=='509cc9785cb5eb3dca9f7a8a3fd1d3ea334887a98d3834b9f327266b3c6bbdce';a=Archive(data)
 out=D/'inputs01';out.mkdir(exist_ok=False);target=Image.new('RGBA',(1536,1536));style=Image.new('RGBA',(1536,1536));frames=[];relations=[]
 for row,(form,mask) in enumerate((('base',0),('fourth',15))):
  for col,n in enumerate((122,123)):
   im=a.composite(n,mask,2)[0];target.alpha_composite(im.crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
   st=0 if col==0 else 106;style.alpha_composite(a.composite(st,mask,2)[0].crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
   frames.append({'cell':row*2+col,'form':form,'mask':mask,'ref':n,'rgba_sha256':sha(im.tobytes()),'bbox':im.getbbox()})
  page([(f'{form} low HP {n}',a.composite(n,mask,2)[0]) for n in range(120,126)],a.composite(0,mask)[0],out/f'{form}_current.png',cols=3,scale=4)
  for n in (120,122,124):
   p=np.array(a.composite(n,mask,2)[0]);q=np.array(a.composite(n+1,mask,2)[0]);yy,xx=np.where(np.any(p!=q,axis=2));diff=list(zip((xx-160).tolist(),(yy-160).tolist()));relations.append({'form':form,'pair':[n,n+1],'mouth_rgba_diff_world':diff,'body_bbox':list(a.composite(n,mask,2)[0].getbbox()),'shared_stream':a.banks[0]['frames'][n]['offset']==a.banks[0]['frames'][n+1]['offset']})
 target.save(out/'targets.png');style.save(out/'style.png')
 prompt='''Use case: style-transfer; fixed-registration PS1 Mega Man X4 sprite sheet.
 Image 1 is the edit target with FOUR Nana low-health sprites in a 2x2 grid. TOP row: accepted black beret, long pink hair, fitted black blouse and skirt, asymmetric dark stockings/boots. BOTTOM row: accepted Fourth Armor black folded hood/veil over pink hair, black costume with white ornamental hem, pale legs and small red-black shoes. LEFT column is mouth closed, RIGHT column mouth slightly open; each row must otherwise be exactly the same pose and body. Image 2 is STYLE ONLY: accepted idle at left and newly detailed reaction at right in the matching costume rows.
 Redraw the target low-health pose with the accepted idle's careful thin selective dark contour, distinct pink hair locks with light/mid/dark clusters, readable black cloth folds, cuffs and boot seams. Keep a compact human figure of the exact current size, not a rounded chibi. Preserve current shoulders, face/eye location, torso length, waist, hip, knee, ankle, foot contact, head height and entire fixed-cell placement. Preserve the tired forward lean with one hand resting on the abdomen and the other hand holding Nana's small pink/black pistol loosely downward. The pistol is her weapon Sarang: keep its current size, angle and hand contact; do not omit it or turn the hand into a black lump. Keep the veil's accepted length and layered folds and keep hair distinct underneath.
 Face expression: tired, with the same tiny green eye at the same location. In the right column ONLY open the mouth a tiny amount; no other face, hair, limb or clothing movement. Do not add tears, sweat drops, stars, wounds, blood, exaggerated grimacing or extra effects. This is a neutral fully clothed game animation.
 Canvas1536x1536, 2x2 grid of768px cells; each cell represents96x96 game pixels at exact8x enlargement. Keep the entire transparent cell framing, do not crop/auto-center/rescale individual sprites. Design crisp clusters suitable for45–50 native-pixel-tall figures; preserve proportional head/body/feet, thin clean outlines and subdued native palette. Output exactly four figures on true transparent background; no captions, dividers, guides, scenery, shadows, bloom, soft brush rendering or antialias halos.'''
 (out/'prompt.txt').write_text(prompt,'utf8')
 (out/'manifest.json').write_text(json.dumps({'source_arc':source.relative_to(ROOT).as_posix(),'source_arc_sha256':sha(data),'frames':frames,'relations':relations,'native_cell':[96,96],'render_scale':8,'inputs':[{'path':(out/n).relative_to(ROOT).as_posix(),'sha256':sha((out/n).read_bytes())} for n in ('targets.png','style.png','prompt.txt')],'scope':'나나 기본/포스 저체력122/123 새 원화 입력.120/124 호흡은 최종 몸체의 원위상·발고정 파생 예정, 게임 파일 미변경.','runtime_verified':False},ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'out':str(out),'relations':relations},ensure_ascii=False))
if __name__=='__main__':main()
