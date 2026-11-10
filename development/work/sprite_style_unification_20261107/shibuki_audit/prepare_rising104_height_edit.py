"""오른팔 쪽은 수용하고 원발사점까지 주먹 높이만 국소 원화 교정한다."""
from pathlib import Path
import sys
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from PIL import Image,ImageDraw,ImageFont
from native_pose_pack import need,sha,write
def main():
    p=H/'rising104_height_edit01';need(not p.exists(),'Fresh retry');p.mkdir();src=H/'rising104_right_hand_retry01/generated.png';im=Image.open(src).convert('RGBA');im.save(p/'target.png');guide=Image.new('RGB',im.size,(28,32,43));guide.paste(im,(0,0),im);d=ImageDraw.Draw(guide);font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',25)
    for ox in(0,768):
        d.ellipse((ox+430,184,ox+482,236),outline=(20,240,240),width=5);d.line((ox+484,280,ox+456,212),fill=(20,240,240),width=5);d.line((ox+456,212,ox+447,236),fill=(20,240,240),width=5);d.line((ox+456,212,ox+478,225),fill=(20,240,240),width=5)
        d.text((ox+30,65),'RAISE RIGHT FIST TO CYAN CIRCLE',fill='white',font=font);d.text((ox+30,920),'KEEP HEAD / FACE / TORSO / FEET IN PLACE',fill='white',font=font)
    guide.save(p/'guide.png');prompt='''Edit ONLY the high RIGHT punching arm of both pixel-art sprites. The arm is now on the correct side; DO NOT change its side. Extend/unfold its elbow so the right fist rises into the cyan target circle. This is a small localized height correction, not a new pose or costume. Preserve all other sprite pixels: head, ears, face, flower, front lower guard arm, torso, waist, bent legs, feet, clothing design.
Current high fist centers are around(484,280)left sprite and(1252,280)right sprite. Required fist centers are(456,212)and(1224,212). MOVE each high fist about28pxLEFT and68pxUP on the1536x1024canvas, while naturally straightening that raised FAR-arm elbow and redrawing its connecting sleeve folds. Keep shoulder at its current position behind the right-side hair. The fist top must visibly extend about80canvaspixels ABOVE the ear tips, approximately6-7nativepixels, as cyan circle shows. Do not leave fist level with ears. Do not merely keep the old short bent arm. Do not lengthen a thin straight rectangular sleeve; draw a natural raised elbow and sleeve with same width, fullness, folds and shoulder connection. Left sprite has white/red sleeve, rightsprite darkpurple/gold sleeve. Exactlytwohands, the LOW frontfist is unchanged.
Input1 is image to edit, input2 only positioningguide. Use same transparent1536x1024canvas and exact character scale/registration. No wholebody scaling/translation/mirroring. Head still looksLEFT, fist remainsonRIGHT. Preserve all fine hair/clothing detail. No guides, circles, labels, effects, background or shadows in final. Output the same2sprites with only the highright arm extended upward to target.'''
    (p/'prompt.txt').write_text(prompt,'utf8');write(p/'manifest.json',{'source_sha256':sha(src.read_bytes()),'target_fist_centers_canvas':[[456,212],[1224,212]],'native_centers':[6,-29],'only_high_right_arm':True,'not_wholebody_scaling':True});print(p)
if __name__=='__main__':main()
