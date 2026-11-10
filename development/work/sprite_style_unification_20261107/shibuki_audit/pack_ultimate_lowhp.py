"""얼티밋 새 이동 누적본 위에 저체력 6참조를 무손실 등록한다."""
from pathlib import Path
import sys,json,struct
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import sha,need,write,crop,lossless_pack,same_rgba,SOURCE_SHA
from prepare_ultimate_lowhp_targets import targets
from scripts.export_x_consistency import Archive,page
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_shibuki_ultimate_production import repack_parts,records
from scripts.overhaul_sprites_costume_pack import repack_variable
from scripts.discover_inputs import psx_arc
from src.psx_player import composition_frame,decode_stream,bank_offsets,indexed_atlas
from src.psx_compress import encode_stream

P=H/'prepared_run_complete03/PL02_U.ARC'
PSHA='c7eb1c7998a6780d04f4397a64af653265e3d83985c3c05768dd3de46eae5265'
BASELINE='98ab01e8581d6bca15d75d703e7605899f2a871e042f5b09b13c5f2e07cf132e'
PARTS=(0,5,6,7,8);SELECTED=set(range(120,126))
O=H/'prepared_ultimate_lowhp01'

def pack(data,full,base):
    need(sha(data)==PSHA,'Wrong frozen run parent')
    need(set(full)==set(base)==SELECTED,'Exact six lowHP refs required')
    a=Archive(data);g,c=a.g,a.c
    changes={b:{}for b in PARTS};replacements={};counts={};expected={};reports=[]
    groups={}
    for f in a.banks[0]['frames']:groups.setdefault(f['offset'],[]).append(f['index'])
    for off,refs in groups.items():
        if not SELECTED.intersection(refs):continue
        need(set(refs)<=SELECTED,'Unexpected external raw alias')
        planes=[];keys=[];target={}
        for n in refs:
            for q in (full[n],base[n]):need(q.shape==(384,384) and q.dtype==np.uint8 and int(q.max())<16,'Wrong indexed art')
            need(not np.any((base[n]>0)&(full[n]==0)),'After alpha outside before')
            target[n,0]=base[n]
            target[n,5]=np.where(same_rgba(a,full[n],base[n]),0,full[n]).astype(np.uint8)
            for b in (6,7,8):
                need(not a.layer(n,b)[0].any(),'Unexpected independent Ultimate armor layer')
                target[n,b]=np.zeros((384,384),np.uint8)
            for b in PARTS:
                v=crop(target[n,b])
                if v.any():keys.append((n,b));planes.append(v)
        raw,assigned,method=lossless_pack(planes)
        rr={(n,b):[]for n in refs for b in PARTS}
        for key,r in zip(keys,assigned):rr[key]=r
        atlas=np.frombuffer(indexed_atlas(raw,32)[0],np.uint8).reshape(32,256)
        need(not atlas[:,0].any(),'GPU U boundary first column is opaque')
        for n in refs:
            for b in PARTS:
                r=rr[n,b] or [(0,72,72,0)]
                need(len(r)<=24,'Too many parts')
                for t,x,y,f in r:
                    need(-128<=x-80<=127 and -128<=y-80<=127,'Signed origin overflow')
                    if f&128 and t//16==0:need(not atlas[0,t%16*16:t%16*16+16].any(),'GPU V boundary')
                changes[b][n]=b''.join(struct.pack('<BBbb',f,t,x-80,y-80)for t,x,y,f in r)
                expected[n,b]=target[n,b]
            replacements[n]=raw;counts[n]=32
        reports.append({'refs':refs,'method':method,'used_tiles':sorted({t for r in assigned for t,x,y,f in r}),'part_counts':{str(n):{str(b):len(rr[n,b])or 1 for b in PARTS}for n in refs},'encoded_bytes':len(encode_stream(raw))})
    nc=c;slack={}
    for b,change in changes.items():nc,slack[b]=repack_parts(nc,b,change)
    ng,gr=repack_variable(g,replacements,counts)
    result=replace_entry(replace_entry(data,2,ng),3,nc);out=Archive(result)
    for (n,b),v in expected.items():need(np.array_equal(out.layer(n,b)[0],v),f'Layer target mismatch {n}/{b}')
    raw_count=0;unchanged_raw=0
    for gb,bank in enumerate(a.banks):
        for f in bank['frames']:
            n=f['index'];old=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
            nf=out.banks[gb]['frames'][n];new=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data
            want=replacements[n] if gb==0 and n in replacements else old
            need(new==want,f'Raw changed unexpectedly {gb}/{n}');raw_count+=1
            unchanged_raw+=int(gb!=0 or n not in replacements)
    part_count=0
    for b in range(len(bank_offsets(c))):
        for n in range(composition_frame(c,b,0)['bank_frame_count']):
            if b in changes and n in changes[b]:continue
            need(records(c,b,n)==records(nc,b,n),f'Unselected composition changed {b}/{n}');part_count+=1
    kept=0;selected=0
    for n in range(237):
        if n in {105,*range(175,183)}:continue
        for mask in (0,15):
            actual=out.composite(n,mask)[0]
            if n in SELECTED:
                want=a.rgba(base[n],0)if mask==0 else a.rgba(full[n],16)
                need(actual.tobytes()==want.tobytes(),f'Composite target mismatch {n}/{mask}');selected+=1
            else:
                need(actual.tobytes()==a.composite(n,mask)[0].tobytes(),f'Unselected display changed {n}/{mask}');kept+=1
    for e in psx_arc(data):
        typ=int(e['type'],16)
        if typ not in (2,3):need(entry(data,typ)==entry(result,typ),f'Non-graphics entry changed {typ}')
    need(len(result)==len(data),'ARC size changed')
    return result,{'passed':True,'source_arc_sha256':sha(data),'after_arc_sha256':sha(result),'selected_refs':sorted(SELECTED),'groups':reports,'parts_slack':slack,'graphics':gr,'raw_checked':raw_count,'non_target_raw_preserved':unchanged_raw,'non_target_part_records':part_count,'exact_target_layers':len(expected),'exact_target_composites':selected,'non_target_composites_preserved':kept,'palette_audio_timing_other_entries_exact':True,'all_prior_run_60_displays_preserved':True,'runtime_verified':False,'old_art_overwrite':False,'pixel_loss':False}

if __name__=='__main__':
    need(not O.exists(),'Fresh output required')
    arc,full,base,source=targets();result,proof=pack(P.read_bytes(),full,base)
    O.mkdir();(O/'PL02_U.ARC').write_bytes(result)
    actual=Archive(result)
    for name,mask in (('before',15),('after',0)):
        folder=O/name;folder.mkdir()
        for n in sorted(SELECTED):actual.composite(n,mask)[0].save(folder/f'{n:03}.png')
        page([(f'{n} actual ARC',actual.composite(n,mask)[0])for n in sorted(SELECTED)],actual.composite(0,mask)[0],folder/'actual.png',cols=3,scale=5)
    proof['source_art']=source
    write(O/'verification.json',proof)
    write(O/'proposal.json',{'project':'ver_buki_riko','baseline_sha256':SOURCE_SHA,'files':{'PL02_U.ARC':{'path':(O/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':BASELINE,'after':sha(result)}},'sequential_parent':{'path':P.relative_to(ROOT).as_posix(),'sha256':PSHA},'supersedes':'prepared_run_complete03; cumulative run3..32 plus lowHP120..125','runtime_verified':False})
    print(json.dumps({k:proof[k]for k in ('after_arc_sha256','parts_slack','raw_checked','non_target_composites_preserved')}))
