"""Verify the complete emblem, palette-layer union and protected native assets."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.inventory_cliche_logo import D,PARENT_HASH,SOURCE_HASH,REFERENCE_HASH,load,indexed
from scripts.prepare_cliche_logo_v2 import TITLE_TARGETS,old_records,full_art
from scripts.prepare_cliche_logo import background_indices
from scripts.prepare_riko_ui import entry
from scripts.project import digest
from scripts.discover_inputs import sha256,psx_arc
from src.psx_ui_atlas import aliased_composition,local_composition,tile_pixels
from src.psx_static_effect import compose_static

SCOPE={'ST0E_U0.ARC':{0x10002,0x12},'MOJIPAT.ARC':None,'LOAD_U.ARC':{0x10008},'ST0E_U1.ARC':{0x10000},'ST0F_UX.ARC':{0x10000},'ST0F_UZ.ARC':{0x10000}}

def verify(candidate,repro):
    for p in (candidate,repro):
        if not p.resolve().is_relative_to(D.resolve()):raise ValueError('Wrong task directory')
    rr,old=load();r=json.loads((candidate/'recipe.json').read_text())
    if r['kind']!='cliche_logo_v2' or r['parent_sha256']!=PARENT_HASH or r['source_sha256']!=SOURCE_HASH or r['reference_sha256']!=REFERENCE_HASH or set(r['files'])!=set(SCOPE):raise ValueError('Invalid recipe scope or identity')
    if r['generated_sha256']!=digest(D/'cliche_full_generated.png'):raise ValueError('Artwork differs')
    new={};entries=0;gpu=0;protected_frames=0;protected_bg=0
    layout=lambda b:[(e['type'],e['offset'],e['size']) for e in psx_arc(b)]
    for name,allowed in SCOPE.items():
        data=(candidate/name).read_bytes();m=r['files'][name]
        if len(data)!=len(old[name]) or sha256(old[name])!=m['before'] or sha256(data)!=m['after'] or data!=(repro/name).read_bytes() or rr[name]!=r['records'][name]:raise ValueError('Resource hash/size/reproduction differs')
        new[name]=data
        if allowed is None:continue
        if layout(data)!=layout(old[name]):raise ValueError('Resource layout moved')
        for e in psx_arc(data):
            k=int(e['type'],16)
            if k not in allowed:
                if entry(data,k)!=entry(old[name],k):raise ValueError('Protected resource changed')
                entries+=1
    name='ST0E_U0.ARC';g=entry(old[name],0x10002);ng=entry(new[name],0x10002);p=struct.pack('<I',4)+entry(old[name],0x12);np1=struct.pack('<I',4)+entry(new[name],0x12)
    for n in range(35):
        c=aliased_composition(p,0,n);nc=aliased_composition(np1,0,n)
        a=compose_static(g,local_composition(c))[:3];b,sz,bb,_=compose_static(ng,local_composition(nc))
        if n in TITLE_TARGETS:
            arr=np.load(candidate/f'title_{n}.npy');meta=r['checks']['title_targets'][str(n)];origin=meta['origin'];reconstructed=np.zeros_like(arr)
            x,y=bb[0]-origin[0],bb[1]-origin[1]
            if x<0 or y<0 or x+sz[0]>arr.shape[1] or y+sz[1]>arr.shape[0]:raise ValueError('Title part outside declared canvas')
            reconstructed[y:y+sz[1],x:x+sz[0]]=np.frombuffer(b,np.uint8).reshape(sz[1],sz[0])
            if not np.array_equal(arr,reconstructed):raise ValueError(f'Title {n} roundtrip differs')
        else:
            if old_records(p,0)[n]!=old_records(np1,0)[n] or a!=(b,sz,bb):raise ValueError('Non-logo frame changed')
            protected_frames+=1
        for q in nc['parts']:
            if q['page']*256+q['tile']>=len(ng)//128:raise ValueError('GPU tile outside atlas')
            gpu+=1
    # Check every opaque master pixel survives the two palette layers, with
    # exact same world-space origin after accounting for the two object anchors.
    blue=np.load(candidate/'title_0.npy');gold=np.load(candidate/'title_1.npy');expected=np.array(full_art().resize((240,64),Image.Resampling.LANCZOS))[:,:,3]>=128
    if np.any((blue>0)&(gold>0)) or not np.array_equal((blue>0)|(gold>0),expected):raise ValueError('Title layer seam or missing master pixel')
    if tuple(np.array(r['checks']['title_targets']['0']['origin'])+[144,72])!=tuple(np.array(r['checks']['title_targets']['1']['origin'])+[160,72]):raise ValueError('Title world anchors differ')
    p=old['MOJIPAT.ARC'];np1=new['MOJIPAT.ARC'];s=struct.unpack_from('<4I',p)
    if p[:s[2]]!=np1[:s[2]] or p[s[3]:]!=np1[s[3]:]:raise ValueError('Non-logo menu bank or palette changed')
    g=entry(old['LOAD_U.ARC'],0x10008);ng=entry(new['LOAD_U.ARC'],0x10008);a=indexed(g);b=indexed(ng);mask=np.zeros_like(a,bool);mask[112:144,:144]=True;mask[208:256,:112]=True
    if not np.array_equal(a[~mask],b[~mask]):raise ValueError('Other menu pixels changed')
    for n in range(53):
        c=aliased_composition(p,2,n);nc=aliased_composition(np1,2,n);aa=compose_static(g,local_composition(c))[:3];bb=compose_static(ng,local_composition(nc))[:3]
        if n in (1,2):
            expected=np.load(candidate/('loading_left.npy' if n==1 else 'loading_right.npy'))
            if bb[0]!=expected.tobytes() or aa[1:]!=bb[1:]:raise ValueError('Small logo reconstruction/anchor differs')
        elif n!=25:
            if aa!=bb:raise ValueError(f'Protected menu frame {n} changed')
            for x,y in zip(c['parts'],nc['parts']):
                if any(x[k]!=y[k] for k in ('flags','x','y')):raise ValueError('Protected menu geometry/CLUT changed')
            protected_frames+=1
        gpu+=len(nc['parts'])
    if not np.array_equal(b[208:256,:112],np.load(candidate/'save_pattern.npy')):raise ValueError('Save logo differs')
    left=np.load(candidate/'loading_left.npy');right=np.load(candidate/'loading_right.npy');union=np.zeros((32,112),bool);union[:,:80]|=left>0;union[:,48:]|=right>0
    if not np.array_equal(union,np.array(full_art().resize((112,32),Image.Resampling.LANCZOS))[:,:,3]>=128):raise ValueError('Small logo missing pixel')
    for name in ('ST0E_U1.ARC','ST0F_UX.ARC','ST0F_UZ.ARC'):
        arr,_=background_indices(new[name])
        if not np.array_equal(arr,np.load(candidate/f'{name}_background.npy')):raise ValueError('Background render differs')
        a=entry(old[name],0x10000);b=entry(new[name],0x10000);mp=np.frombuffer(entry(old[name],0),'<u2');info=np.frombuffer(entry(old[name],1),'<u4')
        changed={i for i in range(len(a)//128) if tile_pixels(a,i)!=tile_pixels(b,i)};target={int(info[int(v)&16383])>>16&4095 for v in mp[256:768] if v&16383}
        if not changed<=target:raise ValueError('Non-pattern tiles changed')
        for v in np.r_[mp[:256],mp[768:]]:
            t=int(info[int(v)&16383])>>16&4095
            if tile_pixels(a,t)!=tile_pixels(b,t):raise ValueError('Other illustration/background tile changed')
            protected_bg+=1
    result={'passed':True,'reproduced_resources':6,'protected_entries':entries,'protected_frames':protected_frames,'protected_background_cells':protected_bg,'gpu_parts_checked':gpu,'title_replacement_frames':len(TITLE_TARGETS),'complete_logo_alpha_reconstructed':True,'exe_palettes_maps_timing_unchanged':True,'runtime_verified':False}
    (candidate/'verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result));return r

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--repro',type=Path,required=True);a=p.parse_args();verify(a.candidate,a.repro)
