"""승인된 가역 시험: 고정길이 entry2 안의 상대주소만 조정해 새32를 저장.

원게임/BIN/포인터는 쓰지 않는다. 0/141/142와 비대상 decoded raw·조립은
보존하며, 다른 gfx은행은 원래 압축본문을 복사하고 캡슐 꼬리만 줄인다.
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
from pack_dash_complete import protected_entries
from prepare_lowhp_final import compose
from pack_base_run_complete import validate_inputs
P=H/'prepared_dash_base01/PL00_U.ARC';PARENT='dd8504d31ed2f169825fd6daf8e0eae236e6a97f045d0b476e9f83c250824d3b'
D=H/'base_run_complete_targets01';TARGET_LOCK='44170f9268ab8df6d1aefb26fdaec75981533e16477fa16f1897d7d1d29f3e65'
STORAGE=['base_run_compact_flip01/result.json','base_run_alpha_compact_flip01/result.json','base_run_idle_alias02/result.json','base_run_compact_hill_a01/result.json','base_run_compact_hill_b01/result.json']
SLOCK=H/'base_run_storage_inputs01/LOCK.json';PARTS=(0,5,6,7,8)
STORAGE_LOCK_SHA='d49098bac24ee711caa53c798afc6071fabb4271dec7e7af15c2a325e07697fc'

def validate(data,read=lambda p:p.read_bytes()):
    validate_inputs(data,D,TARGET_LOCK,read)
    blob=read(SLOCK);need(sha(blob)==STORAGE_LOCK_SHA,'Changed storage lock');lock=json.loads(blob)
    need(lock['parent_sha256']==PARENT and lock['target_lock_sha256']==TARGET_LOCK,'Wrong storage lock parent')
    for name,h in lock['files'].items():need(sha(read(H/name))==h,'Changed storage input '+name)
    return lock

def chosen_storage(read=lambda p:p.read_bytes()):
    a,b,idle,ha,hb=[json.loads(read(H/p))for p in STORAGE]
    need(len(a['groups'])==len(b['groups'])==16 and len(ha['groups'])==len(hb['groups'])==8,'Unfinished storage search')
    choices={}
    for x,y in zip(a['groups'],b['groups']):need(x['refs']==y['refs'],'Group refs mismatch');choices[x['refs'][0]]=min((x,y),key=lambda v:v['after'])
    del choices[1];choices[2]=idle['shot2']
    for p in ha['groups']+hb['groups']:
        n=p['refs'][0];need(p['refs']==choices[n]['refs'],'Hill target changed')
        if p['after']<choices[n]['after']:choices[n]=p
    return list(sorted(choices.values(),key=lambda v:v['refs'][0])),idle['idle_alias']

def build(data,read=lambda p:p.read_bytes()):
    lock=validate(data,read);a=Archive(data);choices,idle=chosen_storage(read);changes={b:{}for b in PARTS};raws={1:bytes.fromhex(idle['raw'])};counts={1:idle['tile_count']}
    for b in PARTS:changes[b][1]=bytes.fromhex(idle['parts'][str(b)]);need(changes[b][1]==records(a.c,b,0),'Idle alias is not original0')
    f=a.banks[0]['frames'][0];need(raws[1]==decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128).data and counts[1]==f['tile_count'],'Idle raw alias changed')
    for v in choices:
        for n in v['refs']:
            need(n not in raws,'Duplicate target');raws[n]=bytes.fromhex(v['raw']);counts[n]=v['count'];need(0<counts[n]<=32 and len(raws[n])==counts[n]*128,'Bad target raw/count')
            need(counts[n]>=a.banks[0]['frames'][n]['tile_count'],'Reduced upload below original target')
            for b in PARTS:changes[b][n]=bytes.fromhex(v['parts'][str(b)][str(n)])
    need(set(raws)==set(range(1,33)),'Wrong target scope');nc=a.c;slack={}
    for b,rr in changes.items():nc,slack[b]=repack_parts(nc,b,rr)
    need(bank_offsets(nc)==bank_offsets(a.c),'Composition bank moved')
    bank=a.banks[0];header=4*len(bank['frames']);block=bytearray(header);cache={};offsets={};frame0=None
    for f in bank['frames']:
        n=f['index'];r=raws.get(n);count=counts.get(n,f['tile_count'])
        if r is None:r=decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128).data
        key=(r,count)
        if key not in offsets:
            offsets[key]=len(block);code=encode_stream(r);cache[key]=code;block.extend(code)
        need(offsets[key]<1<<20,'Native relative20bit overflow');struct.pack_into('<I',block,n*4,(count<<20)|offsets[key])
        if n==0:frame0=offsets[key]
    need(frame0==header,'First frame sentinel moved');block.extend(bytes((-len(block))%4));oldspan=bank['end']-bank['base'];grow=len(block)-oldspan
    need(0<=grow<=944,'Candidate exceeds reviewed relocation proposal')
    trims={};remaining=grow
    for bi,maximum in((10,344),(11,400),(12,200)):
        trims[bi]=min(remaining,maximum);remaining-=trims[bi]
    need(remaining==0,'Insufficient approved tails');ng=bytearray(len(a.g));ng[56:56+len(block)]=block;cursor=56+len(block);mapped={bank['base']:56};relocations=[{'bank':0,'old_start':56,'new_start':56,'old_span':oldspan,'new_span':len(block)}]
    for bi,ba in enumerate(a.banks[1:],1):
        if ba['base']in mapped:continue
        trim=trims.get(bi,0);end=ba['end']-trim;last=max(decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128).end for f in ba['frames']);need(end>=last,'Trim would consume stream');payload=a.g[ba['base']:end]
        need(cursor%4==0 and len(payload)%4==0,'Unaligned bank');mapped[ba['base']]=cursor;ng[cursor:cursor+len(payload)]=payload;relocations.append({'bank':bi,'old_start':ba['base'],'new_start':cursor,'old_span':ba['end']-ba['base'],'new_span':len(payload),'trimmed_tail':trim,'header_compressed_bytes_exact':True});cursor+=len(payload)
    need(cursor==len(a.g),'Entry2 length changed')
    for bi,ba in enumerate(a.banks):struct.pack_into('<I',ng,bi*4,mapped[ba['base']])
    need(mapped[a.banks[13]['base']]==a.banks[13]['base'] and bytes(ng[a.banks[13]['base']:])==a.g[a.banks[13]['base']:],'Bank13 moved or changed')
    new=replace_entry(replace_entry(data,2,bytes(ng)),3,nc);actual=Archive(new);checks=nonraw=nonparts=nonlayers=targetlayers=partial=gunchecks=gpu=0
    for bi,ba in enumerate(a.banks):
        bb=actual.banks[bi];need(len(ba['frames'])==len(bb['frames']),'Frame count changed')
        for old,f in zip(ba['frames'],bb['frames']):
            n=f['index'];r=decode_stream(actual.g,f['offset'],f['limit'],f['tile_count']*128).data;oldraw=decode_stream(a.g,old['offset'],old['limit'],old['tile_count']*128).data;checks+=1
            if bi==0 and n in raws:need(r==raws[n] and f['tile_count']==counts[n],'Selected raw/count mismatch')
            else:need(r==oldraw and f['tile_count']==old['tile_count'],'Non-target raw/count changed');nonraw+=1
    for b in range(len(bank_offsets(a.c))):
        for n in range(composition_frame(a.c,b,0)['bank_frame_count']):
            if b in changes and n in raws:need(records(actual.c,b,n)==changes[b][n],'Target records differ')
            else:need(records(actual.c,b,n)==records(a.c,b,n),'Non-target records differ');nonparts+=1
    unreconstructed=[]
    for n in range(len(a.banks[0]['frames'])):
        if n not in raws:
            for b in PARTS:
                try:oldlayer=a.layer(n,b)[0]
                except(ValueError,IndexError)as ex:
                    try:actual.layer(n,b)
                    except(ValueError,IndexError)as ex2:need(type(ex)==type(ex2)and str(ex)==str(ex2),'Unreconstructed reference behavior changed');unreconstructed.append([n,b,str(ex)]);continue
                    raise ValueError('Previously invalid layer changed behavior')
                need(np.array_equal(oldlayer,actual.layer(n,b)[0]),'Non-target layer differs');nonlayers+=1
    for n in sorted(raws):
        targets={b:np.array(Image.open(D/f'{n:03}_bank{b}_indices.png'))for b in PARTS}
        for b in PARTS:need(np.array_equal(actual.layer(n,b)[0],targets[b]),'Target layer differs');targetlayers+=1
        if n%2==0:
            gm=np.array(Image.open(H/f'base_run_shot_inputs01/barrels/{n:03}_mask.png'))>0;gi=np.array(Image.open(H/f'base_run_shot_inputs01/barrels/{n:03}_indices.png'));gun=np.array(a.rgba(gi))
        for mask in range(16):
            for arm in(1,2):
                got=actual.composite(n,mask,arm)[0];need(got.tobytes()==compose(a,targets,mask,arm).tobytes(),'Partial RGBA differs');partial+=1
                if n%2==0:need(np.array_equal(np.array(got)[gm],gun[gm]),'Original gun changed');gunchecks+=1
        f=actual.banks[0]['frames'][n];at=np.frombuffer(indexed_atlas(raws[n],counts[n])[0],np.uint8).reshape(-1,256)
        for b in PARTS:
            for fl,t,x,y in struct.iter_unpack('<BBbb',records(actual.c,b,n)):
                need(t<counts[n] and not fl&0x3f,'Part outside uploaded tiles/unsupported flags');tx,ty=t%16*16,t//16*16
                if t%16==0:need(not at[ty:ty+16,tx].any(),'GPU U edge')
                if fl&128 and ty==0:need(not at[ty,tx:tx+16].any(),'GPU V edge')
                gpu+=1
    preserved=protected_entries(data,new)
    for n in(0,141,142):
        for b in PARTS:need(records(actual.c,b,n)==records(a.c,b,n)and np.array_equal(actual.layer(n,b)[0],a.layer(n,b)[0]),'Protected idle/arrival changed')
    return new,{'passed':True,'before':PARENT,'after':sha(new),'target_lock':TARGET_LOCK,'storage_lock_sha256':sha(read(SLOCK)),'selected_refs':sorted(raws),'selected_tile_counts':counts,'raw_references':checks,'non_target_raw_exact':nonraw,'target_layers_exact':targetlayers,'non_target_layers_exact':nonlayers,'non_target_parts_exact':nonparts,'unreconstructed_layers_preserved':unreconstructed,'partial_rgba_exact':partial,'original_gun_checks':gunchecks,'gpu_parts':gpu,'parts_slack':slack,'graphics_entry_length':len(actual.g),'bank0_growth':grow,'capsule_tail_trims':trims,'relocations':relocations,'bank13_absolute_range_byte_exact':True,'protected_0_141_142':True,'preserved_entries':preserved,'palette_audio_exe_lba_changed':False,'native_cpu_verified':False,'runtime_verified':False,'actual_readback_visual_reviewed':False,'approval_scope':'root가 기존 사용자 전체 재작화 범위의 가역시험으로 판단. 새offset의 사용자직접승인 기록 아님.'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);z=ap.parse_args();o=(H/z.output).resolve();need(o.is_relative_to(H.resolve())and not o.exists(),'Fresh isolated output');data=P.read_bytes();new,report=build(data);o.mkdir();(o/'PL00_U.ARC').write_bytes(new);a=Archive(new)
    for form,mask in(('base',0),('fourth',15)):
        items=[(f'{form} {n:03}',a.composite(n,mask)[0])for n in range(1,33)]
        for i in range(0,len(items),6):page(items[i:i+6],a.composite(0,mask)[0],o/f'{form}_readback_{i//6:02}.png',cols=3,scale=4)
    write(o/'report.json',report);print(json.dumps({k:report[k]for k in('after','bank0_growth','raw_references','target_layers_exact','partial_rgba_exact','parts_slack')}))
if __name__=='__main__':main()
