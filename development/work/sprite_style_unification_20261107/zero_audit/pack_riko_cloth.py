"""Register four accepted clothing keys and exact translated shared poses."""
from pathlib import Path
import sys,json,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent;sys.path.insert(0,str(D))
import pack_rin_keys as native
from fit_rin_windows import fit_windows
from scripts.prepare_shibuki_ultimate_production import repack_parts,records,fast_fit
from scripts.solve_sprite_cover import cover
import scripts.prepare_shibuki_armor_motion as motion
PARENT=D/'riko_restore/prepared_rear_v1/PL01_U.ARC';PARENT_SHA='f8f346691709107a4ae774b49f0f46d662941442f75bf92ee0eead97bbf671c8'
ART=D/'riko_cloth_inputs/registered_candidate_v1';OUT=D/'riko_restore/prepared_cloth_v1';CACHE=D/'riko_restore/cloth_pack_cache_v1'
PNG_SHA={8:'029fb4961a2ebc0b6f5c42d12979a5ea8791711f32f4453e38a7c6de8e7a797c',14:'ce5ae55ab051133ca719673b541c01f661d3eca0ea1415c6d67c24c0be22bacc',27:'c68a5c88dfd6ac157d5bf773334900185078c3473288aac233573092d17b15cc',133:'30b7cb8e28d7cbeec9d37ac5f401b6ceb4da586a56502730888e049a76862195'}
KEYS={(0,8):(8,0,0),(0,14):(14,0,0),**{(0,n):(27,0,0)for n in range(27,33)},**{(0,n):(133,0,0)for n in(133,134,246)},**{(1,n):(133,0,0)for n in(87,91,93)},**{(1,n):(133,-5,0)for n in(95,96,98,99)}}

def shifted(a,dx,dy):
    out=np.zeros_like(a);ys,xs=np.nonzero(a);native.need(np.all((xs+dx>=0)&(xs+dx<384)&(ys+dy>=0)&(ys+dy<384)),'Shift outside canvas');out[ys+dy,xs+dx]=a[ys,xs];return out

def get_targets(arc):
    native.need(native.sha(arc)==PARENT_SHA,'Wrong working ARC')
    native.need(native.sha((D/'riko_cloth_inputs/generated.png').read_bytes())=='597fc11dc684df34658627582e9c744e571a6d76d7864665cda97dff8da6df6b','Source art changed')
    masters={}
    for k,h in PNG_SHA.items():
        p=ART/f'b0_{k:03d}_indices.png';native.need(native.sha(p.read_bytes())==h,'Registered clothes changed');a=np.array(Image.open(p));native.need(a.shape==(384,384)and a.dtype==np.uint8 and a.max()<=15,'Invalid native target')
        mask=np.array(Image.open(D/'riko_cloth_inputs'/f'b0_{k:03d}_preserve_head_mask.png'))>0;old=native.render(arc,0,0,k)[0];native.need(int(mask.sum())==309 and np.array_equal(a[mask],old[mask]),'Accepted head changed');masters[k]=a
    result={}
    for (b,n),(k,dx,dy)in KEYS.items():
        old=native.render(arc,b,b*5,n)[0];master=native.render(arc,0,0,k)[0];native.need(np.array_equal(old,shifted(master,dx,dy)),'Non-identical shared pose')
        result[(b,n)]=shifted(masters[k],dx,dy)
    return result

def patient_fit(mask,count):
    got=fast_fit(mask,count)
    if got is not None:return got
    result=cover(mask,count,20);return result['rects']if result['fits']else None
motion.fit=patient_fit

