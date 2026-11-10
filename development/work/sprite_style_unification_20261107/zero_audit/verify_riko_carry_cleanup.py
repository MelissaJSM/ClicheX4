"""Independently model GPU row uploads; no producer/atlas mapping calls."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent
from scripts.prepare_riko_ui import entry,replace_entry
from src.psx_player import graphics_bank,decode_stream,composition_frame
from scripts.overhaul_sprites_audit import render
sha=lambda b:hashlib.sha256(b).hexdigest()
P=ROOT/'work/sprite_style_unification_20261107/riko/prepared_head_spaces_v1/PL01_U.ARC'
Q=D/'riko_restore/hidden_cleanup_v2/PL01_U.ARC'
a=P.read_bytes();b=Q.read_bytes()
assert sha(a)=='488b679ed027fd8916e0f48716c9e3fa65d03ff42d4ac21d38dffb6ed0a7edaf'
assert sha(b)=='349c83306897a5d92d6de1f894ec11a860e2c67f290e633c886a8ea18ae0c5ca'
g,ng,c=entry(a,2),entry(b,2),entry(a,3)
assert replace_entry(b,2,g)==a
mask=np.zeros((32,256),bool)
for n in range(42,50):
    for part in composition_frame(c,5,n)['parts']:
        assert part['page']==0 and part['tile']<32
        y,x=part['tile']//16*16,part['tile']%16*16;mask[y:y+16,x:x+16]=True

def upload(vram,raw,count):
    """Same rectangular copy geometry as the native upload queue."""
    offset=0
    for first in range(0,count,16):
        width=min(16,count-first)*16;nbytes=width*16//2
        packed=np.frombuffer(raw[offset:offset+nbytes],np.uint8)
        pixels=np.empty(packed.size*2,np.uint8);pixels[::2]=packed&15;pixels[1::2]=packed>>4
        y=(first//16)*16;vram[y:y+16,:width]=pixels.reshape(16,width);offset+=nbytes
    assert offset==len(raw)

ob,nb=graphics_bank(g,1),graphics_bank(ng,1);partial={};changed=[];sequence_count=0;rows=[]
for n in range(42,50):
    of,nf=ob['frames'][n],nb['frames'][n]
    raw=decode_stream(g,of['offset'],of['limit'],of['tile_count']*128).data
    assert raw==decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data and of['tile_count']==nf['tile_count']==1
    partial[n]=raw
for of,nf in zip(ob['frames'],nb['frames']):
    n=of['index'];count=of['tile_count'];assert count==nf['tile_count']
    ar=decode_stream(g,of['offset'],of['limit'],count*128).data;br=decode_stream(ng,nf['offset'],nf['limit'],count*128).data
    va=(np.arange(8192,dtype=np.uint16).reshape(32,256)%16).astype(np.uint8);vb=va.copy()
    upload(va,ar,count);upload(vb,br,count)
    assert np.array_equal(va[mask],vb[mask]),f'Previous upload differs on carried coordinates: {n}'
    for k,raw in partial.items():
        ca,cb=va.copy(),vb.copy();upload(ca,raw,1);upload(cb,raw,1)
        assert np.array_equal(ca[mask],cb[mask]),f'Partial transition differs: {n}->{k}';sequence_count+=1
    if ar!=br:
        assert np.all((va==vb)|(vb==0));changed.append(n)
    rows.append({'prior_ref':n,'tiles':count,'native_upload_widths_pixels':[min(16,count-first)*16 for first in range(0,count,16)],'all8_partial_reads_exact':True})
display=0
for gb in(0,1):
    for f in graphics_bank(g,gb)['frames']:
        n=f['index']
        if gb==1 and 42<=n<=49:continue
        assert np.array_equal(render(a,gb,gb*5,n)[0],render(b,gb,gb*5,n)[0]);display+=1
assert display==436 and sequence_count==1520
report={'passed':True,'source_sha256':sha(a),'candidate_sha256':sha(b),'direct_gpu_upload_model':True,'producer_or_indexed_atlas_mapping_called':False,'all190_prior_uploads_x8_partial_frames':sequence_count,'partial_vram_read_pixels':int(mask.sum()),'changed_raw_refs':changed,'all436_normal_displays_exact':True,'composition_palette_other_entries_exact':True,'rows':rows,'scope':'비표시 데이터 정리 단계만 검증한다. 새 의상으로 바뀌는 표시 픽셀까지 원형 보존이라고 주장하지 않는다.','runtime_verified':False}
(Q.parent/'independent_carry.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'prior_uploads':len(rows),'partial_sequences':sequence_count,'changed_raw_refs':len(changed),'candidate_sha256':sha(b)}))
