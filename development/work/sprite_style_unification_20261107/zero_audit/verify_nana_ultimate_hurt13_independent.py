"""Independent Ultimate hurt13 reader: no producer imports or build calls."""
from pathlib import Path
import collections,hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import binary_dilation,label,distance_transform_cdt
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from src.psx_player import decode_stream,composition_frame,bank_offsets,indexed_atlas,compose_indices
D=Path(__file__).parent;N=D.parent/'nana_audit';H=N/'ultimate_hurt_repaint'
P=H/'packed_hurt_candidate_v1';T=H/'final_targets_v1';O=D/'nana_ultimate_hurt13_independent01'
PBS=(0,5,6,7,8);REFS=set(range(106,115))|set(range(233,237));RESERVED={105,*range(175,183)}
sha=lambda v:hashlib.sha256(v).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();tracked={}
def read(p):
    v=p.read_bytes();h=sha(v)
    if p in tracked:assert tracked[p]==h,str(p)
    tracked[p]=h;return v
def js(p):return json.loads(read(p))
def arr(p):
    read(p);v=np.array(Image.open(p));assert v.shape==(384,384) and v.dtype==np.uint8
    return v
def raw(ar,gb,n):
    f=ar.banks[gb]['frames'][n];return decode_stream(ar.g,f['offset'],f['limit'],f['tile_count']*128).data
def parts(ar,pb,n):return composition_frame(ar.c,pb,n)['parts']
sig=lambda p:(p['flags'],p['tile'],p['x'],p['y'])
def render(ar,n,ps):
    out=np.zeros((384,384),np.uint8)
    if not ps:return out
    f=ar.banks[0]['frames'][n];px,size,box,_=compose_indices(raw(ar,0,n),f['tile_count'],{'parts':ps},allowed_cluts={0,1,2,3})
    v=np.frombuffer(px,np.uint8).reshape(size[1],size[0]);yy,xx=np.nonzero(v)
    out[yy+box[1]+160,xx+box[0]+160]=v[yy,xx];return out
def tile(data,count,t):
    v=np.frombuffer(indexed_atlas(data,count)[0],np.uint8).reshape(-1,256)
    y,x=t//16*16,t%16*16;return v[y:y+16,x:x+16]
def full(ar,n):
    v=ar.layer(n,0)[0].copy()
    for pb in (8,5,7,6):
        z=ar.layer(n,pb)[0];v[z>0]=z[z>0]
    return v

oldpath=N/'rising_repaint/packed_ultimate_candidate_v1/PL02_U.ARC';newpath=P/'PL02_U.ARC'
old,new=read(oldpath),read(newpath)
assert sha(old)=='4132738ac872750507538cd8d150e13a510422df81cea99b502e7371b6753cd9'
assert sha(new)=='c9e68442829a7f149ae86317c88172e27dbce545e454687b98310fad28ef83a5'
frozen=js(P/'INPUT_FROZEN.json')
assert frozen['candidate_sha256']==sha(new) and frozen['parent_sha256']==sha(old)
for e in frozen['files']:assert sha(read(ROOT/e['path']))==e['sha256'],e['path']
a,b=Archive(old),Archive(new);counts=collections.Counter();assert len(old)==len(new) and a.p==b.p
ae,be=psx_arc(old),psx_arc(new)
assert [(e['type'],e['offset'],e['size'])for e in ae]==[(e['type'],e['offset'],e['size'])for e in be]
protected=np.ones(len(old),bool)
for e in ae:
    if int(e['type'],16)in(2,3):protected[e['offset']:e['offset']+e['size']]=False
