"""90/91 각기 다른 몸·다리 반동을 유지하는 기본/포스 네 표시 입력."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,metrics
def main():
    d=H/'standing_fire_inputs02';need(not d.exists(),'Fresh input');p=H/'prepared_standing_special_base01/PL00_U.ARC';a=Archive(p.read_bytes())
    need(sha(p.read_bytes())=='fdba798cc2586f53f576d9255a2b44ddfffda7b7dc850effc7ee4dace5dfc08e','Parent changed')
    target=Image.new('RGBA',(1536,1536));style=Image.new('RGBA',target.size);guide=Image.new('RGBA',target.size,(28,32,40,255));rows=[];crop=(112,112,208,208)
    for row,n in enumerate((90,91)):
        for col,(form,mask)in enumerate((('base',0),('fourth',15))):
            old=a.composite(n,mask)[0];cut=old.crop(crop);need(np.count_nonzero(np.array(cut)[:,:,3])==np.count_nonzero(np.array(old)[:,:,3]),'Clipping')
            target.alpha_composite(cut.resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
            sp=H/f'standing_fire_native02/{form}_{85 if row==0 else 89:03}.png';sty=Image.open(sp).convert('RGBA');style.alpha_composite(sty.crop(crop).resize((768,768),Image.Resampling.NEAREST),(col*768,row*768))
            rows.append({'row':row,'column':col,'form':form,'mask':mask,'ref':n,'old_metrics':metrics(old),'style':{'path':sp.relative_to(ROOT).as_posix(),'sha256':sha(sp.read_bytes())}})
    guide.alpha_composite(target);dr=ImageDraw.Draw(guide)
    for r in rows:
        x,y=r['column']*768,r['row']*768;dr.text((x+20,y+20),f"{r['form']} ref{r['ref']} / fixed96 / origin48,48",fill='white');dr.line((x+180,y+568,x+600,y+568),fill=(75,125,100),width=1)
    d.mkdir();target.save(d/'edit_target.png');style.save(d/'new_style_reference.png');guide.convert('RGB').save(d/'coordinate_reference.png')
    prompt='''Use case: style-transfer. Refine the two distinct follow-through poses in Image1 to match the detailed sprite art in Image2. Preserve the target's actual pose geometry and exact cell positions.
Image1 EDIT TARGET:1536x1536 transparent sprite page,2columns by2rows. Each768cell is a96x96 logical-pixel window at8x, origin48,48. LEFT is Tenko Shibuki's base costume; RIGHT is the same character in the Fourth costume. Keep figures about46-48 logical pixels tall with the present generous transparent margins. Never enlarge them to fill the cells.
TOP row90: a dynamic wider-legged stance, torso angled and buster lifted diagonally toward upper left. Preserve both legs' separate knee/foot positions and weight shift, the raised bent elbow, other arm, head/gaze angle and original muzzle. BOTTOM row91: another distinct stance with the firing arm extending horizontally left and a short buster at the far left. Preserve its own shoulder/torso turn, wide-legged stance, knee/boot spacing and lower head position. Do not replace these bodies with the upright89 stance from the style reference. These are two DIFFERENT native poses, not just different arms.
Image2 is STYLE/COSTUME only: the newly refined same-character85/89 in the same columns. Match its clean medium-tone lavender hair locks, braid, gold eyes, ear planes, crisp dark-purple contour, compact head/body ratio, cloth folds and boot detail. Reinterpret the target's own head angle; do not paste the reference head or shrink the body. Keep the target's exact hair/ear scale, full-body height, hands, foot soles, ankles, all joints, buster size/orientation and muzzle position. Exactly two arms/two hands.
LEFT base: white/light-blue/lavender sleeves with red trim, red shrine outfit with structured folds, lavender-white boots. RIGHT Fourth: dark navy/black and violet outfit, gold belt/cuff accents, long dark cloth panels, violet sleeves with narrow lighter-purple fold highlights and a small white NECK collar. Both right-column firing sleeves must be violet/dark navy all the way to the buster. The old targets' white firing sleeve and red chest are incorrect materials: remove those broad white/red clothing blocks while preserving the pose. The white collar remains white; the sleeve does not. No flat black fills or noisy lines.
Image3 is coordinate guidance only. Do not reproduce any text or guide lines. Preserve existing short busters instead of adding or replacing a weapon, and do not shift them inward. No extra arm/fist, new ornament, aura, effect, dust, glow, floor or background. Output only the same four detailed sprites on clean transparent alpha in the exact2x2 layout.'''
    (d/'prompt.txt').write_text(prompt,'utf8');write(d/'input.json',{'parent':{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())},'refs':[90,91],'forms_by_column':['base','fourth'],'layout':{'canvas':[1536,1536],'grid':[2,2],'native_cell':[96,96],'origin':[48,48],'crop':list(crop)},'rows':rows,'native_relation_evidence':{'path':'work/sprite_style_unification_20261107/zero_audit/shibuki_standing85_92_relations01/report.json','sha256':'3fc0eb8beb650be2ad8e8706bfe00bb9634f2afebd68ac11d63a00de4ca3f1f9'},'policy':'90/91은89의팔별칭이아닌각각의몸·다리자세로제작. 기존머리전체덮기/전신비율변형 금지.','files':{f.name:sha(f.read_bytes())for f in d.iterdir()if f.is_file()}});print(d)
if __name__=='__main__':main()
