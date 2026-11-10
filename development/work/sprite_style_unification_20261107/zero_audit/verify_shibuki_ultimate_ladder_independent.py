"""Ultimate ladder14 independent reader; no producer/packer imports or calls."""
from pathlib import Path
import sys,json,hashlib,collections
import numpy as np
from PIL import Image

D=Path(__file__).resolve().parent
ROOT=D.parents[2]
sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from src.psx_player import bank_offsets,decode_stream,composition_frame,indexed_atlas

H=D.parent/'shibuki_audit'
P=H/'prepared_ultimate_ladder01'
T=H/'ultimate_ladder_complete_targets01'
O=D/'shibuki_ultimate_ladder_independent01'
O.mkdir(exist_ok=True)
tracked={}
sha=lambda x:hashlib.sha256(x).hexdigest()
def read(p):
    p=Path(p);v=p.read_bytes();h=sha(v)
    if p in tracked:assert tracked[p]==h,(str(p),'changed during read')
    tracked[p]=h
    return v
def js(p):return json.loads(read(p))
def arr(p):
    read(p);v=np.array(Image.open(p));assert v.shape==(384,384) and v.dtype==np.uint8
    return v
def rel(p):return p.relative_to(ROOT).as_posix()
def mirror(v,k):
    out=np.zeros_like(v);yy,xx=np.nonzero(v);nx=320-xx+k
    assert not len(nx) or (nx.min()>=0 and nx.max()<384)
    out[yy,nx]=v[yy,xx]
    return out
def shift(v,dx,dy):
    out=np.zeros_like(v);yy,xx=np.nonzero(v);assert np.all((xx+dx>=0)&(xx+dx<384)&(yy+dy>=0)&(yy+dy<384))
    out[yy+dy,xx+dx]=v[yy,xx];return out

q=js(P/'proposal.json');assert sha(read(P/'proposal.json'))=='30d7263fc10df85783ebd76089c7c0010a1cf042ef29192ef228811ac0f994ef'
prepared=js(P/'PREPARED_LOCK.json')
for name,h in prepared['files'].items():assert sha(read(P/name))==h,name
oldpath=H/'prepared_ultimate_dash01/PL02_U.ARC';newpath=P/'PL02_U.ARC'
old,new=read(oldpath),read(newpath)
assert sha(old)=='bdcf0f648e2102a208307e21a941b53439a2f342014e69981a6de156a4dfbdfb'
assert sha(new)=='03a675626035b93ad2e2feef8dd643365ed8a3e1a61a1eb02a476063e2c55e8a'
assert read(H/'ultimate_ladder_pack01/PL02_U.ARC')==new
lock=js(T/'LOCK.json');assert sha(read(T/'LOCK.json'))=='05318a68afb484c6dbe782ca12ddaee7ebe2d01a49e6a79b40a6e44e76ad2599'
meta=js(T/'targets.json');assert sha(read(T/'targets.json'))==lock['target_manifest_sha256']
for name,h in lock['files'].items():assert sha(read(T/name))==h,name
for name,h in lock['sources'].items():assert sha(read(H/name))==h,name
a,b=Archive(old),Archive(new)
refs=set(range(143,156))|{183};PBS=(0,5,6,7,8);counts=collections.Counter()
assert set(q['selected_refs'])==refs==set(meta['refs'])
assert len(old)==len(new)
assert [{k:v for k,v in e.items()if k!='sha256'}for e in psx_arc(old)]==[{k:v for k,v in e.items()if k!='sha256'}for e in psx_arc(new)]
unchanged=np.ones(len(old),bool)
for ent in psx_arc(old):
    if ent['type'] in ('0x2','0x3'):unchanged[ent['offset']:ent['offset']+ent['size']]=False
assert np.array_equal(np.frombuffer(old,np.uint8)[unchanged],np.frombuffer(new,np.uint8)[unchanged])
assert a.p==b.p
assert bank_offsets(a.g,allow_aliases=True)==bank_offsets(b.g,allow_aliases=True)
assert bank_offsets(a.c)==bank_offsets(b.c)
layers={};full={};source_rows=[]
for n in sorted(refs):
    folder=H/('ultimate_ladder_shots_registered01' if n in (150,155) else 'ultimate_ladder_contacts01')
    before=arr(folder/f'before_{n:03}_indices.png').copy();after=arr(folder/f'after_{n:03}_indices.png')
    edge=(after>0)&(before==0)
    pts=[[int(x)-160,int(y)-160,int(after[y,x])]for y,x in zip(*np.where(edge))]
    assert pts==([[-13,-3,15],[-12,-2,15],[-8,-1,15]] if n==155 else []),(n,pts)
    if n==155:
        assert a.words[15]==a.words[31]
        before[edge]=after[edge]
    same=np.all(np.array(a.rgba(before,16))==np.array(a.rgba(after,0)),2)
    expected={0:after,5:np.where(same,0,before).astype(np.uint8),**{pb:np.zeros_like(after) for pb in (6,7,8)}}
    for pb,v in expected.items():
        assert np.array_equal(arr(T/f'{n:03}_bank{pb}_indices.png'),v),(n,pb,'source layer')
        layers[n,pb]=v
    for form,v,pal in [('before',before,16),('after',after,0)]:
        assert np.array_equal(arr(T/f'{form}_{n:03}_indices.png'),v)
        full[form,n]=v
        counts['registered_full_costumes_reconstructed']+=1
    source_rows.append({'ref':n,'source_folder':rel(folder),'source_outline_added_to_jacket':pts,
                        'after_alpha_subset':bool(not np.any((after>0)&(before==0)))})

