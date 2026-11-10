"""Independent reader: Shibuki base/Fourth13, fixed source targets and original FX."""
from pathlib import Path
import collections,hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import binary_dilation
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from src.psx_player import decode_stream,composition_frame,bank_offsets,indexed_atlas,compose_indices
from src.psx_ui_atlas import local_composition
D=Path(__file__).parent;H=D.parent/'shibuki_audit';P=H/'prepared_hurt_base01';T=H/'hurt_effect_probe01';O=D/'shibuki_hurt13_independent01'
PBS=(0,5,6,7,8);REFS=set(range(106,115))|set(range(233,237));RESERVED={105,*range(175,183)}
sha=lambda b:hashlib.sha256(b).hexdigest();read=lambda p:json.loads(p.read_text('utf8'));rel=lambda p:p.relative_to(ROOT).as_posix()
oldpath=H/'prepared_base_run01/PL00_U.ARC';newpath=P/'PL00_U.ARC';old=oldpath.read_bytes();new=newpath.read_bytes()
assert sha(old)=='381d83fa2623d58a3302914196ffdd73bd8c972e27aa584380af05d819e688ce'
assert sha(new)=='87e7d1db40c2380815ca2986bc27382db73f718d9c338d2eaad776372a2e257b'
lockpath=H/'hurt_locked_inputs01/LOCK.json';lock=read(lockpath)
assert sha(lockpath.read_bytes())=='8373993dab8b729ae466f64a9633f3e5a1cddd44c7ae01e8a39e65b875ee277d'
assert lock['parent_sha256']==sha(old)and lock['candidate_sha256']==sha(new)and set(lock['refs'])==REFS
for p,h in lock['files'].items():assert sha((ROOT/p).read_bytes())==h,p
sourcepath=D/'shibuki_hurt_sources01/report.json';assert sha(sourcepath.read_bytes())=='202898054ae9061a626b1a9088bfde79bf3ef15339963acfc3f4d3d0c49b348c'
src=read(sourcepath)['archives'][0];assert src['source_sha256']==sha(old)
a,b=Archive(old),Archive(new);counts=collections.Counter();raws={}
assert len(old)==len(new)and a.p==b.p
ae,be=psx_arc(old),psx_arc(new)
assert [(e['type'],e['offset'],e['size'])for e in ae]==[(e['type'],e['offset'],e['size'])for e in be]
allowed=np.zeros(len(old),bool)
for e in ae:
    if int(e['type'],16)in(2,3):allowed[e['offset']:e['offset']+e['size']]=True
assert not np.any((np.frombuffer(old,np.uint8)!=np.frombuffer(new,np.uint8))&~allowed)
assert bank_offsets(a.g,allow_aliases=True)==bank_offsets(b.g,allow_aliases=True)
assert bank_offsets(a.c)==bank_offsets(b.c)
for gb,(ob,nb)in enumerate(zip(a.banks,b.banks)):
    assert (ob['base'],ob['end'],len(ob['frames']))==(nb['base'],nb['end'],len(nb['frames']))
    if gb:
        assert a.g[ob['base']:ob['end']]==b.g[nb['base']:nb['end']]
        counts['other_graphics_banks_byte_exact']+=1
    for f,g in zip(ob['frames'],nb['frames']):
        n=f['index'];assert n==g['index']
        x=decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128)
        y=decode_stream(b.g,g['offset'],g['limit'],g['tile_count']*128)
        assert x.serialize()==a.g[x.start:x.end]and y.serialize()==b.g[y.start:y.end]
        counts['raw_checked']+=1
        if gb==0 and n in REFS:
            assert g['tile_count']==32;raws[n]=(x.data,f['tile_count'],y.data)
        else:
            assert x.data==y.data and f['tile_count']==g['tile_count'];counts['non_target_raw_exact']+=1
def atlas(data,count):return np.frombuffer(indexed_atlas(data,count)[0],np.uint8).reshape(-1,256)
def tile(data,count,t):
    x,y=t%16*16,t//16*16;return atlas(data,count)[y:y+16,x:x+16]