assert np.array_equal(np.frombuffer(old,np.uint8)[protected],np.frombuffer(new,np.uint8)[protected])
assert bank_offsets(a.g,allow_aliases=True)==bank_offsets(b.g,allow_aliases=True) and bank_offsets(a.c)==bank_offsets(b.c)
raws={}
for gb,(ab,bb)in enumerate(zip(a.banks,b.banks)):
    assert (ab['base'],ab['end'],len(ab['frames']))==(bb['base'],bb['end'],len(bb['frames']))
    if gb:assert a.g[ab['base']:ab['end']]==b.g[bb['base']:bb['end']];counts['other_graphics_banks_byte_exact']+=1
    for f,g in zip(ab['frames'],bb['frames']):
        n=f['index'];assert n==g['index'];x=decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128);y=decode_stream(b.g,g['offset'],g['limit'],g['tile_count']*128)
        assert x.serialize()==a.g[x.start:x.end] and y.serialize()==b.g[y.start:y.end];counts['raw_checked']+=1
        if gb==0 and n in REFS:assert g['tile_count']==32;raws[n]=(x.data,f['tile_count'],y.data)
        else:assert x.data==y.data and f['tile_count']==g['tile_count'];counts['non_target_raw_exact']+=1
m=js(T/'manifest.json');assert set(map(int,m['targets']))==REFS and m['parent_sha256']==sha(old)
target={}
for n in range(237):
    if n in RESERVED:continue
    for pb in PBS:
        v=b.layer(n,pb)[0];counts['layers_checked']+=1
        if n in REFS:
            z=arr(T/f'layer{pb}_{n:03}.png');assert z.max()<48 and sha(z.tobytes())==m['targets'][str(n)][str(pb)]
            assert np.array_equal(z,v),(n,pb);target[n,pb]=z;counts['registered_target_layers_exact']+=1
        else:assert np.array_equal(v,a.layer(n,pb)[0]);counts['non_target_layers_exact']+=1
gpu_exceptions=[]
for pb in range(len(bank_offsets(a.c))):
    assert composition_frame(a.c,pb,0)['bank_frame_count']==composition_frame(b.c,pb,0)['bank_frame_count']
    for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
        op,np_=parts(a,pb,n),parts(b,pb,n)
        if pb in PBS and n in REFS:
            for p in np_:
                t=p['tile']+p['page']*256;assert 0<=t<32;z=tile(raws[n][2],32,t)
                u=t%16==0 and bool(z[:,0].any());v=p['flip_y'] and t//16%16==0 and bool(z[0].any())
                if u or v:
                    assert sig(p)in[sig(x)for x in op] and np.array_equal(z,tile(raws[n][0],raws[n][1],t))
                    gpu_exceptions.append({'ref':n,'bank':pb,'part':sig(p),'U':u,'V':v})
                counts['GPU_parts_checked']+=1
        else:assert [sig(p)for p in op]==[sig(p)for p in np_];counts['non_target_compositions_exact']+=1

# Rebuild the two costumes from fixed registered artwork, not packed targets.
costumes={}
for n in (106,110,233,234):
    before,after=arr(H/f'costume_pair_probe_v4/before_{n:03}.png'),arr(H/f'costume_pair_probe_v4/after_{n:03}.png')
    assert not np.any((after>0)&(before==0))
    assert np.array_equal(target[n,0],after)
    assert np.array_equal(target[n,5],np.where((before!=after)|(before==15),before,0))
    assert all(not target[n,p].any()for p in(6,7,8))
    for mask,z,pal in((0,after,0),(15,before,16)):
        assert b.composite(n,mask)[0].tobytes()==a.rgba(z,pal).tobytes();costumes[n,mask]=z
        counts['registered_full_body_costumes_exact']+=1

# Source extraction uses original part records: jacket extras for107/108 and CLUT2 for111.
fxproof=[]
for n,core in ((107,106),(108,106),(111,110)):
    assert b.banks[0]['frames'][n]['offset']==b.banks[0]['frames'][core]['offset']
    if n!=111:
        remaining=collections.Counter(sig(p)for p in parts(a,5,core));extras=[]
        for p in parts(a,5,n):
            if remaining[sig(p)]:remaining[sig(p)]-=1
            else:extras.append(p)
        assert not any(remaining.values())
    else:extras=[p for p in parts(a,0,n)if p['clut']==2]
    fx=render(a,n,extras);assert np.count_nonzero(fx)=={107:99,108:76,111:188}[n]
    used=(0,5)if n!=111 else(0,)
    for pb in PBS:
        e=extras if pb in used else[]
        assert [sig(p)for p in parts(b,pb,n)]==[sig(p)for p in parts(b,pb,core)]+[sig(p)for p in e]
        expected=np.where(fx,fx,target[core,pb])if pb in used else target[core,pb]
        assert np.array_equal(target[n,pb],expected)
    ts=sorted({p['tile']for p in extras})
    for t in ts:
        assert np.array_equal(tile(raws[n][0],raws[n][1],t),tile(raws[n][2],32,t));counts['whole_original_effect_tiles_exact']+=1
    assert np.array_equal(fx,render(b,n,extras))
    fxproof.append({'ref':n,'source_part_bank':5 if n!=111 else 0,'source_clut2_only':n==111,'records':len(extras),
                    'whole_tiles':ts,'pixels':int(np.count_nonzero(fx)),'effect_exact':True,
                    'policy':'107/108 현재 재킷의 분리 가능한 원효과를 새 양폼에 공통 적용'if n!=111 else'원CLUT2효과 그대로'})

