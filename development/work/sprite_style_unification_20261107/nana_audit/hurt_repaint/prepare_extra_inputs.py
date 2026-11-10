"""피격의 다른 두 몸체233/234를 양의상 네 고정셀로 준비한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,write,need,sha

PROMPT='''Use case: style-transfer. Asset: exactly registered game pixel-art sprites.
Image 1 is the edit target: FOUR full-body figures in a 2x2 sheet. TOP LEFT Nana basic outfit alternate recoil pose233; TOP RIGHT basic outfit flying recoil pose234; BOTTOM LEFT Fourth black veil outfit pose233; BOTTOM RIGHT Fourth outfit pose234. Image 2 is the accepted IDLE and new AIRBORNE STYLE ONLY, with the basic outfit on the top row and Fourth outfit on the bottom row.
Redraw just the four target figures with the fine detail density of the accepted style: separate pink hair locks with dark/mid/light clusters; small stable face and hat; crisp selective one-pixel contours; readable black sleeve folds, lace cuffs and skirt panels. The upper row has the long dark boots with burgundy trim; lower row alone has black veil with dark red lining, bare legs/garter lace and dark red short shoes. Keep the clothing identity and its tiny accessory shapes, no added armor.
The target canvas is a FIXED 1536x1536 with four equal 768x768 cells, each corresponding to native96x96 pixels. Keep every original figure's position, head size, overall body scale and recoil pose within the SAME cell. Pose233 and pose234 are DIFFERENT: preserve their own head angle, bent/raised arm, knee bend and diagonal direction of the legs. Keep the hand shielding/raised near the head in its exact target position, preserve hands/face negative spaces. Do not make a standing pose, do not push an airborne foot to a floor. Do not lengthen the leg or change either shoe tip position. Preserve the pose's flowing hair direction, but do not inflate the head or copy a flat old hair block over the new detailed hair. Keep the two legs and feet separately readable at the same native scale.
Output only the FOUR complete sprites in the same fixed 2x2 cells on genuinely transparent background. No text, grid, frames, background, glow, flashes, electric sparks, blood, cast shadows, extra figure or extra limb. No new gun if absent from the target. Preserve any visible held part as shown. Crisp intentional pixel clusters, not smooth illustration or antialiased halo. The new material shading and outline density should match the style idle, while the target posture, scale and contact coordinates stay fixed.'''

def main():
    p=N/'rising_repaint/packed_base_candidate_v1/PL00_U.ARC'
    need(digest(p)=='3bd156730cb932f2a97b43acc85f0d2209537c76cbab6d298c973438bc251b42','부모')
    a=Archive(p.read_bytes());out=D/'extra_inputs_v1';out.mkdir(exist_ok=False)
    target=Image.new('RGBA',(1536,1536));style=Image.new('RGBA',(1536,1536));frames=[]
    for row,mask in enumerate((0,15)):
        for col,n in enumerate((233,234)):
            im=a.composite(n,mask)[0]
            target.alpha_composite(im.crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
            k=0 if col==0 else 47
            style.alpha_composite(a.composite(k,mask)[0].crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
            arr=np.array(im);y,x=np.nonzero(arr[:,:,3])
            frames.append({'cell':row*2+col,'ref':n,'form':'base'if mask==0 else'fourth','mask':mask,
                           'rgba_sha256':sha(im.tobytes()),'world_bbox':[int(x.min())-160,int(y.min())-160,int(x.max())-159,int(y.max())-159],
                           'fixed_cell_world':[-48,-48,48,48]})
    target.save(out/'targets.png');style.save(out/'style.png');(out/'prompt.txt').write_text(PROMPT,'utf8')
    write(out/'manifest.json',{'source_arc':p.relative_to(ROOT).as_posix(),'source_arc_sha256':digest(p),'frames':frames,
                             'native_cell':[96,96],'render_scale':8,
                             'inputs':[{'path':(out/n).relative_to(ROOT).as_posix(),'sha256':digest(out/n)}for n in('targets.png','style.png','prompt.txt')],
                             'source_scope':'현재 나나233/234 고유 몸체만 입력. 번개·광원 효과 제외. 기존 배치와 자세 고정.',
                             'native_packed':False,'runtime_verified':False})
    print(json.dumps({'out':str(out),'refs':[233,234],'figures':4}))
if __name__=='__main__':main()
