"""Move native sampling windows without translating, trimming or scaling artwork."""
from collections import defaultdict
import numpy as np
from src.psx_player import composition_frame,compose_indices,indexed_atlas
from src.psx_frame_edit import frame_coverage

def fit_windows(parts,n,raw,tiles,target,editor,parts_bank=0):
    original=parts
    atlas,locs,_=indexed_atlas(raw,tiles)
    arr=np.frombuffer(atlas,np.uint8).reshape(-1,256)
    def check(data,require_edit=False):
        cp=composition_frame(data,parts_bank,n)
        cov,size,bb=frame_coverage(raw,tiles,cp)
        forbidden=set()
        for p in cp['parts']:
            t=p['tile'];oy,ox=t//16*16,t%16*16
            if t%16==0:
                forbidden.update(locs[(oy+y)*256+ox]for y in range(16))
            if p['flip_y']and t//16%16==0:
                forbidden.update(locs[oy*256+ox+x]for x in range(16))
        safe=np.zeros((384,384),bool)
        safe[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]=np.array([any(s not in forbidden or(raw[s[0]]>>s[1])&15 for s in sources)for sources in cov]).reshape(size[1],size[0])
        bad=int(np.count_nonzero((target>0)&~safe))
        if bad==0 and require_edit:
            crop=target[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]
            try:editor(raw,tiles,[(cp,crop.tobytes(),size)])
            except ValueError:return 9999,safe
        return bad,safe
    bad,safe=check(parts,True)
    if not bad:return parts,[]
    for iteration in range(8):
        cp=composition_frame(parts,parts_bank,n);rows=defaultdict(list);candidates=[]
        for p in cp['parts']:rows[p['y']].append(p)
        # Preserve whole rows first, but do not move unnecessary empty slots.
        for row,ps in rows.items():
            for dx in range(-8,9):
                if not dx:continue
                trial=bytearray(parts)
                for p in ps:trial[p['record_offset']+2]=(p['x']+dx)&255
                score,_=check(trial,True)
                if score<bad:candidates.append(((score,len(ps)*abs(dx),0,row),bytes(trial)))
        missing=np.argwhere((target>0)&~safe)
        for p in cp['parts']:
            t=p['tile'];oy,ox=t//16*16,t%16*16;empty=not arr[oy:oy+16,ox:ox+16].any()
            dxs=range(-3,4)if not empty else sorted(set(int(x)-160-p['x']-k for y,x in missing for k in(0,1,8,15)))
            dys=range(-3,4)if not empty else sorted(set(int(y)-160-p['y']-k for y,x in missing for k in(0,1,8,15)))
            for dx in dxs:
                for dy in dys:
                    if not(dx or dy)or not(-128<=p['x']+dx<=127 and -128<=p['y']+dy<=127):continue
                    trial=bytearray(parts);trial[p['record_offset']+2]=(p['x']+dx)&255;trial[p['record_offset']+3]=(p['y']+dy)&255
                    score,_=check(trial,True)
                    if score<bad:candidates.append(((score,abs(dx)+abs(dy),abs(dy),p['record_offset']),bytes(trial)))
        if not candidates:raise ValueError(f'No lossless fixed-tile window solution for {n}: {bad} pixels')
        _,parts=min(candidates,key=lambda q:q[0]);bad,safe=check(parts,True)
        if not bad:break
    if bad:raise ValueError(f'Uncovered authored pixels {n}: {bad}')
    # Remove incidental row changes that are not necessary for this target.
    for p in composition_frame(original,parts_bank,n)['parts']:
        off=p['record_offset']
        if parts[off+2:off+4]==original[off+2:off+4]:continue
        trial=bytearray(parts);trial[off+2:off+4]=original[off+2:off+4]
        if check(trial,True)[0]==0:parts=bytes(trial)
    edits=[]
    for p,q in zip(composition_frame(original,parts_bank,n)['parts'],composition_frame(parts,parts_bank,n)['parts']):
        if(p['x'],p['y'])!=(q['x'],q['y']):edits.append({'ref':n,'record_offset':p['record_offset'],'tile':p['tile'],'before':[p['x'],p['y']],'after':[q['x'],q['y']]})
    return parts,edits
