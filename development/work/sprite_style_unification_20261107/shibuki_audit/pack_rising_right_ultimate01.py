"""라이징파이어 전후 새 원화 7참조의 고정 경계 네이티브 패킹 후보."""
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
from native_pose_pack import need,sha,write,crop,lossless_pack,same_rgba
from pack_air_targets_probe import pack_pinned
REFS=(103,104)
PARENT_SHA='71d02fe6d965c1fb42cc786766bad62372c792ccd8ecf6d5bc1e40dc8deb8597'
LOCK_SHA='430d144bf4c5cdff29412b32fdacddefd52b1f816f3db4bb78f7b6400066119f'
def validate_inputs(data,d,read=lambda p:p.read_bytes()):
    need(sha(data)==PARENT_SHA,'Wrong exact parent');raw=read(d/'LOCK.json');need(sha(raw)==LOCK_SHA,'Wrong source lock');lock=json.loads(raw)
    for name,digest in lock['files'].items():need(sha(read(d/name))==digest,'Changed target: '+name)
    for name,digest in lock['source_files'].items():need(sha(read(H/name))==digest,'Changed source: '+name)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='rising_right_ultimate_pack01');args=ap.parse_args();o=(H/args.out).resolve()
    need(o.is_relative_to(H.resolve())and o!=H.resolve(),'Output outside work');need(not o.exists(),'Fresh output required')
    data=(H/'prepared_rising_fire_ultimate01/PL02_U.ARC').read_bytes();a=Archive(data);d=H/'rising_right_ultimate_shared02';validate_inputs(data,d)
    images={(n,form):np.array(Image.open(d/f'{form}_{231 if n==232 else n:03}_indices.png'))for n in REFS for form in('before','after')}
    targets={};raws={};changes={0:{},5:{}};groups=[]
    for n in REFS:
        before=images[n,'before'];after=images[n,'after'];need(not np.any((after>0)&(before==0)),'Overlay cannot erase base')
        targets[n,0]=after;targets[n,5]=np.where(same_rgba(a,before,after),0,before).astype(np.uint8)
        for b in(6,7,8):need(not a.layer(n,b)[0].any(),'Unexpected nonblank extra armor layer')
    for n in REFS:
        if n==232:continue
        aliases=[f['index']for f in a.banks[0]['frames']if f['offset']==a.banks[0]['frames'][n]['offset']];need(aliases==[n],'Unexpected native raw alias')
        refs=[n,232]if n==231 else[n]
        blanks={p['tile']for ref in refs for pb in(6,7,8)for p in composition_frame(a.c,pb,ref)['parts']}
        raw,parts,method=pack_pinned(bytes(4096),[crop(targets[n,b])for b in(0,5)],set(range(1,32))-blanks)
        for ref in refs:
            raws[ref]=raw
            for b,rr in zip((0,5),parts):changes[b][ref]=b''.join(struct.pack('<BBbb',fl,t,x-80,y-80+(ref==232))for t,x,y,fl in rr)
        groups.append({'refs':refs,'method':method,'preserved_empty_extra_layer_tiles':sorted(blanks),'parts':{str(b):len(rr)for b,rr in zip((0,5),parts)}})
    nc=a.c;slack={}
    for b,rr in changes.items():nc,slack[b]=repack_parts(nc,b,rr)
    ng,gmeta=repack_variable(a.g,raws,{n:32 for n in REFS});out=replace_entry(replace_entry(data,2,ng),3,nc);b=Archive(out)
    need(bank_offsets(a.c)==bank_offsets(b.c),'Composition boundary moved');need(a.p==b.p,'Palette changed');rawcount=nonraw=nonparts=layers=display=gp=0
    for gb,bb in enumerate(a.banks):
        nb=b.banks[gb];need((bb['base'],bb['end'],len(bb['frames']))==(nb['base'],nb['end'],len(nb['frames'])),'Graphics boundaries moved')
        for f,q in zip(bb['frames'],nb['frames']):
            old=decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128).data;new=decode_stream(b.g,q['offset'],q['limit'],q['tile_count']*128).data;rawcount+=1
            if gb==0 and f['index']in REFS:need(new==raws[f['index']],'Target raw differs')
            else:need(new==old,'Nontarget raw differs');nonraw+=1
    for pb in range(len(bank_offsets(a.c))):
        for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
            if(n,pb)in targets:continue
            need(records(a.c,pb,n)==records(b.c,pb,n),'Nontarget composition differs');nonparts+=1
    for n in range(237):
        if n in{105,*range(175,183)}:continue
        for pb in(0,5,6,7,8):
            expected=targets[n,pb]if(n,pb)in targets else a.layer(n,pb)[0]
            need(np.array_equal(b.layer(n,pb)[0],expected),f'Layer mismatch {n}/{pb} ({int(np.count_nonzero(b.layer(n,pb)[0]!=expected))} pixels)');layers+=1
        for form,mask in(('before',15),('after',0)):
            expected=a.rgba(images[n,form],16 if mask else 0)if n in REFS else a.composite(n,mask)[0]
            need(b.composite(n,mask)[0].tobytes()==expected.tobytes(),'Costume display differs');display+=1
        if n not in REFS:continue
        atlas=np.frombuffer(indexed_atlas(raws[n],32)[0],np.uint8).reshape(32,256)
        for pb in(0,5):
            for part in composition_frame(b.c,pb,n)['parts']:
                gp+=1;t=part['tile'];tile=atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
                if t%16==0:need(not tile[:,0].any(),'GPU U hazard')
                if part['flip_y']:need(not tile[0].any(),'GPU V hazard')
    allowed=np.zeros(len(data),bool)
    for e in psx_arc(data):
        if int(e['type'],16)in(2,3):allowed[e['offset']:e['offset']+e['size']]=True
    need(len(data)==len(out),'ARC size changed');need(not np.any((np.frombuffer(data,np.uint8)!=np.frombuffer(out,np.uint8))&~allowed),'Outside target entries changed')
    o.mkdir();(o/'PL02_U.ARC').write_bytes(out)
    for form,mask in(('before',15),('after',0)):
        pics=[]
        for n in REFS:
            im=b.composite(n,mask)[0];im.save(o/f'{form}_{n:03}.png');pics.extend([(f'{n} parent',a.composite(n,mask)[0]),(f'{n} actual packed',im)])
        for i in range(0,len(pics),6):page(pics[i:i+6],a.composite(0,mask)[0],o/f'{form}_readback_{i//6:02}.png',cols=2,scale=5)
    write(o/'report.json',{'passed':True,'parent_sha256':sha(data),'candidate_sha256':sha(out),'target_refs':list(REFS),'source_index_files':{p.name:sha(p.read_bytes())for p in sorted(d.glob('*_indices.png'))},'raw_checked':rawcount,'non_target_raw_exact':nonraw,'non_target_parts_exact':nonparts,'layers_checked':layers,'costume_displays_checked':display,'new_costume_displays':4,'gpu_parts_checked':gp,'parts_slack':slack,'graphics':gmeta,'pack_groups':groups,'outside_entries_exact':True,'all_palettes_audio_timing_exact':True,'pixel_loss':False,'derived232':'unchanged from frozen parent','runtime_verified':False,'root_review_pending':True,'independent_pending':True})
    print(json.dumps({'sha':sha(out),'slack':slack,'raw':rawcount,'nonraw':nonraw,'displays':display,'parts':nonparts,'groups':groups}))
if __name__=='__main__':main()
