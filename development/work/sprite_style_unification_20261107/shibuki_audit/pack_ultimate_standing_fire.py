"""Ultimate85..92 새40층과 원88 효과를 고정은행 안에서 패킹."""
from pathlib import Path
import sys,json,struct,argparse,io
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,crop
from prepare_ultimate_standing_fire_targets import P,PARENT,PBS,REFS,TD,SOURCES
from scripts.export_x_consistency import Archive,page
from scripts.prepare_shibuki_ultimate_production import repack_parts,records
from scripts.overhaul_sprites_costume_pack import pack_planes
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import bank_offsets,composition_frame,indexed_atlas
from pack_shibuki_hurt import raw,repack_fixed_global
from repack_part_records_lossless import repack as repack_global
from pack_dash_complete import protected_entries
from prepare_lowhp_final import compose
MANIFEST='f28474629281cb7e9cebc38cd48b0dfae1f175fb1cfa972238508504dd2f4654'

def validate(data,read=lambda p:p.read_bytes()):
    need(sha(data)==PARENT,'부모 불일치');blob=read(TD/'manifest.json');need(sha(blob)==MANIFEST,'목표 목록 변경');m=json.loads(blob)
    for name,digest in m['source_files'].items():need(sha(read(ROOT/name))==digest,'출처 변경 '+name)
    need(sha(read(TD/'original_PL02_U.ARC'))=='fa8accf20e35634120fd4fc59bac1f31b0fdadaf639b06a783e92189e93c8042','원US 출처 변경')
    for n in REFS:
        for b in PBS:
            v=np.array(Image.open(io.BytesIO(read(TD/f'{n:03}_bank{b}_indices.png'))))
            need(v.shape==(384,384)and v.dtype==np.uint8 and int(v.max())<16,'목표 색인형식')
            need(sha(v.tobytes())==m['targets'][str(n)][str(b)],'목표층 변경')
    expected_fx=np.zeros((384,384),np.uint8)
    for r in m['effect88']['records']:
        t=r['tile'];tile=np.array(Image.open(io.BytesIO(read(TD/f'088_effect_tile{t}.png'))))
        need(sha(tile.tobytes())==m['effect88']['tiles'][str(t)]['all256_nibble_sha256'],'효과 전체타일 변경')
        need(r['flags']==0,'효과 반전 변경');y,x=r['y']+160,r['x']+160;target=expected_fx[y:y+16,x:x+16];target[tile>0]=tile[tile>0]
    need(np.array_equal(expected_fx,np.array(Image.open(io.BytesIO(read(TD/'088_effect_indices.png'))))),'효과83 좌표 변경')
    return m

