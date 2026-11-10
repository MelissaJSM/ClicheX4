"""C03 の jacket-free Nana pilot: keep armor layers and timing unchanged."""
import json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import D,entry,render,rgba,write,sha
from scripts.prepare_rin_run import quantize
from scripts.extract_zero import save_image
from scripts.prepare_shibuki_ultimate_production import pack_shared,repack_parts,records
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import graphics_bank,composition_frame,decode_stream,bank_offsets
from src.psx_sprite_batch import canvas_from_parts
from src.psx_ui_atlas import local_composition
from src.psx_compress import encode_stream
from src.psx_bank_repack import repack_graphics_bank

PILOTS=(0,85,1,33)

def targets():
    folder=D/'nana_preultimate';arc=(D/'ver_rin_nana/baseline/PL02_U.ARC').read_bytes()
    palette=struct.unpack_from('<16H',entry(arc,9));colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in palette[1:]],np.int32)
    generated=Image.open(folder/'generated.png').convert('RGBA');targets={};reports=[]
    preview=Image.new('RGB',(4*256,3*280),(28,34,45));dr=ImageDraw.Draw(preview)
    for i,n in enumerate(PILOTS):
        base,_=render(arc,0,0,n);full=base.copy();over=np.zeros_like(base)
        for b in (8,5,7,6):
            part,_=render(arc,0,b,n);over[part>0]=part[part>0];full[part>0]=part[part>0]
        y,x=np.nonzero(full);box=(int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1));w,h=box[2]-box[0],box[3]-box[1]
        crop=generated.crop((i%2*generated.width//2,i//2*generated.height//2,(i%2+1)*generated.width//2,(i//2+1)*generated.height//2))
        a=np.array(crop);a[:,:,3]=np.where(a[:,:,3]>=224,255,0);crop=Image.fromarray(a);crop=crop.crop(crop.getbbox())
        # One uniform scale per existing pose; no reshaping of the accepted head or soles.
        px=quantize(crop,colors,h/crop.height);ph,pw=px.shape;target=np.zeros_like(base);left=box[0]+round((w-pw)/2);top=box[3]-ph
        target[top:top+ph,left:left+pw]=px
        # Retain accepted head, including the ear silhouette, and accepted sole registration.
        target[:153]=full[:153];target[176:]=full[176:]
        # Only pixels hidden by the acquired jacket may differ from the existing base.
        # This also preserves exposed blink windows and prevents new base pixels escaping it.
        target[over==0]=base[over==0]
        if not np.array_equal(np.where(over,over,target),full):raise ValueError('Acquired display changed')
        targets[n]=target;save_image(target.tobytes(),(384,384),palette,folder/f'pilot_{n:03}.png')
        for j,img in enumerate([rgba(base,palette),rgba(target,palette),Image.open(D/f'ver_rin_nana/x_ultimate/{n:03}.png').convert('RGBA')]):
            small=img.crop((128,120,192,184)).resize((256,256),Image.Resampling.NEAREST);preview.paste(small,(i*256,j*280+24),small)
            dr.text((i*256+5,j*280+5),f'{n} '+['before','swimsuit pilot','acquired unchanged'][j],fill='white')
        reports.append({'frame':n,'native_bbox':list(box),'generated_uniform_scale':h/crop.height,'head_and_soles_retained':True,'acquired_pixels_unchanged':True,'opaque_pixels':int((target>0).sum())})
    preview.save(folder/'pilot_review.png');write(folder/'pilot.json',{'source_arc_sha256':sha(arc),'generated_sha256':sha((folder/'generated.png').read_bytes()),'frames':reports,'production_complete':False,'runtime_verified':False})
    return arc,targets

def pack_pilot(arc,masters):
    folder=D/'nana_preultimate';g,c,pal=[entry(arc,k)for k in(2,3,9)];bank=graphics_bank(g,0,allow_bank_aliases=True)
    replacements={};changes={};expanded={};reports=[]
    for master,image in masters.items():
        f=bank['frames'][master];refs=[q['index']for q in bank['frames']if q['offset']==f['offset']]
        raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
        images=[]
        for n in refs:
            base,_=render(arc,0,0,n);full=base.copy();over=np.zeros_like(base)
            for b in(8,5,7,6):
                a,_=render(arc,0,b,n);over[a>0]=a[a>0];full[a>0]=a[a>0]
            target=image.copy();target[:153]=full[:153];target[176:]=full[176:];target[over==0]=base[over==0]
            if not np.array_equal(np.where(over,over,target),full):raise ValueError('Alias acquired display changed')
            expanded[n]=target;images.append(target[80:240,80:240])
        protected={q['tile']for n in refs for b in(5,6,7,8)for q in composition_frame(c,b,n)['parts']};pool=set(range(f['tile_count']))-protected
        original_limits=[len(composition_frame(c,0,n)['parts'])for n in refs]
        failure=None
        for extra in range(3):
            limits=[v+extra for v in original_limits]
            try:modified,assignments=pack_shared(raw,f['tile_count'],images,pool,limits);break
            except ValueError as error:failure=error
        else:raise ValueError(f'Frames {refs}, limits {limits}, tiles {len(pool)}: {failure}')from failure
        for n,assignment,limit in zip(refs,assignments,limits):
            if not assignment or len(assignment)>limit:raise ValueError('Part count exceeded')
            assignment=assignment+[assignment[-1]]*(limit-len(assignment));changes[n]=b''.join(struct.pack('<BBbb',fl,t,x-80,y-80)for t,x,y,fl in assignment);replacements[n]=modified
            for b in(5,6,7,8):
                cp=local_composition(composition_frame(c,b,n))
                if not np.array_equal(canvas_from_parts(raw,f['tile_count'],cp),canvas_from_parts(modified,f['tile_count'],cp)):raise ValueError('Protected armor layer changed')
        reports.append({'frames':refs,'pool':sorted(pool),'original_parts':original_limits,'parts':[len(a)for a in assignments],'new_record_counts':limits,'compressed_bytes':len(encode_stream(modified))})
    nc,slack=repack_parts(c,0,changes);ng,repack=repack_graphics_bank(g,0,{n:encode_stream(a)for n,a in replacements.items()});result=replace_entry(replace_entry(arc,2,ng),3,nc)
    checked=0
    for bi in range(len(bank_offsets(g,allow_aliases=True))):
        before=graphics_bank(g,bi,allow_bank_aliases=True);after=graphics_bank(ng,bi,allow_bank_aliases=True)
        if (before['base'],before['end'],len(before['frames']))!=(after['base'],after['end'],len(after['frames'])):raise ValueError('Bank boundaries changed')
        for a,b in zip(before['frames'],after['frames']):
            old=decode_stream(g,a['offset'],a['limit'],a['tile_count']*128).data;new=decode_stream(ng,b['offset'],b['limit'],b['tile_count']*128).data
            if new!=(replacements.get(a['index'],old)if bi==0 else old):raise ValueError('Other graphics changed')
            checked+=1
    for bi in range(len(bank_offsets(c))):
        for n in range(composition_frame(c,bi,0)['bank_frame_count']):
            if bi==0 and n in changes:continue
            if records(c,bi,n)!=records(nc,bi,n):raise ValueError('Other parts changed')
    for n,want in expanded.items():
        actual,_=render(result,0,0,n)
        if not np.array_equal(actual,want):raise ValueError('Pilot readback differs')
    if entry(result,9)!=pal or len(result)!=len(arc):raise ValueError('Palette or length changed')
    (folder/'pilot_PL02_U.ARC').write_bytes(result)
    write(folder/'packing.json',{'source_sha256':sha(arc),'result_sha256':sha(result),'frames':sorted(expanded),'parts_slack':slack,'graphics_repack':repack,'groups':reports,'all_graphics_checked':checked,'armor_layers_preserved':True,'palette_preserved':True,'timing_preserved':True,'production_complete':False,'runtime_verified':False})
    print(json.dumps({'frames':sorted(expanded),'graphics_slack':repack['remaining_slack'],'parts_slack':slack,'checked':checked}))

if __name__=='__main__':pack_pilot(*targets())
