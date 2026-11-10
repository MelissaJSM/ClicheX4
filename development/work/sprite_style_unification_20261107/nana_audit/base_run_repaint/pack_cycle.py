"""Nana 새 run/fire 목표를 bounded native bank에 등록하는 로컬 검토 도구."""
from pathlib import Path
import sys,json,struct,argparse
ROOT=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(ROOT),str(Path(__file__).parent.parent/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
from scripts.prepare_shibuki_ultimate_production import pack_shared,repack_parts,records
from scripts.overhaul_sprites_costume_pack import resize_tile_storage,repack_variable
from scripts.prepare_riko_ui import replace_entry,entry
from src.psx_player import decode_stream,composition_frame,indexed_atlas,bank_offsets
from src.psx_sprite_batch import canvas_from_parts
from src.psx_ui_atlas import local_composition
import numpy as np
from PIL import Image
D=Path(__file__).parent
PARENT='18be60ea9e6745abf2309611cc9617e76acda4ebd984f7abf2995c457ec06908'
RESTORED='fab5256c35d6fd731597379bd1d259d9903ab78ad8c917bd49052419b40b6027'
PLACEHOLDERS={105,*range(175,183)}

def raw(a,gb,n):
    f=a.banks[gb]['frames'][n]
    return decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128).data

def main():
    p=argparse.ArgumentParser();p.add_argument('--targets',default='cycle_registered_v1');p.add_argument('--out',default='packed_run_probe_v1');args=p.parse_args()
    targetdir=D/args.targets;out=D/args.out;out.mkdir(exist_ok=True)
    base=Archive((D/'baseline_PL00_U.ARC').read_bytes());need(sha(base.data)==PARENT,'Baseline guard')
    a=Archive((D.parent/'native_restore/prepared_v1/PL00_U.ARC').read_bytes());need(sha(a.data)==RESTORED,'Ladder restore guard')
    targets={};pending=[]
    for n in range(1,33):
        path=targetdir/f'{"run"if n%2 else"shoot"}_{n:03}.png'
        if path.exists():targets[n]=np.array(Image.open(path))
        else:targets[n]=a.layer(n)[0];pending.append(n)
        need(targets[n].shape==(384,384)and targets[n].max()<16,'Indexed target format')
    replacement={};counts={};changes={};reports=[]
    for n in range(1,33,2):
        refs=[n,n+1];f=a.banks[0]['frames'][n];old=raw(a,0,n)
        need(a.banks[0]['frames'][n+1]['offset']==f['offset'],'Pair sharing changed')
        protected={q['tile']for r in refs for pb in(5,6,7,8)for q in composition_frame(a.c,pb,r)['parts']}
        nr=resize_tile_storage(old,f['tile_count'],32)
        pool=set(range(32))-protected-{0,16}
        images=[targets[r][80:240,80:240]for r in refs]
        nr,assignments=pack_shared(nr,32,images,pool,[16,16])
        old_atlas=np.frombuffer(indexed_atlas(old,f['tile_count'])[0],np.uint8).reshape(-1,256)
        new_atlas=np.frombuffer(indexed_atlas(nr,32)[0],np.uint8).reshape(-1,256)
        for t in protected:
            y,x=t//16*16,t%16*16
            need(np.array_equal(old_atlas[y:y+16,x:x+16],new_atlas[y:y+16,x:x+16]),'Armor tile changed')
        for r,rr in zip(refs,assignments):
            need(0<len(rr)<=16,'Part count')
            changes[r]=b''.join(struct.pack('<BBbb',fl,t,x-80,y-80)for t,x,y,fl in rr)
            replacement[r]=nr;counts[r]=32
        reports.append({'refs':refs,'old_tiles':f['tile_count'],'new_tiles':32,'protected_armor_tiles':sorted(protected),'base_pool':sorted(pool),'parts':[len(rr)for rr in assignments]})
        print(json.dumps({'packed':refs}),flush=True)
    nc,slack=repack_parts(a.c,0,changes);ng,packing=repack_variable(a.g,replacement,counts)
    result=replace_entry(replace_entry(a.data,2,ng),3,nc);b=Archive(result)
    raw_checked=nonselected_raw=0
    for gb,bank in enumerate(a.banks):
        need((bank['base'],bank['end'])==(b.banks[gb]['base'],b.banks[gb]['end']),'Bank bound')
        for n in range(len(bank['frames'])):
            expected=replacement[n]if gb==0 and n in replacement else raw(a,gb,n)
            need(raw(b,gb,n)==expected,f'Raw differs {gb}/{n}');raw_checked+=1
            if not(gb==0 and n in replacement):nonselected_raw+=1
    layers_checked=0
    for n in range(237):
        if n in PLACEHOLDERS:continue
        for pb in(0,5,6,7,8):
            expected=targets[n]if pb==0 and n in targets else a.layer(n,pb)[0]
            need(np.array_equal(b.layer(n,pb)[0],expected),f'Layer differs {n}/{pb}')
            layers_checked+=1
    parts_checked=0
    for pb in range(len(bank_offsets(a.c))):
        count=composition_frame(a.c,pb,0)['bank_frame_count']
        for n in range(count):
            if pb==0 and n in changes:continue
            need(records(a.c,pb,n)==records(b.c,pb,n),'Non-target composition changed');parts_checked+=1
    # New base tile records exclude page first columns; reused immutable armor
    # is left byte-identical, so any existing edge is neither hidden nor altered.
    for n in range(1,33):
        for q in composition_frame(b.c,0,n)['parts']:
            need(q['tile']%16!=0 and not q['flip_y'],'Unsafe new GPU edge')
    need(a.p==b.p and a.p==base.p,'Palette changed')
    original=bytearray(a.data);after=bytearray(b.data)
    from scripts.discover_inputs import psx_arc
    for e in psx_arc(a.data):
        if int(e['type'],16)in(2,3):original[e['offset']:e['offset']+e['size']]=after[e['offset']:e['offset']+e['size']]
    need(original==after,'Other entry changed')
    (out/'PL00_U.ARC').write_bytes(result)
    review=[]
    for n in(1,5,7,15,19,27,31):
        review.append((f'ref {n}',[('대기 기본',base.composite(0)[0]),('새 기본',b.composite(n)[0]),('대기 포스',base.composite(0,15)[0]),('새 기본+기존 포스',b.composite(n,15)[0])]))
    helper.grid(review,out/'base_fourth_review.png',5)
    for n in(1,7,15,19):
        helper.grid([(f'mask {m:02X}',[('기존',a.composite(n,m,1)[0]),('새 기본/기존 파츠 arm1',b.composite(n,m,1)[0]),('새 기본/기존 파츠 arm2',b.composite(n,m,2)[0])])for m in range(16)],out/f'partial_{n:03}.png',4)
    report={'passed':True,'source_arc_sha256':PARENT,'sequential_ladder_input_sha256':RESTORED,'after_sha256':sha(result),'raw_checked':raw_checked,'nonselected_raw_exact':nonselected_raw,'layers_checked':layers_checked,'nonselected_parts_exact':parts_checked,'groups':reports,'packing':packing,'composition_slack':slack,'new_base_refs':[n for n in targets if n not in pending],'pending_firing_refs':pending,'native_scope':'달리기32참조 중 실제 새 그림 파일이 있는 참조만 교체한 중간 자원. 현재 게임 미적용.','runtime_verified':False,'new_gpu_first_column_and_flip_y_safe':True,'armor_layers_exact':True,'armor_composites_art_review_pending':True}
    write(out/'verification.json',report);print(json.dumps({k:v for k,v in report.items()if k not in('groups','packing')}))
if __name__=='__main__':main()
