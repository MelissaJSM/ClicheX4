"""현재 사다리 접점과 동결 Ultimate 스타일을 분리한 원화 편집 입력."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent; ROOT=H.parents[2]; sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive,metrics
from native_pose_pack import need,sha,write
B=H/'prepared_dash_base01/PL00_U.ARC'; U=H/'prepared_ultimate_dash01/PL02_U.ARC'
BS='dd8504d31ed2f169825fd6daf8e0eae236e6a97f045d0b476e9f83c250824d3b'
US='bdcf0f648e2102a208307e21a941b53439a2f342014e69981a6de156a4dfbdfb'
CROP=(128,128,192,192); REFS=(143,144,146)

def cell(im):
    small=im.crop(CROP)
    need(np.count_nonzero(np.array(im)[:,:,3])==np.count_nonzero(np.array(small)[:,:,3]),'Crop clips pose')
    return small.resize((512,512),Image.Resampling.NEAREST)

def main():
    out=H/'ultimate_ladder_inputs01'; need(not out.exists(),'Fresh input output')
    need(sha(B.read_bytes())==BS and sha(U.read_bytes())==US,'Changed source')
    base=Archive(B.read_bytes()); ult=Archive(U.read_bytes()); out.mkdir(); d=out/'page01'; d.mkdir()
    style=Image.new('RGBA',(1536,1024)); poses=style.copy(); old=style.copy(); rows=[]
    for row,mask in enumerate((15,0)):
        for col,n in enumerate((0,57,61)):
            style.alpha_composite(cell(ult.composite(n,mask)[0]),(512*col,512*row))
        for col,n in enumerate(REFS):
            new=base.composite(n,0)[0]; prev=ult.composite(n,mask)[0]
            poses.alpha_composite(cell(new),(512*col,512*row)); old.alpha_composite(cell(prev),(512*col,512*row))
            rows.append({'form':'before' if mask else 'after','ref':n,'pose_reference_metrics':metrics(new),'old_ultimate_metrics':metrics(prev)})
    style.save(out/'accepted_ultimate_style.png'); poses.save(d/'new_pose_reference.png'); old.save(d/'current_ultimate_coordinates.png')
    prompt='''Edit the FIRST image, new_pose_reference.png, into Tenko Shibuki's two accepted Ultimate outfits. This is a costume edit of the six existing detailed sprites, preserving their exact poses, short compact proportions, head angles, hand contacts, knee bends and foot positions. The SECOND image, accepted_ultimate_style.png, is the identity and outfit reference: accepted idle at left, detailed rear-facing wall pose at center, raised-arm wall pose at right. The THIRD image is only the previous Ultimate ladder coordinate reference; its flat coarse hair and cloth are outdated and must NOT be copied.

Transparent 1536x1024 canvas. Three 512x512 cells across, two rows, no cell borders. Each cell represents a 64x64 native-pixel viewport enlarged exactly 8 times; world origin at cell pixel (256,256). All empty space must stay empty. Do not zoom in, increase body height, reframe, fill the margins or independently change scale. The first image's silhouette is the fixed joint/size guide. Fox ears plus head remain about 23 native pixels across upright, short substantial torso and limbs, no long thin legs.

Columns retain the first image's distinct ladder poses: column1 ref143 side-facing left with bent knees and hands in front; column2 ref144 back view with two bent raised arms; column3 ref146 back view with screen-left arm reaching straight above the head and the other arm lower. EXACTLY TWO arms and two legs per figure. Keep both hand endpoints, both foot endpoints, head tilt, shoulder and hip centers as in image1. Do not add a hand or arm behind the hair. No ladder, gun, projectile, speed line, effect, text, grid or floor.

Top row BEFORE capsule: a short loose WHITE jacket over the white/navy sailor swimsuit, navy sailor collar, navy trim and small gold accents, visibly separate soft full sleeves and cuffs. Lavender fold shadows, readable jacket seams, cuff folds and collar. Bottom row AFTER capsule: the same character and same body in the white/navy SLEEVELESS sailor swimsuit, remove the jacket and all sleeves, clearly BARE ARMS from shoulder to wrist. Both forms have pale BARE LEGS and small white/pink sandals. Do not copy the first image's red shrine skirt, shrine boots, wraps, socks, red ornaments or light-blue sleeves. Keep comparable leg volume and the same knee/ankle/foot contacts; changing clothes is not permission to redraw a different pose.

Both rows must share identical new lavender fox ears, human face and golden eyes when visible, long layered lavender hair, hands, legs and sandals at the same coordinates. Use layered midtone locks and coherent highlights in the back hair like the new wall style; do not leave a huge flat lavender slab, do not add dense random black scratches or curly scribbles. Include the dark navy flower hair ornament and the GOLD HEART-SHAPED SUNGLASSES perched above the eyes as the angle permits; do not move eyes onto the back of the head. No animal muzzle and no tail. The two rows differ only in the jacket-covered torso/arms and related clothing folds. Retain refined pixel detail at the fixed native scale; strong clean outline, readable small folds, no smoothing or painted blur. Exact transparent background, no checkerboard drawn into the image, no glow or cast shadow.'''
    (d/'prompt.txt').write_text(prompt+'\n',encoding='utf8')
    files=[out/'accepted_ultimate_style.png',d/'new_pose_reference.png',d/'current_ultimate_coordinates.png',d/'prompt.txt']
    write(out/'manifest.json',{'source_archives':{B.relative_to(ROOT).as_posix():BS,U.relative_to(ROOT).as_posix():US},'layout':{'canvas':[1536,1024],'cell':[512,512],'native_cell':[64,64],'scale':8,'crop':list(CROP),'world_origin_in_cell':[32,32]},'page_refs':list(REFS),'style_refs':[0,57,61],'rows':rows,'files':{p.relative_to(out).as_posix():sha(p.read_bytes())for p in files},'source_art_modified':False,'generated':False,'purpose':'기존 새 기본형의 접점/포즈를 가이드로 Ultimate 두 의상을 새로 편집. 기존 큰 단색 머리/옷 복사 금지.'})
    print(json.dumps({'path':str(d),'refs':REFS,'images':6}))
if __name__=='__main__':main()
