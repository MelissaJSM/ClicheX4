"""새 Ultimate 대시20참조를 원래 은행 경계/32타일에 무손실 등록."""
from pathlib import Path
import sys,json,struct,argparse
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,crop
from prepare_ultimate_dash_targets import P,PARENT
from scripts.export_x_consistency import Archive,page,DRAW_ORDER
from scripts.prepare_shibuki_ultimate_production import records,repack_parts
from scripts.overhaul_sprites_costume_pack import repack_variable
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import bank_offsets,decode_stream,composition_frame,indexed_atlas
from pack_air_targets_probe import pack_pinned
from pack_dash_complete import protected_entries
LOCK='5a3059100769463f18fc065e6b92d8176ce126e16424dc88bc496da219a84ca7'
PARTS=(0,5,6,7,8)
D=H/'ultimate_dash_complete_targets01'

def validate_inputs(data,read):
    need(sha(data)==PARENT,'Parent hash mismatch');raw=read('ultimate_dash_complete_targets01/LOCK.json');need(sha(raw)==LOCK,'Target lock changed');lock=json.loads(raw);raw=read('ultimate_dash_complete_targets01/targets.json');need(sha(raw)==lock['target_manifest_sha256'],'Manifest changed')
    for p,v in lock['files'].items():need(sha(read('ultimate_dash_complete_targets01/'+p))==v,'Target changed '+p)
    for p,v in lock['sources'].items():need(sha(read(p))==v,'Source changed '+p)
    return json.loads(raw)