def build(data,progress=lambda x:None):
    meta=validate(data);a=Archive(data)
    targets={n:{b:np.array(Image.open(TD/f'{n:03}_bank{b}_indices.png'))for b in PBS}for n in REFS}
    for n,ll in targets.items():
        for b,v in ll.items():need(sha(v.tobytes())==meta['targets'][str(n)][str(b)],'목표층 변경')
    fx=np.array(Image.open(TD/'088_effect_indices.png'));fm=fx>0;need(fm.sum()==83,'효과83')
    for b in PBS[1:]:need(np.array_equal(targets[88][b],np.roll(targets[89][b],-1,1)),'88 공통의상 이동')
    need(np.array_equal(targets[88][0],np.where(fm,fx,np.roll(targets[89][0],-1,1))),'88 몸/효과 순서')
    changes={b:{}for b in PBS};raws={};groups=[];gpu=0
    for refs in((85,),(86,),(87,),(88,89),(90,),(91,),(92,)):
        representative=89 if len(refs)==2 else refs[0];keep={7,8}if len(refs)==2 else set();seed_atlas=np.zeros((32,256),np.uint8)
        for t in keep:
            tile=np.array(Image.open(TD/f'088_effect_tile{t}.png'));need(sha(tile.tobytes())==meta['effect88']['tiles'][str(t)]['all256_nibble_sha256'],'효과전체타일 변경')
            seed_atlas[:16,t*16:(t+1)*16]=tile
        seed=bytes((seed_atlas[:,::2]|(seed_atlas[:,1::2]<<4)).ravel())
        nr,pp=pack_planes(seed,32,[crop(targets[representative][b])for b in PBS],set(range(32))-{0,16}-keep,[24]*5)
        atlas=np.frombuffer(indexed_atlas(nr,32)[0],np.uint8).reshape(32,256)
        for t in keep:need(np.array_equal(atlas[:16,t*16:(t+1)*16],seed_atlas[:16,t*16:(t+1)*16]),'효과타일 변경')
        for n in refs:
            for b,ps in zip(PBS,pp):
                dx=-1 if n==88 else 0
                rec=b''.join(struct.pack('<BBbb',fl,t,x-80+dx,y-80)for t,x,y,fl in ps)or struct.pack('<BBbb',0,0,-8,-8)
                if n==88 and b==0:rec+=b''.join(struct.pack('<BBbb',r['flags'],r['tile'],r['x'],r['y'])for r in meta['effect88']['records'])
                need(0<len(rec)<=96,'파트 정원')
                for fl,t,x,y in struct.iter_unpack('<BBbb',rec):
                    tile=atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
                    need(t%16!=0 or not tile[:,0].any(),'GPU U 경계');need(not(fl&128)or t//16!=0 or not tile[0].any(),'GPU V 경계');gpu+=1
                changes[b][n]=rec
            raws[n]=nr
        groups.append({'refs':list(refs),'raw_sha256':sha(nr),'effect_tiles':sorted(keep),'parts':{str(n):{str(b):len(changes[b][n])//4 for b in PBS}for n in refs}});progress(groups[-1])
    nc=a.c;slacks={};methods={}
    for b,rr in changes.items():
        try:nc,slacks[b]=repack_parts(nc,b,rr);methods[b]='existing'
        except ValueError:nc,slacks[b],methods[b]=repack_global(nc,b,rr)
    progress({'parts_slack':slacks});ng,gfx=repack_fixed_global(a,raws,{n:32 for n in REFS})
    out=replace_entry(replace_entry(data,2,ng),3,nc);z=Archive(out)
    need(bank_offsets(nc)==bank_offsets(a.c),'조립경계 변경');need(ng[:56]==a.g[:56]and ng[a.banks[0]['end']:]==a.g[a.banks[0]['end']:],'기타그래픽은행 변경')
    total=nonraw=layers=kept=parts=partial=guns=effects=0
    for gb,bank in enumerate(a.banks):
        need((bank['base'],bank['end'],len(bank['frames']))==(z.banks[gb]['base'],z.banks[gb]['end'],len(z.banks[gb]['frames'])),'그래픽경계 변경')
        for f in bank['frames']:
            n=f['index'];selected=gb==0 and n in REFS;need(raw(z,gb,n)==(raws[n]if selected else raw(a,gb,n)),'원시 불일치');total+=1;nonraw+=not selected
    for n in range(237):
        if n in(105,*range(175,183)):continue
        for b in PBS:need(np.array_equal(z.layer(n,b)[0],targets[n][b]if n in targets else a.layer(n,b)[0]),f'층 불일치 {n}/{b}');layers+=1;kept+=n not in targets
        if n not in targets:continue
        for form,mask in [('before',15),('after',0)]:need(z.composite(n,mask)[0].tobytes()==Image.open(TD/f'{form}_{n:03}.png').convert('RGBA').tobytes(),'완성 표시 불일치')
        if n!=88:
            guard=np.array(Image.open(H/f'{SOURCES[n]}/{n:03}_gun_guard_mask.png'))>0;gun=np.array(Image.open(H/f'{SOURCES[n]}/{n:03}_gun_indices.png'));grgba=np.array(a.rgba(gun))
        for arm in(1,2):
            for mask in range(16):
                im=z.composite(n,mask,arm)[0];need(im.tobytes()==compose(a,targets[n],mask,arm).tobytes(),'부분 표시 불일치');partial+=1
                if n==88:need(np.array_equal(np.array(im)[fm],np.array(a.rgba(fx))[fm]),'효과83 가림');effects+=1
                else:need(np.array_equal(np.array(im)[guard],grgba[guard]),'총열/투명가드');guns+=1
    for b in range(len(bank_offsets(a.c))):
        for n in range(composition_frame(a.c,b,0)['bank_frame_count']):
            if b in PBS and n in REFS:need(records(nc,b,n)==changes[b][n],'목표기록 불일치');continue
            need(records(nc,b,n)==records(a.c,b,n),'비대상기록 변경');parts+=1
    for n in(0,119,135,141,142):
        need(raw(z,0,n)==raw(a,0,n),'공유 대기/보류 참조 변경')
        for b in PBS:need(records(nc,b,n)==records(a.c,b,n),'공유 대기/보류 조립 변경')
    return out,{'passed':True,'parent_sha256':PARENT,'candidate_sha256':sha(out),'target_manifest_sha256':MANIFEST,'refs':list(REFS),'counts':{'raw':total,'non_target_raw':nonraw,'layers':layers,'non_target_layers':kept,'non_target_records':parts,'partial_RGBA':partial,'gun_guards':guns,'effect83_checks':effects,'GPU_parts':gpu},'groups':groups,'part_slack':slacks,'part_methods':methods,'graphics':gfx,'all_bank_boundaries_preserved':True,'protected_entries':protected_entries(data,out),'effect88_policy':meta['effect88'],'reserved_current_135_exact':True,'old_body_copied':False,'pixel_reduction':False,'runtime_verified':False,'native_cpu_pending':True,'independent_pending':True,'root_final_art_pending':True}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',default='ultimate_standing_fire_pack01');args=ap.parse_args();d=(H/args.output).resolve();need(d.is_relative_to(H.resolve())and not d.exists(),'새 소유 출력');d.mkdir();progress=[]
    def log(v):progress.append(v);write(d/'progress.json',progress);print(json.dumps(v),flush=True)
    try:out,proof=build(P.read_bytes(),log)
    except Exception as ex:write(d/'report.json',{'passed':False,'error':str(ex),'arc_written':False,'progress':progress});raise
    (d/'PL02_U.ARC').write_bytes(out);a=Archive(out)
    for form,mask in [('before',15),('after',0)]:
        for i,ns in enumerate(((85,86,87),(88,89,90),(91,92))):page([(f'{n} actual {form}',a.composite(n,mask)[0])for n in ns],a.composite(0,mask)[0],d/f'{form}_readback_{i:02}.png',cols=3,scale=5)
    for n in REFS:page([(f'{n} mask{m:X}',a.composite(n,m)[0])for m in range(16)],a.composite(0,0)[0],d/f'partial_{n:03}.png',cols=4,scale=4)
    write(d/'report.json',proof);print(json.dumps({'candidate':sha(out),'counts':proof['counts'],'graphics':proof['graphics']}))
if __name__=='__main__':main()
