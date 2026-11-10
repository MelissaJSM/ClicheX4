"""피격13의 몸체/파생실루엣과 고정효과를 분리 패킹하는 진단 후보."""
from pathlib import Path
import sys,json,struct
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint'),str(D)]
from preview_restore import Archive,sha,digest,write,need,helper
from pack_cycle import raw,PLACEHOLDERS
from test_body_capacity import tile_copy
from scripts.prepare_shibuki_ultimate_production import pack_shared,repack_parts,records
from scripts.overhaul_sprites_costume_pack import repack_variable,pack_planes
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import composition_frame,bank_offsets,indexed_atlas
from scripts.discover_inputs import psx_arc
PBS=(0,5,6,7,8);REFS=tuple(range(106,115))+(233,234,235,236)
BEFORE='3bd156730cb932f2a97b43acc85f0d2209537c76cbab6d298c973438bc251b42'
PARENT=N/'rising_repaint/packed_base_candidate_v1/PL00_U.ARC'
def composite(a,ls,mask,arm):
    im=a.rgba(ls[0])
    for bit,pb in((8,8),(1,5),(4,7),(2,6)):
        if mask&bit:im.alpha_composite(a.rgba(ls[pb],32 if pb==7 and arm==2 else 16))
    return im
def part_bytes(rr):
    return b''.join(struct.pack('<BBbb',flag,t,x-80,y-80)for t,x,y,flag in rr)
