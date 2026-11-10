"""독립 망토 타일은 그대로 두고 새 몸체를 같은 타일에 공동 등록한다."""
import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];W=ROOT/'work/sprite_style_unification_20261107'
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(W/'zero_audit'))
import pack_riko_cloth as engine
BODY={12,13,14,15,28,29,30,31}

def setup(arc,reg):
    g,c=engine.native.entry(arc,2),engine.native.entry(arc,3)
    original=(W/'riko/prepared_head_spaces_v1/PL01_U.ARC').read_bytes()
    art=W/'riko/vehicle_clothes09/registered01'
    masters={17:engine.native.render(arc,1,5,17)[0]}
    for k in [25,33,41]:masters[k]=np.array(Image.open(art/f'b1_{k:03}_indices.png'))
    group_data={};by_ref={r['ref']:r for r in reg['frames']}
    for key,start,end in [(17,14,22),(25,22,30),(33,30,38),(41,38,42)]:
        source=original if key==17 else arc
        sg,sc=engine.native.entry(source,2),engine.native.entry(source,3)
        desc=engine.native.graphics_bank(sg,1)['frames'][key]
        raw=engine.native.decode_stream(sg,desc['offset'],desc['limit'],desc['tile_count']*128).data
        cp=engine.native.composition_frame(sc,5,key);cp['parts']=[p for p in cp['parts'] if p['tile']in BODY]
        pixels,size,bb,_=engine.native.compose_indices(raw,32,cp)
        small=np.frombuffer(pixels,np.uint8).reshape(size[1],size[0]);body=np.zeros((384,384),np.uint8)
        body[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]=small
        record=by_ref[start];x0,y0,x1,y1=record['body_registration_clear_mask_bounds']
        clear=np.zeros_like(body,bool);clear[y0:y1,x0:x1]=body[y0:y1,x0:x1]==0
        target=masters[key].copy();target[clear]=0
        count=min(sum(p['tile']in BODY for p in engine.native.composition_frame(c,5,n)['parts']) for n in range(start,end) if n in by_ref)
        nr,rr=engine.motion.identical(raw,32,target,BODY,count)
        group_data[key]=(nr,rr)
    def pack(c,b,n,raw,count,target):
        if b!=1 or n not in by_ref:return raw,engine.records(c,b*5,n),dict(type='preserved_shared_support')
        row=by_ref[n];nr,rr=group_data[row['master']];dx,dy=row['translation'];cp=engine.native.composition_frame(c,5,n)
        cape=[c[p['record_offset']:p['record_offset']+4]for p in cp['parts'] if p['tile']not in BODY]
        records=cape+[bytes([0,t,(x+dx-160)&255,(y+dy-160)&255])for t,x,y in rr]
        assert len(records)<=len(cp['parts'])
        while len(records)<len(cp['parts']):records.append(records[-1])
        return nr,b''.join(records),dict(type='shared_body_original_cape',master=row['master'],body_tiles=sorted(BODY),body_part_count=len(rr),cape_part_count=len(cape))
    return pack
