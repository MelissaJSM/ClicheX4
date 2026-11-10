"""순정 화염 발사점에 맞춘 양팔 국소 교정 입력. 순정 그림은 전송하지 않는다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from PIL import Image,ImageDraw,ImageFont
from scripts.export_x_consistency import Archive
from native_pose_pack import need,sha,write

def main():
    out=H/'rising_air_hand_fix_inputs01';need(not out.exists(),'Fresh inputs required');out.mkdir()
    src=[('base','fourth','prepared_rising_fire_base02/PL00_U.ARC','008eb1df4809fe6f8e7002604f98abbe58c885265cfa63a688105f9acf4d29ce'),('ultimate_before','ultimate_after','prepared_rising_fire_ultimate01/PL02_U.ARC','71d02fe6d965c1fb42cc786766bad62372c792ccd8ecf6d5bc1e40dc8deb8597')]
    records=[];font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17)
    for page,(top,bottom,path,expected)in enumerate(src,1):
        a=Archive((H/path).read_bytes());need(sha(a.data)==expected,'Changed input');p=out/f'page{page:02}';p.mkdir();target=Image.new('RGBA',(1536,1024));idle=target.copy();guide=Image.new('RGB',target.size,(27,32,43));g=ImageDraw.Draw(guide);slots=[]
        for row,form in enumerate((top,bottom)):
            mask=(0 if form in('base','ultimate_after')else 15)
            for col,n in enumerate((103,104)):
                ox,oy=col*512,row*512;im=a.composite(n,mask)[0].crop((128,124,192,188)).resize((512,512),Image.Resampling.NEAREST);target.alpha_composite(im,(ox,oy));idle.alpha_composite(a.composite(0,mask)[0].crop((128,124,192,188)).resize((512,512),Image.Resampling.NEAREST),(ox,oy));guide.paste(im,(ox,oy),im)
                # Desired far fist is on the image RIGHT of the face; original effect subtype1 x=+6.
                rect=(3,-18,10,-11)if n==103 else(3,-32,10,-25)
                x0,y0,x1,y1=rect;box=(ox+(32+x0)*8,oy+(36+y0)*8,ox+(32+x1)*8-1,oy+(36+y1)*8-1);g.rectangle(box,outline=(30,240,245),width=2)
                g.line([(ox+304,oy+96),(ox+288,oy+152),(ox+296,oy+208)],fill=(30,240,245),width=2)if n==104 else None
                g.text((ox+8,oy+480),f'{form} {n}: right-side fist, keep face LEFT',fill='white',font=font)
                slots.append({'form':form,'ref':n,'origin':[ox+256,oy+288],'desired_fist_envelope':rect,'costume_palette':16 if mask else 0,'crop_world':[-32,-36,32,28],'pixel_scale':8})
        target.save(p/'current_new_art.png');idle.save(p/'accepted_idle.png');guide.save(p/'contact_guide.png')
        costume=('TOP: original shrine outfit with white cyan-shadow sleeves and red inner dress. BOTTOM: Fourth costume with BLACK/DARK-PURPLE sleeves, gold edging and dark collar. Both remain fully clothed; do not put white shrine sleeves on Fourth.'if page==1 else'TOP: Ultimate white/navy gold-edged short jacket with sleeves. BOTTOM: same character wearing the white/navy sailor swimsuit WITHOUT jacket; BARE ARMS with natural skin, no sleeves/cuffs/bracelets.')
        prompt=f'''Precise local arm-pose edit of FOUR existing custom Tenko Shibuki pixel-art sprites. Preserve the detailed new hair/face, compact body size, current costume, torso, bent legs, feet and absolute pixel registration. Do NOT mirror or move the complete character. The face must continue looking LEFT.
Input1 is the actual image to edit. Input2 is a coordinate guide only; cyan rectangles show the desired NEW clenched fist position on the image RIGHT side of the head. Input3 is accepted idle costume/detail reference. Never copy the old wrong raised arm from input1.
Canvas1536x1024 transparent, three512x512 columns and two rows. ONLY the LEFT and MIDDLE columns contain sprites; keep third column EMPTY. The LEFT column is ref103 preparatory/recovery pose: bend the FAR/right-side arm and position its fist beside the right cheek at native(world +6,-15). The MIDDLE column is ref104 airborne fire release: extend that SAME far/right-side arm upward, partly behind the right hair, with fist centered native(world +6,-29), within cyan rectangle(world+3..+9,y-32..-26). Native origin in each64x64cell=(32,36), artwork is 8x enlargement. This arm must connect anatomically to the right shoulder behind the head, never become a detached hand or a long straight stick.
The old raised arm on the image LEFT must be lowered into the natural second bent guard arm in FRONT of the chest, fist around world(-11,-4). Remove its old high hand/old sleeve through a coherent local repaint; retain TWO arms and TWO hands exactly. Do not add a third arm. Keep the navy/red hair ornament a fabric ornament without flesh-colored spots. Sleeve lengths and muscle proportions match accepted idle, no stretched arm strips.
{costume}
Rows must share the same body pose and joint registration. Retain all fine clustered hair/ear edges, face/eye line, collar, torso folds, waist detail and the existing leg/foot silhouette. Alter only both arms/shoulder connections and necessary local hair occlusion by the raised far arm. No new skin or clothing blobs. No yellow/cyan guide lines, labels, arrows, weapon effects, background or cast shadows in output. Crisp transparent pixel art, 2-3 coherent shade clusters, same sprite scale as input. Never rescale the full pose to fill its cell.''' 
        (p/'prompt.txt').write_text(prompt,encoding='utf8');records.append({'page':page,'parent':path,'parent_sha256':expected,'slots':slots,'files':{f:sha((p/f).read_bytes())for f in('current_new_art.png','accepted_idle.png','contact_guide.png','prompt.txt')}})
    write(out/'manifest.json',{'pages':records,'original_game_images_sent':False,'purpose':'공중 subtype1 발사손의 좌우 의미를 바로잡는 네 의상103/104 국소 교정','gameplay_or_effect_change':False});print(json.dumps({'pages':2,'keys':8}))
if __name__=='__main__':main()