def sig(p):return p['flags'],p['tile'],p['x'],p['y']
def parts(ar,pb,n):return composition_frame(ar.c,pb,n)['parts']
def render(ar,n,pb,ps):
    z=np.zeros((384,384),np.uint8)
    if not ps:return z
    f=ar.banks[0]['frames'][n];rr=decode_stream(ar.g,f['offset'],f['limit'],f['tile_count']*128).data
    cp={'parts':ps}
    if pb:cp=local_composition(cp)
    px,sz,box,_=compose_indices(rr,f['tile_count'],cp,allowed_cluts={0,1,2,3})
    sm=np.frombuffer(px,np.uint8).reshape(sz[1],sz[0]);y,x=np.nonzero(sm);z[y+box[1]+160,x+box[0]+160]=sm[y,x];return z
m=read(T/'manifest.json');assert set(map(int,m['targets']))==REFS and m['parent_sha256']==sha(old)
targets={}
for n in range(237):
    if n in RESERVED:continue
    for pb in PBS:
        z=b.layer(n,pb)[0];counts['layers_checked']+=1
        if n in REFS:
            want=np.asarray(Image.open(T/f'{n:03}_bank{pb}_indices.png'))
            assert want.shape==(384,384)and want.dtype==np.uint8 and want.max()<48
            assert sha(want.tobytes())==m['targets'][str(n)][str(pb)]and np.array_equal(z,want),(n,pb)
            targets[n,pb]=want;counts['registered_layers_exact']+=1
        else:assert np.array_equal(z,a.layer(n,pb)[0]);counts['non_target_layers_exact']+=1
edge_exceptions=[]
for pb in range(len(bank_offsets(a.c))):
    for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
        op,np_=parts(a,pb,n),parts(b,pb,n)
        if pb in PBS and n in REFS:
            assert len(np_)<=24
            for p in np_:
                t=p['tile']+p['page']*256;assert 0<=t<32;v=tile(raws[n][2],32,t)
                u=t%16==0 and bool(v[:,0].any());vv=p['flip_y']and t//16%16==0 and bool(v[0].any())
                if u or vv:
                    assert any(sig(p)==sig(q)for q in op)and np.array_equal(v,tile(raws[n][0],raws[n][1],t))
                    edge_exceptions.append({'ref':n,'bank':pb,'record':sig(p),'U':u,'V':vv})
                counts['target_GPU_parts_checked']+=1
        else:assert [sig(q)for q in op]==[sig(q)for q in np_];counts['non_target_compositions_exact']+=1

# Four fixed registered bodies, no production module imported or executed.
for n in(106,110,233,234):
    for pb in PBS:
        v=np.asarray(Image.open(H/f'hurt_common_probe02/{n:03}_bank{pb}_indices.png'))
        assert np.array_equal(v,targets[n,pb]);counts['body_key_layers_exact']+=1

# Independently preserved original effect records from the earlier source audit.
effects=[]
for e in src['effects']:
    n,core=e['ref'],e['core'];assert b.banks[0]['frames'][n]['offset']==b.banks[0]['frames'][core]['offset']
    for pb in PBS:
        if pb==0:ps=e['original_effect_parts']if n in(107,108)else e['actual_CLUT2_records']
        elif n in(107,108):ps=e['original_armor_effect17_18'][str(pb)]['current_same_number_records']
        else:ps=[]
        assert [sig(p)for p in parts(b,pb,n)]==[sig(p)for p in parts(b,pb,core)]+[sig(p)for p in ps]
        fx=render(a,n,pb,ps);assert np.array_equal(fx,render(b,n,pb,ps))
        assert np.array_equal(targets[n,pb],np.where(fx>0,fx,targets[core,pb]))
        for t in sorted({q['tile']for q in ps}):
            assert np.array_equal(tile(raws[n][0],raws[n][1],t),tile(raws[n][2],32,t));counts['whole_original_effect_tile_uses_exact']+=1
        effects.append({'ref':n,'bank':pb,'opaque':int(np.count_nonzero(fx)),'original_records':[sig(q)for q in ps],'exact':True})
