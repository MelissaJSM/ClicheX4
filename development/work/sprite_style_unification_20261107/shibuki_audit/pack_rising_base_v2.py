"""새 라이징파이어7참조를 고정 은행/32타일 안에 손실 없이 등록한다."""
from pathlib import Path
import sys,json,struct,argparse
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parents[2]))
import numpy as np
from PIL import Image
from scripts.export_x_consistency import Archive,page
from scripts.prepare_shibuki_ultimate_production import repack_parts,records
from scripts.overhaul_sprites_costume_pack import repack_variable
from scripts.prepare_riko_ui import replace_entry
from scripts.discover_inputs import psx_arc
from src.psx_player import decode_stream,bank_offsets,composition_frame,indexed_atlas
from native_pose_pack import need,sha,write,crop,lossless_pack
from prepare_lowhp_final import compose
from probe_air_record_alias import decode_templates,solve
from pack_air_targets_probe import pack_pinned
PARENT_SHA='61495a2aaf002efc32492a4e12c3724a77c82b3f42464538ae1e2cc855da74c0'
LOCK_SHA='06e27b8d005770dd4b473aaaaf1aaee14cb149dbe649d0995a13db2f247e107a'
REFS=(100,101,102,103,104,231,232);BANKS=(0,5,6,7,8)
def validate_inputs(data,d,read=lambda p:p.read_bytes()):
    need(sha(data)==PARENT_SHA,'Wrong exact parent');raw=read(d/'LOCK.json');need(sha(raw)==LOCK_SHA,'Wrong source lock');lock=json.loads(raw)
    for name,digest in lock['files'].items():need(sha(read(d/name))==digest,'Changed target: '+name)
    for name,digest in lock['source_files'].items():need(sha(read(H/name))==digest,'Changed source: '+name)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='rising_base_pack_probe02');args=ap.parse_args();o=(H/args.out).resolve()
    need(o.is_relative_to(H.resolve())and o!=H.resolve(),'Output outside work');need(not o.exists(),'Fresh output required')
    data=(H/'prepared_double_cyclone_base01/PL00_U.ARC').read_bytes();a=Archive(data);d=H/'rising_common_layers02';validate_inputs(data,d)
    targets={n:{b:np.array(Image.open(d/f'{231 if n==232 else n:03}_bank{b}_indices.png'))for b in BANKS}for n in REFS}
    targets[232]={b:np.roll(v,1,0)for b,v in targets[232].items()};changes={b:{}for b in BANKS};raws={};packmeta=[]
    templates=decode_templates(a,7,max_parts=4)
    for n in REFS:
        if n==232:continue
        refs=[n,232]if n==231 else[n]
        aliases=[f['index']for f in a.banks[0]['frames']if f['offset']==a.banks[0]['frames'][n]['offset']]
        need(aliases==[n],f'Unexpected raw alias {aliases}')
        arm_alias=None;points=set(map(int,np.flatnonzero(targets[n][7])))
        for _,length,p,recs,cov in templates:
            if not points<=cov:continue
            solution=solve(targets[n][7],recs)
            if solution is None:continue
            used={t for fl,t,x,y in recs if t};other=(0,5,6,8)
            try:raw,pp,method=pack_pinned(solution[0],[crop(targets[n][b])for b in other],set(range(1,32))-used)
            except ValueError:continue
            arm_alias=a.c[p:p+length*4];rrarm=[(t,x+80,y+80,fl)for fl,t,x,y in recs]
            bybank=dict(zip(other,pp));bybank[7]=rrarm;parts=[bybank[b]for b in BANKS];method='existing_arm_record_alias+'+method;break
        if arm_alias is None:raw,parts,method=lossless_pack([crop(targets[n][b])for b in BANKS])
        for nr in refs:
            raws[nr]=raw
            for b,rr in zip(BANKS,parts):changes[b][nr]=b''.join(struct.pack('<BBbb',fl,t,x-80,y-80+(nr==232))for t,x,y,fl in rr)
        packmeta.append({'refs':refs,'method':method,'arm_record_alias':None if arm_alias is None else arm_alias.hex(),'parts':{str(b):len(rr)for b,rr in zip(BANKS,parts)}})
    nc=a.c;slack={}
    for b,rr in changes.items():nc,slack[b]=repack_parts(nc,b,rr)
    ng,gmeta=repack_variable(a.g,raws,{n:32 for n in REFS});out=replace_entry(replace_entry(data,2,ng),3,nc);b=Archive(out)
    need(bank_offsets(a.c)==bank_offsets(b.c),'Composition boundaries moved');need(a.p==b.p,'Palette changed');rawcount=nonraw=nonparts=layers=conditions=gp=0
    for gb,bb in enumerate(a.banks):
        nb=b.banks[gb];need((bb['base'],bb['end'],len(bb['frames']))==(nb['base'],nb['end'],len(nb['frames'])),'Graphics boundary moved')
        for f,q in zip(bb['frames'],nb['frames']):
            v=decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128).data;w=decode_stream(b.g,q['offset'],q['limit'],q['tile_count']*128).data;rawcount+=1
            if gb==0 and f['index']in REFS:need(w==raws[f['index']],'Target raw mismatch')
            else:need(v==w,'Nontarget raw changed');nonraw+=1
    for pb in range(len(bank_offsets(a.c))):
        for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
            if pb in BANKS and n in REFS:continue
            need(records(a.c,pb,n)==records(b.c,pb,n),'Nontarget composition changed');nonparts+=1
    for n in range(237):
        if n in{105,*range(175,183)}:continue
        for pb in BANKS:
            actual=b.layer(n,pb)[0];expected=targets[n][pb]if n in REFS else a.layer(n,pb)[0]
            need(np.array_equal(actual,expected),f'Layer mismatch {n}/{pb}');layers+=1
        if n not in REFS:continue
        atlas=np.frombuffer(indexed_atlas(raws[n],32)[0],np.uint8).reshape(32,256)
        for pb in BANKS:
            for part in composition_frame(b.c,pb,n)['parts']:
                gp+=1;t=part['tile'];tile=atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
                if t%16==0:need(not tile[:,0].any(),'GPU U boundary hazard')
                if part['flip_y']:need(not tile[0].any(),'GPU V boundary hazard')
        for mask in range(16):
            for arm in(1,2):need(b.composite(n,mask,arm)[0].tobytes()==compose(a,targets[n],mask,arm).tobytes(),'Partial mismatch');conditions+=1
    allowed=np.zeros(len(data),bool)
    for e in psx_arc(data):
        if int(e['type'],16)in(2,3):allowed[e['offset']:e['offset']+e['size']]=True
    need(len(data)==len(out),'ARC size changed');need(not np.any((np.frombuffer(data,np.uint8)!=np.frombuffer(out,np.uint8))&~allowed),'Outside entries changed')
    o.mkdir();(o/'PL00_U.ARC').write_bytes(out)
    for form,mask in(('base',0),('fourth',15)):
        pics=[]
        for n in REFS:
            im=b.composite(n,mask)[0];im.save(o/f'{form}_{n:03}.png');pics.extend([(f'{n} parent',a.composite(n,mask)[0]),(f'{n} actual packed',im)])
        for start in range(0,len(pics),6):page(pics[start:start+6],a.composite(0,mask)[0],o/f'{form}_readback_{start//6:02}.png',cols=2,scale=5)
    for n in REFS:page([(f'{n} mask{m:X}',b.composite(n,m)[0])for m in range(16)],a.composite(0,15)[0],o/f'{n:03}_partial.png',cols=4,scale=4)
    write(o/'report.json',{'passed':True,'parent_sha256':sha(data),'candidate_sha256':sha(out),'target_refs':list(REFS),'source_index_files':{p.name:sha(p.read_bytes())for p in sorted(d.glob('*_indices.png'))},'raw_checked':rawcount,'non_target_raw_exact':nonraw,'non_target_parts_exact':nonparts,'layers_checked':layers,'partial_conditions':conditions,'gpu_parts_checked':gp,'parts_slack':slack,'graphics':gmeta,'pack_groups':packmeta,'outside_entries_exact':True,'all_palettes_audio_timing_exact':True,'preserved_banks':True,'pixel_loss':False,'derived232':'accepted Shibuki231 translated (0,+1); not claimed as original US pose equivalence','runtime_verified':False,'root_review_pending':True,'independent_pending':True})
    print(json.dumps({'sha':sha(out),'slack':slack,'raw':rawcount,'nonraw':nonraw,'partial':conditions,'parts':nonparts,'groups':packmeta}))
if __name__=='__main__':main()