def pack_frame(c,b,n,raw,count,target):
    key=native.sha(PARENT_SHA.encode()+f'{b}:{n}'.encode()+raw+records(c,b*5,n)+target.tobytes()+b'cloth-v1')
    file=CACHE/(f'b{b}_{n:03d}_{key}.json')
    if file.exists():
        v=json.loads(file.read_text('utf8'));return bytes.fromhex(v['raw']),bytes.fromhex(v['records']),v['method']
    try:
        newc,edits=fit_windows(c,n,raw,count,target,native.packer.edit_visible_set,b*5);cp=native.composition_frame(newc,b*5,n);_,size,bb,_=native.compose_indices(raw,count,cp);want=target[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]
        nr=native.packer.edit_visible_set(raw,count,[(cp,want.tobytes(),size)]);rec=records(newc,b*5,n);method={'type':'native_visible_texels','window_edits':edits}
    except ValueError:
        cp=native.composition_frame(c,b*5,n);native.need(all(p['clut']==0 for p in cp['parts']),'Unexpected mixed palette')
        nr,rr=motion.identical(raw,count,target,set(range(count)),len(cp['parts']))
        while len(rr)<len(cp['parts']):rr.append(rr[-1])
        rec=b''.join(bytes([0,t,(x-160)&255,(y-160)&255])for t,x,y in rr);method={'type':'native_window_reassignment'}
    CACHE.mkdir(exist_ok=True);file.write_text(json.dumps({'raw':nr.hex(),'records':rec.hex(),'method':method},indent=2)+'\n','utf8');return nr,rec,method

def build(arc,targets):
    expected=get_targets(arc);native.need(set(targets)==set(KEYS),'Wrong target refs')
    for key in targets:native.need(np.array_equal(targets[key],expected[key]),'Target differs from registered art')
    g,c=native.entry(arc,2),native.entry(arc,3);ng,nc=g,c;layouts=[];methods=[]
    for b in(0,1):
        bank=native.graphics_bank(g,b);raws={};parts={}
        for (bb,n),target in targets.items():
            if bb!=b:continue
            f=bank['frames'][n];raw=native.decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
            nr,rec,method=pack_frame(c,b,n,raw,f['tile_count'],target);raws[n]=nr;parts[n]=rec;methods.append({'bank':b,'ref':n,**method});print(json.dumps({'bank':b,'ref':n,'method':method['type']}),flush=True)
        part_changes={n:r for n,r in parts.items()if r!=records(nc,b*5,n)}
        if part_changes:nc,slack=repack_parts(nc,b*5,part_changes)
        else:slack=None
        groups={};merged=[]
        for n in raws:groups.setdefault(bank['frames'][n]['offset'],[]).append(n)
        for off,ns in groups.items():
            if len(ns)<2:continue
            # Preserve byte-identical authored streams rather than rewriting
            # hidden cape texels through another full-display ownership pass.
            if all(raws[n]==raws[ns[0]] for n in ns):
                merged.append(ns);continue
            first=bank['frames'][ns[0]];raw=native.decode_stream(g,off,first['limit'],first['tile_count']*128).data;edits=[]
            for n in ns:
                cp=native.composition_frame(nc,b*5,n);_,size,bb,_=native.compose_indices(raw,first['tile_count'],cp);want=targets[b,n][160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]];edits.append((cp,want.tobytes(),size))
            try:joined=native.packer.edit_visible_set(raw,first['tile_count'],edits)
            except ValueError:continue
            for n in ns:raws[n]=joined
            merged.append(ns)
        ng,layout=native.packer.repack_raw(ng,b,raws);layouts.append({**layout,'parts_slack':slack,'changed_compositions':sorted(part_changes),'joint_shared_edits':merged})
    out=native.replace_entry(native.replace_entry(arc,2,ng),3,nc)
    native.need(native.replace_entry(native.replace_entry(out,2,g),3,c)==arc,'Other entries changed')
    native.need(native.bank_offsets(g,allow_aliases=True)==native.bank_offsets(ng,allow_aliases=True),'Graphics boundaries')
    native.need(native.bank_offsets(c)==native.bank_offsets(nc),'Composition boundaries')
    totals={'raw':0,'display':0,'non_target_raw_exact':0,'non_target_display_exact':0};changes=[]
    for b in(0,1):
        ob,nb=native.graphics_bank(g,b),native.graphics_bank(ng,b)
        for of,nf in zip(ob['frames'],nb['frames']):
            n=of['index'];selected=(b,n)in targets;native.need(of['tile_count']==nf['tile_count']<=32,'Tile count')
            ar=native.decode_stream(g,of['offset'],of['limit'],of['tile_count']*128).data;br=native.decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data;totals['raw']+=1
            if not selected:
                native.need(ar==br,'Unselected raw');native.need(records(c,b*5,n)==records(nc,b*5,n),'Unselected part records');totals['non_target_raw_exact']+=1
            else:
                aa=np.frombuffer(native.indexed_atlas(ar,of['tile_count'])[0],np.uint8).reshape(-1,256);ba=np.frombuffer(native.indexed_atlas(br,nf['tile_count'])[0],np.uint8).reshape(-1,256)
                for p in native.composition_frame(nc,b*5,n)['parts']:
                    t=p['tile'];y,x=t//16*16,t%16*16
                    if t%16==0:native.need(not np.any((aa[y:y+16,x]==0)&(ba[y:y+16,x]>0)),'New GPU first-column alpha')
                    if p['flip_y']and t//16%16==0:native.need(not np.any((aa[y,x:x+16]==0)&(ba[y,x:x+16]>0)),'New GPU flipped-first-row alpha')
            if b==1 and 42<=n<=49:continue
            old=native.render(arc,b,b*5,n)[0];new=native.render(out,b,b*5,n)[0];native.need(np.array_equal(new,targets[(b,n)]if selected else old),'Readback differs');totals['display']+=1
            if not selected:totals['non_target_display_exact']+=1
            else:changes.append({'bank':b,'ref':n,'changed_pixels':int(np.count_nonzero(old!=new)),'origin_translation_from_key':list(KEYS[b,n][1:]),'head_preserved':True})
    starts=native.bank_offsets(c)
    for b in range(len(starts)):
        if b in(0,5):continue
        end=starts[b+1]if b+1<len(starts)else len(c);native.need(c[starts[b]:end]==nc[starts[b]:end],'Other composition bank')
    return out,{'counts':totals,'methods':methods,'layouts':layouts,'changes':changes,'new_gpu_boundary_alpha':0,'tile_counts_preserved':True,'composition_bytes_exact':nc==c,'source_3rd_saber9_and_rear28_preserved':True,'palette_audio_timing_other_entries_exact':True,'heads_preserved_pixels_per_reference':309,'authored_registered_pixels_exact':True}

