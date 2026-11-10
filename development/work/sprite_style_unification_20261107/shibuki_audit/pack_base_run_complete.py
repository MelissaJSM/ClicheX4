"""새 이동/사격을 원래 16공유스트림·고정 은행 안에 무손실 패킹."""
from pathlib import Path
import sys,json,struct,argparse
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,crop
from scripts.export_x_consistency import Archive,page
from scripts.prepare_shibuki_ultimate_production import records,repack_parts
from scripts.overhaul_sprites_costume_pack import repack_variable
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import bank_offsets,decode_stream,composition_frame
from pack_air_targets_probe import pack_pinned
from probe_air_body_capacity import put
from pack_dash_complete import protected_entries
from prepare_base_run_targets import PARENT,PARTS
from repack_part_records_lossless import repack as repack_global
from src.psx_compress import encode_stream
from pack_run_patterns import candidates as pattern_candidates

def validate_inputs(data,d,lock_sha,read=lambda p:p.read_bytes()):
    need(sha(data)==PARENT,'Wrong source parent');raw=read(d/'LOCK.json');need(sha(raw)==lock_sha,'Changed target lock');lock=json.loads(raw)
    raw=read(d/'targets.json');need(sha(raw)==lock['target_manifest_sha256'],'Changed target manifest')
    for n,s in lock['files'].items():need(sha(read(d/n))==s,'Changed target '+n)
    for n,s in lock['source_files'].items():need(sha(read(H/n))==s,'Changed source '+n)
    return json.loads(raw)