def main():
    td=D/'effect_probe_v1';meta=json.loads((td/'manifest.json').read_text('utf8'));a=Archive(PARENT.read_bytes());need(sha(a.data)==BEFORE,'부모 해시')
    targets={(n,pb):np.array(Image.open(td/f'layer{pb}_{n:03}.png'))for n in REFS for pb in PBS}
    for (n,pb),z in targets.items():
        need(z.shape==(384,384)and z.dtype==np.uint8 and z.max()<48,'목표 포맷');need(sha(z.tobytes())==meta['targets'][str(n)][str(pb)],'목표 해시')
    audit=ROOT/'work/sprite_style_unification_20261107/zero_audit/nana_hurt_relations01/report.json'
    rel={q['ref']:q for q in json.loads(audit.read_text('utf8'))['body_plus_effect_relations']}
    replacement={};counts={};changes={pb:{}for pb in PBS};groups=[];protected=[]
    for ns in((106,107,108),(110,111),(109,),(112,),(113,),(114,),(233,),(234,),(235,),(236,)):
        n=ns[0];keep=set()
        for k in ns:
            if k in rel:
                for ls in rel[k]['layers'].values():keep.update(ls['effect_tiles'])
        if keep:
            oldcnt=a.banks[0]['frames'][n]['tile_count'];seed=tile_copy(raw(a,0,n),oldcnt,keep)
            ims=[targets[n,pb][80:240,80:240]for pb in PBS]
            nr,assign=pack_shared(seed,32,ims,set(range(32))-{0,16}-keep,[16]*5)
        else:
            nr,assign=pack_planes(bytes(4096),32,[targets[n,pb][80:240,80:240]for pb in PBS],set(range(32))-{0,16},[16]*5)
        for k in ns:
            replacement[k]=nr;counts[k]=32
            for pb,rr in zip(PBS,assign):
                record=part_bytes(rr)
                if k in rel:
                    effects=rel[k]['layers'][str(pb)]['extra_effect_records']
                    record+=b''.join(struct.pack('<BBbb',q['flags'],q['tile'],q['x'],q['y'])for q in effects)
                changes[pb][k]=record
        if keep:
            oldatlas=np.frombuffer(indexed_atlas(raw(a,0,n),oldcnt)[0],np.uint8).reshape(-1,256)
            newatlas=np.frombuffer(indexed_atlas(nr,32)[0],np.uint8).reshape(32,256)
            for t in keep:
                y,x=t//16*16,t%16*16;need(np.array_equal(oldatlas[y:y+16,x:x+16],newatlas[y:y+16,x:x+16]),'원효과 타일')
            protected.append({'refs':list(ns),'tiles':sorted(keep),'whole_tiles_exact':True})
        groups.append({'refs':list(ns),'parts':{str(pb):[len(changes[pb][k])//4 for k in ns]for pb in PBS},'raw_sha256':sha(nr)})
    nc=a.c;slack={}
    for pb in PBS:nc,slack[pb]=repack_parts(nc,pb,changes[pb])
    ng,packing=repack_variable(a.g,replacement,counts);result=replace_entry(replace_entry(a.data,2,ng),3,nc);b=Archive(result)
    rawcount=nonraw=0
    for gb,bank in enumerate(a.banks):
        need((bank['base'],bank['end'])==(b.banks[gb]['base'],b.banks[gb]['end']),'은행경계')
        for n in range(len(bank['frames'])):
            expected=replacement[n]if gb==0 and n in replacement else raw(a,gb,n)
            need(raw(b,gb,n)==expected,f'raw{gb}/{n}');rawcount+=1;nonraw+=not(gb==0 and n in replacement)
    layers=nonlayers=0
    for n in range(237):
        if n in PLACEHOLDERS:continue
        for pb in PBS:
            z=targets[n,pb]if n in REFS else a.layer(n,pb)[0]
            need(np.array_equal(b.layer(n,pb)[0],z),f'layer{n}/{pb}');layers+=1;nonlayers+=n not in REFS
    otherparts=0
    for pb in range(len(bank_offsets(a.c))):
        for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
            if pb in PBS and n in REFS:continue
            need(records(a.c,pb,n)==records(b.c,pb,n),f'조립{n}/{pb}');otherparts+=1
    need(a.p==b.p,'팔레트')
    for e in psx_arc(a.data):
        if int(e['type'],16)in(2,3):continue
        sl=slice(e['offset'],e['offset']+e['size']);need(a.data[sl]==result[sl],'기타entry')
    rgba=0
    for n in range(237):
        if n in PLACEHOLDERS:continue
        for mask in range(16):
            for arm in(1,2):
                expected=composite(a,{pb:targets[n,pb]for pb in PBS},mask,arm)if n in REFS else a.composite(n,mask,arm)[0]
                need(b.composite(n,mask,arm)[0].tobytes()==expected.tobytes(),f'RGBA{n}/{mask}/{arm}');rgba+=1
    out=D/'packed_hurt_diagnostic_v1';out.mkdir(exist_ok=False);(out/'PL00_U.ARC').write_bytes(result)
    for k,ns in enumerate(((106,110),(233,234),(107,108,109),(111,112,113),(114,235,236)),1):
        helper.grid([(f'hurt {n}',[('base idle',b.composite(0)[0]),('new base',b.composite(n)[0]),('Fourth idle',b.composite(0,15)[0]),('new Fourth',b.composite(n,15)[0])])for n in ns],out/f'readback_{k}.png',6 if k<3 else 5)
    report={'passed':True,'before':BEFORE,'after':sha(result),'targets_manifest_sha256':digest(td/'manifest.json'),'refs':list(REFS),
            'raw_checked':rawcount,'nonselected_raw_exact':nonraw,'layers_checked':layers,'nonselected_layers_exact':nonlayers,'nonselected_compositions_exact':otherparts,
            'rgba_combinations':rgba,'target_rgba_combinations':len(REFS)*32,'protected_effect_tiles':protected,'groups':groups,'packing':packing,'composition_slack':slack,
            'palette_and_other_entries_exact':True,'scope':'진단용 native 재추출. 미술잔류/오라겹침·GPU경계 원MIPS·원순서/독립검사/동결 전.','frozen':False,'runtime_verified':False}
    write(out/'verification.json',report);print(json.dumps({'sha256':sha(result),'packing':packing,'slack':slack,'rgba':rgba}))
if __name__=='__main__':main()