mask=targets[106,0]>0;flash=np.zeros_like(targets[106,0]);flash[binary_dilation(mask)]=9;flash[mask]=14
assert np.array_equal(flash,targets[109,0])and all(not targets[109,pb].any()for pb in PBS[1:])
def silhouette(n,res,body):
    z=res.copy();m=body>0;ring=binary_dilation(m)
    if n==112:z[ring]=6;z[m]=14
    elif n==113:z[ring]=1
    else:
        z[ring]=1;z[m]=3;z[np.isin(body,(1,2,4,8,15))&m]=5;z[np.isin(body,(6,9))&m]=1
    return np.where(z,z+32,0).astype(np.uint8)
derived=[]
for q in src['silhouettes112_114']:
    n=q['ref'];p=ROOT/q['residual_path'];assert sha(p.read_bytes())==m['source_arrays'][rel(p)]
    res=np.load(p).copy();old_reconstruction=silhouette(n,res,a.layer(110)[0])
    for cell in q['small_components_deleted_coordinates']:
        x,y=cell['x']+160,cell['y']+160;old_reconstruction[y,x]=0;res[y,x]=0
    assert np.array_equal(old_reconstruction,a.layer(n)[0])
    want=silhouette(n,res,targets[110,0]);assert np.array_equal(want,targets[n,0])
    assert all(not targets[n,pb].any()for pb in PBS[1:])
    derived.append({'ref':n,'parent_rule_exact':True,'new_silhouette_exact':True,'preserved_external_pixels':int(np.count_nonzero(res)),'new_small_components_deleted':False})
auras=[]
for q in src['aura235_236']:
    n=q['ref'];p=ROOT/q['historical_effect_path'];assert sha(p.read_bytes())==m['source_arrays'][rel(p)]
    fx=np.load(p);assert np.count_nonzero(fx)==q['historical_original_effect_pixels']
    assert np.array_equal(np.where(a.layer(234)[0]>0,a.layer(234)[0],fx),a.layer(n)[0])
    assert np.array_equal(np.where(targets[234,0]>0,targets[234,0],fx),targets[n,0])
    assert all(np.array_equal(targets[n,pb],targets[234,pb])for pb in PBS[1:])
    full=targets[234,0].copy()
    for pb in(8,5,7,6):v=targets[234,pb];full[v>0]=v[v>0]
    auras.append({'ref':n,'historical_source_pixels':int(np.count_nonzero(fx)),'source_shape_and_colors_not_moved':True,'body_drawn_over_effect_exact':True,
                  'base_visible_external':int(np.count_nonzero((fx>0)&(targets[234,0]==0))),
                  'fourth_visible_external':int(np.count_nonzero((fx>0)&(full==0))),
                  'old_fourth_garment_differences_not_copied':True})
assert b.banks[0]['frames'][234]['offset']==b.banks[0]['frames'][235]['offset']
bodyparts=parts(b,0,234);p235=parts(b,0,235)
assert [sig(p)for p in p235[-len(bodyparts):]]==[sig(p)for p in bodyparts]
actual_fx235=render(b,235,0,p235[:-len(bodyparts)])
assert np.array_equal(actual_fx235,np.load(ROOT/src['aura235_236'][0]['historical_effect_path']))
for pb in PBS[1:]:assert [sig(p)for p in parts(b,pb,235)]==[sig(p)for p in parts(b,pb,234)]

# Undo every declared whole-tile storage permutation and compare every nibble.
recipe=read(H/'hurt_locked_inputs01/tile_recipe.json');permutations=[]
for key,q in recipe['groups'].items():
    n=int(key);order=q['order'];assert sorted(order)==list(range(32))and all(order[t]==t for t in q['fixed_tiles'])
    after=atlas(raws[n][2],32);before=np.zeros_like(after)
    for newtile,oldtile in enumerate(order):
        sy,sx=divmod(newtile,16);dy,dx=divmod(oldtile,16)
        before[dy*16:dy*16+16,dx*16:dx*16+16]=after[sy*16:sy*16+16,sx*16:sx*16+16]
    rr=bytes((before[:,::2]|(before[:,1::2]<<4)).ravel())
    assert sha(rr)==q['source_raw_sha256']and sha(raws[n][2])==q['output_raw_sha256']
    permutations.append({'group_core':n,'all32_tiles_inverse_exact':True,'fixed_tiles':q['fixed_tiles']})
