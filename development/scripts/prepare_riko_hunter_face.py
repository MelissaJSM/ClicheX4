"""Repair face animation registration without redrawing accepted Hunter HQ poses."""
import argparse,json,shutil
from pathlib import Path
import numpy as np
from PIL import Image
from scripts.prepare_riko_illustrations import RGB,repack_one_bank,save
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.project import digest

ART=Path('work/ver_buki_riko/art_pilot/illustrations_v1')


def registered_variant(reference,variant,size,bounds):
    """Use the reference's crop, scale and foot anchor for both expressions."""
    ref=Image.open(reference).convert('RGBA');a=np.array(ref)
    a[:,:,3]=np.where(a[:,:,3]>=192,255,0);ref=Image.fromarray(a)
    bbox=ref.getchannel('A').getbbox();cropped=ref.crop(bbox)
    scaled_size=(round(cropped.width*104/cropped.height),104)
    scaled=cropped.resize(scaled_size,Image.Resampling.LANCZOS)
    ys,xs=np.where(np.array(scaled)[82:,:,3]>=128)
    center=(int(xs.min())+int(xs.max())+1)//2
    im=Image.open(variant).convert('RGBA')
    if im.size!=ref.size:raise ValueError('Variant canvas differs from reference')
    a=np.array(im);a[:,:,3]=np.where(a[:,:,3]>=192,255,0)
    im=Image.fromarray(a).crop(bbox).resize(scaled_size,Image.Resampling.LANCZOS)
    canvas=Image.new('RGBA',size);canvas.alpha_composite(im,(-bounds[0]-center,size[1]-104))
    a=np.array(canvas);distance=((a[:,:,:3].astype(np.int32)[:,:,None,:]-np.array(RGB[1:],np.int32))**2).sum(3)
    return np.where(a[:,:,3]>=128,distance.argmin(2)+1,0).astype('uint8')


def prepare(source,output):
    if output.exists():raise ValueError('Output exists')
    recipe=json.loads((source/'recipe.json').read_text('utf8'))
    for r in recipe['files']:
        if digest(source/r['file'])!=r['sha256']:raise ValueError('Source candidate changed')
    idle=np.array(Image.open(source/'base_00.png'))
    talk=np.array(Image.open(source/'base_06.png'))
    alert=np.array(Image.open(source/'base_10.png'))
    ref=ART/'base_idle_v2_generated.png';blink_source=ART/'base_blink_generated.png'
    registered=registered_variant(ref,ref,(80,112),(-40,-48,40,64))
    if not np.array_equal(registered,idle):raise ValueError('Reference registration no longer matches accepted idle')
    blink=registered_variant(ref,blink_source,(80,112),(-40,-48,40,64))
    # Native eye interiors: protect hair, eyebrows, face contour, nose and neck.
    eye_mask=np.zeros_like(idle,dtype=bool)
    eye_mask[20:23,36:42]=True;eye_mask[21:23,44:46]=True
    # Only the mouth interior; the old 8x4 cut also replaced jaw/hair/neck.
    mouth=np.zeros_like(idle,dtype=bool);mouth[24:27,39:43]=True
    mouth&=np.isin(idle,[10,11,12,15])&np.isin(talk,[10,11,12,15])
    targets={};checks=[]
    for n in range(14):
        old=np.array(Image.open(source/f'base_{n:02d}.png'))
        base=idle if n<=5 else talk if n<=9 else alert if n<=12 else old
        new=base.copy();allowed=np.zeros_like(new,dtype=bool)
        if n in (1,2):new[eye_mask]=blink[eye_mask];allowed=eye_mask
        # Frames 0..5 belong to the repeating standby expression sequence.
        # Never insert speech into those idle frames; 3..5 reopen the eyes.
        if n==8:new[mouth]=idle[mouth];allowed=mouth
        if n==11:
            # Alert canvas is eight pixels wider to the left; same world-space face region.
            for y,x in np.argwhere(mouth):
                if new[y,x+8] in (10,11,12,15):new[y,x+8]=idle[y,x];allowed[y,x+8]=True
        if np.any((new!=base)&~allowed):raise ValueError('Expression changed protected face/body')
        if np.any((new==0)!=(base==0)):raise ValueError('Expression changed silhouette')
        if n<=5 and not np.array_equal(new[24:29],idle[24:29]):
            raise ValueError('Standby expression changed the closed mouth')
        targets[n]=(new.tobytes(),(new.shape[1],new.shape[0]))
        checks.append({'frame':n,'reference_pose':0 if n<=5 else 6 if n<=9 else 10 if n<=12 else 13,
            'expression_changed_pixels':int(np.count_nonzero(new!=base)),
            'repair_changed_pixels':int(np.count_nonzero(new!=old)),
            'protected_pixels_identical':True,'silhouette_identical':True})
    path=source/'ST0D_0Z.ARC';raw=path.read_bytes();g=entry(raw,0x10102);p=entry(raw,10)
    # Regridded Riko art uses one complete palette. Original auxiliary CLUT
    # flags no longer describe the replacement pixels, especially frames7..9.
    ng,np_,report=repack_one_bank(g[63488:81920],p,2,targets,{n:0 for n in targets})
    changed=replace_entry(replace_entry(raw,0x10102,g[:63488]+ng+g[81920:]),10,np_)
    shutil.copytree(source,output)
    (output/'ST0D_0Z.ARC').write_bytes(changed)
    for n,(pixels,size) in targets.items():save(np.frombuffer(pixels,dtype='uint8').reshape(size[1],size[0]),output/f'base_{n:02d}.png')
    for r in recipe['files']:r['sha256']=digest(output/r['file'])
    recipe['checks']['hunter_face_registration']={'reference':str(ref),'reference_sha256':digest(ref),
        'existing_blink_art':str(blink_source),'blink_sha256':digest(blink_source),
        'new_image_generation_used':False,'frames':checks,'atlas':report}
    (output/'recipe.json').write_text(json.dumps(recipe,indent=2)+'\n',encoding='utf8')
    (output.parent/'face_checks.json').write_text(json.dumps(recipe['checks']['hunter_face_registration'],indent=2)+'\n')
    print(json.dumps({'output':str(output),'frames':checks,'atlas':report}))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();prepare(a.source,a.output)
