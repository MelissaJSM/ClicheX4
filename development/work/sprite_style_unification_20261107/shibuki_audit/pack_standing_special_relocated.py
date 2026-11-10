"""고정186228B entry2 안에서 bank12 미소비 후미280B만 회수하는 시험.

새 그림15층을 그대로 저장한다. 외부 ARC 항목·BIN·EXE·LBA는 변경하지 않는다.
은행13 절대위치/전체바이트와 다른 은행의 압축 접두부를 보존한다.
"""
from pathlib import Path
import sys,json,struct,argparse
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
from scripts.prepare_shibuki_ultimate_production import records,repack_parts
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import decode_stream,composition_frame,bank_offsets,indexed_atlas
from src.psx_compress import encode_stream
from pack_shibuki_hurt import raw
from repack_part_records_lossless import repack as repack_global
from pack_dash_complete import protected_entries
from prepare_lowhp_final import compose

PARENT='87e7d1db40c2380815ca2986bc27382db73f718d9c338d2eaad776372a2e257b'
P=H/'prepared_hurt_base01/PL00_U.ARC'
LOCK=H/'standing_special_locked01/LOCK.json'
LOCK_SHA='6986519e57cba7896f5419634c0d5291d456eef3e262c5fe7a73bba52a900ff5'
PBS=(0,5,6,7,8);REFS=(95,96,97)

def validate(data,read=lambda p:p.read_bytes()):
    need(sha(data)==PARENT,'Wrong parent')
    blob=read(LOCK);need(sha(blob)==LOCK_SHA,'Input lock changed');lock=json.loads(blob)
    need(lock['parent_sha256']==PARENT and lock['refs']==list(REFS),'Lock scope mismatch')
    for name,digest in lock['files'].items():
        p=(ROOT/name).resolve();need(p.is_relative_to(ROOT.resolve()),'Source escapes workspace')
        need(sha(read(p))==digest,'Changed source '+name)
    return lock

