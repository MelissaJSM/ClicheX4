"""Ultimate90/91 독립 원화/자원 reader. 제작 함수와 게임은 실행하지 않는다."""
from pathlib import Path
import collections, hashlib, json, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import label, binary_dilation
ROOT = Path(__file__).resolve().parents[3]
D = Path(__file__).parent
sys.path[:0] = [str(ROOT), str(D)]
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from src.psx_player import bank_offsets, composition_frame
from verify_shibuki_ultimate_hurt13_independent import raw, parts, sig, tile, color, polygons
N = D.parent/'nana_audit'
U = N/'ultimate_recoil_repaint'
P = U/'packed_recoil_candidate_v1'
T = U/'targets_v1'
C = U/'common_probe_v2'
O = D/'nana_ultimate_recoil2_independent01'
PBS = (0,5,6,7,8)
REFS = (90,91)
RESERVED = {105,*range(175,183)}
sha = lambda v: hashlib.sha256(v).hexdigest()
rel = lambda p: p.relative_to(ROOT).as_posix()
tracked = {}
def blob(p):
    v=p.read_bytes();tracked[rel(p)]=sha(v);return v
def js(p): return json.loads(blob(p))
def png(p): blob(p);return np.asarray(Image.open(p))
oldp=N/'ultimate_standing_repaint/packed_standing_candidate_v1/PL02_U.ARC'
newp=P/'PL02_U.ARC'
old,new=blob(oldp),blob(newp)
assert sha(old)=='0e69e9e3823c95bfce5b10746f77c587cd6f9e177cdd69b04938e868f3b77331'
assert sha(new)=='ce61617f541fd59a5a3ab0b26bba6ce88cc7740bf5f9d4719c9acb129783c8d0'
a,b=Archive(old),Archive(new)
lock=js(P/'INPUT_FROZEN.json')
assert sha(blob(P/'INPUT_FROZEN.json'))=='5adde5610c628ee33cc8ab15fc2e14ab9023d7902edc0503a7788f7add4c9dd7'
assert lock['parent_sha256']==sha(old) and lock['candidate_sha256']==sha(new)
for q in lock['files']:assert sha(blob(ROOT/q['path']))==q['sha256'],q['path']
assert len(lock['files'])==64
meta=js(T/'manifest.json');cm=js(C/'manifest.json')
assert meta['refs']==list(REFS) and meta['parent_arc_sha256']==cm['parent_arc_sha256']==sha(old)
assert sha(blob(T/'manifest.json'))==lock['target_manifest_sha256']
assert sha(blob(C/'manifest.json'))==meta['common_manifest_sha256']
assert sha(blob(oldp.parent/'FROZEN.json'))==meta['parent_frozen_sha256']
art=U/'a_v1/generated.png';assert sha(blob(art))==cm['source_art_sha256']=='c78d7de88c8b807535d2612e4d9ca8c5ab7e3d89ff20153c7ea4f7ba1733f242'
image=Image.open(art).convert('RGBA');assert image.size==(1254,1254)
registration=js(U/'first_registered_v1/registration.json')
palette=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words],np.float32)
counts=collections.Counter();registered={};quant=[]
def vote(cell,pal,world,excluded):
    ar=np.array(cell);alpha=ar[:,:,3].astype(np.float32)/255
    available=np.array([i for i in range(1,16)if i not in excluded]);indices=np.empty(ar.shape[:2],np.uint8)
    for y in range(len(indices)):
        delta=ar[y,:,:3].astype(np.float32)[:,None,:]-pal[available][None,:,:]
        indices[y]=available[np.square(delta).sum(2).argmin(1)]
    x,y=world;x+=48;y+=48
    votes={str(int(v)):float(np.asarray(Image.fromarray(np.where(indices==v,alpha,0).astype(np.float32),'F').resize((96,96),Image.Resampling.BOX))[y,x])for v in available}
    return int(max(votes,key=votes.get)),votes
