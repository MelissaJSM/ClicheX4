"""Ultimate 호버10을 원은행 경계 안에 손실 없이 수납한다."""
from pathlib import Path
import sys,json,struct,argparse,io
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,crop
from prepare_hover_ultimate_targets import P,PARENT,PBS,REFS,TD,GROUPS
from scripts.export_x_consistency import Archive,page
from scripts.prepare_shibuki_ultimate_production import repack_parts,records
from scripts.overhaul_sprites_costume_pack import pack_planes,resize_tile_storage
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import bank_offsets,composition_frame,indexed_atlas
from src.psx_compress import encode_stream
from pack_shibuki_hurt import raw,repack_fixed_global
from repack_part_records_lossless import repack as repack_global
from pack_dash_complete import protected_entries
from prepare_lowhp_final import compose
MANIFEST='b9567e6d822bc487c3742b14fe73864e17f31cee0f3d1ccf1d72808679ccad3a'
def validate(data,read=lambda p:p.read_bytes()):
    need(sha(data)==PARENT,'부모변경');blob=read(TD/'manifest.json');need(sha(blob)==MANIFEST,'목표목록변경');m=json.loads(blob)
    for name,digest in m['source_files'].items():need(sha(read(ROOT/name))==digest,'출처변경 '+name)
    for n in REFS:
        for b in PBS:
            z=np.array(Image.open(io.BytesIO(read(TD/f'{n:03}_bank{b}_indices.png'))));need(z.shape==(384,384)and z.dtype==np.uint8 and z.max()<16,'목표색인형식');need(sha(z.tobytes())==m['targets'][str(n)][str(b)],'목표층변경')
    return m