def color(z,start=0):
    tab=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]+[0 if i%16==0 else 255]for i,w in enumerate(b.words[start:])],np.uint8)
    return tab[z]
for n in sorted(REFS):
    for mask in range(16):
        for arm in(1,2):
            want=color(targets[n,0])
            for bit,pb in((8,8),(1,5),(4,7),(2,6)):
                if mask&bit:
                    v=color(targets[n,pb],32 if pb==7 and arm==2 else 16);occ=v[:,:,3]>0;want[occ]=v[occ]
            assert np.array_equal(want,np.asarray(b.composite(n,mask,arm)[0]));counts['independent_partial_RGBA']+=1
O.mkdir(exist_ok=True);sheets=[]
for i,ns in enumerate(((106,110),(233,234),(107,108,109),(111,112,113),(114,235,236))):
    cw,ch=292,300;board=Image.new('RGB',(cw*4,ch*len(ns)),'#263345');dr=ImageDraw.Draw(board)
    for row,n in enumerate(ns):
        panels=[('old base',a.composite(n,0,1)[0]),('new base',b.composite(n,0,1)[0]),('old Fourth',a.composite(n,15,2)[0]),('new Fourth',b.composite(n,15,2)[0])]
        for col,(name,im)in enumerate(panels):
            x,y=col*cw,row*ch;dr.text((x+4,y+4),f'{n} {name}',fill='white')
            im=im.crop((127,126,197,194)).resize((280,272),Image.Resampling.NEAREST);board.paste(im,(x+6,y+23),im)
    p=O/f'readback_{i:02}.png';board.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes())})
assert counts['raw_checked']==508 and counts['non_target_raw_exact']==495
assert counts['layers_checked']==1140 and counts['registered_layers_exact']==65 and counts['non_target_layers_exact']==1075
assert counts['independent_partial_RGBA']==416
assert oldpath.read_bytes()==old and newpath.read_bytes()==new
for p,h in lock['files'].items():assert sha((ROOT/p).read_bytes())==h,p
report={'passed':True,'scope':'시부키 기본/포스 피격13 독립 읽기. 제작/정합/패킹 함수 미호출.',
 'parent':rel(oldpath),'parent_sha256':sha(old),'candidate':rel(newpath),'candidate_sha256':sha(new),
 'target_manifest':rel(T/'manifest.json'),'target_manifest_sha256':sha((T/'manifest.json').read_bytes()),
 'target_lock':rel(lockpath),'target_lock_sha256':sha(lockpath.read_bytes()),'locked_inputs_checked':len(lock['files']),
 'independent_historical_source_report_sha256':sha(sourcepath.read_bytes()),'counts':dict(counts),
 'archive_length_directory_palette_audio_other_entries_exact':True,'all_bank_boundaries_exact':True,
 'original_effect_tiles_and_records':effects,'preserved_GPU_edge_exceptions':edge_exceptions,'new_GPU_edge_invasions':0,
 'flash109_inside14_outline9_exact':True,'CLUT2_derived':derived,'historical_auras':auras,
 'shared234235_effect_then_body_order_exact':True,'whole_tile_permutations':permutations,
 'all_non_target_partial_RGBA_follows_from_exact1075_layers_and_palette':True,
 'new_readback_sheets':sheets,'readback_actually_viewed':False,
 'art_generation_quantization_reconstructed':False,'producer_functions_called':False,'native_MIPS_executed_here':False,'runtime_verified':False,
 'limits':['고정 등록65층과 기존독립 원효과 출처를 실제 ARC에 대조했다. 새 생성원화의 양자화 전과정은 별도다.',
 '235/236은256/464px 원오라를 뒤에 놓고 새234로 가리는 규칙이다. 구형 포스의상 차이나 옛 오라 재색상을 그대로 복사한 것은 아니다.',
 '실제피격 팔레트전환·60Hz·게임·사용자 수용은 별도이며 이 보고서로 확대하지 않는다.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'counts':dict(counts),'auras':auras,'report_sha256':sha((O/'report.json').read_bytes())}))
