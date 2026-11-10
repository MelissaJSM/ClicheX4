"""Independent native decoding, scope and reproducibility checks for logos."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.inventory_cliche_logo import D,PARENT_HASH,SOURCE_HASH,REFERENCE_HASH,load,indexed
from scripts.prepare_cliche_logo import TITLE_FRAMES,background_indices
from scripts.prepare_riko_ui import entry
from scripts.project import digest
from scripts.discover_inputs import sha256,psx_arc
from src.psx_ui_atlas import aliased_composition,local_composition,tile_pixels
from src.psx_static_effect import compose_static
from src.psx_ui_render import render_static_rgba

SCOPE={'ST0E_U0.ARC':{0x10002,0x12},'LOAD_U.ARC':{0x10008},'ST0E_U1.ARC':{0x10000},'ST0F_UX.ARC':{0x10000},'ST0F_UZ.ARC':{0x10000}}

def verify(candidate,repro):
    for p in (candidate,repro):
        if not p.resolve().is_relative_to(D.resolve()):raise ValueError('Wrong task directory')
    rr,old=load();r=json.loads((candidate/'recipe.json').read_text())
    if r['kind']!='cliche_logo' or r['parent_sha256']!=PARENT_HASH or r['source_sha256']!=SOURCE_HASH or r['reference_sha256']!=REFERENCE_HASH or set(r['files'])!=set(SCOPE):raise ValueError('Invalid recipe scope or identity')
    if r['generated_sha256']!=digest(D/'cliche_word_generated.png'):raise ValueError('Artwork differs')
    new={};entries=0;gpu_parts=0;protected_frames=0;protected_bg=0
    layout=lambda b:[(e['type'],e['offset'],e['size']) for e in psx_arc(b)]
    for name,allowed in SCOPE.items():
        data=(candidate/name).read_bytes();m=r['files'][name]
        if len(data)!=len(old[name]) or sha256(old[name])!=m['before'] or sha256(data)!=m['after'] or data!=(repro/name).read_bytes() or rr[name]!=r['records'][name]:raise ValueError('Resource hash/size/reproduction differs')
        if layout(data)!=layout(old[name]):raise ValueError('Resource layout moved')
        for e in psx_arc(data):
            k=int(e['type'],16)
            if k not in allowed:
                if entry(data,k)!=entry(old[name],k):raise ValueError('Protected resource changed')
                entries+=1
        new[name]=data
    name='ST0E_U0.ARC';g=entry(old[name],0x10002);ng=entry(new[name],0x10002);p=struct.pack('<I',4)+entry(old[name],0x12);np1=struct.pack('<I',4)+entry(new[name],0x12)
    pal=entry(old['COL0E_U0.ARC'],5)
    count=aliased_composition(p,0,0)['bank_frame_count'];starts=[]
    for n in range(count):
        c=aliased_composition(p,0,n);nc=aliased_composition(np1,0,n)
        a,sz,bb,_=compose_static(g,local_composition(c));b,nsz,nb,_=compose_static(ng,local_composition(nc))
        if sz!=nsz or bb!=nb or len(c['parts'])!=len(nc['parts']):raise ValueError('Title anchor/part count moved')
        if n in TITLE_FRAMES:
            arr=np.load(candidate/f'title_{n}.npy')
            if b!=arr.tobytes():raise ValueError('Title replacement did not roundtrip')
            if any(x['clut']!=y['clut'] or x['flip_x']!=y['flip_x'] or x['flip_y']!=y['flip_y'] for x,y in zip(c['parts'],nc['parts'])):raise ValueError('Title GPU flags changed')
            starts.extend(range(q['record_offset'],q['record_offset']+4) for q in c['parts'])
        else:
            if c!=nc or a!=b:raise ValueError('Title non-logo frame changed')
            protected_frames+=1
        for q in nc['parts']:
            if q['page']*256+q['tile']>=len(ng)//128:raise ValueError('GPU tile out of bounds')
            gpu_parts+=1
    allowed={i for span in starts for i in span}
    if any(x!=y and i not in allowed for i,(x,y) in enumerate(zip(p,np1))):raise ValueError('Title animation/header changed')
    # Save/load: hard-coded UV rectangles plus all unaffected bank-2 frames.
    g=entry(old['LOAD_U.ARC'],0x10008);ng=entry(new['LOAD_U.ARC'],0x10008);a=indexed(g);b=indexed(ng);mask=np.zeros_like(a,bool);mask[112:144,:80]=True;mask[208:256,:112]=True
    if not np.array_equal(a[~mask],b[~mask]) or b[:16,:16].shape!=(16,16):raise ValueError('Other menu texture changed')
    if not np.array_equal(b[112:144,:80],np.load(candidate/'loading_word.npy')) or not np.array_equal(b[208:256,:112],np.load(candidate/'save_pattern.npy')):raise ValueError('Menu logo differs')
    if np.any(b[112:128,:16]):raise ValueError('Loading blank corner lost')
    p=old['MOJIPAT.ARC']
    for n in range(53):
        c=aliased_composition(p,2,n);aa=compose_static(g,local_composition(c))[:3];bb=compose_static(ng,local_composition(c))[:3]
        if n==1:
            if bb[0]!=np.load(candidate/'loading_word.npy').tobytes():raise ValueError('Loading frame1 mismatch')
        elif n!=25:
            if aa!=bb:raise ValueError(f'Protected menu frame {n} changed')
            protected_frames+=1
        gpu_parts+=len(c['parts'])
    for name in ('ST0E_U1.ARC','ST0F_UX.ARC','ST0F_UZ.ARC'):
        arr,_=background_indices(new[name])
        if not np.array_equal(arr,np.load(candidate/f'{name}_background.npy')):raise ValueError('Background render differs')
        a=entry(old[name],0x10000);b=entry(new[name],0x10000);mp=np.frombuffer(entry(old[name],0),'<u2');info=np.frombuffer(entry(old[name],1),'<u4')
        changed={i for i in range(len(a)//128) if tile_pixels(a,i)!=tile_pixels(b,i)}
        target={int(info[int(v)&16383])>>16&4095 for v in mp[256:768] if v&16383}
        if not changed<=target:raise ValueError('Non-pattern tiles changed')
        for v in np.r_[mp[:256],mp[768:]]:
            t=int(info[int(v)&16383])>>16&4095
            if tile_pixels(a,t)!=tile_pixels(b,t):raise ValueError('Other illustration/background tile changed')
            protected_bg+=1
    result={'passed':True,'reproduced_resources':5,'protected_entries':entries,'protected_frames':protected_frames,'protected_background_cells':protected_bg,'gpu_parts_checked':gpu_parts,'title_replacement_frames':9,'exe_palettes_maps_timing_unchanged':True,'runtime_verified':False}
    (candidate/'verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result));return r

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--repro',type=Path,required=True);a=p.parse_args();verify(a.candidate,a.repro)
