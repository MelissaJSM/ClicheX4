"""Read-only audit of ROOT Nana ladder14; no producer/packer imports."""
from pathlib import Path
import collections,hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy.ndimage import label

D=Path(__file__).resolve().parent;ROOT=D.parents[2];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from src.psx_player import bank_offsets,composition_frame,decode_stream,indexed_atlas
L=D.parent/'root_nana_ladder';T=L/'joint_layers05';P=L/'packed_ladder07';O=D/'nana_base_ladder14_independent01';O.mkdir(exist_ok=True)
sha=lambda x:hashlib.sha256(x).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();tracked={}
def read(p):
    v=p.read_bytes();h=sha(v)
    if p in tracked:assert tracked[p]==h,(str(p),'changed')
    tracked[p]=h;return v
def js(p):return json.loads(read(p))
def arr(p):
    read(p);v=np.array(Image.open(p));assert v.shape==(384,384) and v.dtype==np.uint8 and v.max()<16;return v
def sem(cp):return [(p['flags'],p['tile'],p['x'],p['y'])for p in cp['parts']]
def mirror(z,k):
    out=np.zeros_like(z);y,x=np.nonzero(z);out[y,320-x+k]=z[y,x];return out
def bbox(mask):
    y,x=np.nonzero(mask);return[int(x.min()-160),int(y.min()-160),int(x.max()-159),int(y.max()-159)]if len(x)else None
def polygon(points):
    im=Image.new('L',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in points],fill=1);return np.array(im)>0

meta=js(T/'manifest.json');packreport=js(P/'report.json');oldpath=ROOT/meta['parent_arc'];newpath=P/'PL00_U.ARC'
old,new=read(oldpath),read(newpath)
assert sha(old)==meta['parent_sha256']=='978a9fc18e31f221d20568d747078f098f37fb120c303c64afc916442721be9f'
assert sha(new)=='509cc9785cb5eb3dca9f7a8a3fd1d3ea334887a98d3834b9f327266b3c6bbdce'
assert sha(read(T/'manifest.json'))==packreport['targets_manifest_sha256']=='1d6ac17b1e59211422a29ec72c5dba550566d17cd54f19e35e51a843b0ec873f'
a,b=Archive(old),Archive(new);PBS=(0,5,6,7,8);refs=set(range(143,156))|{183};counts=collections.Counter();layers={};original={};source_rows=[]
assert set(meta['refs'])==refs==set(packreport['refs'])
assert len(old)==len(new)
assert [{k:v for k,v in e.items()if k!='sha256'}for e in psx_arc(old)]==[{k:v for k,v in e.items()if k!='sha256'}for e in psx_arc(new)]
outside=np.ones(len(old),bool)
for e in psx_arc(old):
    if e['type']in('0x2','0x3'):outside[e['offset']:e['offset']+e['size']]=False
assert np.array_equal(np.frombuffer(old,np.uint8)[outside],np.frombuffer(new,np.uint8)[outside])
assert a.p==b.p and bank_offsets(a.g,allow_aliases=True)==bank_offsets(b.g,allow_aliases=True) and bank_offsets(a.c)==bank_offsets(b.c)
Y,X=np.indices((384,384));Y-=160;X-=160
head_centers={143:(1,-16),144:(0,-18),146:(0,-16),149:(-2,-17),151:(0,-19),153:(0,-13),154:(-6,-3),183:(0,3)}
for row in meta['frames']:
    n=row['ref']
    for pb in PBS:
        v=arr(T/f'layer{pb}_{n:03}.png');assert sha(v.tobytes())==row['layer_hashes'][str(pb)];layers[n,pb]=v
    if 'mirror_of'in row:continue
    src=row['source_new_body'];q=meta['semantic_geometry'][str(src)];ex,ey=q['eye'];owner=np.full(X.shape,6,np.uint8)
    owner[(Y>=q['lower'])|((X>=ex+10)&(Y>=ey+4))]=8
    owner[(Y<ey+6)&((X>=ex-3)|(Y<ey-2))]=5
    for poly in q['arms']:owner[polygon(poly)]=7
    cx,cy=head_centers[src];head=(X>=cx-7)&(X<cx+9)&(Y>=cy-8)&(Y<cy+8);owner[head]=5
    if n in(150,155):
        body=arr(L/f'shot_modules03/base_{n:03}_body.png');costume=arr(L/f'shot_modules03/fourth_{n:03}_body.png');arm=arr(L/f'shot_modules03/base_{n:03}_arm.png');owner[arm>0]=7
    else:
        body=arr(L/f'common_legs02/base_{n:03}_indices.png');costume=arr(L/f'common_legs02/fourth_{n:03}_indices.png')
    assert np.array_equal(owner,arr(T/f'owner_{n:03}.png')),(n,'owner')
    full=np.where(costume,costume,body).astype(np.uint8)
    palette_difference=(a.words[:16]!=a.words[16:32])[full]
    changed=((full!=body)|((costume>0)&palette_difference))&(full>0)
    expected={0:body,**{pb:np.where(changed&(owner==pb),full,0).astype(np.uint8)for pb in(5,6,7,8)}}
    for pb in PBS:assert np.array_equal(expected[pb],layers[n,pb]),(n,pb,'source reconstruction');counts['canonical_source_layers_reconstructed']+=1
    original[n]=(body,costume)
    source_rows.append({'ref':n,'source_body_ref':src,'registered_body_plus_costume_exact':True,
                        'owner_pixel_counts':{str(pb):int(np.count_nonzero(changed&(owner==pb)))for pb in(5,6,7,8)},
                        'head_crown_window_world':[cx-7,cy-8,cx+9,cy+8],
                        'after_source_alpha_outside_base':int(np.count_nonzero((costume>0)&(body==0)))})

