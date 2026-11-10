"""얼티밋 벽의 실제 좌표/공유/총구를 분석하고 소량 재작화 입력을 준비한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import sha,need,write
from scripts.export_x_consistency import Archive,page
P=H/'prepared_ultimate_lowhp01/PL02_U.ARC';O=H/'ultimate_wall_inputs01'
SHA='3dd0d9a2cafd8e4d4355ef131c69c39f794698f6752524b39cf488f5b3bc737b'

def main():
    need(sha(P.read_bytes())==SHA and not O.exists(),'Fresh input / frozen parent required')
    a=Archive(P.read_bytes());O.mkdir()
    history=ROOT/'work/ver_buki_riko/shibuki_art/wall_v1/production19/pairs.json'
    need(sha(history.read_bytes())=='107ddf7a7506377d199a7c7f555fcfc95ca1b0ec23e9cfb21f48a90f587a46da','Muzzle source changed')
    pairs=json.loads(history.read_text('utf8'))['frames'];records=[]
    for n in range(55,67,2):
        r=next(v for v in pairs if v['run']==n);muzzle=list(map(int,r['original_muzzle_world']));f=a.banks[0]['frames'][n]
        aliases=[q['index']for q in a.banks[0]['frames']if q['offset']==f['offset']]
        mx,my=muzzle;rect=[mx-1,my-3,mx+9,my+5]
        for name,mask in (('before',15),('after',0)):
            a.composite(n,mask)[0].save(O/f'{name}_{n:03}.png');a.composite(n+1,mask)[0].save(O/f'{name}_{n+1:03}.png')
            q=a.composite(n+1,mask)[0];barrel=Image.new('RGBA',q.size);barrel.alpha_composite(q.crop(tuple(v+160 for v in rect)),(rect[0]+160,rect[1]+160));barrel.save(O/f'{name}_{n+1:03}_barrel.png')
        records.append({'body_ref':n,'shot_ref':n+1,'shared_raw_refs':aliases,'original_muzzle_world':muzzle,'barrel_rect_world':rect,'native_body_world_bbox':list(a.composite(n,15)[0].getbbox()),'barrel_is_current_resource_not_new_art':True})
    for k,nums in enumerate(((55,57,59),(61,63,65)),1):
        for name,mask in (('before',15),('after',0)):
            sheet=Image.new('RGBA',(1536,512))
            for col,n in enumerate(nums):
                q=a.composite(n,mask)[0];al=np.array(q.getchannel('A'))
                need(not al[:120].any() and not al[184:].any() and not al[:,:128].any() and not al[:,192:].any(),'Pose clipped')
                sheet.alpha_composite(q.crop((128,120,192,184)).resize((512,512),Image.Resampling.NEAREST),(col*512,0))
            sheet.save(O/f'page{k:02}_{name}_poses.png')
        page([(f'{name} {n}',a.composite(n,mask)[0])for name,mask in (('before',15),('after',0))for n in nums],a.composite(0,15)[0],O/f'page{k:02}_review.png',cols=3,scale=5)
    style=Image.new('RGBA',(1536,1024))
    for row,mask in enumerate((15,0)):
        for col,n in enumerate((0,13,120)):style.alpha_composite(a.composite(n,mask)[0].crop((128,128,192,192)).resize((512,512),Image.Resampling.NEAREST),(col*512,row*512))
    style.save(O/'accepted_style.png')
    prompt='''Edit page01_before_poses.png into THREE detailed Tenko Shibuki wall-movement sprites, same exact compact native proportions and pose/contact coordinates. Transparent1536x512, three512x512 cells corresponding to native64x64 viewport(-32,-40..32,24), origin(32,40). The positions are distinct: left55 curled wall entry, middle57 side/back tilted wall pose, right59 raised diagonal wall-contact hand. Keep each pose, facing direction, palm and sole coordinates, eye line, curled knees and action geometry. No firing weapon yet.
Only redraw the visual detail into accepted_style.png's refined game-pixel style. This is the Ultimate BEFORE acquisition white/navy jacket costume, not red shrine clothes, black/gold Fourth clothes, futuristic mechanical armor or a swimsuit-only pose. Keep lavender layered hair, gold heart sunglasses resting atop hair, navy floral side ornament, human face, short full-bodied fox-girl proportions, oversized but SHORT jacket sleeves, dark sailor collar, gold piping, crisp cuffs/hem, short white/light-lavender sailor swim-dress under the open jacket, bare thighs and white/pink sandals. Preserve the accepted head including ears about21~23 native pixels high, and body width/limb thickness from idle. Do not enlarge the head/ears, stretch wrists or straighten the legs to fill the cell.
Replace the coarse old head and white clothing blobs with coherent hair-lock middle tones, a few clean dark contours, clear eye/face planes and jacket folds/trim. Use original-style low-resolution clusters, not noisy scratches, curls, repeated black stripes or smooth illustration. Keep short flowing hair/tail shape consistent with the reference. All three complete sprites must fit their existing64x64 windows with transparent margins, no whole-body bounding-box resize, labels, guide lines, extra poses, shadows, platform/wall or background. The other two rows of accepted_style.png show the same character in jacket (top) and sleeveless swim dress (bottom) for identity; ONLY the jacket top costume is requested in this first page.'''
    (O/'page01_prompt.txt').write_text(prompt+'\n','utf8')
    write(O/'manifest.json',{'parent':str(P.relative_to(ROOT)),'parent_sha256':SHA,'refs':records,'source_palette_rows':[0,1],'first_page':[55,57,59],'next_page':[61,63,65],'layout':{'native_cell':[64,64],'world_crop':[-32,-40,32,24],'source':[1536,512],'scale':8},'sources':{p.name:sha(p.read_bytes())for p in O.glob('*.png')},'generation_started':False,'game_written':False,'plan':'먼저 재킷형3자세 전체 디테일을 제작하고 다음 편집에서 같은 몸의 재킷만 제거한다. 양폼 공통 머리/다리와 총구는 원점 보존. 사격6팔은 별도 정합한다.','all12_refs_need_finish':True,'current_art_defects':['머리 윗면과 옆머리가 큰 라벤더 단색면','금테 선글라스·목 칼라 정보 누락','재킷 소매/몸통이 넓은 흰덩어리로 이어짐'],'not_generation_evidence':True})
    print(json.dumps({'out':str(O),'muzzles':{str(r['shot_ref']):r['original_muzzle_world']for r in records}}))

if __name__=='__main__':main()
