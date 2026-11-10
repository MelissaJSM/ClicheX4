"""린 헌터베이스 14표정을 같은 기준점·팔레트로 고정 공간에 등록한다."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.project import digest
from scripts.discover_inputs import DiscReader,sha256
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_rin_selection_portrait import RGB
from scripts.extract_zero import save_image
from scripts.prepare_shibuki_ui import panel_layout
from src.psx_ui_atlas import aliased_composition,local_composition,repack_frames
from src.psx_ui_render import render_static_rgba
from src.psx_static_effect import compose_static

PARENT=ROOT/'out/ver_rin_nana/rin_select_portrait_20261029T014739739774Z'
PARENT_SHA='aad1e761d49a201b5486981edaf6a33c7eb92e4702bea553fdf6b59c6b90ea04'
ART=ROOT/'work/ver_rin_nana/illustrations/hunter_v1'
RESOURCES={'ST0D_0Z.ARC':(9747,272384,'7c398de8934dab8af29c2b89bcc76df99bed71b56f0857b597ea59433f1030e4'),
           'COL0D_0Z.ARC':(179,6144,'958a2831b8c51b517586a6dee701158c18b523c0bb3063aefc0bdaed0626d5fb')}
LO,HI=63488,81920
WORDS=[0]+[0x8000|(r>>3)|((g>>3)<<5)|((b>>3)<<10) for r,g,b in RGB]
PAL=struct.pack('<16H',*WORDS)
COLORS=np.array([[int(w>>s&31)*255//31 for s in (0,5,10)] for w in WORDS[1:]],np.int32)

def sources():
    m=json.loads((PARENT/'manifest.json').read_text('utf8'))
    if digest(PARENT/'rin_nana.bin')!=PARENT_SHA or m['modified_bin']['sha256']!=PARENT_SHA:raise ValueError('Accepted parent changed')
    records=[];original={}
    with (PARENT/'rin_nana.bin').open('rb') as f:
        d=DiscReader(f,m['modified_bin']['size']);iso={q['path']:q for q in d.inspect()['files']}
        for name,(lba,size,h) in RESOURCES.items():
            r=iso['/ARC/'+name+';1']
            if (r['lba'],r['size'])!=(lba,size):raise ValueError('HQ layout changed')
            data=d.read(lba,size)
            if sha256(data)!=h:raise ValueError('Expected original HQ resource')
            original[name]=data;records.append({**r,'sha256':h})
    return m,records,original

def prepare_poses(out):
    im=Image.open(ART/'generated.png').convert('RGBA')
    if im.size!=(1536,1024):raise ValueError('Unsupported generated sheet')
    crops=[]
    for n in range(6):
        boxes=[(0,0,512,512),(512,0,1024,512),(1024,0,1536,512),(0,512,512,1024),(512,512,980,1024),(980,512,1536,1024)]
        cell=im.crop(boxes[n]);a=np.array(cell)
        a[:,:,3]=np.where(a[:,:,3]>=192,255,0);cell=Image.fromarray(a);box=cell.getchannel('A').getbbox()
        if not box:raise ValueError('Empty pose')
        crops.append((cell,box))
    scale=104/(crops[0][1][3]-crops[0][1][1]);poses=[];registration=[]
    for n,(cell,box) in enumerate(crops):
        pic=cell.crop(box);size=(round(pic.width*scale),round(pic.height*scale))
        pic=pic.convert('RGBa').resize(size,Image.Resampling.LANCZOS).convert('RGBA');a=np.array(pic)
        pixels=np.where(a[:,:,3]>=128,((a[:,:,:3].astype(np.int32)[:,:,None,:]-COLORS)**2).sum(3).argmin(2)+1,0).astype('uint8')
        # Stand poses share the body/boots axis, independent of long ribbons.
        yy,xx=np.nonzero(pixels);floor=int(yy.max())+1
        if n<5:
            _,feet=np.nonzero(pixels[max(0,floor-18):floor]);center=(int(feet.min())+int(feet.max()))//2;world_floor=64
        else:
            center=round(pixels.shape[1]*0.35);world_floor=51
        x=128-center;y=world_floor-floor+64
        if x<0 or y<0 or x+pixels.shape[1]>256 or y+pixels.shape[0]>144:raise ValueError('Pose registration clips')
        canvas=np.zeros((144,256),np.uint8);canvas[y:y+pixels.shape[0],x:x+pixels.shape[1]]=pixels
        poses.append(canvas);registration.append({'pose':n,'source_bbox':box,'scale':scale,'size':size,'world_bounds':[x-128,y-64,x+size[0]-128,y+size[1]-64],'floor':world_floor})
        pic=save_image(canvas.tobytes(),(256,144),WORDS,out/f'pose_{n}.png');pic.resize((1024,576),Image.Resampling.NEAREST).save(out/f'pose_{n}_4x.png')
    (out/'registration.json').write_text(json.dumps(registration,indent=2)+'\n','utf8')
    return poses,registration

def repack_bank(texture,parts,targets):
    offsets=struct.unpack_from('<'+'I'*(struct.unpack_from('<I',parts)[0]//4),parts)
    start=offsets[2];end=min((x for x in offsets if x>start),default=len(parts))
    one=struct.pack('<I',4)+parts[start:end]
    ng,np_,report=repack_frames(texture,one,0,targets,{n:0 for n in targets},guard_uv_zero=True)
    return ng,parts[:start]+np_[4:]+parts[end:],report

def verify(original,new,targets,world_images):
    a,b=original['ST0D_0Z.ARC'],new['ST0D_0Z.ARC'];g,ng=entry(a,0x10102),entry(b,0x10102);p,np_=entry(a,10),entry(b,10)
    if g[:LO]!=ng[:LO] or g[HI:]!=ng[HI:]:raise ValueError('Other HQ texture changed')
    expected=replace_entry(replace_entry(a,0x10102,ng),10,np_)
    if expected!=b or len(p)!=len(np_):raise ValueError('Non-graphic HQ data changed')
    oldcol=entry(original['COL0D_0Z.ARC'],5);newcol=entry(new['COL0D_0Z.ARC'],5)
    if newcol!=oldcol[:35*32]+PAL+oldcol[36*32:] or replace_entry(original['COL0D_0Z.ARC'],5,newcol)!=new['COL0D_0Z.ARC']:raise ValueError('Other palette changed')
    bank_count=struct.unpack_from('<I',p)[0]//4;protected=0;checks=[]
    for bank in range(bank_count):
        count=aliased_composition(p,bank,0)['bank_frame_count']
        for n in range(count):
            c=aliased_composition(p,bank,n);nc=aliased_composition(np_,bank,n)
            if bank!=2:
                if c!=nc:raise ValueError('Other HQ bank changed')
                protected+=1;continue
            if len(c['parts'])!=len(nc['parts']) or any(q['clut'] for q in nc['parts']):raise ValueError('Frame count/palette mismatch')
            px,size,bb,_=compose_static(ng[LO:HI],local_composition(nc))
            if (px,size)!=targets[n]:raise ValueError('HQ index roundtrip differs')
            im,ib=render_static_rgba(ng[LO:HI],nc,{0:WORDS})
            rgba=[tuple((WORDS[i]>>s&31)*255//31 for s in (0,5,10))+(255 if i else 0,) for i in range(16)]
            indexed=Image.frombytes('RGBA',size,bytes(v for i in px for v in rgba[i]))
            if im.tobytes()!=indexed.tobytes():raise ValueError('Actual CLUT render differs')
            actual={(i%size[0]+bb[0],i//size[0]+bb[1]):v for i,v in enumerate(px) if v}
            arr=world_images[n];desired={(int(x)-128,int(y)-64):int(arr[y,x]) for y,x in np.argwhere(arr)}
            if actual!=desired:raise ValueError('HQ world registration or clipping differs')
            checks.append({'frame':n,'size':size,'bounds':bb,'opaque_pixels':len(actual),'actual_clut_verified':True})
    if any(not np.array_equal(world_images[n],world_images[0]) for n in (3,4,5)):raise ValueError('Idle mouth/body changes')
    return {'frames':checks,'other_hq_frame_records_preserved':protected,'other_texture_banks_exact':True,'palette_row':35,'all_target_cluts_zero':True,'fixed_archive_and_composition_lengths':True,'idle_closed_mouth_preserved':True}

def forward_departure(original,out):
    im=Image.open(ART/'departure_forward.png').convert('RGBA');a=np.array(im);a[:,:,3]=np.where(a[:,:,3]>=192,255,0)
    im=Image.fromarray(a);bbox=im.getchannel('A').getbbox();im=im.crop(bbox)
    scale=92/im.height;size=(round(im.width*scale),92)
    im=im.convert('RGBa').resize(size,Image.Resampling.LANCZOS).convert('RGBA');a=np.array(im)
    pixels=np.where(a[:,:,3]>=128,((a[:,:,:3].astype(np.int32)[:,:,None,:]-COLORS)**2).sum(3).argmin(2)+1,0).astype('uint8')
    arc=original['ST0D_0Z.ARC'];px,sz,bb,_=compose_static(entry(arc,0x10102)[LO:HI],local_composition(aliased_composition(entry(arc,10),2,13)))
    old=np.frombuffer(px,np.uint8).reshape(sz[1],sz[0]);yy,xx=np.nonzero(old);floor=int(yy.max())+1
    _,foot=np.nonzero(old[floor-3:floor]);world_x=bb[0]+(int(foot.min())+int(foot.max()))/2;world_y=bb[1]+floor
    yy,xx=np.nonzero(pixels);new_floor=int(yy.max())+1;_,foot=np.nonzero(pixels[new_floor-3:new_floor]);center=(int(foot.min())+int(foot.max()))/2
    x=round(128+world_x-center);y=64+world_y-new_floor;canvas=np.zeros((144,256),np.uint8)
    if x<0 or y<0 or x+size[0]>256 or y+size[1]>144:raise ValueError('Forward departure clips')
    canvas[y:y+size[1],x:x+size[0]]=pixels
    report={'source':(ART/'departure_forward.png').relative_to(ROOT).as_posix(),'sha256':digest(ART/'departure_forward.png'),
            'prompt':(ART/'departure_prompt.txt').relative_to(ROOT).as_posix(),'source_alpha_bbox':bbox,'uniform_scale':scale,
            'native_size':size,'original_front_foot_anchor':[world_x,world_y],'perspective':'front_three_quarter_toward_viewer'}
    (out/'departure_registration.json').write_text(json.dumps(report,indent=2)+'\n','utf8')
    return canvas,report

def prepare(out,preview_only=False,forward=False):
    out=out.resolve()
    if not out.is_relative_to(ART) or out.exists():raise ValueError('Expected new HQ work directory')
    out.mkdir();poses,registration=prepare_poses(out)
    if preview_only:return
    m,records,original=sources();world_images={};departure_report=None
    if forward:departure,departure_report=forward_departure(original,out)
    # Only native eye interiors are taken from the generated blink. All hair,
    # face outline, mouth, body and ribbons remain the accepted base pose.
    eye=np.zeros_like(poses[0],bool);eye[39:43,125:131]=True;eye[39:42,121:124]=True
    eye&=np.isin(poses[0],[2,3,4,9,10,11,12])&np.isin(poses[1],[2,3,4,10,11,12])
    blink=poses[0].copy();blink[eye]=poses[1][eye]
    if not (1<=np.count_nonzero(blink!=poses[0])<=28):raise ValueError('Invalid blink mask')
    for n in range(14):
        base=poses[0] if n<=5 else poses[2] if n==6 else poses[3] if n<=9 else poses[4] if n<=12 else poses[5]
        a=base.copy()
        if n in (1,2):a=blink.copy()
        # Closed speaking variants change only the mouth's brown/skin pixels.
        if n in (8,11):
            region=(slice(46,48),slice(122,126)) if n==8 else (slice(47,49),slice(125,129))
            mouth=a[region];mouth[np.isin(mouth,[10,11])]=12
        # HQ actor stands on the left of Iris. Reflect the complete native pose
        # about the unchanged body anchor, including gestures and departure.
        # The separately accepted character-select panel is not involved.
        a=a[:,::-1].copy()
        if n==13 and forward:a=departure.copy()
        world_images[n]=a
        save_image(a.tobytes(),(a.shape[1],a.shape[0]),WORDS,out/f'world_{n:02d}.png')
    raw=original['ST0D_0Z.ARC'];g=entry(raw,0x10102);p=entry(raw,10);np_=bytearray(p);targets={};layouts=[]
    for n,a in world_images.items():
        c=aliased_composition(p,2,n);yy,xx=np.nonzero(a)
        x0=max(0,int(xx.min())-1);y0=max(0,int(yy.min())-1);x1=min(a.shape[1],int(xx.max())+2);y1=min(a.shape[0],int(yy.max())+2)
        aa=a[y0:y1,x0:x1];layout=panel_layout(aa>0,len(c['parts']))
        if not layout['fits']:
            key=sha256(aa.tobytes()+bytes([len(c['parts'])]));cache=ART/f'cover_{key}.json'
            mirror_key=sha256(aa[:,::-1].copy().tobytes()+bytes([len(c['parts'])]));mirror_cache=ART/f'cover_{mirror_key}.json'
            if cache.exists():layout=json.loads(cache.read_text('utf8'))
            elif mirror_cache.exists():
                layout=json.loads(mirror_cache.read_text('utf8'))
                layout['rects']=[[aa.shape[1]-16-x,y] for x,y in layout['rects']]
                cache.write_text(json.dumps(layout,indent=2)+'\n','utf8')
            else:
                from scripts.solve_sprite_cover import cover
                layout=cover(aa>0,len(c['parts']),25)
                if layout['fits']:cache.write_text(json.dumps(layout,indent=2)+'\n','utf8')
            if not layout['fits']:raise ValueError(f'Frame {n} cannot fit original windows')
        rects=layout['rects'];positions=rects+[rects[-1]]*(len(c['parts'])-len(rects))
        for q,(x,y) in zip(c['parts'],positions):
            wx=x+x0-128;wy=y+y0-64
            if not -128<=wx<=127 or not -128<=wy<=127:raise ValueError('HQ signed coordinate overflow')
            off=q['record_offset'];np_[off:off+4]=bytes((0,0,wx&255,wy&255))
        # Solver windows may omit the transparent corners of the work canvas.
        xa=min(x for x,y in rects);ya=min(y for x,y in rects);xb=max(x+16 for x,y in rects);yb=max(y+16 for x,y in rects)
        aa=aa[ya:yb,xa:xb]
        targets[n]=(aa.tobytes(),(aa.shape[1],aa.shape[0]))
        save_image(aa.tobytes(),(aa.shape[1],aa.shape[0]),WORDS,out/f'frame_{n:02d}.png')
        layouts.append({'frame':n,'used_windows':len(rects),'original_windows':len(c['parts']),'world_origin':[x0-128,y0-64]})
    ng,np_,packing=repack_bank(g[LO:HI],bytes(np_),targets)
    new={'ST0D_0Z.ARC':replace_entry(replace_entry(raw,0x10102,g[:LO]+ng+g[HI:]),10,np_)}
    col=original['COL0D_0Z.ARC'];cp=entry(col,5);new['COL0D_0Z.ARC']=replace_entry(col,5,cp[:35*32]+PAL+cp[36*32:])
    checks=verify(original,new,targets,world_images)
    for name,data in new.items():(out/name).write_bytes(data)
    (out/'palette.bin').write_bytes(PAL)
    sheet=Image.new('RGB',(7*200,2*300),(38,46,59));d=ImageDraw.Draw(sheet)
    for n,a in world_images.items():
        b=Image.open(out/f'frame_{n:02d}.png').convert('RGBA');b=b.resize((b.width*2,b.height*2),Image.Resampling.NEAREST)
        x=n%7*200;y=n//7*300;sheet.paste(b,(x+(200-b.width)//2,y+35),b);d.text((x+8,y+8),f'Rin HQ {n}',fill='white')
    sheet.save(out/'review.png')
    recipe={'kind':'rin_hunter','parent_sha256':PARENT_SHA,'generated_source':(ART/'generated.png').relative_to(ROOT).as_posix(),
            'generated_sha256':digest(ART/'generated.png'),'prompt':(ART/'prompt.txt').relative_to(ROOT).as_posix(),'tool':'built-in image_gen',
            'registration':registration,'display_facing':'right_toward_iris','native_world_reflection_x':-0.5,
            'forward_departure':departure_report,
            'layouts':layouts,'packing':packing,'verification':checks,'blink_changed_pixels':int(np.count_nonzero(blink!=poses[0])),
            'files':[{'source':r,'file':r['name'].split(';')[0],'sha256':sha256(new[r['name'].split(';')[0]])} for r in records]}
    (out/'recipe.json').write_text(json.dumps(recipe,indent=2)+'\n','utf8');print(json.dumps({'output':str(out),'packing':packing,'checks':checks}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--preview-only',action='store_true');p.add_argument('--forward-departure',action='store_true');a=p.parse_args();prepare(a.output,a.preview_only,a.forward_departure)
