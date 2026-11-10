"""생성 원화의 세번째 손 실패를 명시한 국소 재교정 입력. 아트를 수정하지 않는다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from PIL import Image,ImageDraw
from inspect_air_layers import P
from scripts.export_x_consistency import Archive
from native_pose_pack import need,sha,write

def main():
    out=H/'air_shot_extra_hand_retry01';need(not out.exists(),'Fresh output required');out.mkdir();a=Archive(P.read_bytes())
    source=H/'air_shot_inputs02/page02/generated.png';need(sha(source.read_bytes())=='d67c69212f4dee6371c122095b3eb84d5fcb252ce24d38750bfa90d3d46890de','Source changed')
    im=Image.open(source).convert('RGBA');need(im.size==(1536,1024),'Wrong input dimensions');im.save(out/'edit_target.png');guide=im.copy();draw=ImageDraw.Draw(guide)
    boxes=[(140,88,195,181),(630,70,700,174),(1138,118,1196,193)]
    for row in range(2):
        for x0,y0,x1,y1 in boxes:
            box=(x0,y0+row*512,x1,y1+row*512);draw.rectangle(box,outline=(255,55,10,255),width=5);draw.line((x0,y0+row*512,x1,y1+row*512),fill=(255,55,10,255),width=4);draw.line((x1,y0+row*512,x0,y1+row*512),fill=(255,55,10,255),width=4)
    guide.save(out/'remove_extra_upper_left_arm_guide.png')
    ref=Image.new('RGBA',(1536,1024))
    for row,mask in enumerate((0,15)):
        for col,n in enumerate((40,42,44)):
            pic=a.composite(n,mask)[0].crop((128,124,192,188)).resize((512,512),Image.Resampling.NEAREST);ref.alpha_composite(pic,(col*512,row*512))
    ref.save(out/'correct_two_arm_pose_reference.png')
    prompt='''Use case: precise local object removal and repair of a game sprite. Image1 is the editing target with six sprites,1536x1024, three512px columns and two512px rows. Each sprite currently has an erroneous THIRD ARM: a small raised fist at the UPPER LEFT of its head, in addition to the left-firing foreground arm and the proper raised rear arm on the right. Image2 marks ONLY that extra upper-left arm with red X boxes; those boxes are guides and must not appear in output. Image3 shows the correct original TWO-ARM pose for each of the six sprites, solely as an anatomy/arm-count guide. Do NOT copy its coarse hair/body/detail.
Remove the extra upper-left fist and its connected old raised sleeve in every cell. Keep exactly TWO ARMS: one short front arm firing left into the existing fixed purple buster, and the OTHER rear arm raised high on the right exactly as in image3. The area uncovered by removing the erroneous arm is transparent background or the already-present natural ear/hair contour as shown in image3; do not add skin patches, a flat color blob, an extra hand, or a new hair mound. Preserve both fox ears, all accepted newly detailed layered hair, eyes/face and neck. Do not confuse a fox ear or red flower ornament with the extra hand. Image3 distinguishes them clearly.
Everything else in image1 is authoritative: exact barrel/muzzle location and size, existing front firing-arm reach, head direction and height, short compact torso, layered shrine outfit or purple/gold cloak, bent knees, boots/feet and original canvas origins. No stretching, no global repaint, no resizing, no additional pose. Top row is white/red basic sleeves; bottom row purple/navy/gold Fourth sleeves. Keep crisp native-pixel texture, detailed folds and original shade clusters. Output the same six complete sprites in exactly the same positions on TRUE TRANSPARENT background, no glow/shadow/matte/guides/text.'''
    (out/'prompt.txt').write_text(prompt+'\n','utf8');write(out/'inputs.json',{'source_path':source.relative_to(ROOT).as_posix(),'source_sha256':sha(source.read_bytes()),'source_arc_sha256':sha(P.read_bytes()),'refs':[40,42,44],'forms':['base','fourth'],
              'problem':'새 발사팔에 더해 기존 들린 앞팔이 남아 팔3개가 된 생성 실패. 올바른2팔 원포즈를 참고해 국소 재생성한다.',
              'no_native_arm_stretch_or_flat_fill_attempted':True,'generation_started':False,'game_written':False})
    print(out)
if __name__=='__main__':main()
