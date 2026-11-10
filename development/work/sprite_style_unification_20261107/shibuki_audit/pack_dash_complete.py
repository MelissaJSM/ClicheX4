"""새 대시20참조를 원래 은행 경계·32타일 내에서 무손실 패킹한다."""
from pathlib import Path
import json,sys,struct,argparse
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,crop
from scripts.export_x_consistency import Archive,page
from scripts.prepare_shibuki_ultimate_production import records,repack_parts
from scripts.overhaul_sprites_costume_pack import repack_variable
from scripts.prepare_riko_ui import replace_entry,entry
from scripts.discover_inputs import psx_arc
from src.psx_player import bank_offsets,decode_stream,composition_frame,indexed_atlas
from pack_air_targets_probe import pack_pinned
from probe_air_body_capacity import put
from prepare_dash_body_layers import P
PARENT='13a29023365419d32475cf5a6551adc4658116c8f03622d962d5b8071744e8b8'
LOCK='42eb8f357570b936f013293c4b82ed47625e91417d5d9862e10956b2551a940c'
PARTS=(0,5,6,7,8)
def validate_inputs(data,read):
    """출력 전에 모든 고정 입력을 검증한다. read의 경로는 H 기준이다."""
    need(sha(data)==PARENT,'Parent hash mismatch')
    prefix='dash_complete_targets01/'
    raw=read(prefix+'LOCK.json');need(sha(raw)==LOCK,'Target lock changed');lock=json.loads(raw)
    raw=read(prefix+'targets.json');need(sha(raw)==lock['target_manifest_sha256'],'Manifest changed')
    for name,digest in lock['files'].items():need(sha(read(prefix+name))==digest,'Target changed '+name)
    for name,digest in lock['source_reports'].items():need(sha(read(name))==digest,'Source report changed '+name)
    return json.loads(raw)
