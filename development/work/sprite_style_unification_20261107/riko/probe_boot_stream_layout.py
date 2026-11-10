"""Find a pixel-exact layout saving without touching unconsumed/support tiles."""
from pathlib import Path
import sys, json, hashlib, itertools
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parent
ROOT=R.parents[2]
sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry
from scripts.prepare_shibuki_ultimate_production import records
from src.psx_player import graphics_bank,decode_stream,indexed_atlas,composition_frame,compose_indices
from src.psx_compress import encode_stream
sys.path.insert(0,str(R.parent/"zero_audit"))
from pack_rin_keys import packer

P=R/'prepared_ground_boots_v4/PL01_U.ARC'
arc=P.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(arc)=='540658ec80aa24415d1df97e37dac0c1a28898907cc8778ba5fa037224e87eb2'
reg=json.loads((R/'ground_remaining22/targets02/registration.json').read_text('utf8'))
targets={(q['bank'],q['ref']):np.array(Image.open(ROOT/q['target'])) for q in reg['frames']}
g,c=entry(arc,2),entry(arc,3);bank=graphics_bank(g,1);logs=[]
output=R/'boot_stream_layout.json'
assert not output.exists()

def canvas(raw,count,cp):
    pix,size,bb,_=compose_indices(raw,count,cp)
    result=np.zeros((384,384),np.uint8)
    result[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]=np.frombuffer(pix,np.uint8).reshape(size[1],size[0])
    return result

for ref in(130,87,95,101):
    f=bank['frames'][ref];count=f['tile_count']
    ns=[v['index'] for v in bank['frames'] if v['offset']==f['offset']]
    old=decode_stream(g,f['offset'],f['limit'],count*128).data
    cps={n:composition_frame(c,5,n) for n in ns}
    wants={n:targets.get((1,n),canvas(old,count,cps[n])) for n in ns}
    edits=[]
    for n in ns:
        _,size,bb,_=compose_indices(old,count,cps[n]);t=wants[n][160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]
        edits.append((cps[n],t.tobytes(),size))
    joint=packer.edit_visible_set(old,count,edits)
    fixed={p['tile'] for n in ns if (1,n) not in targets for p in cps[n]['parts']}
    owned={p['tile'] for n in ns if (1,n) in targets for p in cps[n]['parts']}
    pool=sorted(owned-fixed-{0,16})
    pixels,locations,_=indexed_atlas(joint,count);atlas=np.frombuffer(pixels,np.uint8).reshape(-1,256)
    tiles={t:atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16].copy() for t in range(count)}
    size0=len(encode_stream(joint));attempts=0
    operations=[('flip',a,None) for a in pool]+[('swap',a,b) for a,b in itertools.combinations(pool,2)]
    for kind,a,b in operations:
        if kind=='swap' and np.array_equal(tiles[a],tiles[b]):continue
        replacements={a:tiles[a][:,::-1]} if kind=='flip' else {a:tiles[b],b:tiles[a]}
        out=bytearray(joint)
        for t,patch in replacements.items():
            for y in range(16):
                for x in range(16):
                    pos,shift=locations[(t//16*16+y)*256+t%16*16+x]
                    out[pos]=(out[pos]&~(15<<shift))|int(patch[y,x])<<shift
        out=bytes(out);size1=len(encode_stream(out));attempts+=1
        if size1>size0-4:continue
        recs={}
        for n in ns:
            rec=bytearray(records(c,5,n));cp={**cps[n],'parts':[dict(p) for p in cps[n]['parts']]}
            for i,p in enumerate(cp['parts']):
                if kind=='flip' and p['tile']==a:
                    rec[4*i]^=64;p['flip_x']=not p['flip_x']
                elif kind=='swap' and p['tile'] in(a,b):
                    p['tile']=b if p['tile']==a else a;rec[4*i+1]=p['tile']
            assert np.array_equal(canvas(out,count,cp),wants[n])
            if (1,n) not in targets:assert rec==records(c,5,n)
            recs[n]=bytes(rec)
        aa=np.frombuffer(indexed_atlas(out,count)[0],np.uint8).reshape(-1,256)
        for t in set(range(count))-set(replacements):
            assert np.array_equal(aa[t//16*16:t//16*16+16,t%16*16:t%16*16+16],tiles[t])
        proof={'type':'lossless_consumed_tile_'+kind,'tiles':[a] if b is None else [a,b],
               'frames':ns,'raw_before_sha256':sha(old),'joint_sha256':sha(joint),
               'code_before':size0,'code_after':size1,'saved_bytes':size0-size1,
               'support_and_unconsumed_tiles_exact':True,'boundary_tiles_exact':[0,16],
               'all_display_pixels_exact':True,'attempts':attempts}
        output.write_text(json.dumps({'parent_sha256':sha(arc),'raw':out.hex(),
            'records':{str(n):v.hex() for n,v in recs.items()},'proof':proof},indent=2)+'\n','utf8')
        print(json.dumps(proof));sys.exit(0)
    logs.append({'reference':ref,'attempts':attempts,'pool':pool,'code_bytes':size0})
    print(json.dumps(logs[-1]),flush=True)
(R/'boot_stream_layout_rejected.json').write_text(json.dumps(logs,indent=2)+'\n','utf8')
raise RuntimeError('No pixel-exact saving found')
