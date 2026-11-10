"""Independent pilot roundtrip, layer, palette and non-target regressions."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.analyze_shibuki_ultimate import load,D
from scripts.prepare_riko_ui import entry
from scripts.discover_inputs import psx_arc,sha256
from scripts.prepare_shibuki_ultimate_idle import FRAMES
from src.psx_player import bank_offsets,graphics_bank,decode_stream,composition_frame,indexed_atlas
from src.psx_sprite_batch import canvas_from_parts
from src.psx_ui_atlas import local_composition

def verify(candidate,repro):
    _,sources=load();old=sources['parent']['PL02_U.ARC'];base=sources['parent']['PL00_U.ARC'];new=(candidate/'PL02_U.ARC').read_bytes();r=json.loads((candidate/'recipe.json').read_text())
    if new!=(repro/'PL02_U.ARC').read_bytes() or len(new)!=len(old) or sha256(new)!=r['modified_arc_sha256']:raise ValueError('Reproduction/hash/length mismatch')
    if [{k:v for k,v in e.items() if k!='sha256'} for e in psx_arc(old)]!=[{k:v for k,v in e.items() if k!='sha256'} for e in psx_arc(new)]:raise ValueError('ARC directory changed')
    checks={'reproducible_arc':True,'non_target_entries':0,'protected_compositions':0,'decoded_graphic_references':0,'base_roundtrips':0,'armor_roundtrips':0,'full_layer_direction_combinations':0,'gpu_part_edges':0,'protected_palette_rows':0}
    for e in psx_arc(old):
        k=int(e['type'],16)
        if k not in (2,3,9):
            if entry(old,k)!=entry(new,k):raise ValueError('Inherited UI/text/sound entry altered')
            checks['non_target_entries']+=1
    og,ng,oc,nc,op,npal,bg,bc,bp=[entry(a,k) for a,k in ((old,2),(new,2),(old,3),(new,3),(old,9),(new,9),(base,2),(base,3),(base,9))]
    for bi,o in enumerate(bank_offsets(oc)):
        for n in range(struct.unpack_from('<I',oc,o)[0]>>16):
            if bi in (0,5) and n in FRAMES:continue
            if composition_frame(oc,bi,n)!=composition_frame(nc,bi,n):raise ValueError('Non-target composition changed')
            checks['protected_compositions']+=1
    for bi in range(len(bank_offsets(og,allow_aliases=True))):
        ob=graphics_bank(og,bi,allow_bank_aliases=True);nb=graphics_bank(ng,bi,allow_bank_aliases=True)
        if ob!=nb:raise ValueError('Graphics locations/counts changed')
        for f in ob['frames']:
            a=decode_stream(og,f['offset'],f['limit'],f['tile_count']*128).data;b=decode_stream(ng,f['offset'],f['limit'],f['tile_count']*128).data
            if not (bi==0 and f['index'] in FRAMES) and a!=b:raise ValueError('Non-target bitmap changed')
            checks['decoded_graphic_references']+=1
    frames={};ob=graphics_bank(ng,0,allow_bank_aliases=True);bb=graphics_bank(bg,0,allow_bank_aliases=True)
    for n in FRAMES:
        f=ob['frames'][n];bf=bb['frames'][n];raw=decode_stream(ng,f['offset'],f['limit'],f['tile_count']*128).data;br=decode_stream(bg,bf['offset'],bf['limit'],bf['tile_count']*128).data
        base0=canvas_from_parts(br,bf['tile_count'],composition_frame(bc,0,n));base1=canvas_from_parts(raw,f['tile_count'],composition_frame(nc,0,n));armor=canvas_from_parts(raw,f['tile_count'],composition_frame(nc,5,n))
        if not np.array_equal(base0,base1):raise ValueError('Pre-capsule accepted base changed')
        if not np.array_equal(armor,np.array(Image.open(candidate/f'overlay_{n:03}.png'))):raise ValueError('Armor bitmap mismatch')
        checks['base_roundtrips']+=1;checks['armor_roundtrips']+=1
        full=np.where(armor,armor,base1);want=np.array(Image.open(candidate/f'ultimate_{n:03}.png'))
        if not np.array_equal(full,want):raise ValueError('Composite outfit differs')
        y,x=np.nonzero(full);floor=int(y.max());feet=np.nonzero(full[floor-2:floor+1])[1]
        if floor!=102 or abs((int(feet.min())+int(feet.max()))/2-79)>.5:raise ValueError('Sole/foot anchor changed')
        exposed=(base1>0)&(armor==0)
        if np.count_nonzero(exposed)!=9:raise ValueError('Unexpected underlying costume exposed')
        for color in np.unique(base1[exposed]):
            if bp[int(color)*2:int(color)*2+2]!=npal[32+int(color)*2:34+int(color)*2]:raise ValueError('Eye colors do not match')
        atlas,_,_=indexed_atlas(raw,f['tile_count'])
        for bi in (0,5,6,7,8):
            for q in composition_frame(nc,bi,n)['parts']:
                t=q['tile'];pixels=np.array([list(atlas[(t//16*16+iy)*256+t%16*16:(t//16*16+iy)*256+t%16*16+16]) for iy in range(16)])
                if t%16==0 and any(pixels[:,0]):raise ValueError('Opaque U boundary clips under world mirror')
                if q['flip_y'] and (t//16)%16==0 and any(pixels[0]):raise ValueError('Opaque V boundary under flip')
                checks['gpu_part_edges']+=1
        for mask in range(16):
            composite=base1.copy()
            for bit,bi in ((8,8),(1,5),(4,7),(2,6)):
                if mask&bit:
                    layer=canvas_from_parts(raw,f['tile_count'],local_composition(composition_frame(nc,bi,n)));composite=np.where(layer,layer,composite)
            expected=want if mask&1 else base1
            for mirror in (False,True):
                if not np.array_equal(composite[:,::-1] if mirror else composite,expected[:,::-1] if mirror else expected):raise ValueError('Layer combination differs')
                checks['full_layer_direction_combinations']+=1
        frames[n]=full
    # A breathing cycle must move the connected body, retain the feet, and blink.
    if np.array_equal(frames[0],frames[115]) or np.array_equal(frames[0],frames[119]) or np.array_equal(frames[115],frames[116]):raise ValueError('Missing breathing or blinking')
    allowed=set(r['body_palette_rows'])|set(r['armor_palette_rows'])
    for row in range(len(op)//32):
        if row not in allowed:
            if op[row*32:(row+1)*32]!=npal[row*32:(row+1)*32]:raise ValueError('Effect palette changed')
            checks['protected_palette_rows']+=1
    checks.update({'passed':True,'runtime_verified':False,'frame_scope':list(FRAMES),'armor_head_bit_controls_full_outfit_in_pilot':True,'archive_sha256':sha256(new)})
    (candidate/'regression.json').write_text(json.dumps(checks,indent=2));print(json.dumps(checks));return checks

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--repro',type=Path,required=True);a=p.parse_args();verify(a.candidate,a.repro)
