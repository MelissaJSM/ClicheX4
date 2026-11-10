"""사다리14를 원PL02 은행 경계/32타일 내 무손실 패킹하는 검토 후보."""
from pathlib import Path
import sys,json,struct,argparse
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,crop
from prepare_ultimate_ladder_targets import P,PARENT,REFS
from scripts.export_x_consistency import Archive,page,DRAW_ORDER
from scripts.prepare_shibuki_ultimate_production import records,repack_parts
from scripts.overhaul_sprites_costume_pack import repack_variable
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import bank_offsets,decode_stream,composition_frame,indexed_atlas
from pack_air_targets_probe import pack_pinned
from pack_dash_complete import protected_entries
D=H/'ultimate_ladder_complete_targets01';LOCK='05318a68afb484c6dbe782ca12ddaee7ebe2d01a49e6a79b40a6e44e76ad2599';PARTS=(0,5,6,7,8)
def validate(data,read=None):
    read=read or (lambda p:(H/p).read_bytes());rel=D.relative_to(H).as_posix()
    need(sha(data)==PARENT,'Wrong parent');blob=read(rel+'/LOCK.json');need(sha(blob)==LOCK,'Target lock changed');lk=json.loads(blob);need(sha(read(rel+'/targets.json'))==lk['target_manifest_sha256'],'Manifest changed')
    for p,h in lk['files'].items():need(sha(read(rel+'/'+p))==h,'Target changed '+p)
    for p,h in lk['sources'].items():need(sha(read(p))==h,'Source changed '+p)
