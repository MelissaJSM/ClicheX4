"""피격13 새몸/원효과를 현재 고정은행 안에 패킹하는 검토 후보."""
from pathlib import Path
import sys,json,struct,argparse
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,crop
from prepare_shibuki_hurt_effects import PBS,REFS,PARENT
from scripts.export_x_consistency import Archive,page
from scripts.prepare_shibuki_ultimate_production import repack_parts,records,pack_shared
from scripts.overhaul_sprites_costume_pack import repack_variable,pack_planes
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import bank_offsets,decode_stream,composition_frame,indexed_atlas
from pack_dash_complete import protected_entries
from prepare_lowhp_final import compose
from repack_part_records_lossless import repack as repack_global
from pack_air_targets_probe import pack_pinned
from src.psx_compress import encode_stream
from optimize_hurt_tile_storage import optimize
from scripts.optimize_rin_style_tiles import permute
TD=H/'hurt_effect_probe01';MANIFEST='8a9d44e67fb42b5a48b43ee882a33bb7fc52448c6b73f170ad5a776d6cdf593e'
LOCK=H/'hurt_locked_inputs01/LOCK.json';LOCK_SHA='8373993dab8b729ae466f64a9633f3e5a1cddd44c7ae01e8a39e65b875ee277d'

def validate_inputs(data,read=lambda p:p.read_bytes()):
    need(sha(data)==PARENT,'Wrong parent')
    blob=read(LOCK);need(sha(blob)==LOCK_SHA,'Changed input lock');lock=json.loads(blob)
    need(lock['parent_sha256']==PARENT and lock['refs']==list(REFS),'Wrong lock scope')
    for name,expected in lock['files'].items():
        p=(ROOT/name).resolve();need(p.is_relative_to(ROOT.resolve()),'Input escapes workspace')
        need(sha(read(p))==expected,'Changed source: '+name)
    return lock

def raw(a,gb,n):
    f=a.banks[gb]['frames'][n];return decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128).data

