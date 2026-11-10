"""Pack the accepted detailed run cycle plus the seven-key pilot without clipping."""
from pathlib import Path
import sys,json,struct,hashlib,argparse
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D))
import pack_rin_keys as base
from fit_rin_windows import fit_windows
from scripts.overhaul_sprites_costume_pack import repack_variable,resize_tile_storage
from scripts.prepare_shibuki_ultimate_production import repack_parts,records,fast_fit
from scripts.solve_sprite_cover import cover
import scripts.prepare_shibuki_armor_motion as motion

EXPECTED=set(range(7,21))|{49,95,97,99,101}
MANIFEST=D/'rin_extension/run_art_sources_v1.json'
CACHE=D/'rin_extension/run_pack_cache_v1'
OUT=D/'rin_extension/prepared_run_v1'

def patient_fit(mask,count):
    result=fast_fit(mask,count)
    if result is not None:return result
    solved=cover(mask,count,20)
    return solved['rects']if solved['fits']else None

motion.fit=patient_fit

def get_targets():
    meta=json.loads(MANIFEST.read_text('utf8'))
    base.need(meta['source_arc_sha256']==base.SHA,'Manifest ARC source')
    result={}
    for row in meta['frames']:
        n=row['ref'];path=ROOT/row['path']
        base.need(path.resolve().is_relative_to((ROOT/'work/sprite_style_unification_20261107').resolve()),'Art outside authored folder')
        base.need(base.sha(path.read_bytes())==row['sha256'],'Registered art changed')
        a=np.array(Image.open(path));base.need(a.shape==(384,384)and a.dtype==np.uint8 and a.max()<=15,'Invalid indexed target')
        base.need(n not in result,'Duplicate reference');result[n]=a
    base.need(set(result)==EXPECTED,'Incomplete run scope')
    for row in meta['generated_sources']:
        base.need(base.sha((ROOT/row['path']).read_bytes())==row['sha256'],'Authored source changed')
    return result

def one_frame(c,n,raw,count,target):
    key=base.sha(base.SHA.encode()+str(n).encode()+raw+records(c,0,n)+target.tobytes()+b'run-v1')
    path=CACHE/(str(n)+'_'+key+'.json')
    if path.exists():
        row=json.loads(path.read_text('utf8'));return bytes.fromhex(row['raw']),row['count'],bytes.fromhex(row['records']),row['method']
    cp=base.composition_frame(c,0,n);base.need(all(p['flags']==0 for p in cp['parts']),'Unexpected run palette/flip flags')
    try:
        if n in(9,10,15,16):raise ValueError('Measured fixed-window cover requires reassignment')
        local,edits=fit_windows(c,n,raw,count,target,base.packer.edit_visible_set)
        newcp=base.composition_frame(local,0,n);_,size,bb,_=base.compose_indices(raw,count,newcp)
        crop=target[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]
        new=base.packer.edit_visible_set(raw,count,[(newcp,crop.tobytes(),size)])
        rec=records(local,0,n);method={'type':'sampling_window_adjustment','edits':edits}
    except ValueError:
        newcount=count+1 if n==15 else count
        limit=len(cp['parts'])+(1 if n==15 else 0)
        expanded=resize_tile_storage(raw,count,newcount)
        new,rr=motion.identical(expanded,newcount,target,set(range(newcount)),limit)
        # Empty spare records duplicate an identical opaque tile; no new paint or timing.
        while len(rr)<limit:rr.append(rr[-1])
        base.need(len(rr)==limit,'Native part limit')
        rec=b''.join(bytes([0,t,(x-160)&255,(y-160)&255])for t,x,y in rr)
        method={'type':'native_window_reassignment','old_tiles':count,'new_tiles':newcount,'old_parts':len(cp['parts']),'new_parts':limit}
        count=newcount
    CACHE.mkdir(exist_ok=True)
    path.write_text(json.dumps({'raw':new.hex(),'count':count,'records':rec.hex(),'method':method},indent=2)+'\n','utf8')
    return new,count,rec,method

