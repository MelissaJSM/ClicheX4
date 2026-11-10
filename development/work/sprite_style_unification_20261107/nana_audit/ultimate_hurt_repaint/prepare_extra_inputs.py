"""Ultimate 몸통아머 피격233/234 두 몸체의 전후 의상 입력."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need
PROMPT="""Use case: style-transfer. A precisely registered neutral full-body pixel-art game animation sheet.
Image1 is the EDIT TARGET: FOUR sprites, fixed2x2 grid. TOP LEFT Nana Ultimate pink-jacket outfit recoil233. TOP RIGHT the same pink-jacket outfit recoil234. BOTTOM LEFT and BOTTOM RIGHT are identical poses in her accepted black-and-pink swimsuit outfit after acquisition, with bare arms and no jacket. Image2 is STYLE ONLY: accepted idle and accepted detailed airborne pose for each costume row.
Refine the four full bodies to match the accepted idle's small crisp selective outlines, layered pink fringe, clearly separated hair strands and dark/middle/light clusters. Improve pink jacket cuffs, folds, hem and sleeve planes. Keep the same bunny ears, small green eyes, compact face, black/pink straps, green ankle accents and dark shoes. Lower row has truly bare arms, no pink sleeve or cuff leftovers; preserve pink hair where it overlaps the shoulders. The head/face and visible legs are the same character across rows, not separate designs.
Preserve each target pose EXACTLY: pose233 is the first recoiling airborne body with the forward hand at chest level and the knees bent. Pose234 is diagonal airborne recoil, one hand shielding the forehead and legs angled down-left, hair streaming back. Do NOT change either to a standing pose or a punch. Keep both target faces/eyes, shoulders, elbow/wrist, knee, ankle and shoe-tip positions, the raised shielding hand and negative spaces between limbs. Preserve original overlap order. No whole-body scaling, enlarged head, lengthened leg, thinner ankle or shortened shoe. No invented weapon or visual effects.
The target sheet is1536x1536 with four equal768px cells, representing96x96 native pixels each. Keep all four figures at exactly their own existing center, origin and scale. Each full silhouette remains in its original cell. Copy the new DETAIL DENSITY of style references, not their different poses. Do not paste flat old head/skin blocks over newly drawn details.
Output exactly FOUR figures only with true transparent background, in the same2x2 layout. No labels, guides, cell borders, extra characters, sparks, aura, shadows, blood, light effects, glow, backdrop or antialias halo. Crisp game pixel clusters, no soft painterly shading. Neutral animation reference sheet."""
def main():
    p=N/'rising_repaint/packed_ultimate_candidate_v1/PL02_U.ARC';need(digest(p)=='4132738ac872750507538cd8d150e13a510422df81cea99b502e7371b6753cd9','부모')
    a=Archive(p.read_bytes());out=D/'extra_inputs_v1';out.mkdir(exist_ok=False);target=Image.new('RGBA',(1536,1536));style=Image.new('RGBA',(1536,1536));frames=[]
    for row,mask in enumerate((15,0)):
        for col,n in enumerate((233,234)):
            im=a.composite(n,mask)[0];target.alpha_composite(im.crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
            k=0 if col==0 else 47;style.alpha_composite(a.composite(k,mask)[0].crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
            yy,xx=np.nonzero(np.array(im)[:,:,3]);frames.append({'cell':row*2+col,'ref':n,'form':'before'if mask else'after','mask':mask,'rgba_sha256':sha(im.tobytes()),'world_bbox':[int(xx.min())-160,int(yy.min())-160,int(xx.max())-159,int(yy.max())-159],'fixed_cell_world':[-48,-48,48,48]})
    target.save(out/'targets.png');style.save(out/'style.png');(out/'prompt.txt').write_text(PROMPT,'utf8')
    write(out/'manifest.json',{'source_arc':p.relative_to(ROOT).as_posix(),'source_arc_sha256':digest(p),'frames':frames,'native_cell':[96,96],'render_scale':8,'inputs':[{'path':(out/n).relative_to(ROOT).as_posix(),'sha256':digest(out/n)}for n in('targets.png','style.png','prompt.txt')],'source_scope':'나나 Ultimate 고유233/234만 입력,235/236오라 제외.','native_packed':False,'runtime_verified':False})
    print(json.dumps({'input':str(out)}))
if __name__=='__main__':main()
