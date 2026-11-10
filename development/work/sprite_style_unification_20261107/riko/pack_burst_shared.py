"""낙봉파 네 참조를 같은18타일 자원에 묶어 원화 품질을 보존한다."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];W=ROOT/'work/sprite_style_unification_20261107';Z=W/'zero_audit'
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(Z))
import pack_riko_cloth as review
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_shibuki_ultimate_production import repack_parts,records
from scripts.overhaul_sprites_audit import render
from src.psx_player import graphics_bank,decode_stream,indexed_atlas,composition_frame,bank_offsets
from src.psx_compress import encode_stream
sha=lambda b:hashlib.sha256(b).hexdigest()
P=W/'riko/prepared_ceremony_v2/PL01_U.ARC';PSHA='590ed75799910795db7f237688bbd10ef3a282a7d12910956d798f497e67f818'
D=W/'riko/burst_cape_variants01/native02';OUT=W/'riko/prepared_burst_variants_v2'
reg=json.loads((D/'registration.json').read_text('utf8'));expected={}
for r in reg['frames']:
    p=ROOT/r['target'];assert sha(p.read_bytes())==r['sha256'];expected[r['ref']]=np.array(Image.open(p))
expected[184]=expected[182].copy()

def build(arc,art):
    if sha(arc)!=PSHA:raise ValueError('Unsupported parent')
    if set(art)!=set(expected) or any(not np.array_equal(art[n],expected[n]) for n in art):raise ValueError('Art differs from registered source')
    targets={**art,183:render(arc,1,5,183)[0]}
    g,c=entry(arc,2),entry(arc,3);bank=graphics_bank(g,1);f=bank['frames'][182]
    raw=decode_stream(g,f['offset'],f['limit'],18*128).data
    _,locations,_=indexed_atlas(raw,18)
    coords=list(dict.fromkeys((p['x']+160,p['y']+160) for p in composition_frame(c,5,183)['parts']))
    assert len(coords)==7
    joined=bytearray(raw);tiles={};recs={}
    for n in sorted(targets):
        rr=[]
        for x,y in coords:
            pixels=targets[n][y:y+16,x:x+16];key=pixels.tobytes()
            if key not in tiles:
                t=len(tiles)+1;assert t<16;tiles[key]=t
                for yy in range(16):
                    for xx in range(16):
                        pos,shift=locations[yy*256+t*16+xx]
                        joined[pos]=(joined[pos]&~(15<<shift))|(int(pixels[yy,xx])<<shift)
            rr.append((tiles[key],x,y))
        while len(rr)<len(composition_frame(c,5,n)['parts']):rr.append(rr[-1])
        recs[n]=b''.join(bytes([0,t,(x-160)&255,(y-160)&255]) for t,x,y in rr)
    joined=bytes(joined);nc,slack=repack_parts(c,5,recs)
    codes={};keys={};raws={};counts={};old_seen={}
    for f in bank['frames']:
        n=f['index'];old=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128)
        count=18 if n in targets else f['tile_count'];data=joined if n in targets else old.data
        key=(count,sha(data));keys[n]=key;raws[n]=data;counts[n]=count
        code=encode_stream(data) if n in targets else g[f['offset']:old.end]
        if key not in codes or len(code)<len(codes[key]):codes[key]=code
        old_seen[f['offset']]=old.end-f['offset']
    cursor=bank['base']+4*len(bank['frames']);positions={}
    for key,code in codes.items():positions[key]=cursor;cursor+=len(code)
    assert cursor<=bank['end'],f'Capacity exceeded by {cursor-bank["end"]}'
    assert positions[keys[0]]==bank['base']+4*len(bank['frames'])
    ng=bytearray(g)
    for key,code in codes.items():pos=positions[key];ng[pos:pos+len(code)]=code
    for f in bank['frames']:
        n=f['index'];struct.pack_into('<I',ng,bank['base']+n*4,counts[n]<<20|positions[keys[n]]-bank['base'])
    ng=bytes(ng);assert ng[:bank['base']]==g[:bank['base']] and ng[bank['end']:]==g[bank['end']:]
    out=replace_entry(replace_entry(arc,2,ng),3,nc)
    assert replace_entry(replace_entry(out,2,g),3,c)==arc
    assert bank_offsets(g)==bank_offsets(ng) and bank_offsets(c)==bank_offsets(nc)
    totals={'raw':0,'display':0,'non_target_raw':0,'non_target_display':0,'new_art_exact':0,'partial_raw_parts_exact':0}
    changed=[]
    for gb in (0,1):
        for a,b in zip(graphics_bank(g,gb)['frames'],graphics_bank(ng,gb)['frames']):
            n=a['index'];selected=gb==1 and n in targets
            ar=decode_stream(g,a['offset'],a['limit'],a['tile_count']*128).data
            br=decode_stream(ng,b['offset'],b['limit'],b['tile_count']*128).data;totals['raw']+=1
            assert b['tile_count']<=32
            if selected:
                assert br==joined and b['tile_count']==18
                assert len(composition_frame(c,5,n)['parts'])==len(composition_frame(nc,5,n)['parts'])
                assert all(0<p['tile']<16 and p['flags']==0 for p in composition_frame(nc,5,n)['parts'])
            else:
                assert ar==br and a['tile_count']==b['tile_count']
                assert records(c,gb*5,n)==records(nc,gb*5,n);totals['non_target_raw']+=1
            if gb==1 and 42<=n<=49:
                assert not selected;totals['partial_raw_parts_exact']+=1;continue
            before,after=render(arc,gb,gb*5,n)[0],render(out,gb,gb*5,n)[0]
            assert np.array_equal(after,targets[n] if selected else before),(gb,n)
            totals['display']+=1
            if selected:
                totals['new_art_exact']+=1;changed.append({'ref':n,'pixels':int(np.count_nonzero(before!=after)),
                    'tile_count_before':a['tile_count'],'tile_count_after':b['tile_count']})
            else:totals['non_target_display']+=1
    assert totals=={'raw':444,'display':436,'non_target_raw':440,'non_target_display':432,'new_art_exact':4,'partial_raw_parts_exact':8}
    assert np.array_equal(render(out,1,5,183)[0],render(arc,1,5,183)[0])
    return out,{'counts':totals,'changes':changed,'same_raw_refs':[182,183,184,185],'common_tiles':len(tiles),
        'old_bank_slack':bank['end']-bank['base']-4*len(bank['frames'])-sum(old_seen.values()),
        'new_bank_slack':bank['end']-cursor,'parts_slack':slack,'bank_boundaries_exact':True,
        'all_other_entries_exact':True,'native_buffer_limit':32,'current_shared_upload_tiles':18,
        'partial_transition_scope':'부분42..49 자체와 조립은 보존.182..185 직후 남는 VRAM까지 이전과 동일하다고 주장하지 않는다.',
        'partial_transitions_runtime_verified':False}

def main():
    assert not OUT.exists();arc=P.read_bytes();out,proof=build(arc,expected);again,_=build(arc,expected);assert again==out
    cases=[]
    for case in ('wrong_parent','wrong_target'):
        a=arc;ts={k:v.copy()for k,v in expected.items()}
        if case=='wrong_parent':a=bytes([a[0]^1])+a[1:]
        else:ts[182][160,160]^=1
        try:build(a,ts)
        except ValueError as e:cases.append({'case':case,'reason':str(e)})
        else:raise AssertionError('Invalid input accepted')
    OUT.mkdir();(OUT/'PL01_U.ARC').write_bytes(out)
    review.OUT=OUT;review.KEYS={(1,n):(n,0,0)for n in expected};review.boards(arc,out)
    report={'source_arc':str(P.relative_to(ROOT)),'source_arc_sha256':PSHA,'resource':str((OUT/'PL01_U.ARC').relative_to(ROOT)),
        'after_sha256':sha(out),'new_art_refs':[182,184,185],'cumulative_ref_count':80,'verification':proof,
        'reproducible':True,'negative_checks':cases,'static_sync_pending':True,'not_ready_for_disc':True,
        'partial_ref_77_80_call_path_status':'기존 US-EXE 정상 차량 setter 조사에서는77..80 호출 미발견. 전체프로그램 비도달 증명은 아님.',
        'gameplay_runtime_verified':False}
    (OUT/'proposal.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({'sha256':sha(out),'proof':proof}))
if __name__=='__main__':main()
