"""등장133/135 두 포즈×전후 의상의 고정원점 입력. 원본/ARC 수정 없음."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need
PROMPT="""Use case: style-transfer. A neutral full-body character animation reference sheet for a 1990s console pixel-art action game.
Image 1 is the EDIT TARGET, exactly four complete adult-character sprites in a fixed 2x2 grid: top left is Nana in her pink jacket landing pose133; top right is the same jacket outfit rising into ready pose135. Bottom row repeats those same two poses in her accepted black-and-pink athletic swimsuit costume, without a jacket. Image 2 is STYLE ONLY: accepted idle and accepted detailed airborne art for each costume row.
Redraw the two poses with the accepted idle's crisp small pixel clusters: layered pink fringe and separated dark/middle/light hair strands, compact face and small green eyes, recognizable bunny-ear head accessory, subtle selective outlines. Restore the TOP row's clearly readable pink JACKET: long sleeves to the pale cuffs, shoulder and elbow folds, lapels and hem as shown in the accepted idle. The old target's tiny jacket fragments are not the clothing design to copy. Preserve the neutral outfit coverage, torso identity and natural full-body game pose. Bottom row has bare arms and the established black straps/pink waist accents, no leftover pink cuffs or jacket collar. Preserve the same visible face, hair, hand and leg anatomy across the two costume versions.
Pose133 is a low landing crouch: front knee deeply bent, the opposite leg extending back-right, one hand lowered near the ground and the other forward. Pose135 is a rising ready posture, both feet on the original floor, bent arms near the chest. Preserve exact target facing direction, eye and ear center, shoulder/wrist positions, each knee/ankle/shoe-tip position, both soles, overlap order and silhouette negative spaces. No whole-body scaling, enlarged face, shortened calves, thick legs, shoe enlargement or pose replacement. Keep any visible tiny held pistol part at its original position; do not invent an extra weapon or firing effect.
The input is1536x1536, four equal768x768 cells representing96x96 native pixels. Each figure must stay at exactly its own existing cell origin and scale. Use Image2 for detail density and clothing identity, NOT its other poses. No copying old flat hair or skin blocks over the new detailed art.
Output only FOUR complete figures in the same2x2 layout, genuinely transparent background. No labels, guide lines, border, particles, aura, light effects, cast shadows, gloss, blur or halo. This is a neutral, nonsexual game animation study with ordinary outfit coverage and no body-part emphasis. Crisp intentional pixel clusters and small readable clothing folds."""
def main():
    p=N/'ultimate_hurt_repaint/packed_hurt_candidate_v1/PL02_U.ARC';need(digest(p)=='c9e68442829a7f149ae86317c88172e27dbce545e454687b98310fad28ef83a5','현재 동결 부모')
    frozen=p.parent/'FROZEN.json';need(json.loads(frozen.read_text('utf8'))['frozen'],'피격 동결 필요')
    a=Archive(p.read_bytes());out=D/'first_inputs_v1';out.mkdir(exist_ok=False);target=Image.new('RGBA',(1536,1536));style=Image.new('RGBA',(1536,1536));frames=[]
    for row,mask in enumerate((15,0)):
        for col,n in enumerate((133,135)):
            im=a.composite(n,mask)[0];target.alpha_composite(im.crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
            ref=0 if col==0 else 47;style.alpha_composite(a.composite(ref,mask)[0].crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
            yy,xx=np.nonzero(np.array(im)[:,:,3]);frames.append({'cell':row*2+col,'ref':n,'form':'before'if mask else'after','mask':mask,'rgba_sha256':sha(im.tobytes()),'world_bbox':[int(xx.min())-160,int(yy.min())-160,int(xx.max())-159,int(yy.max())-159],'fixed_cell_world':[-48,-48,48,48]})
    target.save(out/'targets.png');style.save(out/'style.png');(out/'prompt.txt').write_text(PROMPT,'utf8')
    write(out/'manifest.json',{'source_arc':p.relative_to(ROOT).as_posix(),'source_arc_sha256':digest(p),'source_frozen_sha256':digest(frozen),'frames':frames,'native_cell':[96,96],'render_scale':8,'inputs':[{'path':(out/n).relative_to(ROOT).as_posix(),'sha256':digest(out/n)}for n in('targets.png','style.png','prompt.txt')],'scope':'Ultimate 두 등장몸체×두 의상만 입력.134 및140 등 효과는 생성입력에 포함하지 않음.','native_packed':False,'runtime_verified':False})
    print(json.dumps({'out':str(out),'frames':len(frames)}))
if __name__=='__main__':main()
