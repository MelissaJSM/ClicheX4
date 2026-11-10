"""새 기본/포스 벽 12참조를 독립 네이티브 검토 ARC로 패킹한다."""
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
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import composition_frame,bank_offsets
from scripts.discover_inputs import psx_arc
PBS=(0,5,6,7,8);REFS=range(55,67);BEFORE='b5b3157a5c09c8603eec579f66251d8c69228b5948ceb9f35b5303ac52dd6f97'
def validate_source(data):
    need(sha(data)==BEFORE,'Parent hash');return Archive(data)
def validate_output(out):
    out=out.resolve();need(out.is_relative_to(D.resolve())and not out.exists(),'Fresh isolated output required');return out
def validate_targets(targets,manifest):
    need(manifest['source_arc_sha256']==BEFORE,'Target parent');need(set(targets)=={(n,pb)for n in REFS for pb in PBS},'Coverage')
    need({q['ref']for q in manifest['frames']}==set(REFS)and len(manifest['frames'])==12,'Manifest coverage')
    for q in manifest['frames']:
        for pb in PBS:
            ar=targets[q['ref'],pb];need(ar.shape==(384,384)and ar.dtype==np.uint8 and ar.max()<16,'Target format');need(sha(ar.tobytes())==(q['base_sha256']if pb==0 else q['layers'][str(pb)]),'Target hash')
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='packed_wall_candidate_v4');parser.add_argument('--targets',default='joint_layers_probe_v4');args=parser.parse_args();out=validate_output(D/args.out)
    parent=D.parent/'base_run_repaint/packed_joint_v2/PL00_U.ARC';a=validate_source(parent.read_bytes());td=D/args.targets;manifest=json.loads((td/'manifest.json').read_text('utf8'));need(manifest['source_arc_sha256']==BEFORE,'Target parent');targets={}
    for q in manifest['frames']:
        n=q['ref'];need(n in REFS,'Unexpected target')
        for pb in PBS:
            ar=np.array(Image.open(td/f'layer{pb}_{n:03}.png'));need(ar.shape==(384,384)and ar.dtype==np.uint8 and ar.max()<16,'Target format');need(sha(ar.tobytes())==(q['base_sha256']if pb==0 else q['layers'][str(pb)]),'Target hash');targets[n,pb]=ar
    validate_targets(targets,manifest);out.mkdir();replacement={};counts={};changes={pb:{}for pb in PBS};groups=[]
    for n in range(55,67,2):
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
    ng,packing=repack_variable(a.g,replacement,counts);result=replace_entry(replace_entry(a.data,2,ng),3,nc);b=Archive(result);rawcount=nonraw=0
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
    need(before==after,'Other entry');(out/'PL00_U.ARC').write_bytes(result)
    # Native archive re-read is the source of these review sheets.
    for i,start in enumerate((55,61)):
        helper.grid([(f'wall {n}/{n+1}',[('기본 대기',b.composite(0)[0]),('새 기본',b.composite(n)[0]),('새 사격',b.composite(n+1)[0]),('포스 대기',b.composite(0,15)[0]),('새 포스',b.composite(n,15)[0]),('새 포스 사격',b.composite(n+1,15)[0])])for n in range(start,start+6,2)],out/f'readback_{i+1}.png',5)
    verify={'passed':True,'scope':'기술 검토 후보. 미술 수용·부분파츠 검토·실기 완료 아님.','before':BEFORE,'after':sha(result),'raw_checked':rawcount,'nonselected_raw_exact':nonraw,'layers_checked':layercount,'nonselected_layers_exact':nonlayers,'nonselected_compositions_exact':parts,'composition_slack':slack,'packing':packing,'groups':groups,'palette_and_other_entries_exact':True,'gpu_boundary_guard':True,'runtime_verified':False,'targets_manifest_sha256':digest(td/'manifest.json')};write(out/'verification.json',verify)
    write(out/'proposal.json',{'project':'ver_rin_nana','parent_arc_sha256':BEFORE,'files':{'PL00_U.ARC':{'path':(out/'PL00_U.ARC').relative_to(ROOT).as_posix(),'before':BEFORE,'after':sha(result)}},'candidate_only':True});print(json.dumps({'after':sha(result),'slack':slack,'out':str(out)}),flush=True)
if __name__=='__main__':main()
