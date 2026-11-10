"""새 공중 몸체와 원래 총구만 사용한 발사팔 편집 입력. 게임/자원 무변경."""
from pathlib import Path
import sys,json,hashlib
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.export_x_consistency import Archive,page
from native_pose_pack import need,sha,write
from inspect_air_layers import P,arrays
from prepare_lowhp_final import compose
from prepare_air_body_layers import rect,ownership

def main():
    o=H/'air_shot_inputs02';need(not o.exists(),'Fresh output required');o.mkdir();a=Archive(P.read_bytes());d=H/'air_body_layers01'
    guarddir=H/'air_barrel_guard02';guardmeta=json.loads((guarddir/'guard.json').read_text('utf8'))
    source=ROOT/'work/ver_buki_riko/shibuki_art/air_v1/production05/pairs.json';anchors=json.loads(source.read_text('utf8'))['frames'];rows=[];gunpics=[]
    groups=((33,35,37),(39,41,43),(45,47,49),(51,53))
    for pn,refs in enumerate(groups,1):
        folder=o/f'page{pn:02}';folder.mkdir();cols=len(refs);canvas=Image.new('RGBA',(cols*512,1024));guide=Image.new('RGBA',canvas.size);gd=ImageDraw.Draw(guide)
        for row,(form,mask)in enumerate((('base',0),('fourth',15))):
            for col,n in enumerate(refs):
                layers={b:np.array(Image.open(d/f'{n:03}_bank{b}_indices.png'))for b in(0,5,6,7,8)};body=compose(a,layers,mask)
                q=next(v for v in anchors if v['run']==n);mx,my=map(int,q['original_muzzle_world']);bounds=[mx-1,my-3,mx+9,my+5];x0,y0,x1,y1=bounds
                gm=next(g for g in guardmeta['rows']if g['shot_ref']==n+1);gun=np.array(Image.open(guarddir/f'{n+1:03}_indices.png'));protect=np.array(Image.open(guarddir/f'{n+1:03}_mask.png'))>0
                need(sha(gun.tobytes())==gm['casing_index_sha256'],'Barrel guard changed')
                actual=a.composite(n+1,mask)[0];whole=np.array(body);barrel=a.rgba(gun);whole[protect]=np.array(barrel)[protect]
                target=Image.fromarray(whole)
                target.save(folder/f'{form}_{n+1:03}_edit_target.png');barrel.save(folder/f'{form}_{n+1:03}_barrel.png')
                cut=target.crop((128,124,192,188));need(np.count_nonzero(np.array(cut)[:,:,3])==np.count_nonzero(whole[:,:,3]),'Input clipped')
                tile=cut.resize((512,512),Image.Resampling.NEAREST);canvas.alpha_composite(tile,(col*512,row*512));guide.alpha_composite(tile,(col*512,row*512))
                sx,sy={33:(-5,-4),35:(-5,-4),37:(-6,-6),39:(-3,-5),41:(-3,-5),43:(-4,-4),45:(-5,-4),47:(-5,-4),49:(-5,-4),51:(-5,0),53:(-5,-1)}[n]
                points=[(mx+9,my-5),(sx+3,sy-4),(sx+4,sy+6),(mx+8,my+7)]
                gd.line([(col*512+(x+32)*8,row*512+(y+36)*8)for x,y in points+[points[0]]],fill=(0,255,128,230),width=3)
                # Orange marks the old bent/raised foreground arm, which must
                # be removed rather than retained as an extra hand. Not art.
                oy,ox=np.nonzero(ownership(n)==7);r0=(int(ox.min())-160,int(oy.min())-160,int(ox.max())-160,int(oy.max())-160)
                gd.rectangle((col*512+(r0[0]+32)*8,row*512+(r0[1]+36)*8,col*512+(r0[2]+32)*8,row*512+(r0[3]+36)*8),outline=(255,170,0,230),width=2)
                rows.append({'page':pn,'form':form,'body_ref':n,'shot_ref':n+1,'barrel_world_rect_exclusive':bounds,'muzzle_world':[mx,my],'shoulder_world':[sx,sy],
                             'source_body_layer_hashes':{str(b):sha(v.tobytes())for b,v in layers.items()},'full_rgba_barrel_sha256':sha(actual.crop(tuple(t+160 for t in bounds)).tobytes()),
                             'barrel_mask_path':(guarddir/f'{n+1:03}_mask.png').relative_to(ROOT).as_posix(),'barrel_guard':gm,
                             'target_path':(folder/f'{form}_{n+1:03}_edit_target.png').relative_to(ROOT).as_posix(),'no_old_sleeve_head_body_copied':True})
                if row==0:gunpics.extend([(f'{n+1} actual gun',barrel),(f'{n+1} old full reference',actual)])
        canvas.save(folder/'edit_target.png');guide.save(folder/'arm_guide.png')
        prompt=f'''Use case: precise object edit. Image1 is the exact sprite editing target, {cols} columns by2 rows on a transparent {cols*512}x1024 canvas. Each512x512 cell is a64x64 native window, origin32,36 at8x. Image2 has green target-arm guides and orange current-arm guides only, which must not appear in output. Orange identifies the bent/raised FOREGROUND arm to remove; leave the far rear hand unchanged. Top row is Tenko Shibuki basic red shrine outfit/white short loose sleeves; bottom row is the SAME compact lavender fox-girl in a purple/navy Fourth cloak with gold trim and short sleeve. Refs{refs} preserve each input's bent knees, head angle, feet and rear hand.
Change ONLY the bent foreground arm into a naturally extended LEFT-firing buster arm. The compact gun already placed at the left is the exact original weapon; preserve its size, muzzle point, angle, every barrel pixel and transparency. Connect the same shoulder to its back edge by a short upper arm, elbow and forearm with properly folded clothing. Remove the old foreground fist rather than adding a second one. Keep the newly detailed ears, hair strands, eyes, face, neck, all torso/cloth, rear arm, legs and feet exactly in place. Preserve the current compact limb length and sleeve volume. NO rectangular sleeve stretching, no scaled whole figure, no long sausage arm, no floating shoulder/wrist. For raised-arm poses, lower ONLY the foreground shooting arm; the rear raised arm remains exactly as supplied. Basic sleeve has white/lightblue folds/red cuff; Fourth sleeve has purple/navy folds/gold cuff. Same joint centerline across two costumes. Keep detailed crisp pixel clusters from the target. True transparent background, unchanged cell layout and sprite origin, no added labels, guides, shadow or extra pose.'''
        (folder/'prompt.txt').write_text(prompt+'\n','utf8')
    for i in range(0,len(gunpics),8):page(gunpics[i:i+8],a.composite(0,0)[0],o/f'barrel_reference_{i//8:02}.png',cols=2,scale=4)
    write(o/'inputs.json',{'source_arc_sha256':sha(P.read_bytes()),'original_anchor_path':source.relative_to(ROOT).as_posix(),'original_anchor_sha256':sha(source.read_bytes()),
                          'body_candidate_only_not_frozen':True,'native_crop_world':[-32,-36,32,28],'source_cell':[512,512],'native_cell':[64,64],
                          'rows':rows,'generation_started':False,'resource_written':False,'full_casing_shape_and_alpha_guard':True,'old_full_rectangle_superseded_by_casing_mask':True,
                          'barrel_guard_sha256':sha((guarddir/'guard.json').read_bytes()),'only_44_occluded_casing_restored_pixels':21})
    print(json.dumps({'path':str(o),'poses':len(rows),'pages':4}))
if __name__=='__main__':main()
