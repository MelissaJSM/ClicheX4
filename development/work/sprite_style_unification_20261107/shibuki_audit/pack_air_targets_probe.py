"""새 공중/사격 22참조를 고정 은행 경계 안에서 손실 없이 시험 패킹한다."""
from pathlib import Path
import sys,json,struct,argparse
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from PIL import Image
import numpy as np
from inspect_air_layers import P,REFS
from scripts.export_x_consistency import Archive
from scripts.prepare_shibuki_armor_remaining import pack_many_patterns
from scripts.prepare_shibuki_ultimate_production import records,repack_parts
from scripts.overhaul_sprites_costume_pack import repack_variable
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import bank_offsets,graphics_bank,decode_stream,composition_frame
from native_pose_pack import need,sha,write,crop,shared_components
from probe_air_body_capacity import candidates,put

def pack_pinned(raw,images,pool):
    try:
        nr,rr=pack_many_patterns(raw,32,images,pool,[24]*len(images));return nr,rr,'whole'
    except ValueError as first:
        parts,which=shared_components(images)
        try:nr,pp=pack_many_patterns(raw,32,parts,pool,[24]*len(parts))
        except ValueError as second:raise ValueError(str(first)+' / components: '+str(second))from second
        rr=[[r for k in ks for r in pp[k]]for ks in which];need(all(len(v)<=24 for v in rr),'Part limit exceeded');return nr,rr,'shared_exact_components'

PARENT_SHA='78b329a07d888682c24b440386cb365f826572402346b3ee6620216ce951617e'
LOCK_SHA='50117af7e0a8b0c64b387d2dd0b4424bb3a2eac8b66f1581ad411f0c6eb61af6'
def validate_inputs(data,d,read=lambda p:p.read_bytes()):
    need(sha(data)==PARENT_SHA,'Wrong exact parent')
    raw=read(d/'LOCK.json');need(sha(raw)==LOCK_SHA,'Wrong frozen target lock');lock=json.loads(raw)
    need(sha(read(d/'targets.json'))==lock['target_manifest_sha256'],'Changed target manifest')
    for name,expected in lock['files'].items():need(sha(read(d/name))==expected,'Changed indexed target: '+name)
    for name,expected in lock['accepted_generation_inputs'].items():need(sha(read(H/name))==expected,'Changed original generation: '+name)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='air_pack_probe01');args=ap.parse_args();o=(H/args.output).resolve();need(o.is_relative_to(H.resolve())and o!=H.resolve(),'Output must be inside isolated work folder');need(not o.exists(),'Fresh output required');d=H/'air_targets_probe02';data=P.read_bytes();validate_inputs(data,d);a=Archive(data);o.mkdir();target={n:{b:np.array(Image.open(d/f'{n:03}_bank{b}_indices.png'))for b in(0,5,6,7,8)}for n in range(33,55)}
    changes={b:{}for b in(0,5,6,7,8)};raws={};reports=[];failed=[]
    for n in sorted(REFS):
        raw=bytes(4096);used=set();head_data=[]
        for ref in(n,n+1):
            ar=target[ref][5];same=next((r for im,r in head_data if np.array_equal(im,ar)),None)
            if same is None:
                same=next((r for r in candidates(a.c,5,ar)if r[1]not in used),None)
                if same is None:failed.append({'refs':[n,n+1],'reason':'No fixed-bank Head template'});break
                raw=put(raw,same,ar);head_data.append((ar,same));used.add(same[1])
            changes[5][ref]=same
        if n+1 not in changes[5]:continue
        order=[(ref,b)for ref in(n,n+1)for b in(0,6,7,8)];images=[crop(target[ref][b])for ref,b in order]
        try:nr,rr,mode=pack_pinned(raw,images,set(range(1,32))-used)
        except ValueError as ex:failed.append({'refs':[n,n+1],'reason':str(ex)});continue
        for (ref,b),parts in zip(order,rr):changes[b][ref]=b''.join(struct.pack('<BBbb',fl,t,x-80,y-80)for t,x,y,fl in parts)
        for ref in(n,n+1):raws[ref]=nr
        reports.append({'refs':[n,n+1],'packing':mode,'head_templates':[changes[5][ref].hex()for ref in(n,n+1)],'part_counts':{str(ref):{str(b):len(changes[b][ref])//4 for b in changes}for ref in(n,n+1)},'same_pair_raw':True})
    result={'candidate_only':True,'source_sha256':sha(P.read_bytes()),'target_manifest_sha256':sha((d/'targets.json').read_bytes()),'groups':reports,'failures':failed,'game_written':False}
    if failed:write(o/'report.json',result);print(json.dumps(result));return
    try:
        nc=a.c;slack={}
        for b,rr in changes.items():nc,slack[b]=repack_parts(nc,b,rr)
        ng,gr=repack_variable(a.g,raws,{n:32 for n in raws});data=replace_entry(replace_entry(a.data,2,ng),3,nc);b=Archive(data)
        need(bank_offsets(nc)==bank_offsets(a.c),'Composition bank boundary moved')
        for n,ll in target.items():
            for bank,ar in ll.items():need(np.array_equal(b.layer(n,bank)[0],ar),'Packed art differs')
        raw_checks=0;nonraw=0
        for bi,ab in enumerate(a.banks):
            bb=b.banks[bi]
            need((ab['base'],ab['end'],len(ab['frames']))==(bb['base'],bb['end'],len(bb['frames'])),'Graphics bank boundary moved')
            for old,new in zip(ab['frames'],bb['frames']):
                oldraw=decode_stream(a.g,old['offset'],old['limit'],old['tile_count']*128).data;newraw=decode_stream(b.g,new['offset'],new['limit'],new['tile_count']*128).data;raw_checks+=1
                expected=raws.get(old['index'])if bi==0 else None
                if expected is None:need(newraw==oldraw,'Non-target raw changed');nonraw+=1
                else:need(newraw==expected,'Target raw changed')
        nonparts=0
        for bi in range(len(bank_offsets(a.c))):
            for n in range(composition_frame(a.c,bi,0)['bank_frame_count']):
                if bi in changes and n in target:continue
                need(records(a.c,bi,n)==records(b.c,bi,n),'Non-target part bytes changed');nonparts+=1
        result.update(passed=True,sha256=sha(data),parts_slack=slack,graphics=gr,target_layers_exact=len(target)*5,raw_references=raw_checks,non_target_raw_exact=nonraw,non_target_part_records_exact=nonparts,part_boundaries_preserved=True,visual_review_and_native_cpu_pending=True)
        (o/'candidate_PL00_U.ARC').write_bytes(data)
    except ValueError as ex:result.update(passed=False,packing_error=str(ex),completed_part_slack=locals().get('slack',{}))
    write(o/'report.json',result);print(json.dumps(result))
if __name__=='__main__':main()
