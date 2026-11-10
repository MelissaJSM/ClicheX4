"""기본/포스 이동 잔여의 출처와 첫 새원화 입력만 준비한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
P=H/'prepared_dash_base01/PL00_U.ARC'
PSHA='dd8504d31ed2f169825fd6daf8e0eae236e6a97f045d0b476e9f83c250824d3b'
O=H/'base_run_followup02';KEYS=(3,11,19);CROP=(128,124,192,188)
def main():
    need(not O.exists(),'Fresh output');need(sha(P.read_bytes())==PSHA,'Parent changed');O.mkdir();a=Archive(P.read_bytes());B=ROOT/'work/ver_buki_riko/shibuki_art/human_run_v1';matches=[]
    for n in range(1,33):
        bn=n if n%2 else n-1;typ='run'if n%2 else'shoot';file=B/'paired04'/f'{typ}_{bn:03}.png';q=np.zeros((384,384),np.uint8)
        if file.exists():
            src=np.array(Image.open(file));need(src.shape==(80,96),'Unexpected old canvas');q[120:200,112:208]=src;matches.append({'ref':n,'path':file.relative_to(ROOT).as_posix(),'sha256':sha(file.read_bytes()),'layer0_exact':bool(np.array_equal(a.layer(n)[0],q)),'different_pixels':int(np.count_nonzero(a.layer(n)[0]!=q))})
    for form,m in(('base',0),('fourth',15)):
        items=[(f'{form} {n}',a.composite(n,m)[0])for n in range(1,33)]
        for k in range(0,32,8):page(items[k:k+8],a.composite(0,m)[0],O/f'{form}_all_{k//8:02}.png',cols=4,scale=4)
    target=Image.new('RGBA',(1536,1024));style=Image.new('RGBA',(1536,1024));anchors=[]
    for row,(form,m)in enumerate((('base',0),('fourth',15))):
        for col,n in enumerate(KEYS):
            im=a.composite(n,m)[0];crop=im.crop(CROP);need(np.count_nonzero(np.array(crop)[:,:,3])==np.count_nonzero(np.array(im)[:,:,3]),'Clipped input');target.alpha_composite(crop.resize((512,512),Image.Resampling.NEAREST),(col*512,row*512));im.save(O/f'{form}_{n:03}.png');yy,xx=np.nonzero(np.array(im)[:,:,3]);anchors.append({'form':form,'ref':n,'bbox_world':[int(xx.min()-160),int(yy.min()-160),int(xx.max()+1-160),int(yy.max()+1-160)],'max_foot_y':int(yy.max()-160)})
        for col,n in enumerate((0,33,67)):style.alpha_composite(a.composite(n,m)[0].crop(CROP).resize((512,512),Image.Resampling.NEAREST),(col*512,row*512))
    target.save(O/'edit_target.png');style.save(O/'accepted_style.png')
    prompt='''Precise game pixel-art repaint. Image1 is the edit target: six exact current compact Tenko Shibuki poses, TWO rows by THREE columns, transparent1536x1024. Each512x512 cell is a native64x64 window enlarged8x, native world origin32,36. Image2 is the accepted style reference at the same scale: idle0, new air33, new dash67, top BASE and bottom FOURTH. Use their crisp detail and compact proportions, not their actions. Keep every target head/eye/neck position, short full-bodied torso, shoulder height, two arm positions, knees, ankles, feet and original foot-contact coordinates. Do not stretch or enlarge to fill cells.
Columns are3 the transition into movement with its forward lean and split legs,11 a walking stride,19 the different mid-step walking pose. Preserve each exact leg arrangement and arm gesture from Image1. Both costume rows are ONE character with the same skeleton, same gaze to LEFT, same head size and joints; clothing alone differs. Improve the entire target drawing's hair locks, ears, gold human eyes, collar, sleeves, cords, garment edge and shoe shading instead of preserving old broad flat hair/chest blobs.
TOP BASE: lavender fox ears and flowing layered lavender hair, red side flower/ribbon, white loose shrine sleeves with blue-lavender folds and red edge, red dress/skirt and decorative cords, pale lavender striped leg wraps, white/red shoes. BOTTOM FOURTH: same hair/face, dark navy/purple cloak and dark dress with restrained WHITE FUR only on collar/edge, purple sleeves and gold trim, dark stockings and white/gold shoes. Match accepted Fourth idle dark chest: never replace it with a large white shirt/chest panel or pale-blue base sleeve. Keep the compact full cloth silhouette and short thighs of the accepted idle. No sunglasses in these two costumes. No new accessories, fox tail, animal muzzle, third arm or changes to existing pose.
Pixel art only: clean thin dark-purple contour, coherent 2-3 middle-tone lavender hair clusters with distinct locks, readable folds and small gold/red accents. Detailed at native resolution but no scribbles, thick black blobs, glow, blurred gradients or excessive hatching. Exactly SIX complete sprites in their fixed cells, same native scale and transparent margins. No weapon, projectile, dust, labels, grid, floor or shadow. Keep the long-hair flow and separate legs. Do not paste an older coarse idle head; redraw at the accepted detailed reference quality while preserving its size.'''
    (O/'prompt.txt').write_text(prompt+'\n','utf8');write(O/'manifest.json',{'parent':P.relative_to(ROOT).as_posix(),'parent_sha256':PSHA,'source_readonly':True,'original_layer0_provenance':matches,'old_registration_scripts':{name:sha((B/name).read_bytes())for name in('prepare_body.py','refine_transitions.py','refine11.py','refine13.py')},'provenance_correction':'followup01의unified_idle_run_v4는후보32개가모두현재와불일치했고과거반려안임을DECISIONS/SHIBUKI_HUMAN_RUN에서확인.이02는실제human_run_v1/paired04를직접대조.처음01입력그림자체는현재ARC정적추출이므로변하지않으나출처설명은채택하지않음.','first_new_keys':list(KEYS),'layout':{'canvas':[1536,1024],'cell':[512,512],'native_cell':[64,64],'origin':[32,36],'crop':list(CROP),'scale':8},'anchors':anchors,'standing2_scope':'포스2는원래preserve판정을철회.기존총구/대기접점유지국소상의교정별도필요.이첫몸체3키페이지에는사격없음.','runtime_trigger':'root v13 armor15고정2→4→68의밝은가슴/옷깃차이','generation_started':False,'art_modified':False});print(json.dumps({'source_matches':sum(r['layer0_exact']for r in matches),'source_refs':len(matches),'first_keys':KEYS}))
if __name__=='__main__':main()