def build(data,d,lock_sha,progress=None):
    meta=validate_inputs(data,d,lock_sha);a=Archive(data)
    target={r['ref']:{b:np.array(Image.open(d/f'{r["ref"]:03}_bank{b}_indices.png'))for b in PARTS}for r in meta['rows']}
    need(set(target) in (set(range(3,33)),set(range(1,33))),'Unexpected target set')
    changes={b:{}for b in PARTS};raws={};groups={};reports=[]
    for n in target:groups.setdefault(a.banks[0]['frames'][n]['offset'],[]).append(n)
    for offset,refs in sorted(groups.items()):
        refs=sorted(refs);allrefs=[f['index']for f in a.banks[0]['frames']if f['offset']==offset];need(allrefs==refs,'Shared stream escapes selected refs')
        raw=bytes(4096);used=set();headcache=[]
        for n in refs:
            ar=target[n][5];found=next((r for im,r in headcache if np.array_equal(im,ar)),None)
            if found is None:
                y,x=np.nonzero(ar);need(len(x)>0 and x.max()-x.min()<16 and y.max()-y.min()<16,'Head needs more than one tile')
                tile=10+len(headcache);need(tile<16,'Head tile overflow');found=struct.pack('<BBbb',0,tile,int(x.min()-160),int(y.min()-160));raw=put(raw,found,ar);headcache.append((ar,found));used.add(tile)
            changes[5][n]=found
        need(len(refs)==2,'Expected one moving/firing pair')
        order=[(n,b)for n in refs for b in (7,8)]
        images=[crop(target[n][b])for n,b in order];bodykeys=[];common_stats={}
        for bank in(0,6):
            left,right=(target[n][bank]for n in refs);same=(left==right)&(left>0)
            common=np.where(same,left,0).astype(np.uint8);deltas=[np.where(same,0,v).astype(np.uint8)for v in(left,right)]
            common_stats[bank]={'common_pixels':int(same.sum()),'delta_pixels':[int((v>0).sum())for v in deltas]}
            for name,ar in (('common',common),('left',deltas[0]),('right',deltas[1])):
                if ar.any():bodykeys.append((bank,name));images.append(crop(ar))
        options=pattern_candidates(raw,images,set(range(1,32))-used);_,nr,rr,mode=options[0]
        def encoded(parts):return b''.join(struct.pack('<BBbb',fl,t,x-80,y-80)for t,x,y,fl in parts)
        for (n,b),parts in zip(order,rr):changes[b][n]=encoded(parts)
        pieces={k:encoded(parts)for k,parts in zip(bodykeys,rr[len(order):])}
        # Disjoint common/delta pixels permit either order. Choosing the shared
        # sequence as suffix/prefix makes native record storage aliasable while
        # every target texel and every per-layer render remains exact.
        for bank in(0,6):
            changes[bank][refs[0]]=pieces.get((bank,'left'),b'')+pieces.get((bank,'common'),b'')
            changes[bank][refs[1]]=pieces.get((bank,'common'),b'')+pieces.get((bank,'right'),b'')
        for n in refs:raws[n]=nr
        reports.append({'refs':refs,'packing':mode,'storage_candidates':[{'bytes':v[0],'mode':v[3],'parts':list(map(len,v[2]))}for v in options],'pinned_head_tiles':sorted(used),'shared_layer_texels':common_stats,'parts':{str(n):{str(b):len(changes[b][n])//4 for b in PARTS}for n in refs}})
        if progress:progress({'stage':'groups','groups':reports})
    nc=a.c;slack={};repack_methods={}
    for b,rr in changes.items():
        try:nc,slack[b]=repack_parts(nc,b,rr);repack_methods[b]='existing_exact_record_repacker'
        except ValueError:
            nc,slack[b],repack_methods[b]=repack_global(nc,b,rr)
        if progress:progress({'stage':'parts','groups':reports,'part_slack':slack})
    if progress:
        progress({'stage':'graphics','groups':reports,'part_slack':slack,'part_repack_methods':repack_methods,'raws':{str(n):r.hex()for n,r in raws.items()},'parts':{str(b):{str(n):r.hex()for n,r in v.items()}for b,v in changes.items()},'compressed_group_sizes':[{ 'refs':v['refs'],'new':len(encode_stream(raws[v['refs'][0]])),'old':decode_stream(a.g,a.banks[0]['frames'][v['refs'][0]]['offset'],a.banks[0]['frames'][v['refs'][0]]['limit'],a.banks[0]['frames'][v['refs'][0]]['tile_count']*128).end-a.banks[0]['frames'][v['refs'][0]]['offset']}for v in reports]})
    ng,graphics=repack_variable(a.g,raws,{n:32 for n in raws});new=replace_entry(replace_entry(data,2,ng),3,nc);actual=Archive(new)
    need(bank_offsets(nc)==bank_offsets(a.c),'Part bank moved')
    for n,ll in target.items():
        for b,want in ll.items():need(np.array_equal(actual.layer(n,b)[0],want),'Readback target mismatch '+str((n,b)))
    rawcount=otherraw=otherparts=otherlayers=0
    for bi,ab in enumerate(a.banks):
        bb=actual.banks[bi];need((ab['base'],ab['end'],len(ab['frames']))==(bb['base'],bb['end'],len(bb['frames'])),'Graphics bank moved')
        for f,ff in zip(ab['frames'],bb['frames']):
            old=decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128).data;got=decode_stream(actual.g,ff['offset'],ff['limit'],ff['tile_count']*128).data;rawcount+=1
            if bi==0 and f['index']in raws:need(got==raws[f['index']],'Target raw differs')
            else:need(old==got,'Non-target raw changed');otherraw+=1
    for b in range(len(bank_offsets(a.c))):
        for n in range(composition_frame(a.c,b,0)['bank_frame_count']):
            if b in changes and n in target:continue
            need(records(a.c,b,n)==records(actual.c,b,n),'Non-target parts changed');otherparts+=1
    for n in range(228):
        if n in target:continue
        for b in PARTS:need(np.array_equal(a.layer(n,b)[0],actual.layer(n,b)[0]),'Non-target displayed layer changed');otherlayers+=1
    preserved=protected_entries(data,new)
    return new,{'passed':True,'before':PARENT,'after':sha(new),'target_lock':lock_sha,'target_refs':sorted(target),'groups':reports,'part_slack':slack,'part_repack_methods':repack_methods,'graphics':graphics,'raw_references':rawcount,'non_target_raw':otherraw,'exact_target_layers':len(target)*5,'non_target_parts':otherparts,'non_target_layers':otherlayers,'preserved_entries':preserved,'idle0_141_142_raw_parts_pixels_preserved':True,'native_cpu_verified':False,'visual_readback_pending':True}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--targets',required=True);ap.add_argument('--lock',required=True);ap.add_argument('--output',required=True);z=ap.parse_args();o=(H/z.output).resolve();d=(H/z.targets).resolve();need(o.is_relative_to(H.resolve())and d.is_relative_to(H.resolve())and not o.exists(),'Fresh isolated output');o.mkdir();data=(H/'prepared_dash_base01/PL00_U.ARC').read_bytes()
    try:new,report=build(data,d,z.lock,lambda r:write(o/'progress.json',r))
    except ValueError as ex:write(o/'report.json',{'passed':False,'reason':str(ex)});print(str(ex));return
    (o/'PL00_U.ARC').write_bytes(new);a=Archive(new)
    for form,mask in (('base',0),('fourth',15)):
        pics=[(f'{form} {n}',a.composite(n,mask)[0])for n in report['target_refs']]
        for i in range(0,len(pics),6):page(pics[i:i+6],a.composite(0,mask)[0],o/f'{form}_readback_{i//6:02}.png',cols=3,scale=4)
    write(o/'report.json',report);print(json.dumps({k:report[k]for k in('passed','after','part_slack','non_target_raw','exact_target_layers')}))

if __name__=='__main__':main()