def build(data,read=lambda p:(H/p).read_bytes()):
    meta=validate_inputs(data,read);a=Archive(data);targets={r['ref']:{b:np.array(Image.open(D/f'{r["ref"]:03}_bank{b}_indices.png'))for b in PARTS}for r in meta['rows']};changes={b:{}for b in PARTS};raws={};reports=[]
    orig=Archive((ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/original.arc').read_bytes());need(sha(orig.data)=='92b2a3209ad6603cf519616dc580400434271f87e8e7129495430c04d0d1c35a','Original changed')
    f=orig.banks[0]['frames'][73];oraw=decode_stream(orig.g,f['offset'],f['limit'],f['tile_count']*128).data;tile=np.frombuffer(indexed_atlas(oraw,f['tile_count'])[0],np.uint8).reshape(-1,256)[:16,96:112].copy();need(sha(tile.tobytes())=='00fd53e3ddd31a3e9c7e3ad76ac50d167def46121cb490fa3e5f6238a5faaaf1','Original tile changed');tail={n:records(orig.c,0,n)[-36:]for n in(73,74)};groups={}
    for n in targets:groups.setdefault(a.banks[0]['frames'][n]['offset'],[]).append(n)
    for offset,refs in sorted(groups.items()):
        refs=sorted(refs);allrefs=[f['index']for f in a.banks[0]['frames']if f['offset']==offset];need(set(refs)==set(allrefs),'Sharing escapes targets');raw=bytes(4096);pool=set(range(1,32));pinned=73 in refs
        if pinned:
            atlas=np.frombuffer(indexed_atlas(raw,32)[0],np.uint8).reshape(32,256).copy();atlas[:16,96:112]=tile;raw=bytes((atlas[:,0::2]|(atlas[:,1::2]<<4)).ravel());pool.remove(6)
        order=[(n,b)for n in refs for b in PARTS if targets[n][b].any()and not(b==0 and n in(73,74))];images=[crop(targets[n][b])for n,b in order];nr,rr,method=pack_pinned(raw,images,pool)
        for n in refs:
            for b in PARTS:changes[b][n]=struct.pack('<BBbb',0,0,-8,-8)
        for(n,b),parts in zip(order,rr):changes[b][n]=b''.join(struct.pack('<BBbb',fl,t,x-80,y-80)for t,x,y,fl in parts)
        for n,bn in((73,71),(74,72)):
            if n in refs:changes[0][n]=changes[0][bn]+tail[n]
        atlas=np.frombuffer(indexed_atlas(nr,32)[0],np.uint8).reshape(32,256);need(not atlas[:,0].any(),'GPU U boundary')
        for n in refs:
            raws[n]=nr
            for b in PARTS:
                r=changes[b][n];need(len(r)//4<=24,'Part count overflow')
                for i in range(0,len(r),4):
                    fl,t,x,y=struct.unpack('<BBbb',r[i:i+4]);need(t<32,'Tile overflow')
                    if fl&128 and t//16==0:need(not atlas[0,t%16*16:t%16*16+16].any(),'GPU V boundary')
        reports.append({'refs':refs,'mode':method,'original9_streak_records':pinned,'parts':{str(n):{str(b):len(changes[b][n])//4 for b in PARTS}for n in refs},'used_tiles':sorted({r[1]for n in refs for b in PARTS for r in struct.iter_unpack('<BBbb',changes[b][n])})})
    nc=a.c;slack={}
    for b,rr in changes.items():nc,slack[b]=repack_parts(nc,b,rr)
    ng,graphics=repack_variable(a.g,raws,{n:32 for n in raws});new=replace_entry(replace_entry(data,2,ng),3,nc);actual=Archive(new);need(bank_offsets(nc)==bank_offsets(a.c),'Composition boundary moved');layers=0
    for n,ll in targets.items():
        for b,want in ll.items():need(np.array_equal(actual.layer(n,b)[0],want),f'Layer readback mismatch {n}/{b}');layers+=1
    rawtotal=otherraw=0
    for bi,oldbank in enumerate(a.banks):
        newbank=actual.banks[bi];need((oldbank['base'],oldbank['end'],len(oldbank['frames']))==(newbank['base'],newbank['end'],len(newbank['frames'])),'Graphics boundary moved')
        for f,ff in zip(oldbank['frames'],newbank['frames']):
            r=decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128).data;s=decode_stream(actual.g,ff['offset'],ff['limit'],ff['tile_count']*128).data;rawtotal+=1
            if bi==0 and f['index']in raws:need(s==raws[f['index']],'Target raw mismatch')
            else:need(r==s,'Non-target raw changed');otherraw+=1
    otherparts=0
    for b in range(len(bank_offsets(a.c))):
        for n in range(composition_frame(a.c,b,0)['bank_frame_count']):
            if b in changes and n in targets:continue
            need(records(a.c,b,n)==records(actual.c,b,n),'Non-target composition changed');otherparts+=1
    keptlayers=partschecks=gunchecks=0
    for n in range(237):
        if n in(105,*range(175,183)):continue
        for b in PARTS:
            if n not in targets:need(np.array_equal(actual.layer(n,b)[0],a.layer(n,b)[0]),'Non-target layer changed');keptlayers+=1
        if n not in targets:continue
        for arm in(1,2):
            for mask in range(16):
                im=a.rgba(targets[n][0],0)
                for bit,b in DRAW_ORDER:
                    if mask&bit:im.alpha_composite(a.rgba(targets[n][b],32 if b==7 and arm==2 else 16))
                out=actual.composite(n,mask,arm)[0];need(im.tobytes()==out.tobytes(),f'Partial mismatch {n}/{mask}/{arm}');partschecks+=1
                if n in(68,70,72,76,78,80,82,84):
                    gd=H/'ultimate_dash_barrel_guard01';gm=np.array(Image.open(gd/f'{n:03}_mask.png'))>0;gi=np.array(Image.open(gd/f'{n:03}_indices.png'));need(np.array_equal(np.array(out)[gm],np.array(a.rgba(gi,0))[gm]),'Canonical gun RGBA changed');gunchecks+=1
        for form,mask in(('before',15),('after',0)):
            expected=np.array(Image.open(D/f'{form}_{n:03}_indices.png'));need(actual.composite(n,mask)[0].tobytes()==a.rgba(expected,16 if mask else 0).tobytes(),'Full costume differs')
    for n in(73,74):need(records(actual.c,0,n)[-36:]==tail[n],'Original effect record changed')
    entries=protected_entries(data,new)
    return new,{'passed':True,'before':PARENT,'after':sha(new),'target_lock':LOCK,'selected_refs':sorted(targets),'groups':reports,'part_slack':slack,'graphics':graphics,'raw_references':rawtotal,'non_target_raw':otherraw,'target_layers_exact':layers,'non_target_layers':keptlayers,'non_target_parts':otherparts,'partial_composites':partschecks,'canonical_gun_composites':gunchecks,'preserved_entries':entries,'original_speedline_tile_sha256':sha(tile.tobytes()),'original_speedline_parts':18,'original_speedline_pixels_per_ref':54,'old_art_overwrite':False,'pixel_loss':False,'native_cpu_verified':False,'gameplay_verified':False,'root_visual_review':False}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',default='ultimate_dash_pack_probe01');z=ap.parse_args();o=(H/z.out).resolve();need(o.is_relative_to(H.resolve())and not o.exists(),'Fresh own output');o.mkdir()
    try:new,proof=build(P.read_bytes())
    except ValueError as e:write(o/'report.json',{'passed':False,'reason':str(e)});raise
    (o/'PL02_U.ARC').write_bytes(new);actual=Archive(new)
    for form,mask in(('before',15),('after',0)):
        pics=[(f'{form} actual {n}',actual.composite(n,mask)[0])for n in proof['selected_refs']]
        for n in proof['selected_refs']:actual.composite(n,mask)[0].save(o/f'{form}_{n:03}.png')
        for j in range(0,len(pics),6):page(pics[j:j+6],actual.composite(0,mask)[0],o/f'{form}_readback_{j//6:02}.png',cols=3,scale=4)
    write(o/'report.json',proof);print(json.dumps({k:proof[k]for k in('after','part_slack','target_layers_exact','non_target_raw','partial_composites')}))
if __name__=='__main__':main()
