"""소매가 남은 새 after93만 국소 편집하는 비파괴 입력."""
from pathlib import Path
import sys,json
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive

def main():
    o=H/'ultimate_dash93_barearm01';need(not o.exists(),'Fresh edit input');o.mkdir();src=H/'ultimate_dash_inputs01/page04/generated.png';need(sha(src.read_bytes())=='8276860eddc45ba5e398e2251b27b2a105b2e8dfd146a26972db908223a04634','Source changed')
    im=Image.open(src).convert('RGBA');im.crop((0,512,512,1024)).resize((1024,1024),Image.Resampling.NEAREST).save(o/'edit_target.png')
    a=Archive((H/'prepared_ultimate_air01/PL02_U.ARC').read_bytes());a.composite(0,0)[0].crop((128,124,192,188)).resize((1024,1024),Image.Resampling.NEAREST).save(o/'accepted_sleeveless_reference.png')
    prompt='''Precise local correction of IMAGE1, one existing detailed Tenko Shibuki sprite on a transparent1024x1024 canvas. Image2 only explains her accepted SLEEVELESS white/navy sailor swimsuit and bare arms; do NOT copy its standing pose or coarse head. Image1 is a64x64 native viewport enlarged16x, origin32,36. Keep the exact same compact airborne bent-knee pose, silhouette size, head/ears/hair, gold heart sunglasses, eyes, navy flower, neck, swimsuit, rear arm, legs and sandal, all coordinates and margins.
Correct ONLY the raised FRONT / SCREEN-LEFT arm next to her face. It currently mistakenly has a white cloth sleeve and a dark gold-trim cuff. Remove ALL sleeve fabric and cuff from that one arm, show a naturally bent BARE SKIN upper arm, elbow and forearm in the SAME pose. The fist at the upper-left beside the face, shoulder and elbow remain at their exact current positions. Keep that hand connected to the existing shoulder around the side of the face; do not straighten or lengthen it. Both arms must be bare because this is her after-acquisition sleeveless swimsuit outfit. Exactly TWO arms total, no new fist, no wristband, no glove and no white tube around the forearm. Preserve the face/eye/hair boundaries where the arm overlaps. Refined crisp PS1-style pixel clusters and source shading quality; no old-art replacement. Every region outside this tiny front arm is unchanged. No glow, haze, ground, effects, text, borders or background. Return one complete sprite at the exact input scale and location, genuine transparency.'''
    (o/'prompt.txt').write_text(prompt+'\n',encoding='utf8');write(o/'input.json',{'source':src.relative_to(ROOT).as_posix(),'source_sha256':sha(src.read_bytes()),'crop':[0,512,512,1024],'display_scale':2,'native_scale':1/16,'ref':93,'form':'after','reason':'새 원화의 올린 앞팔에 흰 소매와 커프가 남음. 채택 보류 후 해당 팔만 builtin 교정.','images':{p.name:sha(p.read_bytes())for p in o.glob('*.png')},'game_modified':False});print(str(o))
if __name__=='__main__':main()
