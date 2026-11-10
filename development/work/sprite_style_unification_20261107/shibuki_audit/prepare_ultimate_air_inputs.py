"""새 기본 공중의 접지/관절을 참고해 얼티밋 전후22참조 미술 입력을 준비한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scripts.export_x_consistency import Archive,page,metrics
from native_pose_pack import need,sha,write
BASE=H/'prepared_rising_fire_base02/PL00_U.ARC';ULT=H/'prepared_rising_fire_ultimate01/PL02_U.ARC'
B_SHA='008eb1df4809fe6f8e7002604f98abbe58c885265cfa63a688105f9acf4d29ce';U_SHA='71d02fe6d965c1fb42cc786766bad62372c792ccd8ecf6d5bc1e40dc8deb8597'
CROP=(128,124,192,188);PAGES=((33,35,39),(37,41,43),(45,47,49),(51,53))
def scaled(im):
    q=np.array(im)[:,:,3];z=q.copy();z[124:188,128:192]=0;need(not z.any(),'Pose viewport clips art');return im.crop(CROP).resize((512,512),Image.Resampling.NEAREST)
def main():
    o=H/'ultimate_air_inputs01';need(not o.exists(),'Fresh input only');need(sha(BASE.read_bytes())==B_SHA and sha(ULT.read_bytes())==U_SHA,'Wrong parent');o.mkdir();b=Archive(BASE.read_bytes());a=Archive(ULT.read_bytes());font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17)
    style=Image.new('RGBA',(1536,1024))
    for row,mask in enumerate((15,0)):
        for col,n in enumerate((0,13,120)):style.alpha_composite(scaled(a.composite(n,mask)[0]),(512*col,512*row))
    style.save(o/'accepted_ultimate_style.png');rows=[]
    pairsfile=ROOT/'work/ver_buki_riko/shibuki_art/air_v1/production05/pairs.json';pairs=json.loads(pairsfile.read_text('utf8'))['frames']
    for n in range(33,55,2):
        r=next(x for x in pairs if x['run']==n);raw=a.banks[0]['frames'][n]['offset'];aliases=[f['index']for f in a.banks[0]['frames']if f['offset']==raw]
        rows.append({'body':n,'shot':n+1,'shared_raw_refs':aliases,'original_muzzle_world':r['original_muzzle_world'],'before_current':metrics(a.composite(n,15)[0]),'after_current':metrics(a.composite(n,0)[0]),'new_base_pose':metrics(b.composite(n,0)[0]),'new_base_is_pose_reference_only':True})
    for form,mask in(('before',15),('after',0)):
        pics=[]
        for n in range(33,55):
            im=a.composite(n,mask)[0];im.save(o/f'{form}_{n:03}.png');pics.extend([(f'{n} current Ultimate',im),(f'{n} new base pose only',b.composite(n,0)[0])])
        for start in range(0,len(pics),8):page(pics[start:start+8],a.composite(0,mask)[0],o/f'{form}_diagnosis_{start//8:02}.png',cols=2,scale=5)
    for p,refs in enumerate(PAGES,1):
        d=o/f'page{p:02}';d.mkdir();pose=Image.new('RGBA',(1536,1024));current=pose.copy();review=Image.new('RGB',(1536,1024),(27,32,43));draw=ImageDraw.Draw(review)
        for row,mask in enumerate((15,0)):
            for col,n in enumerate(refs):
                xy=(col*512,row*512);pose.alpha_composite(scaled(b.composite(n,0)[0]),xy);current.alpha_composite(scaled(a.composite(n,mask)[0]),xy);review.paste(scaled(a.composite(n,mask)[0]),xy,scaled(a.composite(n,mask)[0]));draw.text((xy[0]+8,xy[1]+8),f'{"before jacket"if mask else"after swimsuit"} / {n}',font=font,fill='white')
        pose.save(d/'new_pose_reference.png');current.save(d/'current_ultimate_reference.png');review.save(d/'current_review.png')
        prompt=f'''Edit the SIX compact Tenko Shibuki air-movement sprites in new_pose_reference.png into the two accepted Ultimate costumes in accepted_ultimate_style.png. The first image is the exact POSE AND DETAIL REFERENCE; its red shrine clothing must be replaced, not retained. The second image is the COSTUME, FACE, HAIR AND PROPORTION REFERENCE: top row white/navy jacket, bottom row sleeveless white sailor swimsuit. current_ultimate_reference.png only explains the old action and coordinates; do NOT copy its coarse head or flat clothing.
Transparent1536x1024 canvas, three512x512 cells across/two rows. Each cell is a native64x64 viewport, world(-32,-36..32,28), origin(32,36). Columns are refs {','.join(map(str,refs))}. Keep EACH new-pose silhouette, facing direction, eye line, bent hip/knees, palms, fingertips and feet at the same coordinates. Head includingears about23 native pixels, compact short torso, short substantial limbs matching the accepted idle. Do not stretch the legs, straighten the knees, make a tall narrow body or fill the cell by rescaling the complete sprite.
Both rows are the SAME character in precisely the SAME pose and perspective. Preserve lavender fox ears, layered lavender hair with middle-tone locks, human face/golden eyes, navy floral ornament, readable GOLD HEART SUNGLASSES resting above the eyes, bare thigh/leg skin and small white/pink sandals. TOP is BEFORE acquisition: short loose white jacket with navy sailor collar, gold piping and crisp lavender fold shadows, short full sleeves and cuffs, open front over the white sailor swim dress. BOTTOM is AFTER acquisition: same short white/light-lavender sailor swim dress, navy collar and gold detail; remove the outer jacket and sleeve fabric to expose BARE ARMS. Do not leave old white shrine sleeves on the swimsuit, add bracelets, add a second forearm, animal muzzle, tail or new costume.
Use the detailed low-resolution pixel cluster style of accepted_ultimate_style: clean contour, layered hair strands grouped into2~3 coherent tones, crisp collar/hem/gold detail. Preserve the new pose's fine facial/hair detail rather than replacing it with the old blob. TOP and BOTTOM must have identical hair/face/hand/leg/sandal geometry at the same pixels; only jacket-covered torso and arms differ. No third hand, extra arm, buster or shot yet. Retain both original arms naturally bent as the pose reference shows. No labels, guides, background, cast shadow, wall or ground. Leave transparent margins.''' 
        if len(refs)<3:prompt+=' Third column stays completely transparent in both rows.'
        (d/'prompt.txt').write_text(prompt+'\n','utf8')
    write(o/'manifest.json',{'ultimate_parent':ULT.relative_to(ROOT).as_posix(),'ultimate_parent_sha256':U_SHA,'new_basic_pose_reference':BASE.relative_to(ROOT).as_posix(),'new_basic_pose_reference_sha256':B_SHA,'scope':list(range(33,55)),'body_keys':list(range(33,55,2)),'page_keys':[list(r)for r in PAGES],'pairs':rows,'source_muzzle_table_sha256':sha(pairsfile.read_bytes()),'layout':{'source':[1536,1024],'native_cell':[64,64],'origin':[160,160],'world_crop':[-32,-36,32,28],'fixed_scale':0.125},'generation_started':False,'new_body_has_not_been_registered':True,'game_written':False,'confirmed_art_gaps':['現在의 옆머리 큰 단색면과 누락된 선글라스','재킷 칼라/소매 넓은 단색면','공중 맨다리의 단순한 명암과 부츠처럼 보이는 하단 덩어리'],'shot_pair_plan':'각 새몸을 유지한 새 발사팔이 원총구에 닿도록 후속 편집. 전역팔 늘임/옛몸 복사 금지.34 총열과44 소매혼입 사례는 별도 원시마스크 대조.'})
    print(json.dumps({'path':str(o),'body_keys':11,'shots':11,'pages':len(PAGES)}))
if __name__=='__main__':main()
