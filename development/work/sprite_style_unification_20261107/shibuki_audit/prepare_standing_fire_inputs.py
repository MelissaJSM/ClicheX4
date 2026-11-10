"""85/89의 기존 포즈·원점을 보존하는 기본/포스 첫 상세 원화 입력."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,metrics

def main():
    d=H/'standing_fire_inputs01';need(not d.exists(),'Fresh input directory')
    p=H/'prepared_standing_special_base01/PL00_U.ARC'
    need(sha(p.read_bytes())=='fdba798cc2586f53f576d9255a2b44ddfffda7b7dc850effc7ee4dace5dfc08e','Parent changed')
    a=Archive(p.read_bytes());target=Image.new('RGBA',(1536,1536));style=Image.new('RGBA',target.size)
    guide=Image.new('RGBA',target.size,(28,32,40,255));rows=[];crop=(112,112,208,208)
    for row,n in enumerate((85,89)):
        for col,(form,mask) in enumerate((('base',0),('fourth',15))):
            im=a.composite(n,mask)[0];cut=im.crop(crop)
            need(np.count_nonzero(np.array(cut)[:,:,3])==np.count_nonzero(np.array(im)[:,:,3]),'Clipping')
            target.alpha_composite(cut.resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
            ref=0 if row==0 else 97
            style.alpha_composite(a.composite(ref,mask)[0].crop(crop).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
            rows.append({'row':row,'column':col,'ref':n,'form':form,'mask':mask,'metrics':metrics(im),'rgba_sha256':sha(im.tobytes()),'style_ref':ref})
    guide.alpha_composite(target);draw=ImageDraw.Draw(guide)
    for r in rows:
        x=r['column']*768;y=r['row']*768
        draw.line((x+384,y+160,x+384,y+620),fill=(65,90,105),width=1)
        draw.line((x+128,y+384,x+640,y+384),fill=(65,90,105),width=1)
        draw.line((x+192,y+568,x+576,y+568),fill=(80,110,95),width=1)
        draw.text((x+24,y+24),f"{r['form']} ref{r['ref']} / fixed 96px cell / origin48,48",fill='white')
    d.mkdir();target.save(d/'edit_target.png');style.save(d/'accepted_style.png');guide.convert('RGB').save(d/'coordinate_reference.png')
    prompt='''Use case: style-transfer. Precisely refine this transparent PS1 pixel-art sprite page using its accepted character reference. This is a detail/costume edit, not a new pose design.
Image1 is the EDIT TARGET: a1536x1536 page,2columns by2rows, each768x768cell representing an exact96x96 logical-pixel canvas at8x. Keep every figure in its own cell, at its current scale and position. Figures are about46-47 logical pixels tall. Preserve the large transparent margins; never enlarge to fill the cells.
Left column is Tenko Shibuki in her base costume; right column is the same character in the Fourth costume. TOP row85 faces left with the short buster held horizontally very near the face and elbow bent. BOTTOM row89 faces left with the buster raised diagonally above the forehead and the elbow bent upward. Preserve each figure's exact gaze/head tilt, buster size/orientation/muzzle location, arm bend and elbow, other lowered hand, shoulder position, torso angle, knees/ankles, foot positions and sole height. Exactly two arms and two hands. The short purple buster is already correct: do not replace it with a fist, add another gun, lengthen the barrel or move it.
Image2 is STYLE/COSTUME reference: accepted idle above and newly detailed ready stance below, in the same left-base/right-Fourth columns. Match its compact proportions, short torso and limbs, softly rounded body, small gold eyes, layered lavender hair and braid, readable ear planes, crisp dark-purple contours and controlled medium-tone locks. Refine each pose's own head angle instead of pasting the idle head. Keep head/ear size unchanged. The hair must gain deliberate separated locks and shading, without tangled black scribbles or a noisy outline.
Base costume: white sleeves with light blue/lavender folded shadows and red accents, red shrine-style bodice/skirt, lavender-white boots. Fourth costume: dark navy/black and violet bodice/coat, purple sleeves with narrow lavender highlights, white collar and gold details, existing dark long garment panels and boots. The RIGHT targets currently contain incorrect broad white sleeves and a red chest: replace only those materials with the accepted Fourth dark-purple costume while keeping the exact pose and appropriate sleeve volume. Do not turn the Fourth bodice red or add broad white chest/sleeve blocks. Draw coherent collar, sleeve folds, belt/hem and boot shading at the accepted reference's detail density.
Image3 is only the coordinate guide. Do not include its lines, labels or background. Do not change the pose, body proportions or limb length. No extra limb, extra face, new accessory, aura, projectile, glow, ground shadow or effect. Transparent background with clean alpha, no text. Output the same2x2 layout and generous transparent margins.'''
    (d/'prompt.txt').write_text(prompt,'utf8')
    write(d/'input.json',{'refs':[85,89],'forms_by_column':['base','fourth'],'parent':{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())},'layout':{'canvas':[1536,1536],'grid':[2,2],'native_cell':[96,96],'native_origin':[48,48],'crop':list(crop),'scale':.125},'rows':rows,'policy':'현재 포즈·원총구 보존을 목표로 한 상세 재작화. 다른85..92 관계/원표는 별도 읽기이며 단순별칭으로 간주하지 않는다.','original_game_art_sent':False,'generated':False,'files':{q.name:sha(q.read_bytes())for q in d.iterdir()if q.is_file()}})
    print(d)
if __name__=='__main__':main()
