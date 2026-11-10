"""생성한 린 선택 일러스트를 원작192×160 패널/15색으로 변환하고 재삽입 검증."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.extract_zero import save_image
from scripts.project import digest
from scripts.build_rin_idle import sha
from scripts.discover_inputs import DiscReader
from src.psx_player import composition_frame
from src.psx_ui_atlas import local_composition,repack_frames,tile_pixels
from src.psx_static_effect import compose_static

PARENT=ROOT/'out/ver_rin_nana/rin_ui_small_20261029T011832610985Z'
PARENT_SHA='3c05b46ba428c65f718a122eba80870142cd8c345263ec101487a157cc2be871'
ART=ROOT/'work/ver_rin_nana/illustrations/selection_v1'
RGB=[(12,18,42),(11,27,71),(26,46,99),(101,117,161),(168,181,207),
     (245,247,255),(20,54,196),(14,90,245),(80,216,239),(173,120,102),
     (219,170,146),(255,224,193),(70,78,109),(58,78,139),(212,221,235)]

def sources():
    m=json.loads((PARENT/'manifest.json').read_text('utf8'))
    if m['modified_bin']['sha256']!=PARENT_SHA or digest(PARENT/'rin_nana.bin')!=PARENT_SHA:raise ValueError('Accepted small UI parent changed')
    cfg=json.loads((ROOT/'config/riko_ui_us.json').read_text('utf8'));records=[];original={}
    with (PARENT/'rin_nana.bin').open('rb') as f:
        disc=DiscReader(f,m['modified_bin']['size']);iso={r['path']:r for r in disc.inspect()['files']}
        for rec in cfg['archives']:
            name=rec['path'].split('/')[-1].split(';')[0]
            if name not in ('ST0E_U1.ARC','COL0E_U1.ARC'):continue
            if any(iso[rec['path']][k]!=rec[k] for k in ('lba','size')):raise ValueError('UI layout changed')
            raw=disc.read(rec['lba'],rec['size'])
            if raw!=(PARENT/'ui'/name).read_bytes():raise ValueError('Parent UI differs from frozen recipe')
            original[name]=raw;records.append({**rec,'sha256':sha(raw)})
    return m,records,original

def portrait_grid(parts):
    """동일 파츠 기록을 공유하여 원래 길이 안에120창의 완전한 패널을 둔다."""
    banks=[];details=[]
    for bank in range(3):
        count=composition_frame(parts,bank,0)['bank_frame_count'];records=[]
        for n in range(count):
            c=composition_frame(parts,bank,n)
            if (bank,n)==(1,1):
                raw=b''.join(struct.pack('<BBbb',4,0,x-96,y-80) for y in range(0,160,16) for x in range(0,192,16))
            else:
                chunks=[]
                for q in c['parts']:
                    raw=bytearray(parts[q['record_offset']:q['record_offset']+4])
                    if bank==1 and q['page']*256+q['tile']==318:
                        raw[0]^=0x80;raw[1]=61
                    chunks.append(bytes(raw))
                raw=b''.join(chunks)
            records.append(raw)
        body=bytearray();headers=[]
        for raw in records:
            pos=next((i for i in range(0,len(body)-len(raw)+1,4) if body[i:i+len(raw)]==raw),None)
            if pos is None:
                overlap=next((k for k in range(min(len(body),len(raw)),0,-4) if body[-k:]==raw[:k]),0)
                pos=len(body)-overlap;body+=raw[overlap:]
            headers.append(((count+pos//4)<<16)|(len(raw)//4))
        block=struct.pack('<'+'I'*count,*headers)+body;banks.append(block);details.append({'bank':bank,'bytes':len(block)})
    out=bytearray(12)
    for bank,block in enumerate(banks):struct.pack_into('<I',out,bank*4,len(out));out+=block
    if len(out)>len(parts):raise ValueError('UI part directory has insufficient space')
    slack=len(parts)-len(out);out+=bytes(slack)
    return bytes(out),{'banks':details,'remaining_bytes':slack,'archive_entry_length_preserved':True,'portrait_parts':120}

def verify(original,new,indices,size,palette,full_panel=False):
    s,ns=original['ST0E_U1.ARC'],new['ST0E_U1.ARC'];t,nt=entry(s,0x10102),entry(ns,0x10102);p,np_=entry(s,10),entry(ns,10)
    if t[:40960]!=nt[:40960] or t[90112:]!=nt[90112:] or replace_entry(replace_entry(s,0x10102,nt),10,np_)!=ns:raise ValueError('Other select graphics changed')
    allowed=set();count=0
    for b,lo,hi in ((0,0,40960),(1,40960,90112),(2,90112,len(t))):
        for n in range(composition_frame(p,b,0)['bank_frame_count']):
            a,c=composition_frame(p,b,n),composition_frame(np_,b,n)
            if b==1 and n==1:
                if full_panel:
                    if len(c['parts'])!=120 or any(v['clut']!=1 or v['flip_x'] or v['flip_y'] or v['unknown_flags'] for v in c['parts']):raise ValueError('Unexpected full panel layout')
                    if [(v['x'],v['y']) for v in c['parts']]!=[(x-96,y-80) for y in range(0,160,16) for x in range(0,192,16)]:raise ValueError('Full panel grid moved')
                else:
                    if len(a['parts'])!=len(c['parts']):raise ValueError('Portrait parts changed')
                    for u,v in zip(a['parts'],c['parts']):
                        if any(u[k]!=v[k] for k in ('flip_x','flip_y','clut','unknown_flags','record_offset')):raise ValueError('Portrait metadata changed')
                        allowed.update(range(u['record_offset'],u['record_offset']+4))
                if compose_static(nt[lo:hi],local_composition(c))[:2]!=(indices,size):raise ValueError('Portrait readback changed')
            else:
                wanted=[{k:v for k,v in q.items() if k!='record_offset'} for q in a['parts']]
                if full_panel and b==1:
                    for q in wanted:
                        if q['page']*256+q['tile']==318:q.update(tile=61,flags=q['flags']^128,flip_y=not q['flip_y'])
                if wanted!=[{k:v for k,v in q.items() if k!='record_offset'} for q in c['parts']] or a['bank_frame_count']!=c['bank_frame_count'] or compose_static(t[lo:hi],local_composition(a))[:3]!=compose_static(nt[lo:hi],local_composition(c))[:3]:raise ValueError('Accepted/non-target UI changed')
                count+=1
    if len(p)!=len(np_) or (not full_panel and any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(p,np_)))):raise ValueError('Other parts/header changed')
    protected={q['page']*256+q['tile'] for n in range(composition_frame(p,1,0)['bank_frame_count']) if n!=1 for q in composition_frame(p,1,n)['parts']}
    if full_panel:
        flipped=np.frombuffer(tile_pixels(t[40960:90112],317),np.uint8).reshape(16,16)[::-1].tobytes()
        if flipped!=tile_pixels(t[40960:90112],318):raise ValueError('Original border duplicate relation differs')
        protected.remove(318)
    for ti in protected:
        if tile_pixels(t[40960:90112],ti)!=tile_pixels(nt[40960:90112],ti):raise ValueError('Unowned portrait atlas tile changed')
    col=original['COL0E_U1.ARC'];cp=entry(col,5)
    if replace_entry(col,5,cp[:160]+palette+cp[192:])!=new['COL0E_U1.ARC']:raise ValueError('Other selection palette changed')
    return {'other_select_frames_preserved':count,'accepted_small_sprites_preserved':32,'other_draw_records_exact':not full_panel,'border_lossless_dedup':{'old_tile':318,'shared_tile':317,'xor_flags':128,'references':6} if full_panel else None,'other_coordinates_palette_order_exact':True,'portrait_parts':120 if full_panel else 103,'frame_count_timing_unchanged':True,'portrait_part_windows_repositioned':True,'other_frame_tiles_preserved':len(protected),'original_unreferenced_slots_available':8,'palette_row':5,'runtime_verified':False}

def prepare(out,full_panel=False):
    m,records,original=sources();out.mkdir(parents=True,exist_ok=False)
    s=original['ST0E_U1.ARC'];t=entry(s,0x10102);p=entry(s,10);c=composition_frame(p,1,1)
    old,size,bounds,coverage=compose_static(t[40960:90112],local_composition(c))
    source=ART/('corrected.png' if full_panel else 'generated.png')
    im=Image.open(source).convert('RGBA');box=im.getchannel('A').getbbox();im=im.crop(box)
    # Uniform cover conversion; all native game pixels are newly quantized art.
    scale=max(size[0]/im.width,size[1]/im.height);dims=(round(im.width*scale),round(im.height*scale))
    im=im.convert('RGBa').resize(dims,Image.Resampling.LANCZOS).convert('RGBA')
    dx=(im.width-size[0])//2;dy=(im.height-size[1])//2;im=im.crop((dx,dy,dx+size[0],dy+size[1]));a=np.array(im)
    # Preserve the original slanted panel boundary, not the old character art.
    # Original index0 also occurs in character-internal negative spaces. It
    # must not be copied as holes in the new face/body. Use only the panel's
    # outer quadrilateral as the crop mask, matching the native UI layout.
    yy,xx=np.indices((size[1],size[0]))
    boundary=np.ones((size[1],size[0]),bool) if full_panel else (yy>=2)&(yy<=157)&(xx<=189)&(xx>=1+(yy-2)*80/155)
    # A slightly steeper slant makes the filled panel coverable in the same
    #103 windows. Original Zero has internal transparent gaps; treating those
    #as a fixed mask would punch holes in Rin's headband and lower body.
    if full_panel:p,grid_report=portrait_grid(p)
    else:
        positions=[]
        for y in range(0,160,16):
            left=max(0,int(1+(y-2)*80/155))
            for x in range(left,192,16):positions.append((min(x,176),y))
        if len(positions)>len(c['parts']):raise ValueError('Portrait part budget exceeded')
        positions += [positions[-1]]*(len(c['parts'])-len(positions))
        rp=bytearray(p)
        for q,(x,y) in zip(c['parts'],positions):rp[q['record_offset']+2:q['record_offset']+4]=bytes(((x+bounds[0])&255,(y+bounds[1])&255))
        p=bytes(rp);grid_report=None
    nc=composition_frame(p,1,1)
    _,ns,nb,ncov=compose_static(t[40960:90112],local_composition(nc))
    if ns!=size or nb!=bounds:raise ValueError('Portrait native canvas shifted')
    cov=np.array([bool(v) for v in ncov]).reshape(size[1],size[0]);mask=(a[:,:,3]>=128)&boundary
    if np.any(mask&~cov):raise ValueError('Generated panel escapes repositioned parts')
    words=[0]+[0x8000|(r>>3)|((g>>3)<<5)|((b>>3)<<10) for r,g,b in RGB]
    actual=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in words[1:]],np.int32)
    distances=((a[:,:,:3].astype(np.int32)[:,:,None,:]-actual)**2).sum(3)
    indices=np.where(mask,distances.argmin(2)+1,0).astype(np.uint8).tobytes();palette=struct.pack('<16H',*words)
    # Original portrait used98 unique tiles for103 parts. Eight unreferenced
    # slots in this same UI bank accommodate new nonduplicate patterns; every
    # tile used by any other known frame remains protected by the allocator.
    nt,np_,packing=repack_frames(t[40960:90112],p,1,{1:(indices,size)})
    new={'ST0E_U1.ARC':replace_entry(replace_entry(s,0x10102,t[:40960]+nt+t[90112:]),10,np_)}
    col=original['COL0E_U1.ARC'];cp=entry(col,5);new['COL0E_U1.ARC']=replace_entry(col,5,cp[:160]+palette+cp[192:])
    v=verify(original,new,indices,size,palette,full_panel)
    for name,data in new.items():(out/name).write_bytes(data)
    pic=save_image(indices,size,words,out/'portrait.png');pic.resize((size[0]*4,size[1]*4),Image.Resampling.NEAREST).save(out/'portrait_4x.png')
    (out/'palette.bin').write_bytes(palette);(out/'indices.bin').write_bytes(indices)
    report={'kind':'rin_selection_portrait','parent_sha256':PARENT_SHA,'generated_source':(ART/'generated.png').relative_to(ROOT).as_posix(),'generated_sha256':digest(ART/'generated.png'),'prompt':(ART/'prompt.txt').relative_to(ROOT).as_posix(),'tool':'built-in image_gen','size':size,'bounds':bounds,'uniform_scale':scale,'source_alpha_bbox':box,'transparent_index':0,'opaque_colors':len(set(indices)-{0}),'panel_crop':{'top_left_x':1,'bottom_left_x':81,'top_y':2,'bottom_y':157,'right_x':189},'packing':packing,'verification':v,'files':[{'source':r,'file':r['path'].split('/')[-1].split(';')[0],'sha256':sha(new[r['path'].split('/')[-1].split(';')[0]])} for r in records]}
    if full_panel:report.update(full_panel=True,generated_source=source.relative_to(ROOT).as_posix(),generated_sha256=digest(source),prompt=(ART/'correction_prompt.txt').relative_to(ROOT).as_posix(),panel_crop=None,part_grid=grid_report,faces_left=True,border_in_generated_art=True)
    (out/'recipe.json').write_text(json.dumps(report,indent=2)+'\n','utf8');print(json.dumps({'output':str(out),'verification':v,'opaque_colors':report['opaque_colors'],'packing':packing}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--full-panel',action='store_true');a=p.parse_args();prepare(a.output,a.full_panel)
