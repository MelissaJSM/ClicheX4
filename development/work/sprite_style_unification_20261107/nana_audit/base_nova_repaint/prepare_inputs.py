"""기본/포스 Nova 준비213/215 고정셀. 원ARC 입력전용, 새작업폴더만 출력."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
P=ROOT/'work/sprite_style_unification_20261107/root_nana_hover/packed_hover_final01/PL00_U.ARC'
EXPECTED='9c1ff453a2308ddc40f39e5790de0aa6a5cf41dda43165b0fa16808f8c3a643c'
def main():
    need(digest(P)==EXPECTED,'동결부모');a=Archive(P.read_bytes());out=D/'a_inputs_v1';out.mkdir(exist_ok=False)
    target=Image.new('RGBA',(1536,1536));style=target.copy();frames=[];rows=[];crop=(112,112,208,208)
    for row,(form,mask) in enumerate((('base',0),('fourth',15))):
        for col,n in enumerate((213,215)):
            im=a.composite(n,mask)[0];alpha=np.array(im)[:,:,3].copy();alpha[112:208,112:208]=0;need(not alpha.any(),'고정창 절단')
            target.alpha_composite(im.crop(crop).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
            style.alpha_composite(a.composite(0 if col==0 else 89,mask)[0].crop(crop).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
            frames.append({'ref':n,'form':form,'mask':mask,'cell':row*2+col,'original_rgba_sha256':sha(im.tobytes())})
            rows.append((f'{form} {n}',[('approved idle',a.composite(0,mask)[0]),('old target',im),('approved charge',a.composite(89,mask)[0])]))
    target.save(out/'targets.png');style.save(out/'style.png');helper.grid(rows,out/'input_review.png',5)
    prompt='''Use case: style-transfer. Edit the FIRST transparent 2 by 2 pixel sprite sheet. The SECOND sheet is the approved adult Nana character detail and clothing reference. Output exactly FOUR sprites on the FIRST sheet's transparent square canvas, same two columns and two rows.
The first sheet is a fixed pose and position template: every cell is 96 by 96 game pixels enlarged eight times. Preserve all blank margins, exact eye/head location and head size, torso angle, shoulders, both hands, hips, knees, ankles, toe endpoints and foot heights. Do not zoom, enlarge, stretch, shift or recenter a character. Both costume versions in each column have the same joint positions.
Left column: tightly bent knees in a compact airborne preparation stance. One small fist is held in front of the chest pointing left, and the other arm bends close to the right side of the torso. Right column: the left-facing hand is raised high next to/above the forehead, with its wrist joined to the bent arm; the other hand is near the waist. The front knee is folded up and the rear boot/shoe reaches diagonally down-right. Preserve the high fist in the right column. It is a hand and cuff, not a hat ornament. Keep exactly two arms and two legs in every sprite.
Top row is Nana's approved BASE costume from the top of the second image: black beret, pink curled hair, dark black long-sleeved dress with readable collar and folded sleeves, the same skirt and compact dark boots. Bottom row is Nana's approved FOURTH costume from the bottom of the second image: the matching black bonnet/veil, dark fitted dress and the same exposed leg and small shoe design as the reference. Keep the veil trailing behind the head and distinguish it from pink hair. These are fully clothed neutral action poses of an adult game heroine. Do not substitute a pink jacket, swimsuit, white shorts, different armor or other costume.
Replace broad flat hair areas with darker curled locks, mid-pink strands and small bright highlights like the approved second image. Add meaningful face/eye, collar, sleeve-fold, skirt-fold and boot/shoe details at the SAME small game scale. Keep a thin variable dark silhouette and natural skin shadow at knees/ankles/hands. Preserve compact torso and the existing leg lengths, boot widths and feet separation. Do not flatten the curls into a smooth pink blob, lengthen the legs, make pencil-thin ankles, or make thick uniform outlines.
This is a non-firing preparation pose. Preserve the EMPTY HANDS shown in the first image; no pistol, arm cannon, projectile, glowing aura or new effect. No extra hand/limb, duplicated ear/hat, labels, grid, text, cast shadow, scenery or background. Transparent RGBA only, exactly four sprites in their unchanged cells.'''
    (out/'prompt.txt').write_text(prompt,'utf8')
    write(out/'manifest.json',{'parent_arc':P.relative_to(ROOT).as_posix(),'parent_sha256':EXPECTED,'source_keys':[213,215],'native_cell':[96,96],'world_crop':[-48,-48,48,48],'frames':frames,'files':[{'path':(out/f).relative_to(ROOT).as_posix(),'sha256':digest(out/f)}for f in('targets.png','style.png','prompt.txt','input_review.png')],'scope':'기본/포스 준비 고유2몸체×의상4셀의 새상세 입력.214는119/34셀 차이의 손/효과 출처조사 중으로별도유지.216현재215별칭은후속검증.218219 별도에너지/220몸연동구조를Ultimate와혼동하지않음.','native_packed':False,'runtime_verified':False})
    print('Base/Fourth Nova preparation inputs saved.')
if __name__=='__main__':main()
