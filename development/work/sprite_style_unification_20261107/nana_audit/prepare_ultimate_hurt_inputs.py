"""Ultimate 피격의 현재4고유몸체를 재검토하고 첫2×2 원화 입력을 준비한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
N=Path(__file__).resolve().parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
PROMPT="""Use case: style-transfer. Precisely registered neutral full-body game pixel-art sprite sheet.
Image 1 is the EDIT TARGET: FOUR complete sprites in a fixed 2x2 grid. Top left and top right are Nana Ultimate before-acquisition outfit, pink jacket, recoil poses106 and110. Bottom left and bottom right are the SAME character and SAME two poses after acquisition, wearing the accepted black-and-pink swimsuit outfit without the jacket. Image 2 is STYLE ONLY, the accepted idle and detailed airborne sprite for the corresponding costume in each row.
Redraw these four recoil figures with the accepted idle's precise small pixel clusters: separated pink hair strands and dark/middle/light planes, layered fringe, recognizable small green eyes, crisp selective outline, and readable jacket cuffs, folds and hem. Keep the same bunny ears, face identity, black-and-pink outfit, green ankle details and dark shoes. The lower row must have genuinely bare arms and shoulders with the accepted black straps: no old pink sleeve or jacket collar left on those arms. Hair touching the shoulder remains pink hair, not a sleeve. Use the style references for hair detail and clothing identity, while preserving every target pose and anchor.
The first image is a 1536 square divided into four 768 square cells, each equivalent to96x96 native pixels. Every figure must remain at its own exact position and scale within its cell. Preserve head/eye center, the arm bent toward the chest, shoulder, wrists, knees, ankles and both shoe-tip positions. Keep the recoiling backwards lean and folded knees, not idle or an attack. Pose110 is airborne and its soles must not be lowered to a floor. Do not flatten, widen or lengthen legs; do not enlarge heads or narrow feet. Keep both legs separately readable. Improve detail density rather than changing anatomy or stretching existing shapes. Maintain the same body silhouette and hair across the two costume rows wherever visible, while the jacket naturally occupies its own volume.
Output only the FOUR full-body sprites, clean true transparent background, no labels, cell lines, duplicate figures, effects, flashes, aura, shadows, glow or backdrop. Crisp intentional pixel clusters with no soft illustration blur. Subtle recoil/shock expression should read at native size. No invented weapon; if a tiny held part is visible preserve it in place. Do not paste the old flat hair back over new detail. Render a neutral game animation study with no dramatic camera or scene."""
def main():
    p=N/'rising_repaint/packed_ultimate_candidate_v1/PL02_U.ARC'
    need(digest(p)=='4132738ac872750507538cd8d150e13a510422df81cea99b502e7371b6753cd9','부모')
    a=Archive(p.read_bytes());d=N/'ultimate_hurt_repaint';d.mkdir(exist_ok=True)
    review=d/'scope_review_v1';review.mkdir(exist_ok=False);rows=[]
    for n in(106,110,233,234):
        rows.append((f'Ultimate hurt {n}',[('before idle',a.composite(0,15)[0]),('current before',a.composite(n,15)[0]),('after idle',a.composite(0,0)[0]),('current after',a.composite(n,0)[0])]))
        for pb in(0,5,6,7,8):Image.fromarray(a.layer(n,pb)[0]).save(review/f'layer{pb}_{n:03}.png')
    for i in(0,2):helper.grid(rows[i:i+2],review/f'comparison_{i//2+1}.png',7)
    out=d/'first_inputs_v1';out.mkdir(exist_ok=False)
    target=Image.new('RGBA',(1536,1536));style=Image.new('RGBA',(1536,1536));frames=[]
    for row,mask in enumerate((15,0)):
        for col,n in enumerate((106,110)):
            im=a.composite(n,mask)[0];cell=im.crop((112,112,208,208));target.alpha_composite(cell.resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
            k=0 if col==0 else 47;style.alpha_composite(a.composite(k,mask)[0].crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
            yy,xx=np.nonzero(np.array(im)[:,:,3]);frames.append({'cell':row*2+col,'ref':n,'form':'before'if mask else'after','mask':mask,'rgba_sha256':sha(im.tobytes()),'world_bbox':[int(xx.min())-160,int(yy.min())-160,int(xx.max())-159,int(yy.max())-159],'fixed_cell_world':[-48,-48,48,48]})
    target.save(out/'targets.png');style.save(out/'style.png');(out/'prompt.txt').write_text(PROMPT,'utf8')
    write(out/'manifest.json',{'source_arc':p.relative_to(ROOT).as_posix(),'source_arc_sha256':digest(p),'frames':frames,'native_cell':[96,96],'render_scale':8,'inputs':[{'path':(out/n).relative_to(ROOT).as_posix(),'sha256':digest(out/n)}for n in('targets.png','style.png','prompt.txt')],'source_scope':'현재 나나 Ultimate 고유몸체만 입력. 원작 효과/점멸 제외. 대기와 새공중47은 스타일 기준.','native_packed':False,'runtime_verified':False})
    print(json.dumps({'input':str(out),'review':str(review)}))
if __name__=='__main__':main()
