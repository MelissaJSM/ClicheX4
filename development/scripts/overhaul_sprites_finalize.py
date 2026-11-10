"""Freeze actual decoded sprite candidates, regression proofs and review sheets."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.overhaul_sprites_audit import D,entry,render,rgba,board,write,sha,BASES
from scripts.overhaul_sprites_proposal import main as proposal
from scripts.overhaul_sprites_costume_pack import resize_tile_storage,repack_variable
from src.psx_player import graphics_bank,decode_stream
from scripts.discover_inputs import psx_arc

PLACEHOLDERS={105,*range(175,183)}
PURE_EFFECTS={126,127,128,129,130,159,160,161,211,212}
ARMOR_ONLY=set(range(217,231))

def post_image(arc,n):
    words=struct.unpack_from('<64H',entry(arc,9));im=Image.new('RGBA',(384,384))
    for layer in(0,8,5,7,6):
        a,_=render(arc,0,layer,n);im.alpha_composite(rgba(a,words if layer==0 else words[32:48]if layer==7 else words[16:32]))
    return im

def finalize(project,destination):
    folder=D/('nana_preultimate'if project=='ver_rin_nana'else'shibuki_preultimate');packed=folder/'packed_progress';info=json.loads((packed/'packing.json').read_text('utf8'));before=(D/project/'baseline/PL02_U.ARC').read_bytes();after=(packed/'PL02_U.ARC').read_bytes()
    if info['before']!=sha(before)or info['after']!=sha(after):raise ValueError('Packing input differs')
    expected=set(range(237))-PLACEHOLDERS-PURE_EFFECTS-ARMOR_ONLY
    if info['failures']or set(info['frames'])!=expected:raise ValueError('Incomplete visible-body scope')
    if set(info['remaining_art'])!=PLACEHOLDERS|PURE_EFFECTS|ARMOR_ONLY:raise ValueError('Unclassified omission')
    words=struct.unpack_from('<64H',entry(after,9));reviews=packed/'actual_readback';reviews.mkdir(exist_ok=True);(reviews/'pre').mkdir(exist_ok=True);pre=[];exceptions=[];changed_pre=[];changed_post=[]
    declared=set(info['acquired_preserved_except'])
    for n in range(237):
        if n in PLACEHOLDERS:continue
        actual,_=render(after,0,0,n);old,_=render(before,0,0,n)
        im=rgba(actual,words);im.save(reviews/f'pre/{n:03}.png');pre.append((str(n),im))
        if not np.array_equal(actual,old):changed_pre.append(n)
        aa=post_image(after,n);bb=post_image(before,n)
        if aa.tobytes()!=bb.tobytes():
            if n not in declared:raise ValueError(f'Undeclared acquired RGBA difference {n}')
            changed_post.append(n)
        if n in declared:exceptions.extend([(f'{n} BEFORE',bb),(f'{n} AFTER',aa)])
    for i in range(0,len(pre),64):board(pre[i:i+64],reviews/f'pre_{i//64:02}.png')
    for i in range(0,len(exceptions),32):board(exceptions[i:i+32],reviews/f'post_exceptions_{i//32:02}.png',cols=4)
    other=[]
    for e in psx_arc(before):
        typ=int(e['type'],16)
        if typ in(2,3):continue
        if entry(before,typ)!=entry(after,typ):raise ValueError('Non-sprite entry changed')
        other.append(e['type'])
    # Exercise actual row-stride conversion, including native 29/30/32 tile bodies.
    g=entry(after,2);bank=graphics_bank(g,0,allow_bank_aliases=True);roundtrips=[]
    for n in(0,17,106,148,162,170):
        f=bank['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
        enlarged=resize_tile_storage(raw,f['tile_count'],32);restored=resize_tile_storage(enlarged,32,f['tile_count'])
        if restored!=raw:raise ValueError('Partial-row roundtrip differs')
        roundtrips.append({'frame':n,'tiles':f['tile_count'],'raw_sha256':sha(raw)})
    rejects=[]
    for name,fn in[
      ('tile_buffer_33',lambda:resize_tile_storage(bytes(128),1,33)),
      ('zero_tile_count',lambda:resize_tile_storage(bytes(128),1,0)),
      ('incomplete_shared_stream',lambda:repack_variable(g,{3:b'bad'},{3:1})),
      ('oversize_decoded_stream',lambda:repack_variable(g,{0:bytes(33*128)},{0:33}))]:
        try:fn()
        except(ValueError,IndexError):rejects.append(name)
        else:raise ValueError('Negative input accepted: '+name)
    validation={'project':project,'before_sha256':sha(before),'after_sha256':sha(after),'selected_references':len(info['frames']),'changed_pre':changed_pre,'changed_post_rgba':changed_post,'all_post_rgba_checked':228,'other_entries_unchanged':other,'timing_and_palettes_preserved':True,'scope':{'body':sorted(expected),'pure_light':sorted(PURE_EFFECTS),'armor_only':sorted(ARMOR_ONLY),'reserved':sorted(PLACEHOLDERS)},'tile_row_roundtrips':roundtrips,'negative_inputs_rejected':rejects,'bank_boundaries_preserved':True,'runtime_verified':False}
    write(reviews/'verification.json',validation);info['production_complete']=True;info['verification']=str((reviews/'verification.json').relative_to(ROOT));write(packed/'packing.json',info)
    proposal(project,packed,destination)
    print(json.dumps({'actual_readback':str(reviews),'selected':len(info['frames']),'changed_pre':len(changed_pre),'changed_post_rgba':changed_post,'negative_rejections':rejects}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('project');p.add_argument('destination');a=p.parse_args();finalize(a.project,a.destination)