for row,form,start in((0,'before',16),(1,'after',0)):
    for col,n in enumerate(REFS):
        crop=[col*627,row*627,(col+1)*627,(row+1)*627]
        cell=image.crop(crop);ar=np.array(cell);rgb=ar[:,:,:3].astype(np.float32);alpha=ar[:,:,3].astype(np.float32)/255
        ix=np.empty(alpha.shape,np.uint8)
        for y in range(len(ix)):
            ix[y]=1+np.square(rgb[y,:,None,:]-palette[start+1:start+16][None,:,:]).sum(2).argmin(1)
        green=(rgb[:,:,1]>rgb[:,:,0]+15)&(rgb[:,:,1]>rgb[:,:,2]+15)&(ar[:,:,3]>=128)
        green[len(green)//2:]=False;ix[green]=14
        votes=np.stack([np.asarray(Image.fromarray(np.where(ix==i,alpha,0).astype(np.float32),'F').resize((96,96),Image.Resampling.BOX))for i in range(1,16)])
        coverage=np.asarray(Image.fromarray(alpha,'F').resize((96,96),Image.Resampling.BOX))
        small=1+votes.argmax(0).astype(np.uint8);small[coverage<.5]=0
        eyes=votes[13].copy();eyes[coverage<.5]=0;eyes[48:]=0
        if eyes.max()>.015:small[np.unravel_index(eyes.argmax(),eyes.shape)]=14
        z=np.zeros((384,384),np.uint8);z[112:208,112:208]=small
        q=next(q for q in registration['frames']if q['form']==form and q['ref']==n)
        assert q['source_crop']==crop and q['native_sha256']==sha(z.tobytes())
        assert np.array_equal(z,png(U/f'first_registered_v1/{form}_{n:03}_indices.png'))
        registered[form,n]=z
        quant.append({'ref':n,'form':form,'source_crop':crop,'fixed96_vote_exact':True})
Y,X=np.indices((384,384));Y-=160;X-=160
original85=a.layer(85)[0]
gun=np.where((X>=-22)&(X<=-15)&(Y>=-11)&(Y<=-6)&np.isin(original85,range(1,10)),original85,0).astype(np.uint8)
assert np.count_nonzero(gun)==20
case=np.zeros_like(gun);case[:,:-2]=gun[:,2:]
body={};source_rows=[]
for col,n in enumerate(REFS):
    rec=next(q for q in cm['frames']if q['ref']==n);corrected={}
    for row,form,start in((0,'before',16),(1,'after',0)):
        z=registered[form,n].copy();cell=image.crop((col*627,row*627,(col+1)*627,(row+1)*627))
        for q in rec['eye_source']:
            if q['form']!=form:continue
            x,y=q['world'];assert z[y+160,x+160]==z[y+161,x+160]==14
            v,votes=vote(cell,palette[start:start+16],(x,y),{14,15})
            assert v==q['value'] and votes==q['votes'] and v in(1,2)
            z[y+160,x+160]=v;counts['iris_source_cells']+=1
        corrected[form]=z
    before=corrected['before'];donor=corrected['after'];after=before.copy()
    cell=image.crop((col*627,0,(col+1)*627,627))
    assert sorted(tuple(q['world'])for q in rec['face15_source'])==sorted((int(x-160),int(y-160))for y,x in np.argwhere(before==15))
    for q in rec['face15_source']:
        x,y=q['world'];value,votes=vote(cell,palette[:16],(x,y),{15})
        assert value==q['value'] and votes==q['votes']
        after[y+160,x+160]=value;counts['palette15_source_cells']+=1
    mask=polygons([rec['costume_polygon']])
    for q in rec['source_boundary_links']:
        x,y=q['world'];assert before[y+160,x+160]==q['before_index'] and donor[y+160,x+160]==q['source_after_index']
        mask[y+160,x+160]=True;counts['source_boundary_cells']+=1
    after[mask]=donor[mask];weapon=rec['weapon'];weapon_proof={}
    if n==90:
        assert weapon['polygon']==[[-20,-20],[-11,-20],[-11,-10],[-20,-10]]
        shared=polygons([weapon['polygon']]);after[shared]=before[shared]
        weapon_proof={'new_before_diagonal_gun_hand_shared':True,'canonical85_claim':False}
    else:
        assert weapon['module_sha256']==sha(gun.tobytes()) and weapon['translation']==[-2,0]
        contacts=[]
        for form,z in(('before',before),('after',after)):
            initial=z.copy()
            skin=(X>=-22)&(X<=-17)&(Y>=-9)&(Y<=-6)&np.isin(z,(10,11,12,13))
            remove=(X>=-25)&(X<=-17)&(Y>=-13)&(Y<=-7)&((Y<=-10)|(X<=-20))&np.isin(z,range(1,10))
            q=next(q for q in weapon['registrations']if q['form']==form)
            assert q['removed_source_cells']==[[int(x-160),int(y-160),int(initial[y,x])]for y,x in np.argwhere(remove)]
            assert q['preserved_skin_cells']==[[int(x-160),int(y-160),int(initial[y,x])]for y,x in np.argwhere(skin)]
            z[remove]=0;visible=(case>0)&~skin;z[visible]=case[visible];z[skin]=initial[skin]
            contact=int(((case>0)&binary_dilation(skin,np.ones((3,3)))).sum())
            assert contact==q['gun_skin_contact8']
            contacts.append({'form':form,'visible_canonical_cells':int(visible.sum()),'preserved_skin':int(skin.sum()),'contact8':contact})
        shared=(case>0)|((X>=-22)&(X<=-17)&(Y>=-9)&(Y<=-6)&np.isin(before,(10,11,12,13)))
        assert weapon['common_cells']==[[int(x-160),int(y-160),int(before[y,x])]for y,x in np.argwhere(shared)]
        after[shared]=before[shared]
        weapon_proof={'canonical85_module':sha(gun.tobytes()),'module_cells':20,'translation':[-2,0],'registrations':contacts,'only_module_and_skin_shared':True,'black_cuff_not_shared_by_rectangle':True,'single_frame_firing_origin_verified':False}
    for tag,z in(('before',before),('after',after),('donor',donor),('costume_mask',mask.astype(np.uint8)*255),('outside',((after>0)&(before==0)).astype(np.uint8)*255)):
        assert np.array_equal(z,png(C/f'{tag}_{n:03}_indices.png'))
    assert not np.any((after>0)&(before==0))
    assert label(before>0,np.ones((3,3)))[1]==label(after>0,np.ones((3,3)))[1]==1
    body['before',n],body['after',n]=before,after
    source_rows.append({'ref':n,'source_only_boundary_cells':len(rec['source_boundary_links']),'weapon':weapon_proof,'body_translation':[0,0]})
target={}
for n in REFS:
    before,after=body['before',n],body['after',n]
    target[n,0]=after
    pd=np.array([a.words[i]!=a.words[i+16]for i in range(16)])[before]
    target[n,5]=np.where((before!=after)|pd,before,0).astype(np.uint8)
    for pb in(6,7,8):target[n,pb]=np.zeros_like(after)
    for pb in PBS:
        assert np.array_equal(target[n,pb],png(T/f'layer{pb}_{n:03}.png'))
        assert sha(target[n,pb].tobytes())==meta['targets'][str(n)][str(pb)]

assert len(old)==len(new) and a.p==b.p
ae,be=psx_arc(old),psx_arc(new)
assert [(q['type'],q['offset'],q['size'])for q in ae]==[(q['type'],q['offset'],q['size'])for q in be]
allow=np.zeros(len(old),bool)
for q in ae:
    if int(q['type'],16)in(2,3):allow[q['offset']:q['offset']+q['size']]=True
assert not np.any((np.frombuffer(old,np.uint8)!=np.frombuffer(new,np.uint8))&~allow)
assert bank_offsets(a.g,allow_aliases=True)==bank_offsets(b.g,allow_aliases=True) and bank_offsets(a.c)==bank_offsets(b.c)
for gb,(ab,bb)in enumerate(zip(a.banks,b.banks)):
    assert(ab['base'],ab['end'],len(ab['frames']))==(bb['base'],bb['end'],len(bb['frames']))
    if gb:assert a.g[ab['base']:ab['end']]==b.g[bb['base']:bb['end']]
    for af,bf in zip(ab['frames'],bb['frames']):
        n=af['index'];assert n==bf['index'];counts['raw_checked']+=1
        if gb==0 and n in REFS:assert bf['tile_count']==32
        else:assert raw(a,gb,n)==raw(b,gb,n) and af['tile_count']==bf['tile_count'];counts['non_target_raw_exact']+=1
for n in REFS:
    for ar in(a,b):assert[f['index']for f in ar.banks[0]['frames']if f['offset']==ar.banks[0]['frames'][n]['offset']]==[n]
reserved=[]
for n in range(237):
    for pb in PBS:
        if n in RESERVED:
            try:b.layer(n,pb)
            except(ValueError,IndexError)as ex:
                try:a.layer(n,pb)
                except(ValueError,IndexError)as ex2:assert type(ex)==type(ex2) and str(ex)==str(ex2)
                else:raise AssertionError('new invalid layer')
                reserved.append({'ref':n,'layer':pb,'state':'same_render_exception'});continue
            assert np.array_equal(b.layer(n,pb)[0],a.layer(n,pb)[0]);counts['reserved_renderable_exact']+=1
            reserved.append({'ref':n,'layer':pb,'state':'rendered_exact'});continue
        expected=target[n,pb]if n in REFS else a.layer(n,pb)[0]
        assert np.array_equal(b.layer(n,pb)[0],expected),(n,pb)
        counts['target_layers_exact'if n in REFS else'non_target_layers_exact']+=1
shared=[]
for pb in range(len(bank_offsets(a.c))):
    aps={n:parts(a,pb,n)for n in range(composition_frame(a.c,pb,0)['bank_frame_count'])}
    addresses={q['record_offset']for n in REFS if n in aps and pb in PBS for q in aps[n]}
    for n,ps in aps.items():
        qs=parts(b,pb,n)
        if pb in PBS and n in REFS:
            for q in qs:
                t=q['tile']+q['page']*256;assert 0<=t<32 and q['unknown_flags']==0
                value=tile(b,n,t);assert not(t%16==0 and value[:,0].any()) and not(q['flip_y']and t//16==0 and value[0].any())
                counts['GPU_parts_checked']+=1
        else:
            assert[sig(q)for q in ps]==[sig(q)for q in qs];counts['non_target_compositions_exact']+=1
            overlap=sorted(addresses&{q['record_offset']for q in ps})
            if overlap:shared.append({'bank':pb,'ref':n,'old_shared_offsets':overlap,'nonselected_records_exact':True})
for n in REFS:
    for mask in range(16):
        for arm in(1,2):
            expected=color(b,target[n,0])
            for bit,pb in((8,8),(1,5),(4,7),(2,6)):
                if mask&bit:
                    v=color(b,target[n,pb],32 if pb==7 and arm==2 else 16);m=v[:,:,3]>0;expected[m]=v[m]
            actual=np.asarray(b.composite(n,mask,arm)[0])
            assert np.array_equal(actual,expected)
            assert np.array_equal(actual,color(b,body['before'if mask&1 else'after',n],16 if mask&1 else 0))
            counts['partial_RGBA_exact']+=1
nativep=U/'native_components_v1_native_checks.json';native=js(nativep);assert native['passed']
resource=native['resources']['PL02_U.ARC'];assert resource['candidate_sha256']==sha(new)
native_checks=next(q for q in resource['banks']if q['bank']==0)['native_decoder_checks']
for n in REFS:
    q=next(q for q in native_checks if q['frame']==n)
    assert q['decoded_sha256']==sha(raw(b,0,n)) and q['buffer_outside_and_unused_tail_preserved']
O.mkdir(exist_ok=True);sheets=[]
for form in('before','after'):
    mask=15 if form=='before'else 0;box=(125,128,190,187);w,h=box[2]-box[0],box[3]-box[1]
    cw,ch=w*5+10,h*5+26;board=Image.new('RGB',(cw*3,ch*2),'#263345');draw=ImageDraw.Draw(board)
    for row,n in enumerate(REFS):
        for col,(caption,im)in enumerate((('old',a.composite(n,mask)[0]),('new',b.composite(n,mask)[0]),('idle',b.composite(0,mask)[0]))):
            bb=im.getbbox();assert box[0]<=bb[0] and box[1]<=bb[1] and box[2]>=bb[2] and box[3]>=bb[3]
            x,y=col*cw,row*ch;draw.text((x+4,y+4),f'{n} {form} {caption}',fill='white')
            z=im.crop(box).resize((w*5,h*5),Image.Resampling.NEAREST);board.paste(z,(x+4,y+22),z)
    p=O/f'{form}_readback.png';board.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes()),'no_clipping':True})