raws={};atlases={};rawchanges=[];groups=[]
for gb,(oa,nb)in enumerate(zip(a.banks,b.banks)):
    assert (oa['base'],oa['end'],len(oa['frames']))==(nb['base'],nb['end'],len(nb['frames']))
    if gb:assert a.g[oa['base']:oa['end']]==b.g[nb['base']:nb['end']];counts['other_graphics_banks_byte_exact']+=1
    for of,nf in zip(oa['frames'],nb['frames']):
        n=of['index'];assert n==nf['index']
        od=decode_stream(a.g,of['offset'],of['limit'],of['tile_count']*128);nd=decode_stream(b.g,nf['offset'],nf['limit'],nf['tile_count']*128)
        assert od.serialize()==a.g[od.start:od.end] and nd.serialize()==b.g[nd.start:nd.end]
        counts['raw_references_checked']+=1
        if gb!=0 or n not in refs:
            assert od.data==nd.data and of['tile_count']==nf['tile_count'],(gb,n,'raw');counts['non_target_raw_exact']+=1
        else:
            assert nf['tile_count']==32
            raws[n]=nd.data;atlases[n]=np.frombuffer(indexed_atlas(nd.data,32)[0],np.uint8).reshape(32,256)
            assert not atlases[n][:,0].any()
            rawchanges.append({'ref':n,'old_tiles':of['tile_count'],'new_tiles':32,'old_stream':of['offset'],'new_stream':nf['offset'],'raw_sha256':sha(nd.data)})
for n in sorted(refs):
    oldowners=[q['index']for q in a.banks[0]['frames']if q['offset']==a.banks[0]['frames'][n]['offset']]
    newowners=[q['index']for q in b.banks[0]['frames']if q['offset']==b.banks[0]['frames'][n]['offset']]
    assert oldowners==newowners and set(oldowners)<=refs
    if n==min(oldowners):groups.append({'refs':oldowners,'original_physical_sharing_preserved':True})