def build(data,progress=lambda v:None):
    meta=validate(data);a=Archive(data);targets={n:{b:np.array(Image.open(TD/f'{n:03}_bank{b}_indices.png'))for b in PBS}for n in REFS};changes={b:{}for b in PBS};raws={};counts={};groups=[];gpu=0
    for ns in GROUPS:
        keys=[(n,b)for n in ns for b in PBS];nr,pp=pack_planes(bytes(4096),32,[crop(targets[n][b])for n,b in keys],set(range(1,32))-{16},[24]*len(keys));used={t for ps in pp for t,x,y,fl in ps};cnt=max(used|{0})+1;nr=resize_tile_storage(nr,32,cnt);atlas=np.frombuffer(indexed_atlas(nr,cnt)[0],np.uint8).reshape(-1,256)
        for(n,b),ps in zip(keys,pp):
            rec=b''.join(struct.pack('<BBbb',fl,t,x-80,y-80)for t,x,y,fl in ps)or struct.pack('<BBbb',0,0,-8,-8);need(0<len(rec)<=96,'파트수')
            for fl,t,x,y in struct.iter_unpack('<BBbb',rec):
                tile=atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16];need(t%16!=0 or not tile[:,0].any(),'GPU U경계');need(not(fl&128)or t//16!=0 or not tile[0].any(),'GPU V경계');gpu+=1
            changes[b][n]=rec
        for n in ns:raws[n]=nr;counts[n]=cnt
        groups.append({'refs':list(ns),'tile_count':cnt,'used_tiles':sorted(used),'raw_sha256':sha(nr),'compressed_bytes':len(encode_stream(nr)),'parts':{str(n):{str(b):len(changes[b][n])//4 for b in PBS}for n in ns}});progress(groups[-1])
    nc=a.c;slacks={};methods={}
    for b,rr in changes.items():
        try:nc,slacks[b]=repack_parts(nc,b,rr);methods[b]='existing'
        except ValueError:nc,slacks[b],methods[b]=repack_global(nc,b,rr)
    ng,gfx=repack_fixed_global(a,raws,counts);out=replace_entry(replace_entry(data,2,ng),3,nc);z=Archive(out);need(bank_offsets(nc)==bank_offsets(a.c),'조립은행변경');need(ng[:56]==a.g[:56]and ng[a.banks[0]['end']:]==a.g[a.banks[0]['end']:],'기타그래픽은행변경')
    total=nonraw=layers=kept=parts=partial=guns=0
    for gb,bank in enumerate(a.banks):
        need((bank['base'],bank['end'],len(bank['frames']))==(z.banks[gb]['base'],z.banks[gb]['end'],len(z.banks[gb]['frames'])),'그래픽경계')
        for f in bank['frames']:
            n=f['index'];selected=gb==0 and n in REFS;need(raw(z,gb,n)==(raws[n]if selected else raw(a,gb,n)),'원시불일치');total+=1;nonraw+=not selected
    for n in range(237):
        if n in(105,*range(175,183)):continue
        for b in PBS:need(np.array_equal(z.layer(n,b)[0],targets[n][b]if n in targets else a.layer(n,b)[0]),f'층불일치 {n}/{b}');layers+=1;kept+=n not in targets
        if n not in targets:continue
        need(z.composite(n,15)[0].tobytes()==Image.open(TD/f'actual_{n:03}.png').convert('RGBA').tobytes(),'실제표시불일치')
        for arm in(1,2):
            for mask in range(16):
                got=z.composite(n,mask,arm)[0];need(got.tobytes()==compose(a,targets[n],mask,arm).tobytes(),'부분표시불일치');partial+=1
                if n%2==0:
                    gd=H/'hover_ultimate_shot_inputs01';gm=np.array(Image.open(gd/f'{n:03}_barrel_mask.png'))>0;gi=np.array(Image.open(gd/f'{n:03}_barrel_indices.png'));need(np.array_equal(np.array(got)[gm],np.array(a.rgba(gi,0))[gm]),'정본총 RGBA변경');guns+=1
    for b in range(len(bank_offsets(a.c))):
        for n in range(composition_frame(a.c,b,0)['bank_frame_count']):
            if b in PBS and n in REFS:need(records(nc,b,n)==changes[b][n],'목표기록');continue
            need(records(nc,b,n)==records(a.c,b,n),'비대상기록변경');parts+=1
    return out,{'passed':True,'parent_sha256':PARENT,'candidate_sha256':sha(out),'target_manifest_sha256':MANIFEST,'refs':list(REFS),'counts':{'raw':total,'non_target_raw':nonraw,'target_layers':50,'all_layers':layers,'non_target_layers':kept,'non_target_records':parts,'partial_RGBA':partial,'canonical_barrel_RGBA':guns,'GPU_parts':gpu},'groups':groups,'part_slack':slacks,'part_methods':methods,'graphics':gfx,'all_bank_boundaries_preserved':True,'protected_entries':protected_entries(data,out),'pairs':meta['pairs'],'actual_mask':15,'old_body_copied':False,'pixel_reduction':False,'runtime_verified':False,'native_cpu_pending':True,'independent_pending':True,'root_final_art_pending':True}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='hover_ultimate_pack01');args=ap.parse_args();d=(H/args.output).resolve();need(d.is_relative_to(H.resolve())and not d.exists(),'새소유출력');d.mkdir();progress=[]
    def log(v):progress.append(v);write(d/'progress.json',progress);print(json.dumps(v),flush=True)
    try:out,proof=build(P.read_bytes(),log)
    except Exception as ex:write(d/'report.json',{'passed':False,'error':str(ex),'arc_written':False,'progress':progress});raise
    (d/'PL02_U.ARC').write_bytes(out);a=Archive(out)
    for i,ns in enumerate(GROUPS):page([(f'{n} actual mask15',a.composite(n,15)[0])for n in ns],a.composite(0,0)[0],d/f'actual_readback_{i:02}.png',cols=2,scale=6)
    for n in(221,222,229,230):page([(f'{n} diagnostic mask{m:X}',a.composite(n,m)[0])for m in range(16)],a.composite(0,0)[0],d/f'ownership_{n:03}.png',cols=4,scale=3)
    write(d/'report.json',proof);print(json.dumps({'candidate':sha(out),'counts':proof['counts'],'graphics':proof['graphics'],'part_slack':proof['part_slack']}))
if __name__=='__main__':main()
