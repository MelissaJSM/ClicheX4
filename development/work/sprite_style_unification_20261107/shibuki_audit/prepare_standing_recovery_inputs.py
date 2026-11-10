"""86/87/92를 각각의 실제 현재 자세로 분리해 새 여섯 표시 입력을 만든다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,metrics

def main():
    d=H/'standing_fire_inputs03';need(not d.exists(),'Fresh input')
    p=H/'prepared_standing_special_base01/PL00_U.ARC';need(sha(p.read_bytes())=='fdba798cc2586f53f576d9255a2b44ddfffda7b7dc850effc7ee4dace5dfc08e','Parent changed');a=Archive(p.read_bytes())
    target=Image.new('RGBA',(1536,1024));style=Image.new('RGBA',target.size);guide=Image.new('RGBA',target.size,(28,32,40,255));crop=(128,128,192,192);rows=[]
    for row,(form,mask)in enumerate((('base',0),('fourth',15))):
        for col,n in enumerate((86,87,92)):
            old=a.composite(n,mask)[0];cut=old.crop(crop);need(np.count_nonzero(np.array(cut)[:,:,3])==np.count_nonzero(np.array(old)[:,:,3]),'Clipping')
            target.alpha_composite(cut.resize((512,512),Image.Resampling.NEAREST),(col*512,row*512))
            sp=H/f'standing_fire_native02/{form}_{85 if col==0 else 89:03}.png';sty=Image.open(sp).convert('RGBA');style.alpha_composite(sty.crop(crop).resize((512,512),Image.Resampling.NEAREST),(col*512,row*512))
            rows.append({'row':row,'column':col,'form':form,'mask':mask,'ref':n,'old_metrics':metrics(old),'style':{'path':sp.relative_to(ROOT).as_posix(),'sha256':sha(sp.read_bytes())}})
    guide.alpha_composite(target);dr=ImageDraw.Draw(guide)
    for r in rows:
        x,y=r['column']*512,r['row']*512;dr.text((x+12,y+10),f"{r['form']} ref{r['ref']} / fixed64 / origin32,32",fill='white');dr.line((x+90,y+440,x+420,y+440),fill=(75,125,100),width=1)
    d.mkdir();target.save(d/'edit_target.png');style.save(d/'new_style_reference.png');guide.convert('RGB').save(d/'coordinate_reference.png')
    prompt='''Use case: style-transfer. Refine the six existing compact game sprites in Image1 to match the new detailed same-character sprite style in Image2, keeping all target poses and their exact positions.
Image1 is the EDIT TARGET:1536x1024 transparent page,3columns by2rows. Each512cell is a64x64 logical-pixel window enlarged8x, with origin32,32. TOP ROW is Tenko Shibuki's base costume; BOTTOM ROW is the same character in her Fourth costume. The existing bodies are about47 logical pixels tall, including ears; preserve that exact compact head/body ratio and generous transparent margins. Do not enlarge or stretch to fill cells.
Column1,frame86: short horizontal buster at the left, slight firing recoil with its own bent elbow, torso and skirt. Column2,frame87: separate recovery pose with raised bent arm and buster close to the face, elbow vertical in front of the torso. Column3,frame92: another distinct recovering pose with the firing arm angled diagonally across the upper chest, hand close to the cheek. Preserve each target's particular shoulder rotation, elbow bend, muzzle direction, hand location, other arm, foot spacing, ankles and weight shift. These recovery poses are not idle aliases; do not replace them by the idle or the style-reference poses. Exactly two arms and two hands.
Image2 is STYLE/COSTUME only, not pose: newly refined85/89. Match its layered medium-tone lavender hair locks, braided strands, gold eyes, defined ears, crisp dark-purple contour, readable sleeve folds, collar, cloth panels and boot highlights. Retain the target's own head angle, gaze and size. No pasted old flat hair, no featureless big color patches, no noisy black hatching.
TOP base costume: white/light-blue/lavender sleeves with red trim, red shrine costume, structured red cloth folds and lavender-white boots. BOTTOM Fourth costume: dark navy/black and violet torso/sleeves, gold belt/cuff accents, long dark cloth panels, violet sleeve folds. Keep the small white NECK collar, but all firing sleeves are dark violet/navy rather than broad white with red trim. The old targets' bright white firing sleeves and red chest patches are incorrect materials; replace those materials while keeping every arm joint and silhouette. Preserve short original busters, not new weapons.
Image3 is only a coordinate guide; omit its text and lines. Keep muzzle coordinates, all original foot soles, overall heights and all six cell positions. No extra hands, jewelry, weapons, aura, rays, particles, glow, floor, text or background. Output the same six full sprites in the exact3x2 layout on clean transparent alpha.'''
    (d/'prompt.txt').write_text(prompt,'utf8')
    write(d/'input.json',{'parent':{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())},'refs':[86,87,92],'forms_by_row':['base','fourth'],'layout':{'canvas':[1536,1024],'grid':[3,2],'native_cell':[64,64],'origin':[32,32],'crop':list(crop)},'rows':rows,'native_relation_evidence':{'path':'work/sprite_style_unification_20261107/zero_audit/shibuki_standing85_92_relations01/report.json','sha256':'3fc0eb8beb650be2ad8e8706bfe00bb9634f2afebd68ac11d63a00de4ca3f1f9'},'policy':'86/87/92 현재 실제 서로 다른 자세를 각각 새로 상세화. 85/idle 복사 파생 아님. 원US와 현수용자세의 차이는 별도 기록.','files':{f.name:sha(f.read_bytes())for f in d.iterdir()if f.is_file()}})
    print(d)
if __name__=='__main__':main()