flashes={}
for mask in (0,15):
    z=np.zeros((384,384),np.uint8);m_=costumes[106,mask]>0;z[binary_dilation(m_)]=9;z[m_]=13;flashes[mask]=z
assert np.array_equal(target[109,0],flashes[0])
assert np.array_equal(target[109,5],np.where(flashes[0]!=flashes[15],flashes[15],0))
assert all(not target[109,p].any()for p in(6,7,8))
def silhouette(n,res,body):
    z=res.copy();m_=body>0
    if n==112:z[binary_dilation(m_)]=6;z[m_]=14
    elif n==113:z[binary_dilation(m_)]=1
    else:
        z[binary_dilation(m_)]=1;z[m_]=3
        z[np.isin(body%16,(1,2,4,8,15))&m_]=5;z[np.isin(body%16,(6,9))&m_]=1
    return np.where(z,z+32,0).astype(np.uint8)
historypath=ROOT/'work/overhaul_20261105/sprites/ver_rin_nana/baseline/PL02_U.ARC';history=Archive(read(historypath));derived=[]
assert np.array_equal(full(history,110),full(a,110))
for n in (112,113,114):
    res=(history.layer(n,0)[0]%16).copy();res[binary_dilation(history.layer(110,0)[0]>0,iterations=2)]=0
    if n==114:res[np.isin(res,(3,5))]=0
    assert np.array_equal(silhouette(n,res,full(history,110)),a.layer(n,0)[0])
    assert np.array_equal(silhouette(n,res,costumes[110,15]),target[n,0])
    assert all(not target[n,p].any()for p in PBS[1:])
    derived.append({'ref':n,'source_history':rel(historypath),'external_residual_pixels':int(np.count_nonzero(res)),
                    'old_rule_exact':True,'new_jacket_common_CLUT2_exact':True,'small_new_components_deleted':False})

auram=js(H/'aura_contact_probe_v2/registration.json');assert auram==m['aura_registration'];auras=[]
oldbody=full(a,234);union=np.logical_or.reduce([target[234,p]>0 for p in PBS]);dist=distance_transform_cdt(~union,metric='taxicab')
for q in auram['frames']:
    n=q['ref'];current=full(a,n);assert np.array_equal(current[oldbody>0],oldbody[oldbody>0])
    fx=np.where(oldbody==0,current,0).astype(np.uint8);assert np.count_nonzero(fx)=={235:66,236:135}[n]
    labels,num=label(fx>0,np.ones((3,3),bool));out=np.zeros_like(fx);seen=set();moves=collections.defaultdict(set)
    for sx,sy,x,y,val in q['source_links']:
        assert fx[sy+160,sx+160]==val and val!=0 and (sx,sy)not in seen and out[y+160,x+160]==0
        seen.add((sx,sy));out[y+160,x+160]=val;moves[int(labels[sy+160,sx+160])].add((x-sx,y-sy))
    assert len(seen)==q['pixels']==np.count_nonzero(fx) and len(moves)==num and all(len(t)==1 for t in moves.values())
    assert sha(out.tobytes())==q['new_effect_sha256'] and not np.any((out>0)&union)
    for pb in PBS:
        want=np.where(out,out,target[234,pb])if pb in(0,5)else target[234,pb]
        assert np.array_equal(target[n,pb],want)
    auras.append({'ref':n,'pixels':len(seen),'eight_connected_components':num,'all_original_component_shape_and_indices_exact':True,
                   'translations':{str(k):list(next(iter(v)))for k,v in moves.items()},'body_overlap':0,
                   'maximum_manhattan_distance':int(dist[out>0].max()),'old_after_extra10_11_not_assumed_effect':True,
                   'hidden_original_effect_restoration_claimed':False})

