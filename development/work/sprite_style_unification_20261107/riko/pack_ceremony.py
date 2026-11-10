"""검토한 승리/탑승/낙봉파 본체와 동일 표시 공유 사본을 등록한다."""
from pathlib import Path
import json, sys, struct
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];W=ROOT/'work/sprite_style_unification_20261107';Z=W/'zero_audit'
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(Z))
import pack_riko_cloth as engine
from scripts.overhaul_sprites_audit import render
from scripts.prepare_riko_ui import entry
from src.psx_player import graphics_bank
from src.psx_compress import encode_stream
from src.psx_frame_edit import frame_coverage
from src.psx_disc import file_hash
ORIGINAL_PARENT=W/'riko/prepared_head_spaces_v1/PL01_U.ARC';ORIGINAL_SHA='488b679ed027fd8916e0f48716c9e3fa65d03ff42d4ac21d38dffb6ed0a7edaf'
P=Z/'riko_restore/hidden_cleanup_v2/PL01_U.ARC';PSHA='349c83306897a5d92d6de1f894ec11a860e2c67f290e633c886a8ea18ae0c5ca'
ART=W/'riko/ceremony_cloth02/registered02';OUT=W/'riko/prepared_ceremony_v2'
assert not OUT.exists() and file_hash(P)==PSHA
arc=P.read_bytes();reg=json.loads((ART/'registration.json').read_text('utf8'))
assert file_hash(ORIGINAL_PARENT)==ORIGINAL_SHA and reg['source_sha256']==ORIGINAL_SHA
masters={}
for r in reg['frames']:
    path=ROOT/r['target'];assert file_hash(path)==r['target_sha256']
    a=np.array(Image.open(path));assert a.shape==(384,384) and a.dtype==np.uint8 and a.max()<=15
    masters[r['ref']]=a
def cropped(a):
    y,x=np.nonzero(a)
    if not len(x):return None
    box=(int(x.min()),int(y.min()),int(x.max())+1,int(y.max())+1)
    part=a[box[1]:box[3],box[0]:box[2]]
    return part.tobytes(),part.shape,box[:2]
keys={};targets={};master_old={n:cropped(render(arc,1,5,n)[0]) for n in masters}
for b in(0,1):
    for f in graphics_bank(entry(arc,2),b)['frames']:
        n=f['index']
        if b==1 and 42<=n<=49:continue
        found=cropped(render(arc,b,b*5,n)[0])
        if found is None:continue
        for master,(pixels,shape,origin) in master_old.items():
            if found[:2]==(pixels,shape):
                dx,dy=found[2][0]-origin[0],found[2][1]-origin[1]
                keys[b,n]=(master,dx,dy);targets[b,n]=engine.shifted(masters[master],dx,dy)
assert set(keys)=={(1,1),(1,5),(1,17),(1,20),(1,183)}
ART_KEYS=dict(keys)
SUPPORT=[0,2,6,14,15,16,18,19,21,182]
for n in SUPPORT:
    keys[1,n]=(None,0,0);targets[1,n]=render(arc,1,5,n)[0].copy()
engine.PARENT=P;engine.PARENT_SHA=PSHA;engine.KEYS=keys;engine.OUT=OUT;engine.CACHE=W/'riko/ceremony_pack_cache'
def expected(data):
    engine.native.need(engine.native.sha(data)==PSHA,'Wrong parent')
    return {k:v.copy() for k,v in targets.items()}
engine.get_targets=expected
original_pack_frame=engine.pack_frame
def pack_with_dome_ownership(c,b,n,raw,count,target):
    if (b,n)!=(1,183):return original_pack_frame(c,b,n,raw,count,target)
    # Bank1/182 owns 0..10. Put the entire new183 in its own existing 11..17
    # slots so both figures coexist instead of splitting the shared raw block.
    assert count==18
    rects=engine.fast_fit(target>0,7)
    assert rects is not None
    rects=sorted(rects,key=lambda p:(p[1],p[0]))
    previous_fit=engine.motion.fit
    try:
        engine.motion.fit=lambda mask,limit:[list(r)for r in rects]
        nr,rr=engine.motion.identical(raw,count,target,set(range(11,18)),11)
    finally:engine.motion.fit=previous_fit
    while len(rr)<11:rr.append(rr[-1])
    rec=b''.join(bytes([0,t,(x-160)&255,(y-160)&255])for t,x,y in rr)
    return nr,rec,{'type':'native_window_reassignment','unchanged_tile_count':18,'owned_tiles':list(range(11,18)),'preserved_182_tiles':list(range(11))}