def build(data):
    validate(data);a=Archive(data);targets={n:{b:np.array(Image.open(D/f'{n:03}_bank{b}_indices.png'))for b in PARTS}for n in REFS};changes={b:{}for b in PARTS};raws={};reports=[];groups={}
    for n in REFS:groups.setdefault(a.banks[0]['frames'][n]['offset'],[]).append(n)
    for offset,refs in sorted(groups.items()):
        refs=sorted(refs);allrefs=[f['index']for f in a.banks[0]['frames']if f['offset']==offset];need(set(refs)==set(allrefs),'Shared outside target');order=[(n,b)for n in refs for b in PARTS if targets[n][b].any()];nr,rr,method=pack_pinned(bytes(4096),[crop(targets[n][b])for n,b in order],set(range(1,32)))
        for n in refs:
            for b in PARTS:changes[b][n]=struct.pack('<BBbb',0,0,-8,-8)
        for(n,b),parts in zip(order,rr):changes[b][n]=b''.join(struct.pack('<BBbb',fl,t,x-80,y-80)for t,x,y,fl in parts)
        atlas=np.frombuffer(indexed_atlas(nr,32)[0],np.uint8).reshape(32,256);need(not atlas[:,0].any(),'U first-column boundary')
        for n in refs:
            raws[n]=nr
            for b in PARTS:
                need(len(changes[b][n])//4<=24,'Parts overflow')
                for fl,t,x,y in struct.iter_unpack('<BBbb',changes[b][n]):
                    need(t<32,'Tile overflow')
                    if fl&128 and t//16==0:need(not atlas[0,t%16*16:t%16*16+16].any(),'V first-row boundary')
        reports.append({'refs':refs,'packing':method,'used_tiles':sorted({r[1]for n in refs for b in PARTS for r in struct.iter_unpack('<BBbb',changes[b][n])}),'part_counts':{str(n):{str(b):len(changes[b][n])//4 for b in PARTS}for n in refs}})
    nc=a.c;slack={}
    for b,rr in changes.items():nc,slack[b]=repack_parts(nc,b,rr)
    ng,graphics=repack_variable(a.g,raws,{n:32 for n in raws});new=replace_entry(replace_entry(data,2,ng),3,nc);actual=Archive(new);need(bank_offsets(nc)==bank_offsets(a.c),'Composition boundaries moved');layers=0
    for n,ll in targets.items():
        for b,v in ll.items():need(np.array_equal(actual.layer(n,b)[0],v),f'Target layer {n}/{b}');layers+=1
    total=otherraw=0
    for bi,bank in enumerate(a.banks):
        nb=actual.banks[bi];need((bank['base'],bank['end'],len(bank['frames']))==(nb['base'],nb['end'],len(nb['frames'])),'Graphics boundaries moved')
        for f,ff in zip(bank['frames'],nb['frames']):
            r=decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128).data;s=decode_stream(actual.g,ff['offset'],ff['limit'],ff['tile_count']*128).data;total+=1
            if bi==0 and f['index']in raws:need(s==raws[f['index']],'Target raw differs')
            else:need(r==s,'Non-target raw changed');otherraw+=1
    parts=0
    for b in range(len(bank_offsets(a.c))):
        for n in range(composition_frame(a.c,b,0)['bank_frame_count']):
            if b in changes and n in REFS:continue
            need(records(a.c,b,n)==records(actual.c,b,n),'Non-target records changed');parts+=1
    kept=partial=guns=0
    for n in range(237):
        if n in(105,*range(175,183)):continue
        for b in PARTS:
            if n not in REFS:need(np.array_equal(actual.layer(n,b)[0],a.layer(n,b)[0]),'Non-target layer changed');kept+=1
        if n not in REFS:continue
        for arm in(1,2):
            for mask in range(16):
                im=a.rgba(targets[n][0],0)
                for bit,b in DRAW_ORDER:
                    if mask&bit:im.alpha_composite(a.rgba(targets[n][b],32 if b==7 and arm==2 else 16))
                got=actual.composite(n,mask,arm)[0];need(got.tobytes()==im.tobytes(),'Partial differs');partial+=1
                if n in(150,155):
                    gd=H/'ultimate_ladder_shot_inputs01';gm=np.array(Image.open(gd/f'{n:03}_barrel_mask.png'))>0;gi=np.array(Image.open(gd/f'{n:03}_barrel_indices.png'));need(np.array_equal(np.array(got)[gm],np.array(a.rgba(gi,0))[gm]),'Gun RGBA changed');guns+=1
        for form,mask,pal in [('before',15,16),('after',0,0)]:want=np.array(Image.open(D/f'{form}_{n:03}_indices.png'));need(actual.composite(n,mask)[0].tobytes()==a.rgba(want,pal).tobytes(),'Full costume differs')
    return new,{'passed':True,'before':PARENT,'after':sha(new),'target_lock':LOCK,'selected_refs':list(REFS),'groups':reports,'part_slack':slack,'graphics':graphics,'raw_references':total,'non_target_raw':otherraw,'target_layers_exact':layers,'non_target_layers':kept,'non_target_parts':parts,'partial_composites':partial,'canonical_gun_composites':guns,'preserved_entries':protected_entries(data,new),'pixel_loss':False,'native_cpu_verified':False,'runtime_verified':False,'independent_pending':True,'root_final_art_review_pending':True,'foot_contact_caveat':'일부새발 외곽최하단이1..2px높은차이는검토중. 원좌표/몸체축소없으나정확사다리접점실기를주장하지않음.','frame155_policy':'현재수용기본형의149공통몸체+반동팔 정책. 원US155의허리/발반동전체복원이아님.'}
def main():
    p=argparse.ArgumentParser();p.add_argument('--out',default='ultimate_ladder_pack01');args=p.parse_args();o=(H/args.out).resolve();need(o.is_relative_to(H.resolve())and not o.exists(),'Fresh own output');o.mkdir()
    try:new,proof=build(P.read_bytes())
    except ValueError as e:write(o/'report.json',{'passed':False,'reason':str(e)});raise
    (o/'PL02_U.ARC').write_bytes(new);a=Archive(new)
    for form,mask in [('before',15),('after',0)]:
        pics=[]
        for n in REFS:im=a.composite(n,mask)[0];im.save(o/f'{form}_{n:03}.png');pics.append((f'{n} actual {form}',im))
        for i in range(0,len(pics),6):page(pics[i:i+6],a.composite(0,mask)[0],o/f'{form}_readback_{i//6:02}.png',cols=3,scale=4)
    write(o/'report.json',proof);print(json.dumps({k:proof[k]for k in('after','part_slack','graphics','raw_references','non_target_raw','target_layers_exact','partial_composites')}))
if __name__=='__main__':main()
