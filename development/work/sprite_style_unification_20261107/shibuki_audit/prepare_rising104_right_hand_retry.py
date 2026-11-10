"""첫 시안의 잘못된 왼쪽손을 반려하고 104만 크게 분리한 편집 가이드."""
from pathlib import Path
import sys
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from PIL import Image,ImageDraw,ImageFont
from scripts.export_x_consistency import Archive
from native_pose_pack import need,sha,write

def main():
    out=H/'rising104_right_hand_retry01';need(not out.exists(),'New retry only');out.mkdir();a=Archive((H/'prepared_rising_fire_base02/PL00_U.ARC').read_bytes());need(sha(a.data)=='008eb1df4809fe6f8e7002604f98abbe58c885265cfa63a688105f9acf4d29ce','Wrong parent')
    # Large viewport: two 768x768 cells in a1536x1024 canvas; 64native px at12x.
    target=Image.new('RGBA',(1536,1024));guide=Image.new('RGB',target.size,(29,34,46));font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',25);d=ImageDraw.Draw(guide);rows=[]
    for col,(form,mask)in enumerate([('base',0),('fourth',15)]):
        im=a.composite(104,mask)[0].crop((128,124,192,188)).resize((768,768),Image.Resampling.NEAREST);target.alpha_composite(im,(col*768,128));guide.paste(im,(col*768,128),im);ox=col*768+384;oy=560
        def pt(x,y):return(ox+x*12,oy+y*12)
        d.rectangle([pt(-17,-33),pt(-8,-13)],outline=(255,50,70),width=5);d.line([pt(-17,-33),pt(-8,-13)],fill=(255,50,70),width=5);d.line([pt(-8,-33),pt(-17,-13)],fill=(255,50,70),width=5)
        d.rectangle([pt(2,-33),pt(10,-24)],outline=(30,240,245),width=5);d.ellipse([pt(4,-31),pt(8,-27)],outline=(30,240,245),width=5)
        d.line([pt(6,-24),pt(5,-17),pt(4,-10)],fill=(30,240,245),width=4)
        d.line([pt(-10,-6),pt(-15,-2),pt(-11,0)],fill=(30,240,245),width=4)
        d.text((col*768+30,40),form.upper()+': FACE LEFT, FIST ON RIGHT',fill='white',font=font);d.text((col*768+30,920),'RED X: remove high hand / CYAN: new far-arm fist',fill='white',font=font);rows.append({'form':form,'origin':[ox,oy],'viewport':[col*768,128,(col+1)*768,896],'scale':12,'desired_hand_center_world':[6,-29]})
    target.save(out/'target.png');guide.save(out/'guide.png')
    prompt='''Move the raised punching hand to the OPPOSITE SIDE of the head in BOTH sprites. This exact edit is mandatory: the original upper fist on the image LEFT is WRONG. DELETE/LOWER that old high left-side arm. Red X in guide marks the arm that must no longer be raised. Draw the raised FAR ARM and fist on the image RIGHT side of the ears, at the CYAN circle/rectangle. Head still looks LEFT. Do NOT mirror the head or entire body. The raised fist must be at the outer RIGHT ear/flower side, never remain over the LEFT ear. The other hand is the bent front guard arm at the lower LEFT chest.
Input1 is custom pixel art to edit; input2 exact spatial instruction guide. Exactly TWO sprites side by side, both have the SAME compact crouched airborne pose. Left shrine version: white sleeve with cyan/lavender shade and red detail. Right Fourth version: black/dark-purple sleeve with gold trim, no white shrine sleeve. Keep the present rich hair, face, ear angle, body/chest clothing, bent legs and foot positions. Only redraw the two arms and tiny shoulder/hair overlap that physically must change. Connect the far raised arm behind the RIGHT side of hair from right shoulder to right-side upright fist. Keep upperarm/forearm normal lengths, do not stretch a long thin noodle. TWO hands and TWO arms only, no third hand. Lower the original raised left arm into a natural forward-bent guard fist next to chest on the left.
Canvas1536x1024 transparent. Each sprite uses a768x768viewport at x0 or768,y128. Native64x64 at12x. Character native origin is(pixel384,560)left and(1152,560)right. Raised fist center MUST be approximately(456,212)left sprite and(1224,212)right sprite: native(+6,-29). The wrong old fist at about(240,212)/(1008,212) must disappear. Preserve the torso and all leg pixels at original absolute positions. Do not enlarge, shift, rotate or flip the full figure. Crisp pixel art of same scale and detailed style. Output no guides,text,arrows,cyan/red markings,background or shadows.'''
    (out/'prompt.txt').write_text(prompt,'utf8');write(out/'manifest.json',{'parent_sha256':sha(a.data),'ref':104,'rows':rows,'prior_rejected':'rising_air_hand_fix_inputs01/page01/generated_rejected104.png','reason':'104 still raised wrong left-side fist','original_game_art_sent':False});print(out)
if __name__=='__main__':main()
