"""기본/포스 체이서 첫2자세의 원점 고정 새 상세 원화 입력."""
from pathlib import Path
import sys,json
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,metrics

def main():
    d=H/'chaser_base_inputs01';need(not d.exists(),'새 입력 폴더 필요')
    p=H/'prepared_standing_fire_base01/PL00_U.ARC';a=Archive(p.read_bytes())
    need(sha(a.data)=='4fe7173665d2bd2e5484a8c62eeb17d286ee61b781abf78e9525e03acb5f8175','기본 부모 변경')
    target=Image.new('RGBA',(1536,1536));style=Image.new('RGBA',target.size);crop=(112,112,208,208);samples=[]
    for row,n in enumerate((162,166)):
        for col,(form,mask)in enumerate((('base',0),('fourth',15))):
            pos=(col*768,row*768);im=a.composite(n,mask)[0]
            need(im.getchannel('A').getbbox()==im.getchannel('A').crop((0,0,384,384)).getbbox(),'전신 캔버스')
            target.alpha_composite(im.crop(crop).resize((768,768),Image.Resampling.NEAREST),pos)
            sr=0 if row==0 else 92
            style.alpha_composite(a.composite(sr,mask)[0].crop(crop).resize((768,768),Image.Resampling.NEAREST),pos)
            samples.append({'form':form,'ref':n,'metrics':metrics(im),'rgba_sha256':sha(im.tobytes()),'style_ref':sr})
    prompt='''Use case: identity-preserve. Asset: detailed native console pixel-art character sprites.
Image1 is the EDIT TARGET: a transparent1536x1536 page, exactly TWO columns and TWO rows. Each768x768 cell is a96x96 logical-pixel square enlarged8x, origin(48,48). Keep all four sprites at their exact existing positions and scale within the large empty cells. Do not crop, recenter, fill the cells, enlarge heads, lengthen limbs or resize the bodies.
Top row is pose162: side-facing compact rider, torso leaning forward, both forearms reaching left to grip unseen vehicle handlebars, thighs bent and feet tucked under the body. Bottom row pose166 leans farther forward: maintain its different head/neck angle, shoulder/hip positions and bent knees. These are riding/crouching poses, not standing poses. Keep the targets' exact hand tips, elbows, seat/hip point, knee bends, ankles and boot soles. The left and right versions of each row represent the SAME character with matching joints and head size, only clothes differ. Exactly two real arms/hands and two legs; do not add a gun, handlebar or vehicle.
Image2 is the STYLE/COSTUME reference. Top row is the current accepted idle of each outfit, bottom row the newly detailed recovery pose92. Use this detail level and character identity to REDRAW the target's old large flat hair and clothes. Preserve the compact fox-like body and short limbs, gentle rounded volume, visible gold eye, pointed fox ears, long lavender hair locks and braid flowing backward. Preserve the target head tilt and gaze left. Head and body sizes stay at their target dimensions: the rider's lower total height comes from crouching, not a smaller or thinner body.
LEFT column BASE costume: red hair ribbon at the back of the ears; light lavender-white wide sleeves with controlled purple folded shadows, red accents/lacing and a red-white short outfit, white/lavender boots. RIGHT column FOURTH costume: the same hair with the small dark/gold ornament; black and dark-purple bodice/sleeves with restrained gold fasteners, pale collar accents and dark boots. Follow the actual respective reference closely; no broad white sleeve or red bodice on the right. Keep gloves/skin boundaries and all limb joints readable.
Draw restrained pixel clusters with2-3tone shaded planes, several coherent lavender hair locks and clear ear planes. Add real cloth folds/hem separation and boot/toe structure at the idle's density, without noisy single-pixel hatching or extra black outlines. Keep the large target silhouette and contact positions while improving interior detail. Transparent background only: no halo, glow, projectile, cast shadow, text, labels, grid or extra objects. Output the same four-cell page.'''
    d.mkdir();target.save(d/'edit_target.png');style.save(d/'accepted_style.png');(d/'prompt.txt').write_text(prompt,'utf8')
    write(d/'input.json',{'refs':[162,166],'forms_by_column':['base','fourth'],'parent':{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(a.data)},
        'relations':{'path':(H/'chaser_sources01/report.json').relative_to(ROOT).as_posix(),'sha256':sha((H/'chaser_sources01/report.json').read_bytes())},
        'layout':{'canvas':[1536,1536],'grid':[2,2],'logical_canvas':[192,192],'cell':[96,96],'origin':[48,48],'crop':list(crop)},
        'samples':samples,'policy':'현 몸체 원점과 체이서 손발/좌석 자세를 유지하며 새 상세로 재작화. 4폼 중 기본/포스 첫2키이며 다른폼 완료로 세지 않음.',
        'files':{q.name:sha(q.read_bytes())for q in d.iterdir()if q.is_file()}})
    print(d)
if __name__=='__main__':main()