def protected_entries(before,after):
    """같은 type이 여러 번 나와도 각각의 디렉터리/본문을 검사한다."""
    aa,bb=psx_arc(before),psx_arc(after);need(len(aa)==len(bb),'Entry count changed');rows=[]
    allowed=np.zeros(len(before),dtype=bool);need(len(before)==len(after),'Archive size changed')
    for a,b in zip(aa,bb):
        for key in ('index','type','offset','size'):need(a[key]==b[key],'Entry boundary changed')
        s=a['offset'];e=s+a['size'];kind=int(a['type'],16)
        if kind in(2,3):allowed[s:e]=True
        else:
            need(before[s:e]==after[s:e],'Other entry changed '+str(a['index']))
            rows.append({'index':a['index'],'type':a['type'],'offset':s,'size':a['size'],'sha256':sha(before[s:e])})
    dif=np.frombuffer(before,np.uint8)!=np.frombuffer(after,np.uint8)
    need(not np.any(dif&~allowed),'Header, padding or unrelated entry changed')
    return rows
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='dash_pack_probe01');z=ap.parse_args();o=(H/z.output).resolve();need(o.is_relative_to(H.resolve())and not o.exists(),'Fresh isolated output');d=H/'dash_complete_targets01';data=P.read_bytes();meta=validate_inputs(data,lambda p:(H/p).read_bytes())
    targets={r['ref']:{b:np.array(Image.open(d/f'{r["ref"]:03}_bank{b}_indices.png'))for b in PARTS}for r in meta['rows']};a=Archive(data);changes={b:{}for b in PARTS};raws={};reports=[];o.mkdir()
    orig=Archive((ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/original.arc').read_bytes());f=orig.banks[0]['frames'][73];original_raw=decode_stream(orig.g,f['offset'],f['limit'],f['tile_count']*128).data;original_tile=np.frombuffer(indexed_atlas(original_raw,f['tile_count'])[0],np.uint8).reshape(-1,256)[:16,96:112].copy();tail={n:records(orig.c,0,n)[-36:]for n in(73,74)};groups={}
    for n in targets:groups.setdefault(a.banks[0]['frames'][n]['offset'],[]).append(n)
    for offset,refs in sorted(groups.items()):
        refs=sorted(refs);allrefs=[f['index']for f in a.banks[0]['frames']if f['offset']==offset];need(set(allrefs)==set(refs),'Sharing escapes selected targets');raw=bytes(4096);used=set();headcache=[]
        for n in refs:
            target=targets[n][5];found=next((r for ar,r in headcache if np.array_equal(ar,target)),None)
            if found is None:
                y,x=np.nonzero(target);need(len(x)>0 and x.max()-x.min()<16 and y.max()-y.min()<16,'Head target not single tile');tile=10+len(headcache);need(tile<16,'Too many unique head pieces');found=struct.pack('<BBbb',0,tile,int(x.min()-160),int(y.min()-160));raw=put(raw,found,target);headcache.append((target,found));used.add(tile)
            changes[5][n]=found
        if 73 in refs:
            atlas=np.frombuffer(indexed_atlas(raw,32)[0],np.uint8).reshape(32,256).copy();atlas[:16,96:112]=original_tile;raw=bytes((atlas[:,0::2]|(atlas[:,1::2]<<4)).ravel());used.add(6)
        order=[(n,b)for n in refs if n not in(73,74)for b in(0,6,7,8)];images=[crop(targets[n][b])for n,b in order]
        try:nr,rr,mode=pack_pinned(raw,images,set(range(1,32))-used)
        except ValueError as ex:write(o/'report.json',{'passed':False,'group':refs,'reason':str(ex),'completed_groups':reports});print(str(ex));return
        for(n,b),parts in zip(order,rr):changes[b][n]=b''.join(struct.pack('<BBbb',fl,t,x-80,y-80)for t,x,y,fl in parts)
        for n,bn in((73,71),(74,72)):
            if n in refs:
                for b in (0,6,7,8):changes[b][n]=changes[b][bn]+(tail[n]if b==0 else b'')
        for n in refs:raws[n]=nr
        reports.append({'refs':refs,'mode':mode,'parts':{str(n):{str(b):len(changes[b][n])//4 for b in PARTS}for n in refs},'pinned_head_tiles':sorted(used-{6}),'original9_streak_records':73 in refs})
    nc=a.c;slack={}
    try:
        for b,rr in changes.items():nc,slack[b]=repack_parts(nc,b,rr)
        ng,graphics=repack_variable(a.g,raws,{n:32 for n in raws});new=replace_entry(replace_entry(data,2,ng),3,nc);actual=Archive(new)
        need(bank_offsets(nc)==bank_offsets(a.c),'Composition boundary moved');layers=0
        for n,ll in targets.items():
            for b,want in ll.items():need(np.array_equal(actual.layer(n,b)[0],want),'Layer readback mismatch '+str((n,b)));layers+=1
        totalraw=untargetraw=0
        for bi,ab in enumerate(a.banks):
            bb=actual.banks[bi];need((ab['base'],ab['end'],len(ab['frames']))==(bb['base'],bb['end'],len(bb['frames'])),'Graphics boundary moved')
            for f,ff in zip(ab['frames'],bb['frames']):
                r=decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128).data;s=decode_stream(actual.g,ff['offset'],ff['limit'],ff['tile_count']*128).data;totalraw+=1
                if bi==0 and f['index']in raws:need(s==raws[f['index']],'Target raw mismatch')
                else:need(r==s,'Non-target raw changed');untargetraw+=1
        otherparts=0
        for b in range(len(bank_offsets(a.c))):
            for n in range(composition_frame(a.c,b,0)['bank_frame_count']):
                if b in changes and n in targets:continue
                need(records(a.c,b,n)==records(actual.c,b,n),'Non-target parts changed');otherparts+=1
        for n in(73,74):need(records(actual.c,0,n)[-36:]==tail[n],'Original speed streak record changed')
        preserved=protected_entries(data,new)
        (o/'PL00_U.ARC').write_bytes(new)
        for form,mask in(('base',0),('fourth',15)):
            pics=[(f'{form} {n}',actual.composite(n,mask)[0])for n in sorted(targets)]
            for i in range(0,len(pics),6):page(pics[i:i+6],actual.composite(0,mask)[0],o/f'{form}_readback_{i//6:02}.png',cols=3,scale=4)
        write(o/'report.json',{'passed':True,'before':PARENT,'after':sha(new),'target_lock':LOCK,'groups':reports,'part_slack':slack,'graphics':graphics,'raw_references':totalraw,'non_target_raw':untargetraw,'exact_target_layers':layers,'non_target_parts':otherparts,'preserved_entries':preserved,'original_streak_tile_texel_sha256':sha(original_tile.tobytes()),'old_audit_tile_hash_correction':'기존 audit의 raw[6*128:7*128] 해시는 행 업로드 배치의 연속 구간이며 tile6해시가 아니었음. 실제16x16 타일은 indexed_atlas 열96:112에서 읽음.','native_cpu_verified':False,'visual_readback_pending':True})
        print(json.dumps({'passed':True,'sha256':sha(new),'part_slack':slack,'groups':len(reports),'layers':layers}))
    except ValueError as ex:write(o/'report.json',{'passed':False,'reason':str(ex),'part_slack':slack,'groups':reports});print(str(ex))
if __name__=='__main__':main()