gpu=[];reserved=[]
for pb in range(len(bank_offsets(a.c))):
    assert composition_frame(a.c,pb,0)['bank_frame_count']==composition_frame(b.c,pb,0)['bank_frame_count']
    for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
        ca,cb=composition_frame(a.c,pb,n),composition_frame(b.c,pb,n)
        if pb not in PBS or n not in refs:
            assert sem(ca)==sem(cb),(pb,n,'non-target parts');counts['non_target_composition_frames_exact']+=1
        else:
            for p in cb['parts']:
                t=p['tile'];assert 0<=t<32
                tile=atlases[n][t//16*16:t//16*16+16,t%16*16:t%16*16+16]
                badu=int(np.count_nonzero(tile[:,0]))if t%16==0 else 0
                badv=int(np.count_nonzero(tile[0]))if p['flip_y']and t//16==0 else 0
                assert badu==badv==0,(pb,n,t,'GPU border')
                r={'ref':n,'part_bank':pb,'tile':t,'flags':p['flags'],'x':p['x'],'y':p['y'],'u_edge_opaque':badu,'v_edge_opaque':badv}
                gpu.append(r);counts['target_GPU_parts_checked']+=1
                if t%16==0 and tile.any():
                    assert not p['flip_x'];reserved.append({**r,'first_column_zero':True,'opaque_pixels':int(np.count_nonzero(tile))})

def composite(ls,mask,arm):
    im=a.rgba(ls[0])
    for bit,pb in((8,8),(1,5),(4,7),(2,6)):
        if mask&bit:im.alpha_composite(a.rgba(ls[pb],32 if pb==7 and arm==2 else 16))
    return im
component_rows=[]
for n in range(237):
    if n in{105,*range(175,183)}:continue
    for pb in PBS:
        counts['all_main_layers_checked']+=1
        if n in refs:assert np.array_equal(b.layer(n,pb)[0],layers[n,pb]),(n,pb,'target');counts['target_layers_exact']+=1
        else:assert np.array_equal(a.layer(n,pb)[0],b.layer(n,pb)[0]),(n,pb,'non-target');counts['non_target_layers_exact']+=1
    if n not in refs:
        for mask in(0,15):assert a.composite(n,mask)[0].tobytes()==b.composite(n,mask)[0].tobytes();counts['non_target_full_displays_exact']+=1
        continue
    ls={pb:layers[n,pb]for pb in PBS}
    for mask in range(16):
        for arm in(1,2):
            got=b.composite(n,mask,arm)[0];assert got.tobytes()==composite(ls,mask,arm).tobytes();counts['independent_partial_RGBA_exact']+=1
            components=label(np.asarray(got)[:,:,3]>0,np.ones((3,3),bool))[1];assert components==1,(n,mask,arm,components)
            component_rows.append({'ref':n,'mask':mask,'arm':arm,'components8':int(components)})
    if n in original:
        body,costume=original[n];expected=a.rgba(body);expected.alpha_composite(a.rgba(costume,16))
        assert b.composite(n,15,1)[0].tobytes()==expected.tobytes();counts['canonical_full_costumes_exact']+=1

mirrors=[]
for src,dst,k in[(144,145,-1),(146,147,0),(149,148,0),(151,152,0)]:
    for pb in PBS:assert np.array_equal(mirror(layers[src,pb],k),layers[dst,pb]),(src,dst,pb)
    mirrors.append({'source':src,'target':dst,'world_x_rule':f'-x{k:+d}','world_y_unchanged':True,'all_five_layers_exact':True})
    counts['mirror_source_layers_reconstructed']+=5
shots=[]
for n in(150,155):
    oldbody=a.layer(n)[0];yy,xx=np.nonzero(oldbody);mx=int(xx.min()-160);my=int(np.median(yy[xx==xx.min()])-160)
    assert(mx,my)==({150:(-24,-9),155:(-21,-13)}[n])
    guard=(X>=mx)&(X<mx+8)&(Y>=my-3)&(Y<=my+5)
    for mask in range(16):
        for arm in(1,2):
            assert np.array_equal(np.array(a.composite(n,mask,arm)[0])[guard],np.array(b.composite(n,mask,arm)[0])[guard]),(n,mask,arm,'gun')
            counts['original_pistol_guard_RGBA_exact']+=1
    diffs={}
    for pb in PBS:
        different=b.layer(n,pb)[0]!=b.layer(149,pb)[0]
        diffs[str(pb)]={'pixels':int(different.sum()),'bbox_world':bbox(different)}
    assert not np.any(b.layer(n,8)[0]!=b.layer(149,8)[0])
    shots.append({'ref':n,'original_muzzle_world':[mx,my],'guard_world_exclusive':[mx,my-3,mx+8,my+6],
                  'guard_opaque_pixels':int(np.count_nonzero(oldbody[guard])),'new149_vs_shot_layers':diffs,
                  'source_policy':'새149 몸체와 새 사격팔의 조합. 원US155 전신반동을 복원했다는 뜻 아님.'})
assert sem(composition_frame(b.c,5,150))==sem(composition_frame(b.c,5,155))
for p in composition_frame(b.c,5,150)['parts']:
    t=p['tile'];sl=(slice(t//16*16,t//16*16+16),slice(t%16*16,t%16*16+16));assert np.array_equal(atlases[150][sl],atlases[155][sl])

native_path=L/'ladder_components_native_checks.json';native=js(native_path)
assert native['passed'] and native['resources']['PL00_U.ARC']['candidate_sha256']==sha(new)
checks={q['frame']:q for bank in native['resources']['PL00_U.ARC']['banks']if bank['bank']==0 for q in bank['native_decoder_checks']}
for n in refs:assert checks[n]['decoded_sha256']==sha(raws[n]) and checks[n]['tiles']==32

font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',13);window=(-32,-40,32,28);scale=4;cw,ch=64*scale+8,68*scale+30
def board(rows,path):
    im=Image.new('RGB',(len(rows[0][1])*cw,len(rows)*ch),'#26303c');dr=ImageDraw.Draw(im)
    for ri,(title,pics)in enumerate(rows):
        for ci,(lab,pic)in enumerate(pics):
            x,y=ci*cw,ri*ch;dr.text((x+3,y+3),f'{title} {lab}',font=font,fill='white')
            crop=pic.crop(tuple(v+160 for v in window)).resize((256,272),Image.Resampling.NEAREST);im.paste(crop,(x,y+25),crop)
    im.save(path);return {'path':rel(path),'sha256':sha(path.read_bytes()),'world_window':window,'scale':scale,'refs':[r[0]for r in rows]}
boards=[];seq=sorted(refs)
for start in range(0,len(seq),3):
    rows=[(str(n),[('이전 기본',a.composite(n)[0]),('새 기본',b.composite(n)[0]),('이전 포스',a.composite(n,15)[0]),('새 포스',b.composite(n,15)[0])])for n in seq[start:start+3]]
    boards.append(board(rows,O/f'full_readback_{start//3:02}.png'))
canonical=sorted(original)
for start in range(0,len(canonical),2):
    rows=[(str(n),[(lab,b.composite(n,mask)[0])for lab,mask in [('머리',1),('몸통',2),('팔',4),('다리',8),('몸통+다리',10)]])for n in canonical[start:start+2]]
    boards.append(board(rows,O/f'partial_readback_{start//2:02}.png'))

assert counts['raw_references_checked']==508 and counts['non_target_raw_exact']==494
assert counts['target_layers_exact']==70 and counts['non_target_layers_exact']==1070
assert counts['independent_partial_RGBA_exact']==448 and counts['original_pistol_guard_RGBA_exact']==64
assert counts['non_target_composition_frames_exact']==1717
for p,h in tracked.items():assert sha(p.read_bytes())==h,str(p)
proof={'passed':True,'scope':'나나 기본/포스 사다리14의 등록 원화·의미소유→70층→실제 패킹 자원을 제작 함수 없이 독립 읽기 대조했다.',
       'parent':rel(oldpath),'parent_sha256':sha(old),'candidate':rel(newpath),'candidate_sha256':sha(new),
       'targets_manifest_sha256':sha(read(T/'manifest.json')),'counts':dict(counts),'source_rows':source_rows,
       'original_groups_preserved':groups,'raw_changes':rawchanges,'mirror_pairs':mirrors,'shots':shots,
       'pinned_head150_155_records_and_entire_consumed_tiles_exact':True,'reserved_edge_parts':reserved,
       'preserved':{'ARC_length_directory':True,'graphics_and_parts_bank_boundaries':True,'other_graphics_banks_full_bytes':True,
                    'other_entry_palette_audio_UI':True,'non_target_part_semantics':True,'new_unsafe_GPU_edges':0},
       'native_evidence_read_only':{'path':rel(native_path),'sha256':sha(read(native_path)),'passed':True,'target14_raw_hash_binding':True,'executed_by_this_agent':False},
       'fresh_readback_sheets':boards,'actually_viewed_here':False,'producer_functions_called':False,'runtime_verified':False,
       'limits':['고정 등록 원화와 부분소유를 재구성했으며 생성 이미지의 전체 양자화 재현은 포함하지 않았다.',
                 '비대상1070층·팔레트/조립 의미 보존으로 그 조합 보존을 입증했고, 제작자7296전수와 독립448대상 검사는 구분한다.',
                 '부분판은10고유 본체를 표시한다.4반전의 부분70층관계는 수치 exact이며 일반/포스 전후판에는14참조를 모두 표시했다.',
                 '연속 원표·실제 사다리 손발 접점·게임·사용자수용은 별도다.'],
       'metadata_note':'target manifest의 status는 초기안·그림검토전이라고 남아 있다. 실제 최신 바이트와 단계는 이 증거 및 루트 후속검토로 구분한다.',
       'input_hashes':{rel(p):h for p,h in tracked.items()}}
(O/'report.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n','utf8')
(O/'gpu_parts.json').write_text(json.dumps(gpu,ensure_ascii=False,indent=2)+'\n','utf8')
(O/'partial_components.json').write_text(json.dumps(component_rows,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'counts':dict(counts),'report':rel(O/'report.json'),'sha256':sha((O/'report.json').read_bytes())}))