assert counts['raw_checked']==512 and counts['non_target_raw_exact']==510 and counts['target_layers_exact']==10 and counts['partial_RGBA_exact']==64
assert counts['source_boundary_cells']==19 and len(reserved)==45
for path,h in tracked.items():assert sha((ROOT/path).read_bytes())==h,path
report={'passed':True,'scope':'Nana Ultimate90/91의 새4셀 직접재양자화→홍채·의상경계19셀·정본/새총→10층→실제자원 독립 읽기',
    'candidate':rel(newp),'candidate_sha256':sha(new),'parent_sha256':sha(old),'input_frozen_sha256':sha((P/'INPUT_FROZEN.json').read_bytes()),'locked_inputs':len(lock['files']),
    'counts':dict(counts),'source_quantization':quant,'source_registration':source_rows,'independent90_91_streams':True,
    'nonselected_shared_compositions':shared,'reserved':reserved,'palette_audio_other_entries_bank_boundaries_exact':True,
    'native_MIPS_existing_evidence':{'path':rel(nativep),'sha256':sha(nativep.read_bytes()),'two_decoded_hashes_match':True,'executed_here':False},
    'readback_sheets':sheets,'readback_actually_viewed':False,'inputs':tracked,'producer_functions_called':False,'runtime_verified':False,'user_accepted':False,'overall_complete':False,
    'limits':['대상64 RGBA와 비대상1130층/1781조립/510raw를 직접 대조했다. 전체7296RGBA 재실행은 아니다.','91 정본20texel과 새 피부 가림·공유는 확인했으나 단독 발사원점 증명은 아니다.','원MIPS 기존결과를 실제후보와 결속했으며 새MIPS/브라우저/실기는 실행하지 않았다.']}
p=O/'report.json';p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'report_sha256':sha(p.read_bytes()),'counts':dict(counts)},ensure_ascii=False))