def boards(arc,out):
    ns=list(KEYS)
    for label,row in(('normal',0),('black',13)):
        pal=struct.unpack_from('<16H',native.entry(arc,9),row*32)
        for start in range(0,len(ns),4):
            subset=ns[start:start+4];sheet=Image.new('RGB',(1200,428*len(subset)),'#64717b');draw=ImageDraw.Draw(sheet)
            for iy,(b,n)in enumerate(subset):
                for ix,(title,a)in enumerate([('idle',native.render(arc,0,0,147)[0]),('before',native.render(arc,b,b*5,n)[0]),('packed clothes',native.render(out,b,b*5,n)[0])]):
                    pic=native.rgba(a,pal).crop((120,112,200,192)).resize((400,400),Image.Resampling.NEAREST);sheet.paste(pic,(ix*400,iy*428+28),pic);draw.text((ix*400+5,iy*428+5),f'b{b}:{n} {title}',fill='white')
            sheet.save(OUT/f'{label}_readback_{start//4:02d}.png')

def main():
    arc=PARENT.read_bytes();targets=get_targets(arc);out,proof=build(arc,targets);again,_=build(arc,targets);native.need(out==again,'Reproduction')
    rejections=[]
    for case in('parent','missing_ref','altered_head','palette_16'):
        aa=arc;tt={k:a.copy()for k,a in targets.items()}
        if case=='parent':aa=bytes([arc[0]^1])+arc[1:]
        elif case=='missing_ref':del tt[1,99]
        elif case=='altered_head':tt[0,8][140,153]^=1
        else:tt[0,14][140,153]=16
        try:build(aa,tt)
        except ValueError as exc:rejections.append({'case':case,'reason':str(exc)})
        else:raise ValueError('Invalid target accepted')
    OUT.mkdir(exist_ok=True);(OUT/'PL01_U.ARC').write_bytes(out);boards(arc,out)
    report={'source_arc':str(PARENT.relative_to(ROOT)),'source_arc_sha256':PARENT_SHA,'resource':str((OUT/'PL01_U.ARC').relative_to(ROOT)),'after_sha256':native.sha(out),'registration':str((ART/'registration.json').relative_to(ROOT)),'target_references':[f'b{b}_{n:03d}'for b,n in KEYS],'verification':proof,'reproducible':True,'rejections':rejections,'game_changed':False,'runtime_verified':False}
    (OUT/'proposal.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'after_sha256':native.sha(out),'verification':proof}))

if __name__=='__main__':main()