def tile_seed(a,n,keep):
    f=a.banks[0]['frames'][n];old=np.frombuffer(indexed_atlas(raw(a,0,n),f['tile_count'])[0],np.uint8).reshape(-1,256);new=np.zeros((32,256),np.uint8)
    for t in keep:
        sl=(slice(t//16*16,t//16*16+16),slice(t%16*16,t%16*16+16));new[sl]=old[sl]
    return bytes((new[:,::2]|(new[:,1::2]<<4)).ravel())

def repack_fixed_global(a,replacements,counts):
    bank=a.banks[0];payload=bytearray(len(bank['frames'])*4);positions={};expected={};codes={};frame0=None
    for f in bank['frames']:
        n=f['index'];r=replacements[n]if n in replacements else raw(a,0,n);cnt=counts.get(n,f['tile_count']);key=(r,cnt)
        if key not in positions:
            positions[key]=len(payload)
            if n in replacements:code=encode_stream(r)
            else:
                dec=decode_stream(a.g,f['offset'],f['limit'],cnt*128);code=a.g[f['offset']:dec.end]
            need(decode_stream(code,0,len(code),cnt*128).data==r,'Encoded raw mismatch');payload.extend(code);codes[key]=len(code)
        struct.pack_into('<I',payload,n*4,(cnt<<20)|positions[key]);expected[n]=(r,cnt)
        if n==0:frame0=positions[key]
    need(frame0==len(bank['frames'])*4,'Frame0 sentinel moved');span=bank['end']-bank['base'];need(len(payload)<=span,f'Graphics bank exceeds capacity by {len(payload)-span} after identical-raw sharing')
    out=bytearray(a.g);out[bank['base']:bank['base']+len(payload)]=payload
    return bytes(out),{'bank':0,'remaining_slack':span-len(payload),'unique_streams':len(positions),'selected_raw_shared':{str(n):[k for k,v in expected.items()if v==expected[n]]for n in replacements},'bank_boundaries_preserved':True,'non_target_decoded_raw_preserved':True,'global_equal_raw_and_count_only':True}

def build(data,progress):
    lock=validate_inputs(data);meta=json.loads((TD/'manifest.json').read_text('utf8'));need(sha((TD/'manifest.json').read_bytes())==MANIFEST,'Target manifest changed')
    recipe=json.loads((H/'hurt_locked_inputs01/tile_recipe.json').read_text('utf8'))
    a=Archive(data);targets={n:{b:np.array(Image.open(TD/f'{n:03}_bank{b}_indices.png'))for b in PBS}for n in REFS}
    for n,ll in targets.items():
        for b,v in ll.items():need(sha(v.tobytes())==meta['targets'][str(n)][str(b)],'Target changed')
    fx=meta['protected_effect_records'];changes={b:{}for b in PBS};raws={};counts={};groups=[];gpu=0
    for ns in((106,107,108),(110,111),(109,),(112,),(113,),(114,),(233,),(234,235),(236,)):
        n=ns[0];keep={int(p['tile'])for k in ns for ps in fx.get(str(k),{}).values()for p in ps};seed=tile_seed(a,n,keep);imgs=[crop(targets[n][b])for b in PBS];pool=set(range(32))-{0,16}-keep
        variant_records=None
        if len(ns)>1 and ns[0]==234:
            # 원오라를 먼저 그리고 새234 몸체를 나중에 그려 가린다.
            # 합성본마다 몸체를 잘라 중복 저장하지 않고 5개 몸체층을 공유한다.
            effects=[np.array(Image.open(TD/f'{ref:03}_historical_effect.png'))for ref in ns[1:]]
            for ref,effect in zip(ns[1:],effects):
                need(np.array_equal(np.where(targets[234][0]>0,targets[234][0],effect),targets[ref][0]),'Aura/body draw order differs')
                need(all(np.array_equal(targets[234][b],targets[ref][b])for b in PBS[1:]),'Aura armor layer differs')
            nr,allrr,mode=pack_pinned(seed,imgs+[crop(v)for v in effects],pool)
            variant_records={(ref,b):list(allrr[i])for ref in ns for i,b in enumerate(PBS)}
            for i,ref in enumerate(ns[1:]):variant_records[ref,0]=allrr[5+i]+variant_records[ref,0]
        elif keep:nr,rr=pack_shared(seed,32,imgs,pool,[24]*5)
        else:nr,rr=pack_planes(seed,32,imgs,pool,[24]*5)
        opt=recipe['groups'][str(n)];need(sha(nr)==opt['source_raw_sha256'],'Layout differs from locked recipe')
        need(opt['fixed_tiles']==sorted(keep|{0,16}),'Protected effect slots differ')
        nr=permute(nr,32,opt['order']);mapping={old:new for new,old in enumerate(opt['order'])}
        need(all(mapping[t]==t for t in keep|{0,16}),'Protected tile moved')
        need(sha(nr)==opt['output_raw_sha256']and len(encode_stream(nr))==opt['after'],'Locked tile permutation differs')
        def remap(ps):return [(mapping[t],x,y,fl)for t,x,y,fl in ps]
        if variant_records is None:rr=[remap(ps)for ps in rr]
        else:variant_records={key:remap(ps)for key,ps in variant_records.items()}
        atlas=np.frombuffer(indexed_atlas(nr,32)[0],np.uint8).reshape(32,256);seedatlas=np.frombuffer(indexed_atlas(seed,32)[0],np.uint8).reshape(32,256)
        for t in keep:
            sl=(slice(t//16*16,t//16*16+16),slice(t%16*16,t%16*16+16));need(np.array_equal(atlas[sl],seedatlas[sl]),'Original effect tile changed')
        for k in ns:
            oldowners=[f['index']for f in a.banks[0]['frames']if f['offset']==a.banks[0]['frames'][k]['offset']];need(set(oldowners)<=set(REFS),'Shared non-target owner')
            raws[k]=nr;counts[k]=32
            for b,parts in ((b,variant_records[k,b])for b in PBS)if variant_records is not None else zip(PBS,rr):
                record=b''.join(struct.pack('<BBbb',fl,t,x-80,y-80)for t,x,y,fl in parts)
                if not record:
                    need(not atlas[:16,:16].any(),'Blank tile0 occupied');record=struct.pack('<BBbb',0,0,-8,-8)
                extra=fx.get(str(k),{}).get(str(b),[]);record+=b''.join(struct.pack('<BBbb',p['flags'],p['tile'],p['x'],p['y'])for p in extra);need(len(record)//4<=24,'Part count')
                for fl,t,x,y in struct.iter_unpack('<BBbb',record):
                    if t not in keep:
                        if t%16==0:need(not atlas[t//16*16:t//16*16+16,0].any(),'GPU U boundary')
                        if fl&128 and t//16==0:need(not atlas[0,t%16*16:t%16*16+16].any(),'GPU V boundary')
                    gpu+=1
                changes[b][k]=record
        groups.append({'refs':list(ns),'effect_tiles_exact':sorted(keep),'raw_sha256':sha(nr),'parts':{str(k):{str(b):len(changes[b][k])//4 for b in PBS}for k in ns},'tile_permutation':opt});progress({'packed_group':list(ns),'parts':groups[-1]['parts'],'tile_permutation':opt})
    nc=a.c;slack={};methods={}
    for b,rr in changes.items():
        try:nc,slack[b]=repack_parts(nc,b,rr);methods[b]='existing_record_repacker'
        except ValueError:nc,slack[b],methods[b]=repack_global(nc,b,rr)
    progress({'part_slack':slack})
    ng,graphics=repack_fixed_global(a,raws,counts);new=replace_entry(replace_entry(data,2,ng),3,nc);actual=Archive(new);need(bank_offsets(nc)==bank_offsets(a.c),'Composition boundaries moved')
    total=nonraw=0
    for gb,bank in enumerate(a.banks):
        nb=actual.banks[gb];need((bank['base'],bank['end'],len(bank['frames']))==(nb['base'],nb['end'],len(nb['frames'])),'Graphics boundaries moved')
        for f in bank['frames']:
            n=f['index'];expected=raws[n]if gb==0 and n in raws else raw(a,gb,n);need(raw(actual,gb,n)==expected,f'Raw mismatch {gb}/{n}');total+=1;nonraw+=not(gb==0 and n in raws)
    layers=kept=partial=parts=0
    for n in range(237):
        if n in(105,*range(175,183)):continue
        for b in PBS:
            expected=targets[n][b]if n in targets else a.layer(n,b)[0];need(np.array_equal(actual.layer(n,b)[0],expected),f'Layer {n}/{b}');layers+=1;kept+=n not in targets
        if n in targets:
            for arm in(1,2):
                for mask in range(16):need(actual.composite(n,mask,arm)[0].tobytes()==compose(a,targets[n],mask,arm).tobytes(),'Partial RGBA');partial+=1
    for b in range(len(bank_offsets(a.c))):
        for n in range(composition_frame(a.c,b,0)['bank_frame_count']):
            if b in PBS and n in REFS:continue
            need(records(actual.c,b,n)==records(a.c,b,n),'Non-target composition changed');parts+=1
    need(sha(new)==lock['candidate_sha256'],'Candidate differs from locked exact build')
    return new,{'passed':True,'before':PARENT,'after':sha(new),'target_manifest_sha256':MANIFEST,'target_lock_sha256':LOCK_SHA,'locked_files':len(lock['files']),'refs':list(REFS),'groups':groups,'part_slack':slack,'part_storage_methods':methods,'graphics':graphics,'raw_checked':total,'non_target_raw':nonraw,'layers_checked':layers,'non_target_layers':kept,'target_layers':len(REFS)*5,'partial_RGBA':partial,'non_target_compositions':parts,'gpu_parts':gpu,'preserved_entries':protected_entries(data,new),'original_effect_tiles_preserved':True,'pixel_loss':False,'scope':'새 피격13 정적 검토 후보. 원효과 타일/고정은행 보존, 원MIPS·독립·최종 미술·실기는 별도.','runtime_verified':False,'native_cpu_verified':False,'frozen':False}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='hurt_pack_probe01');z=ap.parse_args();o=(H/z.output).resolve();need(o.is_relative_to(H.resolve())and not o.exists(),'Fresh own output');o.mkdir();progress=[]
    def log(v):progress.append(v);write(o/'progress.json',progress);print(json.dumps(v),flush=True)
    try:new,report=build((H/'prepared_base_run01/PL00_U.ARC').read_bytes(),log)
    except Exception as e:write(o/'report.json',{'passed':False,'error':str(e),'partial_progress':progress,'arc_written':False});raise
    (o/'PL00_U.ARC').write_bytes(new);a=Archive(new)
    for form,mask in(('base',0),('fourth',15)):
        for i,refs in enumerate(((106,110,233,234),(107,108,109),(111,112,113),(114,235,236))):page([(f'{n} actual {form}',a.composite(n,mask)[0])for n in refs],a.composite(0,mask)[0],o/f'{form}_readback_{i:02}.png',cols=2,scale=5)
    write(o/'report.json',report);print(json.dumps({'after':sha(new),'parts':report['part_slack'],'graphics':report['graphics']}),flush=True)
if __name__=='__main__':main()
