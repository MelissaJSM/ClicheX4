"""새 앞팔의 포스 의상 재질만 교정하는 입력/좌표판."""
from pathlib import Path
import sys,json,shutil
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
def main():
    src=H/'standing_fire_inputs01';d=H/'standing_fire_fourth_sleeves01';need(not d.exists(),'Fresh correction input');d.mkdir()
    p=src/'generated.png';need(sha(p.read_bytes())=='f154fe170593cfbe27573f6f2855141e68f678b7cc7a9b4a7acbfaf6491b9d99','Source changed')
    shutil.copyfile(p,d/'edit_target.png');shutil.copyfile(src/'accepted_style.png',d/'accepted_style.png')
    im=Image.open(p).convert('RGBA');bg=Image.new('RGBA',im.size,(28,32,40,255));bg.alpha_composite(im);draw=ImageDraw.Draw(bg);s=im.width/192
    regions={85:[-13,-10,-4,4],89:[-14,-19,-5,-3]}
    for row,(n,r)in enumerate(regions.items()):
        box=[round((96+48+r[0])*s),round((row*96+48+r[1])*s),round((96+48+r[2])*s),round((row*96+48+r[3])*s)]
        draw.rectangle(box,outline=(80,240,120),width=2);draw.text((box[2]+8,box[1]),f'{n}: FRONT SLEEVE ONLY',fill='white')
    bg.convert('RGB').save(d/'region_guide.png')
    prompt='''Use case: precise-object-edit. Correct ONLY the front sleeve material on the two RIGHT-column sprites in Image1. Preserve the entire page's1254x1254 size,2x2 cell layout, pixel-art style, transparent margins and every figure's exact position and proportions.
Image1 is the newly detailed full edit target. The two LEFT-column base-costume sprites are already correct: preserve them unchanged. On the RIGHT-column Fourth-costume figures only, the arm that connects the purple buster to the shoulder was mistakenly left as a white/light-blue sleeve with red trim. TOP-RIGHT has that folded forearm immediately below the horizontal buster, in front of the cheek. BOTTOM-RIGHT has that long folded sleeve rising beside the face to the diagonal buster above the forehead. Change BOTH of these front sleeves to the accepted dark navy and violet fabric, with purple folds, narrow lavender highlights and small gold cuff accents. They must match the dark-purple OTHER sleeve and costume, not the white/red base outfit. Leave the little white neck collar as white: the collar and the firing sleeve are different materials.
Image2 is the accepted Fourth costume/style reference in the right column. Match its violet sleeve shade and folded material, not a large flat black fill. Image3 marks the two local sleeve regions with green boxes as location guidance only. Never include the boxes or labels in the output. Preserve the exact existing sleeve silhouettes and joint positions, purple busters and their muzzles, hands, face/gold eyes, lavender hair/ears/ornaments/braid, torso/collar/belt, skirt/coat panels, legs and boots. Do not move, stretch, shrink or add any arm or body part. Do not alter the rest of either sprite. Output the same full page with the same clean transparent alpha and no glow, haze, text or background.'''
    (d/'prompt.txt').write_text(prompt,'utf8')
    write(d/'input.json',{'source_sha256':sha(p.read_bytes()),'source_size':list(im.size),'policy':'새85/89의 포스 앞소매 두 부위 재질만 국소 원화 교정. 다른 새몸체·원점·총구·기본폼은 보존.','regions_world':regions,'candidate_not_accepted_reason':'현재 새포스 앞소매가 흰/하늘색·붉은점으로 생성되어 기본 의상과 혼동됨. 팔레트 후처리로 완성 취급하지 않는다.','inputs_actually_viewed_pending':True,'files':{q.name:sha(q.read_bytes())for q in d.iterdir()if q.is_file()}})
    print(d)
if __name__=='__main__':main()
