"""새 기본/포스 run-fire32를 같은 네이티브 뱅크 안에 등록한다."""
from pathlib import Path
import sys,json,struct,argparse
ROOT=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(ROOT),str(Path(__file__).parent),str(Path(__file__).parent.parent/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
from pack_cycle import raw,PARENT,RESTORED,PLACEHOLDERS
from scripts.prepare_shibuki_ultimate_production import pack_shared,repack_parts,records
from scripts.overhaul_sprites_costume_pack import resize_tile_storage,repack_variable
from scripts.prepare_riko_ui import replace_entry,entry
from src.psx_player import composition_frame,bank_offsets
from scripts.discover_inputs import psx_arc
import numpy as np
from PIL import Image
D=Path(__file__).parent
PBS=(0,5,6,7,8)
MANIFEST='2940549d1bb44d631e6b57e7fa992b7b85fe574ff59c0ebaa7f35a325964460e'
OUTPUT='b5b3157a5c09c8603eec579f66251d8c69228b5948ceb9f35b5303ac52dd6f97'
def validate_targets(targets,manifest):
    need(set(targets)=={(n,pb)for n in range(1,33)for pb in PBS},'Target coverage')
    for q in manifest['frames']:
        n=q['ref']
        for pb in PBS:
            ar=targets[n,pb];need(ar.shape==(384,384)and ar.dtype==np.uint8 and ar.max()<16,'Target format')
            expected=q['base_sha256']if pb==0 else q['layers'][str(pb)]
            need(sha(ar.tobytes())==expected,'Target source SHA')
def validate_output(out):
    out=out.resolve();need(out.is_relative_to(D.resolve())and out!=D.resolve(),'Output outside isolated work')
    need(not out.exists(),'Output must be fresh');return out
def main():
    p=argparse.ArgumentParser();p.add_argument('--out',default='packed_joint_v1');args=p.parse_args();out=validate_output(D/args.out)
    a=Archive((D.parent/'native_restore/prepared_v1/PL00_U.ARC').read_bytes());need(sha(a.data)==RESTORED,'Restored input guard')
    parent=Archive((D/'baseline_PL00_U.ARC').read_bytes());need(sha(parent.data)==PARENT,'Parent guard')
    td=D/'joint_layers_v1';need(digest(td/'manifest.json')==MANIFEST,'Target manifest SHA');manifest=json.loads((td/'manifest.json').read_text('utf8'));targets={(n,pb):np.array(Image.open(td/f'layer{pb}_{n:03}.png'))for n in range(1,33)for pb in PBS};validate_targets(targets,manifest);out.mkdir()
    replacement={};counts={};changes={pb:{}for pb in PBS};reports=[]
    for n in range(1,33,2):
        refs=[n,n+1];f=a.banks[0]['frames'][n];old=raw(a,0,n);need(a.banks[0]['frames'][n+1]['offset']==f['offset'],'Pair sharing guard')
        # All five costume layers of both aliases are regenerated as one unit.
        # Zero-init leaves no abandoned original wardrobe pixels in the raw cache.
        blank=bytes(4096);pairs=[(r,pb)for r in refs for pb in PBS];images=[targets[k][80:240,80:240]for k in pairs]
        try:
            nr,assignments=pack_shared(blank,32,images,set(range(32))-{0,16},[16]*len(images));mode='paired'
            groups=[(refs,nr,pairs,assignments)]
        except ValueError as e:
            # Resource bank boundaries stay fixed. A pair can safely have separate
            # streams because both aliases and all of their layers are selected.
            groups=[];mode='separate';print(json.dumps({'split':refs,'reason':str(e)}),flush=True)
            for r in refs:
                ps=[(r,pb)for pb in PBS];nr,assignments=pack_shared(blank,32,[targets[k][80:240,80:240]for k in ps],set(range(32))-{0,16},[16]*5);groups.append(([r],nr,ps,assignments))
        for rr,nr,ps,assignments in groups:
            for r in rr:replacement[r]=nr;counts[r]=32
            for (r,pb),assignment in zip(ps,assignments):
                need(len(assignment)<=16,'Part count');changes[pb][r]=b''.join(struct.pack('<BBbb',flag,t,x-80,y-80)for t,x,y,flag in assignment)
            reports.append({'refs':rr,'mode':mode,'parts':{f'{r}/{pb}':len(ass)for(r,pb),ass in zip(ps,assignments)}})
        print(json.dumps({'packed':refs,'mode':mode}),flush=True)
    write(out/'packing_plan.json',{'groups':reports})
    nc=a.c;slack={}
    for pb in PBS:nc,slack[pb]=repack_parts(nc,pb,changes[pb])
    ng,packing=repack_variable(a.g,replacement,counts);result=replace_entry(replace_entry(a.data,2,ng),3,nc);b=Archive(result)
    rawchecked=nonraw=0
    for gb,bank in enumerate(a.banks):
        need((bank['base'],bank['end'])==(b.banks[gb]['base'],b.banks[gb]['end']),'Bank bounds')
        for n in range(len(bank['frames'])):
            expected=replacement[n]if gb==0 and n in replacement else raw(a,gb,n)
            need(raw(b,gb,n)==expected,f'Raw {gb}/{n} differs');rawchecked+=1;nonraw+=not(gb==0 and n in replacement)
    layers=0;nonlayers=0
    for n in range(237):
        if n in PLACEHOLDERS:continue
        for pb in PBS:
            expected=targets[n,pb]if(n,pb)in targets else a.layer(n,pb)[0]
            need(np.array_equal(b.layer(n,pb)[0],expected),f'Layer {n}/{pb} differs');layers+=1;nonlayers+=(n,pb)not in targets
    parts=0
    for pb in range(len(bank_offsets(a.c))):
        for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
            if pb in changes and n in changes[pb]:continue
            need(records(a.c,pb,n)==records(b.c,pb,n),f'Composition {n}/{pb} differs');parts+=1
    for n in range(1,33):
        for pb in PBS:
            for q in composition_frame(b.c,pb,n)['parts']:need(q['tile']%16!=0 and not q['flip_y'],'Unsafe new GPU edge')
    need(a.p==b.p==parent.p,'Palette changed');original=bytearray(a.data);after=bytearray(result)
    for e in psx_arc(a.data):
        if int(e['type'],16)in(2,3):original[e['offset']:e['offset']+e['size']]=after[e['offset']:e['offset']+e['size']]
    need(original==after,'Other entry changed')
    need(sha(result)==OUTPUT,'Prepared output differs from visually reviewed candidate')
    (out/'PL00_U.ARC').write_bytes(result)
    write(out/'verification.json',{'passed':True,'parent_arc_sha256':PARENT,'ladder_source_sha256':RESTORED,'after_sha256':sha(result),'raw_checked':rawchecked,'nonselected_raw_exact':nonraw,'layers_checked':layers,'nonselected_layers_exact':nonlayers,'nonselected_compositions_exact':parts,'composition_slack':slack,'packing':packing,'groups':reports,'new_gpu_safe':True,'runtime_verified':False})
    print(json.dumps({'passed':True,'sha256':sha(result),'composition_slack':slack}),flush=True)
if __name__=='__main__':main()