engine.pack_frame=pack_with_dome_ownership
def repack_exact_shared(g,b,replacements):
    """같은 해제 바이트만 공유한다. 은행과 모든 원시/표시 픽셀은 유지한다."""
    bank=graphics_bank(g,b);codes={};keys={};raws={};old_offsets={};old_used=0;key_raw={};recompressed=[]
    for f in bank['frames']:
        decoded=engine.native.decode_stream(g,f['offset'],f['limit'],f['tile_count']*128)
        raw=replacements.get(f['index'],decoded.data)
        engine.native.need(len(raw)==f['tile_count']*128,'Decoded size changed')
        key=(len(raw),engine.native.sha(raw));keys[f['index']]=key;raws[f['index']]=raw;key_raw[key]=raw
        code=g[f['offset']:decoded.end] if raw==decoded.data else encode_stream(raw)
        if key not in codes or len(code)<len(codes[key]):codes[key]=code
        if f['offset'] not in old_offsets:old_used+=decoded.end-f['offset']
        old_offsets[f['offset']]=True
    budget=bank['end']-bank['base']-4*len(bank['frames'])
    total=sum(map(len,codes.values()))
    cache=W/'riko/lossless_compression_cache';cache.mkdir(exist_ok=True)
    for key in sorted(codes,key=lambda k:len(codes[k]),reverse=True):
        if total<=budget:break
        path=cache/(key[1]+'.bin')
        code=path.read_bytes() if path.exists() else encode_stream(key_raw[key])
        engine.native.need(engine.native.decode_stream(code,0,len(code),key[0]).data==key_raw[key],'Lossless compression differs')
        if not path.exists():path.write_bytes(code)
        gain=len(codes[key])-len(code)
        if gain>0:
            codes[key]=code;total-=gain
            recompressed.append({'raw_sha256':key[1],'references':[n for n,k in keys.items() if k==key],'saved_bytes':gain})
            print(json.dumps({'bank':b,'lossless_saved':gain,'remaining_excess':max(0,total-budget)}),flush=True)
    cursor=bank['base']+4*len(bank['frames']);locations={}
    for key,code in codes.items():locations[key]=cursor;cursor+=len(code)
    if b==1 and cursor>bank['end']:
        for refs in ([0,1,2],[5,6],list(range(14,22)),[182,183]):
            print(json.dumps({'joint_probe_refs':refs,'variant_sizes':{str(key):len(codes[key]) for key in set(keys[n]for n in refs)}}),flush=True)
    engine.native.need(cursor<=bank['end'],f'Bank capacity after exact-byte sharing: excess {cursor-bank["end"]}')
    engine.native.need(locations[keys[0]]==bank['base']+4*len(bank['frames']),'Sentinel drift')
    out=bytearray(g)
    for key,code in codes.items():pos=locations[key];out[pos:pos+len(code)]=code
    for f in bank['frames']:struct.pack_into('<I',out,bank['base']+f['index']*4,f['tile_count']<<20|locations[keys[f['index']]]-bank['base'])
    out=bytes(out);engine.native.need(out[:bank['base']]==g[:bank['base']] and out[bank['end']:]==g[bank['end']:],'Escaped bank')
    for f in graphics_bank(out,b)['frames']:
        engine.native.need(engine.native.decode_stream(out,f['offset'],f['limit'],f['tile_count']*128).data==raws[f['index']],'Shared stream differs')
    return out,{'bank':b,'old_slack':bank['end']-bank['base']-4*len(bank['frames'])-old_used,
        'remaining_slack':bank['end']-cursor,'unique_raw_streams':len(codes),'exact_raw_sharing_only':True,
        'lossless_recompressed':recompressed,'bank_boundaries_exact':True}
engine.native.packer.repack_raw=repack_exact_shared
result,proof=engine.build(arc,targets);again,_=engine.build(arc,targets);assert result==again
rejections=[]
for case in('parent','missing','pixel'):
    data=arc;bad={k:v.copy() for k,v in targets.items()}
    if case=='parent':data=bytes([arc[0]^1])+arc[1:]
    elif case=='missing':del bad[1,5]
    else:bad[1,1][160,160]^=1
    try:engine.build(data,bad)
    except ValueError as e:rejections.append({'case':case,'reason':str(e)})
    else:raise AssertionError('Bad candidate accepted')
proof.pop('heads_preserved_pixels_per_reference',None)
proof['registration']=reg
proof['global_hidden_cleanup_used']=True
proof['display_preserving_parent_cleanup']=json.loads((P.parent/'analysis.json').read_text('utf8'))
assert proof['display_preserving_parent_cleanup']['carried_mapping_uses_each_stream_upload_width']
proof['per_target_hidden_cleanup_used']=False
original_arc=ORIGINAL_PARENT.read_bytes()
for b in (0,1):
    for f in graphics_bank(entry(original_arc,2),b)['frames']:
        n=f['index']
        if b==1 and 42<=n<=49:continue
        if (b,n) not in ART_KEYS:
            assert np.array_equal(render(original_arc,b,b*5,n)[0],render(result,b,b*5,n)[0])
proof['original_parent_non_target_431_displays_exact']=True
proof['unchanged_display_shared_support_refs']=SUPPORT
proof['static_dome_182_185_sources_unchanged']=all(np.array_equal(render(arc,1,5,n)[0],render(result,1,5,n)[0]) for n in(182,185))
assert proof['static_dome_182_185_sources_unchanged'] and entry(arc,0x10206)==entry(result,0x10206)
OUT.mkdir();(OUT/'PL01_U.ARC').write_bytes(result);engine.KEYS=ART_KEYS;engine.boards(arc,result)
for (b,n),a in targets.items():Image.fromarray(a).save(OUT/f'b{b}_{n:03d}_indices.png')
report={'source_arc':str(ORIGINAL_PARENT.relative_to(ROOT)),'source_arc_sha256':ORIGINAL_SHA,
    'resource':str((OUT/'PL01_U.ARC').relative_to(ROOT)),
    'after_sha256':engine.native.sha(result),'target_references':[f'b{b}_{n:03d}' for b,n in ART_KEYS],
    'verification':proof,'reproducible':True,'rejections':rejections,'cumulative_ref_count':77,
    'static_note':'낙봉파 돔23/24의실제원본참조는185/182이므로새183을무근거덮지않음. 후속182/185수정시동기화필요.',
    'game_changed':False,'runtime_verified':False}
(OUT/'proposal.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'sha256':report['after_sha256'],'refs':report['target_references'],'counts':proof['counts']}))
