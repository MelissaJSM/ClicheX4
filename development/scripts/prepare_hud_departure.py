"""Repair native HUD framing and replace only the two Hunter departure poses."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.inventory_hud_departure import load,PARENT,PARENT_SHA,D
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_shibuki_ui import static_repack
from scripts.discover_inputs import sha256
from scripts.extract_zero import save_image
from scripts.inventory_shibuki_ui import sheet
from scripts.prepare_riko_illustrations import repack_one_bank
from src.psx_ui_atlas import aliased_composition,local_composition
from src.psx_static_effect import compose_static

def repair_hud(original,current):
    """Restore the native connected bezel; never erase its alpha silhouette."""
    rows=json.loads((ROOT/'config/riko_hud_mark_us.json').read_text())['background_rows'];targets={};proof=[]
    for n in range(69,78):
        px,sz,bb,_=compose_static(entry(original,0x10206),local_composition(aliased_composition(entry(original,3),1,n)))
        prev,ps,pb,_=compose_static(entry(current,0x10206),local_composition(aliased_composition(entry(current,3),1,n)))
        if ps!=sz or pb!=bb:raise ValueError('HUD geometry differs from original')
        a=np.frombuffer(px,np.uint8).reshape(sz[1],sz[0]).copy();before=a.copy();old=np.frombuffer(prev,np.uint8).reshape(a.shape)
        for y,x1,x2 in rows:
            yy=y-17-bb[1];lo=x1-24-bb[0];hi=x2-24-bb[0]+1;a[yy,lo:hi]=14
        # Remove the last blue X interior pixels without changing silver framing.
        ys,xs=np.indices(a.shape);interior=(ys+bb[1]>=26)&(ys+bb[1]<=38)&(xs+bb[0]>=-19)&(xs+bb[0]<=3)
        a[interior&(a>=1)&(a<=9)]=14
        bx,by=-15-bb[0],27-bb[1];badge=old[by:by+12,bx:bx+15];region=a[by:by+12,bx:bx+15];region[badge>0]=badge[badge>0]
        if np.any((before>0)!=(a>0)):raise ValueError('HUD outer silhouette or transparency changed')
        allowed=(ys+bb[1]>=26)&(ys+bb[1]<=38)&(xs+bb[0]>=-19)&(xs+bb[0]<=3)
        if np.any((before!=a)&~allowed):raise ValueError('HUD repair escaped emblem interior')
        targets[1,n]=a;proof.append({'frame':n,'alpha_silhouette_equals_original':True,'outside_emblem_equals_original':True,'restored_opaque_pixels':int(np.count_nonzero((a>0)&(old==0)))})
    ng,np_,report=static_repack(entry(current,0x10206),entry(current,3),targets)
    return replace_entry(replace_entry(current,0x10206,ng),3,np_),targets,{'frames':proof,'packing':report}

def preview_hud():
    records,original,current=load();output=D/'hud_review';output.mkdir(exist_ok=True);items=[]
    pal=struct.unpack('<16H',(ROOT/'work/ver_buki_riko/art_pilot/hud_mark_v1/hud_palette.bin').read_bytes())
    for name in ('PL00_U.ARC','PL02_U.ARC'):
        raw,targets,report=repair_hud(original[name],current[name]);(output/name).write_bytes(raw)
        for (bank,n),a in targets.items():
            if n in (69,77):
                im=save_image(a.tobytes(),(a.shape[1],a.shape[0]),pal,output/f'{name}_{n}.png').convert('RGBA');items.append((f'{name} {n}',im.resize((im.width*4,im.height*4),Image.Resampling.NEAREST)))
    sheet(items,output/'review.png',4,(240,370));print(json.dumps({'output':str(output),'checks':report}))

def departure_pose(original,current,palette,suffix,output):
    from scripts.solve_sprite_cover import cover
    name='shibuki' if suffix=='X' else 'riko';n=9 if suffix=='X' else 13;lo=63488;hi=75776 if suffix=='X' else 81920
    height=84 if suffix=='X' else 96;source=D/f'{name}_departure_generated.png';im=Image.open(source).convert('RGBA');a=np.array(im);a[:,:,3]=np.where(a[:,:,3]>=192,255,0);im=Image.fromarray(a);im=im.crop(im.getchannel('A').getbbox())
    im=im.convert('RGBa').resize((round(im.width*height/im.height),height),Image.Resampling.LANCZOS).convert('RGBA');canvas=Image.new('RGBA',(im.width+4,im.height+4));canvas.alpha_composite(im,(2,2));a=np.array(canvas)
    colors=np.array([tuple((w>>s&31)*255//31 for s in (0,5,10)) for w in palette[1:]],np.int32);dist=((a[:,:,:3].astype(np.int32)[:,:,None,:]-colors)**2).sum(3);a=np.where(a[:,:,3]>=128,dist.argmin(2)+1,0).astype('uint8')
    g,p=entry(current,0x10102),entry(current,10);c=aliased_composition(p,2,n)
    op,os,ob,_=compose_static(entry(original,0x10102)[lo:hi],local_composition(aliased_composition(entry(original,10),2,n)));oa=np.frombuffer(op,np.uint8).reshape(os[1],os[0]);yy,xx=np.nonzero(oa);last=int(yy.max());_,sx=np.nonzero(oa[last-3:last+1]);original_foot_center=ob[0]+(int(sx.min())+int(sx.max()))/2;original_floor=ob[1]+last+1
    yy,xx=np.nonzero(a);last=int(yy.max());_,sx=np.nonzero(a[last-3:last+1]);bx=round(original_foot_center-(int(sx.min())+int(sx.max()))/2);by=original_floor-last-1
    key=sha256(a.tobytes()+str(len(c['parts'])).encode());cachepath=D/f'{name}_cover.json'
    if cachepath.exists() and json.loads(cachepath.read_text())['key']==key:layout=json.loads(cachepath.read_text())['layout']
    else:
        layout=cover(a>0,len(c['parts']),30)
        if not layout['fits']:raise ValueError(f'{name} departure exceeds part budget')
        cachepath.write_text(json.dumps({'key':key,'layout':layout},indent=2))
    rects=layout['rects'];positions=rects+[rects[-1]]*(len(c['parts'])-len(rects));np_=bytearray(p)
    for q,(x,y) in zip(c['parts'],positions):
        if not -128<=bx+x<=127 or not -128<=by+y<=127:raise ValueError('Departure coordinate overflow')
        off=q['record_offset'];np_[off]=q['flags']&15;np_[off+2:off+4]=bytes(((bx+x)&255,(by+y)&255))
    x0=min(x for x,y in rects);y0=min(y for x,y in rects);x1=max(x+16 for x,y in rects);y1=max(y+16 for x,y in rects);aa=a[y0:y1,x0:x1];targets={n:(aa.tobytes(),(x1-x0,y1-y0))}
    ng,np_,proof=repack_one_bank(g[lo:hi],bytes(np_),2,targets,{n:0})
    # The packer protects pixel content; also require all other frame coordinates,
    # flags, palette offsets and animation resources to be unchanged.
    for f in range(c['bank_frame_count']):
        if f==n:continue
        if aliased_composition(p,2,f)!=aliased_composition(np_,2,f):raise ValueError('Other HQ frame records changed')
    result=replace_entry(replace_entry(current,0x10102,g[:lo]+ng+g[hi:]),10,np_)
    im=save_image(aa.tobytes(),(aa.shape[1],aa.shape[0]),palette,output/f'{name}_departure.png').convert('RGBA');im.resize((im.width*4,im.height*4),Image.Resampling.NEAREST).save(output/f'{name}_departure_4x.png')
    bb=(bx+x0,by+y0,bx+x1,by+y1);preview=Image.new('RGBA',(180,180));preview.alpha_composite(im,(90+bb[0],110+bb[1]))
    return result,{'frame':n,'native_bounds':bb,'original_front_foot_center':original_foot_center,'original_front_foot_y':original_floor,'source_sha256':sha256(source.read_bytes()),'palette_unchanged':True,'non_target_frame_records_unchanged':True,'packing':proof},preview

def prepare(output):
    output.mkdir(exist_ok=False);records,original,current=load();changes={};checks={};items=[];pal=struct.unpack('<16H',(ROOT/'work/ver_buki_riko/art_pilot/hud_mark_v1/hud_palette.bin').read_bytes())
    for name in ('PL00_U.ARC','PL02_U.ARC'):
        changes[name],targets,checks[name]=repair_hud(original[name],current[name])
        for (bank,n),a in targets.items():
            if n in (69,77):
                im=save_image(a.tobytes(),(a.shape[1],a.shape[0]),pal,output/f'{name}_hud_{n}.png').convert('RGBA');items.append((f'{name} {n}',im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST)))
    for suffix in ('X','Z'):
        name=f'ST0D_0{suffix}.ARC';pal=struct.unpack_from('<16H',entry(current[f'COL0D_0{suffix}.ARC'],5),35*32)
        changes[name],checks[name],im=departure_pose(original[name],current[name],pal,suffix,output);items.append((name+' departure',im))
    files=[]
    for name,data in changes.items():
        if len(data)!=len(current[name]):raise ValueError('Archive resize')
        (output/name).write_bytes(data);files.append({'file':name,'source':records[name],'parent_sha256':sha256(current[name]),'sha256':sha256(data)})
    recipe={'kind':'hud_departure_v3','parent_build':str(PARENT.relative_to(ROOT)),'parent_bin_sha256':PARENT_SHA,'files':files,'checks':checks,'exe_changed':False,'runtime_verified':False,'user_review_pending':True}
    (output/'recipe.json').write_text(json.dumps(recipe,indent=2),encoding='utf8');sheet(items,output/'review.png',3,(250,310));print(json.dumps({'output':str(output),'files':len(files),'checks':checks}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path);a=p.parse_args()
    if a.output:prepare(a.output.resolve())
    else:preview_hud()