atlases={};raws={};raw_changes=[];shared=[]
for gb,(ob,nb) in enumerate(zip(a.banks,b.banks)):
    assert (ob['base'],ob['end'],len(ob['frames']))==(nb['base'],nb['end'],len(nb['frames']))
    if gb:assert a.g[ob['base']:ob['end']]==b.g[nb['base']:nb['end']]
    for of,nf in zip(ob['frames'],nb['frames']):
        n=of['index'];assert n==nf['index']
        x=decode_stream(a.g,of['offset'],of['limit'],of['tile_count']*128)
        y=decode_stream(b.g,nf['offset'],nf['limit'],nf['tile_count']*128)
        assert x.serialize()==a.g[x.start:x.end] and y.serialize()==b.g[y.start:y.end]
        counts['raw_references_checked']+=1
        if gb!=0 or n not in refs:
            assert x.data==y.data and of['tile_count']==nf['tile_count'],(gb,n,'non-target raw')
            counts['non_target_raw_exact']+=1
        else:
            assert nf['tile_count']==32
            atlases[n]=np.frombuffer(indexed_atlas(y.data,32)[0],np.uint8).reshape(32,256)
            raws[n]=y.data
            raw_changes.append({'ref':n,'old_tiles':of['tile_count'],'new_tiles':32,'raw_changed':x.data!=y.data,
                                'old_offset':of['offset'],'new_offset':nf['offset'],'decoded_sha256':sha(y.data)})
for n in sorted(refs):
    of=a.banks[0]['frames'][n];nf=b.banks[0]['frames'][n]
    oldowners=[f['index']for f in a.banks[0]['frames']if f['offset']==of['offset']]
    newowners=[f['index']for f in b.banks[0]['frames']if f['offset']==nf['offset']]
    assert oldowners==newowners and set(oldowners)<=refs
    if n==min(oldowners):shared.append({'refs':oldowners,'same_sharing':True})
