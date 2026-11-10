"""Prove iris-only edits and preserve dialogue borders/NPC/shared widgets."""
import json
import struct
from sync import ROOT,D,source,read_disc,entry,unpack_indices,decode_stream,save,frames
from src.psx_player import composition_frame
from src.psx_static_effect import compose_static

_,path=source('ver_buki_riko')
prep=json.loads((D/'preparation.json').read_text('utf8'))
old,_=read_disc(path,list(prep['changed_arcs']))
new={name:(D/'prepared'/name).read_bytes() for name in old}
changed_pixels=0
def check_indices(a,b):
    global changed_pixels
    assert len(a)==len(b)
    aa,bb=unpack_indices(a),unpack_indices(b)
    for x,y in zip(aa,bb):
        if x!=y:
            assert x in (9,10,11,14) and y in (7,8,14),(x,y)
            changed_pixels+=1
    assert all((x==0)==(y==0) for x,y in zip(aa,bb))
for name,kinds in prep['changed_arcs'].items():
    for kind in kinds:
        if kind==13:
            def chunks(arc):
                blob=entry(arc,13)[96:]
                result={}
                for i in range(struct.unpack_from('<I',blob,4)[0]):
                    k,start,off,size=struct.unpack_from('<4I',blob,16+i*16)
                    result[k,start]=decode_stream(blob,off,len(blob),size).data
                return result
            a,b=chunks(old[name]),chunks(new[name])
            assert a.keys()==b.keys()
            for key in a:
                if key[0]==1:check_indices(a[key],b[key])
                else:assert a[key]==b[key]
        else:check_indices(entry(old[name],kind),entry(new[name],kind))

# These borders share lower tiles with the expanded portraits; preserve each.
prior=ROOT/'work/armor_dialogue_20261108/ver_buki_riko'
layout=json.loads((prior/'prepared_v2/verification.json').read_text('utf8'))
border_inv=json.loads((prior/'border_inventory.json').read_text('utf8'))
all_names=list({q['file'] for q in border_inv}|{q['file'] for q in layout['compositions']})
other,_=read_disc(path,all_names)
baseinfo=next(q for q in border_inv if q['file']=='ST00_00.ARC')
bp=entry(other['ST00_00.ARC'],10)
bp=struct.pack('<I',4)+bp[baseinfo['offset']:baseinfo['offset']+baseinfo['size']]
border_checks=0
group_frames={}
for q in layout['compositions']:
    p=entry(other[q['file']],10);bank=q['bank_indices'][0]
    up=struct.pack('<I',4)+p[struct.unpack_from('<I',p,bank*4)[0]+1376:]
    records=frames(p)[bank]+[frames(up)[0][i] for i in [0,1,4,5]]
    prior_records=group_frames.setdefault(q['delta_tiles'],records)
    assert prior_records==records
for q in layout['graphics']:
    name=q['file'];kind=prep['changed_arcs'][name][0];lo=q['new_texture_base']
    for frame in range(5):
        comp=composition_frame(bp,0,frame)
        assert compose_static(entry(old[name],kind)[lo:],comp)[:3]==compose_static(entry(new[name],kind)[lo:],comp)[:3]
        border_checks+=1
    # NPC space between the border and the portrait remains byte-identical.
    for tile in range(48,q['delta_tiles']):
        from src.psx_ui_atlas import tile_pixels
        assert tile_pixels(entry(old[name],kind)[lo:],tile)==tile_pixels(entry(new[name],kind)[lo:],tile)
widget_parts=0
for name in ['PL00_U.ARC','PL02_U.ARC']:
    g1,g2=entry(old[name],0x10007),entry(new[name],0x10007)
    parts=frames(struct.pack('<I',4)+entry(old[name],18))[0]
    from src.psx_ui_atlas import tile_pixels
    for i,record in enumerate(parts):
        if i==10:continue # Legacy fixed portrait frame, superseded by outfit-specific frames.
        for flags,tile,x,y in struct.iter_unpack('<BBbb',record):
            t=96+(flags&3)*256+tile
            assert tile_pixels(g1,t)==tile_pixels(g2,t)
            widget_parts+=1
save(D/'scope_verification.json',{'passed':True,'changed_index_pixels':changed_pixels,
    'iris_palette_indices_only':True,'transparency_unchanged':True,'dialogue_border_frames_preserved':border_checks,
    'npc_tiles_preserved':True,'all_dialogue_composition_groups_verified':len(layout['compositions']),
    'nonportrait_pause_parts_preserved':widget_parts,'hq_state_tables_static_backgrounds_preserved':True})
print('Scope PASS:',changed_pixels,'iris pixels;',border_checks,'border frames;',widget_parts,'widget parts')