def relocate(a,replacements,counts):
    need(len(a.g)==186228 and a.banks[0]['base']==56 and a.banks[13]['base']==184744,'Unexpected entry layout')
    bank=a.banks[0];block=bytearray(4*len(bank['frames']));offsets={}
    for f in bank['frames']:
        n=f['index'];r=replacements.get(n,raw(a,0,n));count=counts.get(n,f['tile_count']);key=(r,count)
        if key not in offsets:
            offsets[key]=len(block)
            if n in replacements:code=encode_stream(r)
            else:
                dec=decode_stream(a.g,f['offset'],f['limit'],count*128)
                code=a.g[f['offset']:dec.end]
            need(decode_stream(code,0,len(code),count*128).data==r,'Compressed roundtrip differs')
            block.extend(code)
        need(offsets[key]<(1<<20),'Native offset overflow')
        struct.pack_into('<I',block,n*4,(count<<20)|offsets[key])
        if n==0:need(offsets[key]==4*len(bank['frames']),'First-frame sentinel moved')
    block.extend(bytes(-len(block)%4))
    growth=len(block)-(bank['end']-bank['base'])
    need(growth==280,'Outside reviewed exact280B proposal')
    new=bytearray(len(a.g));new[56:56+len(block)]=block
    cursor=56+len(block);mapped={56:56}
    moves=[{'bank':0,'old_start':56,'new_start':56,'old_span':bank['end']-56,'new_span':len(block),'growth':growth}]
    for bi,old in enumerate(a.banks[1:],1):
        if old['base'] in mapped:continue
        trim=280 if bi==12 else 0
        last=max(decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128).end for f in old['frames'])
        end=old['end']-trim
        need(end>=(last+3)//4*4,'Trim reaches native consumed prefix')
        if bi==12:need((old['base'],old['end'],last,end)==(183172,184744,184462,184464),'Bank12 source changed')
        payload=a.g[old['base']:end]
        need(cursor%4==0 and len(payload)%4==0,'Bank alignment changed')
        mapped[old['base']]=cursor;new[cursor:cursor+len(payload)]=payload
        moves.append({'bank':bi,'old_start':old['base'],'new_start':cursor,'old_end':old['end'],
            'new_end':cursor+len(payload),'last_consumed_before':last,'trimmed_unconsumed_tail':trim,
            'preserved_prefix_length':len(payload),'preserved_prefix_sha256':sha(payload),
            'trimmed_nonzero_bytes':sum(v!=0 for v in a.g[end:old['end']])})
        cursor+=len(payload)
    need(cursor==len(a.g),'Entry length changed')
    for bi,old in enumerate(a.banks):struct.pack_into('<I',new,bi*4,mapped[old['base']])
    need(mapped[184744]==184744 and bytes(new[184744:])==a.g[184744:],'Bank13 absolute bytes changed')
    return bytes(new),{'entry2_length':len(new),'bank0_growth':growth,'bank12_tail_trim':280,
        'tail_is_zero_padding':False,'unique_streams_bank0':len(offsets),'moves':moves,
        'bank13_absolute_bytes_preserved':True,'alias1_2_and4_5_preserved':True}

def build(data,read=lambda p:p.read_bytes()):
    lock=validate(data,read);a=Archive(data)
    recipe=json.loads(read(H/'standing_special_storage03/report.json'))
    packed=read(H/'standing_special_storage03/joint.raw')
    need(sha(packed)==recipe['raw_sha256'] and len(packed)==4096,'Wrong joint atlas')
    need(len(encode_stream(packed))==2222,'Joint compressed size changed')
    need(recipe['keys']==[[n,b] for n in (95,97) for b in PBS],'Wrong storage key order')
    targets={n:{b:np.array(Image.open(H/f'standing_special_layers01/{n:03}_bank{b}_indices.png')) for b in PBS} for n in (95,97)}
    for n,layers in targets.items():
        for b,v in layers.items():need(sha(v.tobytes())==lock['targets'][str(n)][str(b)],'Target raster changed')
    targets[96]={b:np.roll(v,1,axis=1) for b,v in targets[95].items()}
    changes={b:{} for b in PBS};gpu=0
    atlas=np.frombuffer(indexed_atlas(packed,32)[0],np.uint8).reshape(32,256)
    for n in REFS:
        owner=95 if n==96 else n;delta=n-owner
        old_owners={f['index'] for f in a.banks[0]['frames'] if f['offset']==a.banks[0]['frames'][n]['offset']}
        need(old_owners<=set(REFS),'Non-target shares replaced original stream')
        for b in PBS:
            ps=recipe['parts'][recipe['keys'].index([owner,b])]
            rec=b''.join(struct.pack('<BBbb',fl,t,x-80+delta,y-80) for t,x,y,fl in ps)
            need(0<len(rec)<=96,'Invalid target record size');changes[b][n]=rec
            for fl,t,x,y in struct.iter_unpack('<BBbb',rec):
                need(t<32 and not fl&0x3f,'Unsupported tile/flags')
                tx,ty=t%16*16,t//16*16
                if t%16==0:need(not atlas[ty:ty+16,tx].any(),'GPU U-edge texel')
                if fl&128 and ty==0:need(not atlas[ty,tx:tx+16].any(),'GPU V-edge texel')
                gpu+=1
    nc=a.c;slack={};methods={}
    for b,r in changes.items():
        try:nc,slack[b]=repack_parts(nc,b,r);methods[b]='existing'
        except ValueError:nc,slack[b],methods[b]=repack_global(nc,b,r)
    need(bank_offsets(nc)==bank_offsets(a.c),'Composition boundaries moved')
    ng,graphics=relocate(a,{n:packed for n in REFS},{n:32 for n in REFS})
    candidate=replace_entry(replace_entry(data,2,ng),3,nc);z=Archive(candidate)
    allraw=nonraw=0
    for bi,bank in enumerate(a.banks):
        need(len(bank['frames'])==len(z.banks[bi]['frames']),'Frame count changed')
        for f in bank['frames']:
            n=f['index'];selected=bi==0 and n in REFS;expected=packed if selected else raw(a,bi,n)
            need(raw(z,bi,n)==expected,f'Raw differs {bi}/{n}')
            need(z.banks[bi]['frames'][n]['tile_count']==(32 if selected else f['tile_count']),'Tile count differs')
            allraw+=1;nonraw+=not selected
    layers=nonlayers=parts=partials=0;unreconstructed=[]
    for n in range(len(a.banks[0]['frames'])):
        for b in PBS:
            try:old=a.layer(n,b)[0]
            except (ValueError,IndexError) as ex:
                need(n not in targets,'Target invalid')
                try:z.layer(n,b)
                except (ValueError,IndexError) as ex2:
                    need(type(ex)==type(ex2) and str(ex)==str(ex2),'Unreconstructed behavior differs')
                    unreconstructed.append([n,b,str(ex)]);continue
                raise ValueError('Previously invalid layer became valid')
            need(np.array_equal(z.layer(n,b)[0],targets[n][b] if n in targets else old),f'Layer mismatch {n}/{b}')
            layers+=1;nonlayers+=n not in targets
        if n in targets:
            for arm in (1,2):
                for mask in range(16):
                    need(z.composite(n,mask,arm)[0].tobytes()==compose(a,targets[n],mask,arm).tobytes(),'Partial RGBA differs')
                    partials+=1
    for b in range(len(bank_offsets(a.c))):
        for n in range(composition_frame(a.c,b,0)['bank_frame_count']):
            if b in PBS and n in REFS:need(records(z.c,b,n)==changes[b][n],'Target record differs');continue
            need(records(z.c,b,n)==records(a.c,b,n),'Non-target records changed');parts+=1
    for n in (0,141,142):
        for b in PBS:need(np.array_equal(z.layer(n,b)[0],a.layer(n,b)[0]),'Idle/arrival changed')
    preserved=protected_entries(data,candidate)
    return candidate,{'passed':True,'before':PARENT,'after':sha(candidate),'target_lock_sha256':LOCK_SHA,
        'selected_refs':list(REFS),'raw_references':allraw,'non_target_raw_exact':nonraw,
        'layers_checked':layers,'target_layers_exact':15,'non_target_layers_exact':nonlayers,
        'non_target_parts_exact':parts,'unreconstructed_layers_preserved':unreconstructed,
        'partial_rgba_exact':partials,'gpu_parts':gpu,'parts_slack':slack,'parts_methods':methods,
        'graphics':graphics,'protected_entries':preserved,'protected_0_141_142':True,
        'old_parent_preserved':sha(P.read_bytes())==PARENT,'no_pixel_reduction':True,
        'native_cpu_pending':True,'independent_pending':True,'root_final_art_pending':True,
        'runtime_verified':False,'frozen':False,
        'scope':'기본/포스95/96/97 새15층. 고정186228B 내부 bank12 원디코더 미소비 후미280B만 재사용하는 가역 시험.'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='standing_special_pack02');args=ap.parse_args()
    o=(H/args.output).resolve();need(o.is_relative_to(H.resolve()) and not o.exists(),'Fresh owned output')
    candidate,proof=build(P.read_bytes());o.mkdir();(o/'PL00_U.ARC').write_bytes(candidate);a=Archive(candidate)
    for form,mask in (('base',0),('fourth',15)):
        page([(f'{n} actual {form}',a.composite(n,mask)[0]) for n in REFS],a.composite(0,mask)[0],o/f'{form}_readback.png',cols=2,scale=5)
    for n in (95,97):page([(f'{n} mask{m:X}',a.composite(n,m)[0]) for m in range(16)],a.composite(0,15)[0],o/f'partial_{n:03}.png',cols=4,scale=4)
    write(o/'report.json',proof)
    print(json.dumps({k:proof[k] for k in ('after','raw_references','target_layers_exact','partial_rgba_exact','parts_slack')}))

if __name__=='__main__':main()
