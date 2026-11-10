"""나나 피격106/110 양의상 2x2 고정셀 편집입력. 효과 미포함."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
N=Path(__file__).resolve().parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need
PROMPT="""Use case: style-transfer. Asset: precisely registered original pixel-art game character sprite sheet.
Image 1 is the EDIT TARGET: exactly FOUR complete sprites in a 2x2 grid. TOP LEFT Nana basic outfit recoil pose106; TOP RIGHT same basic outfit airborne recoil pose110; BOTTOM LEFT Nana Fourth black veil outfit pose106; BOTTOM RIGHT same Fourth outfit pose110. Image 2 is STYLE ONLY: accepted idle and accepted new airborne pose, corresponding basic top/Fourth bottom.
Redraw the four target figures with the fine pixel-art language of the accepted idle: discrete pink hair strands and separated dark/mid/light clusters, layered fringe and clear small green eye, crisp thin selective dark outline, readable black blouse/sleeve folds and skirt panels. Preserve her small black hat; the lower row alone has the long black veil and its red lining, fine lace/garter design and short dark red shoes; the upper row keeps long black boots with burgundy trim. Keep precisely the costume and identity shown, without adding armor or other character features.
The target sheet is a fixed 1536 square with four equal 768 square cells representing 96x96 native pixels each. Keep every figure in its SAME cell at its SAME position and overall scale. The recoil pose leans back and curls the knees, with hands close to the chest. Do not turn it into idle or an attack. Preserve face angle, head center, shoulder, wrist, knee, ankle and both shoe-tip positions. Pose110 is airborne; do not push it down to a floor. Pose106's lower feet should remain at their own original heights. Hair can gain fine strand detail, but no wider head, taller body, longer legs, shortened feet or large new hair mass. Do not stretch a limb or copy a flat old head over the new art.
Output a transparent-background 2x2 sheet, only these FOUR full-body sprites, no labels, no grid lines, no frames, no extra figure, no effects, sparks, blood, flashes, shadows, background or glow. Use crisp intentional pixel clusters, no soft illustration shading or antialias halo. Preserve negative spaces between both legs and arms, thin outline around black boots and wrists, and the original overlap order of the two legs. No new gun or weapon if it is not visible in the target; retain the hands and any small visible held part in place. Match detail density and native body scale of the idle style reference, not the flat hair or blocky sleeve texture of the target."""

def main():
    p=N/'rising_repaint/packed_base_candidate_v1/PL00_U.ARC';need(digest(p)=='3bd156730cb932f2a97b43acc85f0d2209537c76cbab6d298c973438bc251b42','부모')
    a=Archive(p.read_bytes());out=N/'hurt_repaint/first_inputs_v1';out.mkdir(exist_ok=False)
    target=Image.new('RGBA',(1536,1536));style=Image.new('RGBA',(1536,1536));frames=[]
    for row,mask in enumerate((0,15)):
        for col,n in enumerate((106,110)):
            im=a.composite(n,mask)[0];cell=im.crop((112,112,208,208));target.alpha_composite(cell.resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
            k=0 if col==0 else 47;style.alpha_composite(a.composite(k,mask)[0].crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
            arr=np.array(im);yy,xx=np.nonzero(arr[:,:,3]);frames.append({'cell':row*2+col,'ref':n,'form':'base'if mask==0 else'fourth','mask':mask,'rgba_sha256':sha(im.tobytes()),'world_bbox':[int(xx.min())-160,int(yy.min())-160,int(xx.max())-159,int(yy.max())-159],'fixed_cell_world':[-48,-48,48,48]})
    target.save(out/'targets.png');style.save(out/'style.png');(out/'prompt.txt').write_text(PROMPT,'utf8')
    write(out/'manifest.json',{'source_arc':p.relative_to(ROOT).as_posix(),'source_arc_sha256':digest(p),'frames':frames,'native_cell':[96,96],'render_scale':8,'inputs':[{'path':(out/n).relative_to(ROOT).as_posix(),'sha256':digest(out/n)}for n in('targets.png','style.png','prompt.txt')],'source_scope':'현재 나나 고유 그림만 입력. 원작 번개/섬광 효과 제외. 106/110두 포즈를 각 기본/포스 의상으로 제작.','native_packed':False,'runtime_verified':False})
    print(json.dumps({'inputs':str(out),'figures':4}))
if __name__=='__main__':main()
