"""노바 포스 두 자세의 의상 재질 국소 편집 입력. 기존 새 몸체는 보존한다."""
from pathlib import Path
import sys,json
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive
def main():
    d=H/'nova_fourth_costume_inputs01';need(not d.exists(),'새 입력만 작성')
    a=Archive((H/'prepared_chaser_base01/PL00_U.ARC').read_bytes())
    target=Image.new('RGBA',(1536,1024));style=Image.new('RGBA',target.size)
    for col,n in enumerate((213,215)):
        im=Image.open(H/f'nova_base_native01/fourth_{n:03}.png').convert('RGBA')
        target.alpha_composite(im.crop((112,96,208,224)).resize((768,1024),Image.Resampling.NEAREST),(768*col,0))
        style.alpha_composite(a.composite(0 if col==0 else 205,15)[0].crop((112,96,208,224)).resize((768,1024),Image.Resampling.NEAREST),(768*col,0))
    prompt='''Use case: precise-object-edit of two console pixel-art character sprites.
Image1 is the edit target, a1536x1024 transparent sheet with TWO poses side by side, each in its existing768x1024 cell. Image2 is the accepted FOURTH COSTUME reference, idle on left and a raised-hand victory pose on right. Keep the pose, size and placement from Image1 exactly.
Correct ONLY the costume on the two Image1 characters to the black-and-deep-purple Fourth costume in Image2. The current Image1 white sleeve masses and RED NECKTIE are mistakes. Both sleeves must be fitted dark purple/black fabric, including the entire forearm sleeve under the fist above the head in the RIGHT pose and the bent sleeve below the near-face fist in the LEFT pose. Give these sleeves coherent medium-purple fold highlights, deep dark-purple shadow edges and tiny gold cuff accents like Image2. Retain only the SMALL pale collar and shoulder trim from the reference; do not turn either sleeve white. Replace the red center chest/neck strip with the reference dark-purple bodice and small gold fastening. The back head accessory must be black/purple with gold details, with no red ribbon. Preserve the existing costume coverage, dark boots and gloves/hands as shown.
Everything outside these garment/accessory regions must remain unchanged: same detailed lavender fox ears, layered hair and braid, gold eyes, face, actual skin fists, shoulders, elbows, wrist tips, knees, ankle and sole coordinates. Do not move or resize the characters. The LEFT pose stays crouched with a fist near the face; the RIGHT pose keeps one fist above the head on the viewer-left, with the other hand at the waist. Exactly two arms, no new objects.
Preserve fine restrained native pixel clusters. Use the same sheet dimensions and transparent background. Do not crop/recenter, expand the silhouette, draw labels/grid/white backdrop, add a halo or cast shadow. This is a local garment correction, not a new full-body pose.'''
    d.mkdir();target.save(d/'edit_target.png');style.save(d/'accepted_fourth.png');(d/'prompt.txt').write_text(prompt,'utf8')
    write(d/'input.json',{'refs':[213,215],'form':'fourth','parent':{'path':(H/'prepared_chaser_base01/PL00_U.ARC').relative_to(ROOT).as_posix(),'sha256':sha(a.data)},'source_native':{'path':(H/'nova_base_native01/report.json').relative_to(ROOT).as_posix(),'sha256':sha((H/'nova_base_native01/report.json').read_bytes())},'layout':{'canvas':[1536,1024],'logical_canvas':[192,128],'cell':[96,128],'origin':[48,64],'crop':[112,96,208,224]},'policy':'새 머리·손발·몸체 비율은 고정하고 포스 소매/가슴·뒤 장식 원화의 재질만 국소 등록할 후보. 단순 색상 치환 아님.','files':{p.name:sha(p.read_bytes())for p in d.iterdir()if p.is_file()}})
    print(d)
if __name__=='__main__':main()