def build(arc,targets):
    base.need(base.sha(arc)==base.SHA,'Wrong source ARC');expected=get_targets()
    base.need(set(targets)==EXPECTED,'Target set changed')
    for n in targets:base.need(np.array_equal(targets[n],expected[n]),'Native target differs from registered artwork')
    g,c=base.entry(arc,2),base.entry(arc,3);bank=base.graphics_bank(g,0)
    replacements={};counts={};partsets={};methods=[]
    for n in sorted(targets):
        f=bank['frames'][n];raw=base.decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
        nr,count,rec,method=one_frame(c,n,raw,f['tile_count'],targets[n]);replacements[n]=nr;counts[n]=count;partsets[n]=rec;methods.append({'ref':n,**method})
        print(json.dumps({'prepared_ref':n,'tiles':count,'parts':len(rec)//4,'method':method['type']}),flush=True)
    # Variable repacker requires a complete alias group. Unselected references get
    # their exact original raw stream/count; divergent new variants are split.
    touched={bank['frames'][n]['offset']for n in targets}
    for f in bank['frames']:
        if f['offset']in touched and f['index']not in replacements:
            replacements[f['index']]=base.decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;counts[f['index']]=f['tile_count']
    ng,layout=repack_variable(g,replacements,counts);nc,slack=repack_parts(c,0,partsets)
    out=base.replace_entry(base.replace_entry(arc,2,ng),3,nc)
    base.need(base.replace_entry(base.replace_entry(out,2,g),3,c)==arc,'Non-graphics entries changed')
    base.need(base.bank_offsets(g,allow_aliases=True)==base.bank_offsets(ng,allow_aliases=True),'Graphics boundaries changed')
    base.need(base.bank_offsets(c)==base.bank_offsets(nc),'Composition boundaries changed')
    totals={'raw':0,'display':0,'non_target_raw_exact':0,'non_target_display_exact':0};changes=[]
    for bi in(0,1):
        ob=base.graphics_bank(g,bi);nb=base.graphics_bank(ng,bi)
        for of,nf in zip(ob['frames'],nb['frames']):
            n=of['index'];selected=bi==0 and n in targets
            ar=base.decode_stream(g,of['offset'],of['limit'],of['tile_count']*128).data;br=base.decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data;totals['raw']+=1
            base.need(nf['tile_count']<=32,'32-tile limit')
            if not selected:
                base.need(ar==br and of['tile_count']==nf['tile_count'],'Unselected raw differs')
                base.need(records(c,bi*5,n)==records(nc,bi*5,n),'Unselected composition differs');totals['non_target_raw_exact']+=1
            else:
                before_a=np.frombuffer(base.indexed_atlas(ar,of['tile_count'])[0],np.uint8).reshape(-1,256)
                after_a=np.frombuffer(base.indexed_atlas(br,nf['tile_count'])[0],np.uint8).reshape(-1,256)
                for p in base.composition_frame(nc,0,n)['parts']:
                    t=p['tile'];y,x=t//16*16,t%16*16
                    if t%16==0:base.need(not np.any((before_a[y:y+16,x]==0)&(after_a[y:y+16,x]>0)),'New GPU first-column alpha')
                    if p['flip_y']and t//16%16==0:base.need(not np.any((before_a[y,x:x+16]==0)&(after_a[y,x:x+16]>0)),'New GPU flipped first-row alpha')
            if bi==1 and 42<=n<=49:continue
            before=base.render(arc,bi,bi*5,n)[0];after=base.render(out,bi,bi*5,n)[0];want=targets[n]if selected else before
            base.need(np.array_equal(want,after),f'Readback mismatch b{bi}:{n}');totals['display']+=1
            if not selected:totals['non_target_display_exact']+=1
            else:changes.append({'ref':n,'changed_pixels':int(np.count_nonzero(before!=after)),'old_tiles':of['tile_count'],'new_tiles':nf['tile_count'],'old_parts':len(base.composition_frame(c,0,n)['parts']),'new_parts':len(base.composition_frame(nc,0,n)['parts'])})
    # Other composition banks are not repacked, even if they contain aliases.
    starts=base.bank_offsets(c);base.need(c[starts[1]:]==nc[starts[1]:],'Other composition bank bytes')
    return out,{'counts':totals,'methods':methods,'layout':layout,'composition_slack':slack,'changes':changes,'authored_native_pixels_exact':True,'no_cropping_or_rescaling':True,'head_overrides':0,'new_gpu_boundary_alpha':0,'palette_audio_timing_other_entries_exact':True,'reserved_partial8_raw_exact':True}

def boards(arc,out):
    for label,row in(('normal',0),('black',13)):
        pal=struct.unpack_from('<16H',base.entry(arc,9),row*32)
        ns=[147]+list(range(7,21))+[49,95,97,99,101]
        for page in range(0,len(ns),4):
            subset=ns[page:page+4];sheet=Image.new('RGB',(1152,408*len(subset)),'#64717b');draw=ImageDraw.Draw(sheet)
            for iy,n in enumerate(subset):
                for ix,(title,im)in enumerate([('idle',base.render(arc,0,0,147)[0]),('before',base.render(arc,0,0,n)[0]),('packed new',base.render(out,0,0,n)[0])]):
                    pic=base.rgba(im,pal).crop((128,128,192,192)).resize((384,384),Image.Resampling.NEAREST);sheet.paste(pic,(ix*384,iy*408+24),pic);draw.text((ix*384+4,iy*408+5),f'{n} {title}',fill='white')
            sheet.save(OUT/f'{label}_readback_{page//4:02d}.png')

def main():
    parent=ROOT/'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin';base.need(base.sha(parent.read_bytes())==base.BINSHA,'Parent BIN differs')
    arc=base.read_disc(parent,('PL01_U.ARC',))[0]['PL01_U.ARC'];targets=get_targets();out,proof=build(arc,targets);again,_=build(arc,targets);base.need(out==again,'Reproduction differs')
    rejection=[]
    for case in('wrong_source','missing_ref','modified_pixel','palette_out_of_range'):
        aa=arc;tt={n:x.copy()for n,x in targets.items()}
        if case=='wrong_source':aa=bytes([arc[0]^1])+arc[1:]
        elif case=='missing_ref':del tt[17]
        elif case=='modified_pixel':tt[18][140,150]^=1
        else:tt[15][140,150]=16
        try:build(aa,tt)
        except ValueError as exc:rejection.append({'case':case,'error':str(exc)})
        else:raise ValueError('Invalid input accepted')
    OUT.mkdir(exist_ok=True);(OUT/'PL01_U.ARC').write_bytes(out);boards(arc,out)
    report={'source_bin':str(parent.relative_to(ROOT)),'source_bin_sha256':base.BINSHA,'source_arc_sha256':base.SHA,'resource':str((OUT/'PL01_U.ARC').relative_to(ROOT)),'after_sha256':base.sha(out),'references':sorted(EXPECTED),'art_manifest':str(MANIFEST.relative_to(ROOT)),'art_manifest_sha256':base.sha(MANIFEST.read_bytes()),'verification':proof,'reproducible':True,'rejections':rejection,'game_changed':False,'runtime_verified':False}
    (OUT/'proposal.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'sha256':base.sha(out),'verification':proof}))

if __name__=='__main__':main()