def color(z,start=0):
    words=b.words[start:];lut=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]+[0 if i%16==0 else 255]for i,w in enumerate(words)],np.uint8)
    return lut[z]
for n in sorted(REFS):
    for mask in range(16):
        for arm in(1,2):
            want=color(target[n,0])
            for bit,pb in((8,8),(1,5),(4,7),(2,6)):
                if mask&bit:
                    z=color(target[n,pb],32 if pb==7 and arm==2 else 16);opaque=z[:,:,3]>0;want[opaque]=z[opaque]
            assert np.array_equal(want,np.array(b.composite(n,mask,arm)[0]));counts['independent_partial_RGBA']+=1
O.mkdir(exist_ok=True);sheets=[]
for idx,ns in enumerate(((106,110),(233,234),(107,108,109),(111,112,113),(114,235,236))):
    crop=(127,126,197,194);cw,ch=292,300;pic=Image.new('RGB',(cw*4,ch*len(ns)),'#263345');dr=ImageDraw.Draw(pic)
    for row,n in enumerate(ns):
        panels=[('old jacket',a.composite(n,15)[0]),('new jacket',b.composite(n,15)[0]),('old after',a.composite(n)[0]),('new after',b.composite(n)[0])]
        for col,(name,frame)in enumerate(panels):
            x,y=col*cw,row*ch;dr.text((x+4,y+4),f'{n} {name}',fill='white');v=frame.crop(crop).resize((280,272),Image.Resampling.NEAREST);pic.paste(v,(x+6,y+23),v)
    path=O/f'readback_{idx:02}.png';pic.save(path);sheets.append({'path':rel(path),'sha256':sha(path.read_bytes())})
assert counts['raw_checked']==512 and counts['non_target_raw_exact']==499
assert counts['registered_target_layers_exact']==65 and counts['non_target_layers_exact']==1075 and counts['independent_partial_RGBA']==416
for p,h in tracked.items():assert sha(p.read_bytes())==h,str(p)
report={'passed':True,'scope':'나나 Ultimate 피격13 최종 후보의 등록65층·원효과·양폼실루엣·오라를 제작 함수 없이 독립 재독출했다.',
 'candidate':rel(newpath),'candidate_sha256':sha(new),'parent':rel(oldpath),'parent_sha256':sha(old),
 'input_frozen_sha256':sha(read(P/'INPUT_FROZEN.json')),'input_files_checked':len(frozen['files']),
 'target_manifest_sha256':sha(read(T/'manifest.json')),'counts':dict(counts),'original_effects':fxproof,
 'flash109_both_costumes_source_alpha_exact':True,'common_CLUT2_112_114':derived,'aura':auras,
 'preserved_GPU_edge_exceptions':gpu_exceptions,'new_GPU_edge_invasions':0,
 'all_other_entries_palette_audio_static_exact':True,'bank_boundaries_exact':True,
 'new_readback_sheets':sheets,'producer_functions_called':False,'native_MIPS_executed_here':False,'runtime_verified':False,
 'readback_actually_viewed':False,'source_files_preserved':{rel(p):h for p,h in tracked.items()},
 'limits':['원화의 생성·양자화 전과정 재현은 범위 밖이다. 고정 등록 원화와 공통층/효과 파생을 대조했다.',
 '107/108은 기존 재킷층의 분리 가능한 원효과를 새 양폼에 공통화하는 신규 정책이며 옛 맨팔의 뭉개진 몸체까지 보존하는 것은 아니다.',
 '235/236의 현재 재킷234 바깥66/135px를 출처로 삼았다. 구형몸체에 가려진 모든 원효과 복원까지 주장하지 않는다.',
 '현재60Hz 실제피격/부분아머 전조합/팔레트 깜박임이나 사용자 최종수용은 별도이다.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'counts':dict(counts),'aura':auras,'report_sha256':sha((O/'report.json').read_bytes())}))
