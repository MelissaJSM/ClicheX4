"""새 얼티밋 벽 전후 12참조를 독립 네이티브 검토 ARC로 패킹한다."""
from pathlib import Path
import sys,json,struct,argparse
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(D.parent/'native_restore'),str(D.parent/'base_run_repaint')]
from preview_restore import Archive,sha,digest,write,need,helper
from pack_cycle import raw,PLACEHOLDERS
from scripts.prepare_shibuki_ultimate_production import pack_shared,repack_parts,records
from scripts.overhaul_sprites_costume_pack import repack_variable
from repack_identical import repack_identical
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import composition_frame,bank_offsets
from scripts.discover_inputs import psx_arc
PBS=(0,5,6,7,8);REFS=tuple(range(67,85))+(93,94);BEFORE='e151044c37b5a59016f10d8c4d9637ffd4e192563f03c6a76df528383cfb4031'
def validate_source(data):
    need(sha(data)==BEFORE,'Parent hash');return Archive(data)
def validate_output(out):
    out=out.resolve();need(out.is_relative_to(D.resolve())and not out.exists(),'Fresh isolated output required');return out
def validate_targets(targets,manifest):
    need(manifest['source_arc_sha256']==BEFORE,'Target parent');need(set(targets)=={(n,pb)for n in REFS for pb in PBS},'Coverage')
    need({q['ref']for q in manifest['frames']}==set(REFS)and len(manifest['frames'])==20,'Manifest coverage')
    for q in manifest['frames']:
        for pb in PBS:
            ar=targets[q['ref'],pb];need(ar.shape==(384,384)and ar.dtype==np.uint8 and ar.max()<16,'Target format');need(sha(ar.tobytes())==(q['base_sha256']if pb==0 else q['layers'][str(pb)]),'Target hash')
            cropped=ar.copy();cropped[80:240,80:240]=0;need(not cropped.any(),'Target outside packing window')
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='packed_dash_diagnostic_v1');parser.add_argument('--targets',default='joint_native_targets_v1');args=parser.parse_args();out=validate_output(D/args.out)
    parent=D.parent/'ultimate_wall_repaint/packed_wall_candidate_v1/PL02_U.ARC';a=validate_source(parent.read_bytes());td=D/args.targets;manifest=json.loads((td/'manifest.json').read_text('utf8'));need(manifest['source_arc_sha256']==BEFORE,'Target parent');targets={}
    for q in manifest['frames']:
        n=q['ref'];need(n in REFS,'Unexpected target')
        for pb in PBS:
            ar=np.array(Image.open(td/f'layer{pb}_{n:03}.png'));need(ar.shape==(384,384)and ar.dtype==np.uint8 and ar.max()<16,'Target format');need(sha(ar.tobytes())==(q['base_sha256']if pb==0 else q['layers'][str(pb)]),'Target hash');targets[n,pb]=ar
    validate_targets(targets,manifest);out.mkdir();replacement={};counts={};changes={pb:{}for pb in PBS};groups=[]
    for n in tuple(range(67,85,2))+(93,):
        pairs=[(ref,pb)for ref in(n,n+1)for pb in PBS];images=[targets[k][80:240,80:240]for k in pairs];blank=bytes(4096)
        try:
            newraw,assign=pack_shared(blank,32,images,set(range(32))-{0,16},[16]*len(images));group=[([n,n+1],pairs,newraw,assign)];mode='paired'
        except ValueError as e:
            print(json.dumps({'split':[n,n+1],'reason':str(e)}),flush=True);group=[];mode='separate'
            for ref in(n,n+1):
                ps=[(ref,pb)for pb in PBS];newraw,assign=pack_shared(blank,32,[targets[k][80:240,80:240]for k in ps],set(range(32))-{0,16},[16]*5);group.append(([ref],ps,newraw,assign))
        for refs,ps,newraw,assign in group:
            for ref in refs:replacement[ref]=newraw;counts[ref]=32
            for(ref,pb),p in zip(ps,assign):
                need(len(p)<=16,'Part limit');changes[pb][ref]=b''.join(struct.pack('<BBbb',flags,t,x-80,y-80)for t,x,y,flags in p)
            groups.append({'refs':refs,'mode':mode,'parts':{f'{ref}/{pb}':len(p)for(ref,pb),p in zip(ps,assign)}})
        print(json.dumps({'packed':[n,n+1],'mode':mode}),flush=True)
    nc=a.c;slack={}
    for pb in PBS:nc,slack[pb]=repack_parts(nc,pb,changes[pb])
    ng,packing=repack_identical(a.g,replacement,counts);result=replace_entry(replace_entry(a.data,2,ng),3,nc);b=Archive(result);rawcount=nonraw=0
    for gb,bank in enumerate(a.banks):
        need((bank['base'],bank['end'])==(b.banks[gb]['base'],b.banks[gb]['end']),'Bank boundary')
        for n in range(len(bank['frames'])):
            expect=replacement[n]if gb==0 and n in replacement else raw(a,gb,n);need(raw(b,gb,n)==expect,f'Raw {gb}/{n}');rawcount+=1;nonraw+=not(gb==0 and n in replacement)
    layercount=nonlayers=0
    for n in range(237):
        if n in PLACEHOLDERS:continue
        for pb in PBS:
            expect=targets[n,pb]if(n,pb)in targets else a.layer(n,pb)[0];need(np.array_equal(b.layer(n,pb)[0],expect),f'Layer {n}/{pb}');layercount+=1;nonlayers+=(n,pb)not in targets
    parts=0
    for pb in range(len(bank_offsets(a.c))):
        for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
            if pb in PBS and n in REFS:continue
            need(records(a.c,pb,n)==records(b.c,pb,n),f'Parts {n}/{pb}');parts+=1
    for n in REFS:
        for pb in PBS:
            for p in composition_frame(b.c,pb,n)['parts']:need(p['tile']%16!=0 and not p['flip_y'],'Unsafe GPU boundary')
    need(a.p==b.p,'Palette');before=bytearray(a.data);after=bytearray(result)
    for e in psx_arc(a.data):
        if int(e['type'],16)in(2,3):before[e['offset']:e['offset']+e['size']]=after[e['offset']:e['offset']+e['size']]
    need(before==after,'Other entry');(out/'PL02_U.ARC').write_bytes(result)
    # Native archive re-read is the source of these review sheets.
    for i,group_refs in enumerate(((67,69,71),(73,75,77),(79,81,83),(93,))):
        helper.grid([(f'dash {n}/{n+1}',[('후폼 대기',b.composite(0)[0]),('새 후폼',b.composite(n)[0]),('후폼 사격',b.composite(n+1)[0]),('전폼 대기',b.composite(0,15)[0]),('새 전폼',b.composite(n,15)[0]),('전폼 사격',b.composite(n+1,15)[0])])for n in group_refs],out/f'readback_{i+1}.png',5)
    verify={'passed':True,'scope':'기술 검토 후보. 미술 수용·부분파츠 검토·실기 완료 아님.','before':BEFORE,'after':sha(result),'raw_checked':rawcount,'nonselected_raw_exact':nonraw,'layers_checked':layercount,'nonselected_layers_exact':nonlayers,'nonselected_compositions_exact':parts,'composition_slack':slack,'packing':packing,'groups':groups,'palette_and_other_entries_exact':True,'gpu_boundary_guard':True,'runtime_verified':False,'targets_manifest_sha256':digest(td/'manifest.json')};write(out/'verification.json',verify)
    write(out/'proposal.json',{'project':'ver_rin_nana','baseline_sha256':'f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720','parent_arc_sha256':BEFORE,'files':{'PL02_U.ARC':{'path':(out/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':'4564d66c4e8559454f4cc434e78194d3ac89f42b4db5877925755c818153a1fa','working_parent_before':BEFORE,'after':sha(result)}},'candidate_only':True});print(json.dumps({'after':sha(result),'slack':slack,'out':str(out)}),flush=True)
if __name__=='__main__':main()