sem=lambda cp:[(p['flags'],p['tile'],p['x'],p['y'])for p in cp['parts']]
gpu=[]
for pb in range(len(bank_offsets(a.c))):
    assert composition_frame(a.c,pb,0)['bank_frame_count']==composition_frame(b.c,pb,0)['bank_frame_count']
    for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
        ca,cb=composition_frame(a.c,pb,n),composition_frame(b.c,pb,n)
        if pb not in PBS or n not in refs:
            assert sem(ca)==sem(cb),(pb,n,'non-target composition')
            counts['non_target_composition_frames_exact']+=1
        else:
            for part in cb['parts']:
                t=part['tile'];assert 0<=t<32
                tile=atlases[n][t//16*16:t//16*16+16,t%16*16:t%16*16+16]
                u=int(np.count_nonzero(tile[:,0])) if t%16==0 else 0
                v=int(np.count_nonzero(tile[0])) if part['flip_y'] and t//16==0 else 0
                assert u==v==0,(pb,n,t,'GPU edge')
                if pb in (6,7,8):assert not tile.any()
                gpu.append({'ref':n,'part_bank':pb,'tile':t,'flags':part['flags'],'unsafe_u':u,'unsafe_v':v})
                counts['target_GPU_parts_checked']+=1
for n in range(237):
    if n in {105,*range(175,183)}:continue
    for pb in PBS:
        got=b.layer(n,pb)[0];counts['all_main_layers_checked']+=1
        if n in refs:
            assert np.array_equal(got,layers[n,pb]),(n,pb,'target layer')
            counts['registered_target_layers_exact']+=1
        else:
            assert np.array_equal(got,a.layer(n,pb)[0]),(n,pb,'non-target layer')
            counts['non_target_main_layers_exact']+=1
    if n not in refs:
        for mask in (0,15):assert a.composite(n,mask)[0].tobytes()==b.composite(n,mask)[0].tobytes();counts['non_target_full_display_exact']+=1
        continue
    for mask in range(16):
        for arm in (1,2):
            # The three empty layers cannot change the two explicit costume variants.
            pal=16 if mask&1 else 0;form='before'if mask&1 else'after'
            expected=a.rgba(full[form,n],pal)
            assert expected.tobytes()==b.composite(n,mask,arm)[0].tobytes(),(n,mask,arm)
            counts['partial_RGBA_exact']+=1
    for form,mask in [('before',15),('after',0)]:
        im=Image.open(P/f'{form}_{n:03}.png').convert('RGBA');read(P/f'{form}_{n:03}.png')
        assert im.tobytes()==b.composite(n,mask)[0].tobytes()
        counts['prepared_readback_PNG_exact']+=1

mirrors=[]
for src,dst,k in [(144,145,-1),(146,147,0),(149,148,0),(151,152,0)]:
    for pb in PBS:assert np.array_equal(mirror(b.layer(src,pb)[0],k),b.layer(dst,pb)[0]),(src,dst,pb)
    mirrors.append({'source':src,'target':dst,'world_transform':f'x -> -x {k:+d}; y unchanged','five_layers_exact':True,
                    'original_overlay_exception_note':'원US147/148의 overlay5 발하단+1px 예외까지 복원한 것은 아님' if dst in(147,148) else None})

gm=H/'air_barrel_guard02/master_034_mask.png';mask=arr(gm)>0
gunmaster=np.where(mask,a.layer(34,0)[0],0).astype(np.uint8)
assert int(mask.sum())==71 and np.count_nonzero(gunmaster)==60
gun_input=js(H/'ultimate_ladder_shot_inputs01/input.json')
assert sha(read(gm))==gun_input['master_mask_sha256']
for n,dx,dy in [(150,0,1),(155,3,-3)]:
    guard=shift(mask.astype(np.uint8),dx,dy)>0;gun=shift(gunmaster,dx,dy)
    assert np.array_equal(arr(H/f'ultimate_ladder_shot_inputs01/{n:03}_barrel_indices.png'),gun)
    assert np.array_equal(arr(H/f'ultimate_ladder_shot_inputs01/{n:03}_barrel_mask.png')>0,guard)
    for am in range(16):
        for arm in (1,2):
            got=np.array(b.composite(n,am,arm)[0]);want=np.array(a.rgba(gun,0))
            assert np.array_equal(got[guard],want[guard])
            counts['translated_canonical_barrel_RGBA_exact']+=1

assert counts['raw_references_checked']==512 and counts['non_target_raw_exact']==498
assert counts['registered_target_layers_exact']==70 and counts['non_target_main_layers_exact']==1070
assert counts['partial_RGBA_exact']==448 and counts['translated_canonical_barrel_RGBA_exact']==64
assert counts['non_target_composition_frames_exact']==1721 and counts['target_GPU_parts_checked']==209
for p,h in tracked.items():assert sha(p.read_bytes())==h,str(p)
proof={'passed':True,'scope':'시부키 Ultimate 사다리14의 등록 원화→공통70층→실제 자원을 제작 함수 없이 읽기 대조. 새 원화의 생성·양자화 전체 재현이나 실기는 이 검사에 포함하지 않는다.',
       'candidate':rel(newpath),'candidate_sha256':sha(new),'parent':rel(oldpath),'parent_sha256':sha(old),
       'target_lock_sha256':sha(read(T/'LOCK.json')),'counts':dict(counts),'source_reconstruction':source_rows,
       'raw_changes':raw_changes,'stream_groups':shared,'mirror_pairs':mirrors,
       'preserved':{'resource_length':True,'directory_bank_boundaries':True,'other_graphics_banks_entire_bytes':True,
                    'other_entries_and_all_outside_graphics_parts':True,'palette_audio_timing_UI':True,
                    'new_unsafe_GPU_edges':0},
       'frame155_policy':'149 새공통몸체+반동팔은 수용 기본형의 신규 제작 정책. 원US155의 허리/발 전신반동 복원이라고 주장하지 않는다.',
       'gun_policy':'각 옛 총열모양 유지가 아니라 부모 after34의60픽셀+투명11칸을 원150/155 총구로 평행등록함.',
       'limitations':['원US147/148 overlay5 발하단+1px 예외의 전층복원을 주장하지 않음','일부 원래 발끝 대비1~2px 높이차는 패킹 오류가 아니며 사다리 실기 접점 미검증','원MIPS/GPU 실행은 루트 별도; 이 보고는 디코더와 실제 조립 타일의 정적 GPU 경계 검사','미술 열람은 별도 visual_review.json에 기록'],
       'producer_functions_called':False,'native_MIPS_run_here':False,'runtime_verified':False,
       'inputs_preserved':{rel(p):h for p,h in tracked.items()}}
(O/'report.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n','utf8')
(O/'gpu_parts.json').write_text(json.dumps(gpu,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'counts':dict(counts),'report':rel(O/'report.json'),'sha256':sha((O/'report.json').read_bytes())}))
