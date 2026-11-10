"""새149 몸체와 수용34 총열을 사다리150/155 원총구에 둔 팔편집 입력."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
from prepare_ultimate_air_shot_inputs import exact_masked,shift
MUZZLES={150:(-24,-9),155:(-21,-13)}
def main():
    out=H/'ultimate_ladder_shot_inputs01';need(not out.exists(),'Fresh output');out.mkdir();p=H/'prepared_ultimate_dash01/PL02_U.ARC';a=Archive(p.read_bytes());need(sha(a.data)=='bdcf0f648e2102a208307e21a941b53439a2f342014e69981a6de156a4dfbdfb','Parent changed')
    mp=H/'air_barrel_guard02/master_034_mask.png';mastermask=np.array(Image.open(mp))>0;master=exact_masked(a,a.composite(34,0)[0],0,mastermask);need(int((master>0).sum())==60 and int(mastermask.sum())==71,'Master module changed');need(set(np.unique(master))=={0,2,5,8,14,15},'Sleeve/skin mixed');need(a.rgba(master,0).tobytes()==a.rgba(master,16).tobytes(),'Form mismatch')
    board=Image.new('RGBA',(1536,1024));rows=[];pics=[]
    for col,(n,(mx,my))in enumerate(MUZZLES.items()):
        gun=shift(master,mx+24,my+10);guard=shift(mastermask.astype('uint8'),mx+24,my+10)>0;Image.fromarray(gun).save(out/f'{n:03}_barrel_indices.png');Image.fromarray(guard.astype('uint8')*255).save(out/f'{n:03}_barrel_mask.png')
        for row,(form,pal,mask)in enumerate([('before',16,15),('after',0,0)]):
            bodypath=H/f'ultimate_ladder_contacts01/{form}_149_indices.png';body=np.array(Image.open(bodypath));target=body.copy();target[guard]=gun[guard];im=a.rgba(target,pal);im.save(out/f'{form}_{n:03}_target.png');crop=im.crop((112,128,208,192));need(int(np.count_nonzero(np.array(crop)[:,:,3]))==int(np.count_nonzero(target)),'Body clipped');board.alpha_composite(crop.resize((768,512),Image.Resampling.NEAREST),(col*768,row*512))
            old=np.array(a.composite(n,mask)[0]);expected=np.array(a.rgba(gun,pal));diff=guard&np.any(old!=expected,axis=2);oldcrop=np.zeros_like(old);oldcrop[guard]=old[guard];pics.extend([(f'{form} {n} old casing',Image.fromarray(oldcrop)),(f'{form} {n} canonical34',a.rgba(gun,pal))]);rows.append({'ref':n,'form':form,'body_ref':149,'body_sha256':sha(bodypath.read_bytes()),'body_reference_policy':'현재 수용된 기본/포스 사다리사격은150/155 모두새149몸체를사용. 원US별도읽기증거는후속연결.154는사격짝으로쓰지않음.','muzzle_world':[mx,my],'translation_from_master34':[mx+24,my+10],'barrel_opaque':60,'transparent_guard':11,'barrel_raw_sha256':sha(gun.tobytes()),'barrel_mask_sha256':sha(guard.tobytes()),'old_casing_changed_pixels':int(diff.sum())})
    board.save(out/'edit_target.png');guide=board.copy();dr=ImageDraw.Draw(guide)
    for col,(n,(mx,my))in enumerate(MUZZLES.items()):
        for row in range(2):
            pts=[(mx+7,my-5),(-5,-9),(-1,0),(-2,7),(-13,7),(mx+7,my+7)];dr.line([(col*768+(x+48)*8,row*512+(y+32)*8)for x,y in pts+[pts[0]]],fill=(40,255,150,255),width=3)
    guide.save(out/'arm_guide.png')
    prompt='''Use case: precise-object-edit. Image1 is the exact NEW detailed Shibuki sprite edit target. Image2 shows a green arm-edit boundary guide only; do not copy green. Exact1536x1024, TWO columns by TWO rows, each768x512 cell is native96x64 at8x, world origin48,32. Transparent background. All4 sprites face LEFT and climb a ladder: the rear/right arm is raised to hold a rung, the front/left arm must SHOOT.
Only replace the bent front fist/forearm with a compact short firing arm connected from the same shoulder to the existing small lavender buster barrel. Do NOT add a third hand or retain the old front fist beside the chest. Preserve the raised rear hand and its ladder contact exactly. Left column150 barrel muzzle is world(-24,-9); right column155 barrel recoil is world(-21,-13). Keep each barrel's exact position, scale, shape, purple colors and left-pointing opening. The firing shoulder is around(-6,-4). Connect a naturally bent short upperarm/elbow/wrist to the right side of the barrel. The right column arm angles upward slightly more because its barrel is higher and closer. Do not stretch a straight sleeve tube, enlarge the gun, change head/torso position, or move any feet.
Top row BEFORE: detailed white/navy short jacket, small folded white sleeve with lavender middle/shadow folds and dark cuff. Bottom row AFTER: same sailor swimsuit but no jacket, NO SLEEVE; bare upperarm/forearm with natural skin shadow. Match the elbow/wrist/hand position between the two rows, with the bare-arm outer contour entirely inside the corresponding loose jacket sleeve. Keep the SAME head, ears, golden heart sunglasses, gold eye, lavender hair strands, navy flower, raised arm, torso, waist, skirt hems, thighs, knees, sandals and body proportions from the edit target. No coarse older head/body replacement. Remove old front-arm traces using the actual adjacent detailed cloth/hair or transparency, not a flat color patch. Exactly2 arms and2 hands per figure. The new hand may fit behind/under the existing barrel; no skin-colored gun extension.
Use crisp pixel clusters at the existing8x scale, short compact limbs, readable folds without added black hatching. No text, marker, glow, projectile, ladder or backdrop. Every non-arm pixel should stay unchanged.''' 
    (out/'prompt.txt').write_text(prompt+'\n',encoding='utf8')
    for start in range(0,len(pics),4):page(pics[start:start+4],a.composite(0,0)[0],out/f'barrel_comparison_{start//4:02}.png',cols=2,scale=5)
    write(out/'input.json',{'parent_sha256':sha(a.data),'source_body_report_sha256':sha((H/'ultimate_ladder_contacts01/report.json').read_bytes()),'master_mask_sha256':sha(mp.read_bytes()),'layout':{'source':[1536,1024],'cell':[768,512],'native':[96,64],'origin':[48,32],'crop':[112,128,208,192],'scale':0.125},'rows':rows,'original_old_casing_preserved_claimed':False,'scope':'수용34 정본총열60+투명11을원150/155총구로복원.옛총열의의상색혼입은보호대상이아님.새149몸체는편집입력이며팔연결미완성.','generated':False,'packed':False})
if __name__=='__main__':main()
