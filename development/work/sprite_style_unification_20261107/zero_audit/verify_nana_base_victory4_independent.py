"""나나 기본/포스 승리4 독립 읽기: 제작 모듈을 호출하지 않는다."""
from pathlib import Path
import collections, hashlib, json, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import label
ROOT = Path(__file__).resolve().parents[3]
D = Path(__file__).parent
B = D.parent
sys.path[:0] = [str(ROOT), str(D)]
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from src.psx_player import bank_offsets, composition_frame
from verify_shibuki_ultimate_hurt13_independent import raw, parts, sig, tile, color, polygons, render
S = B/'root_nana_victory'
T = S/'joint_targets01'
P = S/'packed_victory02'
O = D/'nana_base_victory4_independent01'
PBS = (0, 5, 6, 7, 8)
REFS = (204, 205, 206, 207)
RESERVED = {105, *range(175, 183)}
sha = lambda b: hashlib.sha256(b).hexdigest()
rel = lambda p: p.relative_to(ROOT).as_posix()
tracked = {}
def blob(p):
    b = p.read_bytes(); tracked[rel(p)] = sha(b); return b
def js(p): return json.loads(blob(p))
def png(p): blob(p); return np.array(Image.open(p))
def poly(points): return polygons([points])
def spans(row):
    xs = np.flatnonzero(row)
    return [] if not len(xs) else np.split(xs, np.flatnonzero(np.diff(xs)>1)+1)
Y, X = np.indices((384, 384)); Y -= 160; X -= 160
oldp = B/'root_nana_arrival/packed_arrival01/PL00_U.ARC'
newp = P/'PL00_U.ARC'
old, new = blob(oldp), blob(newp)
assert sha(old) == '9599ca5fc21828df5ef4d865eafab4d27aa06a7b2391873a063c887120e70f91'
assert sha(new) == '90c614a7996d65ff71381ccc1f673cbfa13b84eccafec83c2e919010310b9239'
a, b = Archive(old), Archive(new)
meta = js(T/'manifest.json')
assert meta['parent_sha256'] == sha(old) and meta['refs'] == list(REFS)
registered = {}; quant = []
sources = [
    ('a01', (204,205), '855aca5daa799c8377bec2ccb99e90e0a194877c1b5c7e4e52a17c6c5581ccc4'),
    ('206_03', (206,), '40f13e2f34a113c84a7a4643a15dfb0784236e037a96debc462a162577a459ce'),
    ('b01', (207,), 'a759008c23065cbf8224ca80c20e436199f4d070af734619c1544ebd35605981'),
]
for name, selected, expected in sources:
    ap = S/f'art_{name}/generated.png'
    assert sha(blob(ap)) == expected
    image = Image.open(ap).convert('RGBA')
    regdir = S/f'registered_{name}'
    reg = js(regdir/'manifest.json')
    assert reg['source_sha256'] == expected and reg['source_size'] == list(image.size)
    assert reg['parent_sha256'] == sha(old)
    for q in reg['frames']:
        form, n = q['form'], q['ref']
        if n not in selected: continue
        start = 16 if form == 'fourth' else 0
        palette = np.array([[(int(w)>>s&31)*255//31 for s in (0,5,10)] for w in a.words[start:start+16]], np.float32)
        rgba = np.asarray(image.crop(q['source_crop']))
        rgb = rgba[:,:,:3].astype(np.float32); alpha = rgba[:,:,3].astype(np.float32)/255
        index = np.empty(alpha.shape, np.uint8)
        for y in range(len(index)):
            index[y] = 1+np.square(rgb[y,:,None,:]-palette[None,1:,:]).sum(2).argmin(1)
        green = (rgb[:,:,1]>rgb[:,:,0]+15)&(rgb[:,:,1]>rgb[:,:,2]+15)&(rgba[:,:,3]>=128)
        green[len(green)//2:] = False; index[green] = 14
        votes = np.stack([np.asarray(Image.fromarray(np.where(index==i,alpha,0).astype(np.float32),'F').resize((96,96),Image.Resampling.BOX)) for i in range(1,16)])
        coverage = np.asarray(Image.fromarray(alpha,'F').resize((96,96),Image.Resampling.BOX))
        small = 1+votes.argmax(0).astype(np.uint8); small[coverage<.5] = 0
        eyes = votes[13].copy(); eyes[coverage<.5] = 0; eyes[48:] = 0
        if eyes.max()>.015: small[np.unravel_index(eyes.argmax(),eyes.shape)] = 14
        z = np.zeros((384,384),np.uint8); z[112:208,112:208] = small
        assert sha(z.tobytes()) == q['indices_sha256']
        assert np.array_equal(z,png(regdir/f'{form}_{n:03}_indices.png'))
        assert sha(color(a,z,start).tobytes()) == q['rgba_sha256']
        registered[form,n] = z
        quant.append({'ref':n,'form':form,'generated_source':rel(ap),'source_sha256':expected,'crop':q['source_crop'],'fixed96_vote_exact':True})
assert len(registered) == 8
target = {}; bodies = {}; proof = []
grips = {204:[[-14,-6],[-3,-6],[-3,2],[-14,2]],205:[[-15,-18],[-5,-18],[-5,-8],[-15,-8]],206:[[-14,-21],[-8,-21],[-8,-8],[-14,-8]],207:[[-15,-39],[-7,-39],[-7,-23],[-15,-23]]}
for n in REFS:
    record = next(q for q in meta['frames'] if q['ref']==n)
    base, fourth = registered['base',n].copy(), registered['fourth',n].copy()
    translation = [0,-5] if n==207 else [0,0]
    assert record['rigid_translation'] == translation and not record['bbox_rescale']
    if n==207:
        assert not base[:5].any() and not fourth[:5].any()
        base = np.roll(base,-5,0); fourth = np.roll(fourth,-5,0)
    assert record['shared_grip_polygon'] == grips[n]
    grip = poly(grips[n]); fourth[grip] = base[grip]
    facepts = [[-8,-23],[-1,-23],[-1,-13],[-8,-13]] if n==207 else [[-7,-17],[1,-17],[1,-9],[-7,-9]]
    assert record['shared_face_polygon'] == facepts
    face = poly(facepts); fourth[face] = base[face]
    donor = fourth.copy(); links = []; max_extension = 0
    for y in range(164 if n==207 else 165,183):
        gaps = spans((base[y]>0)&(fourth[y]==0)); runs = spans(donor[y]>0)
        for gap in gaps:
            assert runs
            near = min(runs,key=lambda row:np.abs(row[:,None]-gap).min())
            left = min(int(near[0]),int(gap[0])); right = max(int(near[-1]),int(gap[-1]))
            extension = max(int(near[0])-left,right-int(near[-1]))
            assert extension<=3
            max_extension = max(max_extension,extension)
            destinations = np.arange(left,right+1)
            assert len(destinations)<=max(3,len(near)*2)
            source_x = near[np.rint(np.linspace(0,len(near)-1,len(destinations))).astype(int)]
            fourth[y,destinations] = donor[y,source_x]
            links.extend({'dst':[int(x-160),y-160],'src':[int(sx-160),y-160],'index':int(donor[y,sx])} for x,sx in zip(destinations,source_x))
    assert links == record['same_row_new_leg_registration']
    inherited = [[int(x-160),int(y-160),int(base[y,x])] for y,x in np.argwhere((base>0)&(fourth==0))]
    assert inherited == record['new_base_shared_outer_pixels']
    owner = np.full(base.shape,6,np.uint8)
    owner[(Y>=5)|((X>=7)&(Y>=-10))] = 8
    owner[(Y<=(-12 if n==207 else -7))&(X>=-9)] = 5
    owner[(X>=7)&(Y<=4)] = 5
    owner[poly([[1,-13 if n==207 else -9],[9,-9 if n==207 else -6],[11,3],[6,6],[1,0]])] = 7
    owner[grip] = 7; owner[face] = 5
    full = np.where(fourth,fourth,base).astype(np.uint8)
    pd = np.array([a.words[i]!=a.words[i+16] for i in range(16)])[full]
    different = ((full!=base)|(pd&(fourth>0)))&(full>0)
    ls = {0:base,**{pb:np.where(different&(owner==pb),full,0).astype(np.uint8) for pb in PBS[1:]}}
    for pb,z in ls.items():
        assert np.array_equal(z,png(T/f'layer{pb}_{n:03}.png'))
        assert sha(z.tobytes()) == record['layer_hashes'][str(pb)]
        target[n,pb] = z
    assert np.array_equal(fourth,png(T/f'fourth_body_{n:03}.png'))
    assert np.array_equal(owner,png(T/f'owner_{n:03}.png'))
    bodies[n] = (base,fourth)
    proof.append({'ref':n,'translation':translation,'shared_new_face_grip_exact':True,'leg_source_links':len(links),'leg_max_row_extension':max_extension,'inherited_new_base_outer_pixels':inherited,'owner_reconstructed':True,'old_body_pixels_copied':False})

counts = collections.Counter()
assert len(old)==len(new) and a.p==b.p
ae,be = psx_arc(old),psx_arc(new)
assert [(q['type'],q['offset'],q['size'])for q in ae] == [(q['type'],q['offset'],q['size'])for q in be]
allow = np.zeros(len(old),bool)
for q in ae:
    if int(q['type'],16) in (2,3): allow[q['offset']:q['offset']+q['size']] = True
assert not np.any((np.frombuffer(old,np.uint8)!=np.frombuffer(new,np.uint8))&~allow)
assert bank_offsets(a.g,allow_aliases=True)==bank_offsets(b.g,allow_aliases=True)
assert bank_offsets(a.c)==bank_offsets(b.c)
for gb,(ab,bb) in enumerate(zip(a.banks,b.banks)):
    assert (ab['base'],ab['end'],len(ab['frames'])) == (bb['base'],bb['end'],len(bb['frames']))
    if gb: assert a.g[ab['base']:ab['end']] == b.g[bb['base']:bb['end']]
    for af,bf in zip(ab['frames'],bb['frames']):
        n = af['index']; assert n==bf['index']; counts['raw_checked'] += 1
        if gb==0 and n in REFS: assert bf['tile_count']==32
        else:
            assert raw(a,gb,n)==raw(b,gb,n) and af['tile_count']==bf['tile_count']
            counts['non_target_raw_exact'] += 1
for n in range(237):
    if n in RESERVED: continue
    for pb in PBS:
        expected = target[n,pb] if n in REFS else a.layer(n,pb)[0]
        assert np.array_equal(expected,b.layer(n,pb)[0]),(n,pb)
        counts['target_layers_exact' if n in REFS else 'non_target_layers_exact'] += 1
shared = []
for pb in range(len(bank_offsets(a.c))):
    aps = {n:parts(a,pb,n) for n in range(composition_frame(a.c,pb,0)['bank_frame_count'])}
    addresses = {q['record_offset'] for n in REFS if n in aps and pb in PBS for q in aps[n]}
    for n,ps in aps.items():
        qs = parts(b,pb,n)
        if pb in PBS and n in REFS:
            for q in qs:
                t = q['tile']+q['page']*256
                assert 0<=t<32 and q['unknown_flags']==0
                value = tile(b,n,t)
                assert not(t%16==0 and value[:,0].any())
                assert not(q['flip_y'] and t//16==0 and value[0].any())
                counts['GPU_parts_checked'] += 1
        else:
            assert [sig(q)for q in ps]==[sig(q)for q in qs]
            counts['non_target_compositions_exact'] += 1
            overlap = sorted(addresses & {q['record_offset']for q in ps})
            if overlap: shared.append({'bank':pb,'ref':n,'old_shared_record_offsets':overlap,'nonselected_records_exact':True})
reserved = []
for n in sorted(RESERVED):
    for pb in PBS:
        results = []
        for ar in (a,b):
            try: results.append(('renderable',ar.layer(n,pb)[0]))
            except Exception as exc: results.append((type(exc).__name__,str(exc)))
        assert results[0][0] == results[1][0]
        if results[0][0]=='renderable':
            assert np.array_equal(results[0][1],results[1][1]); counts['reserved_renderable_exact'] += 1
        else:
            assert results[0][1] == results[1][1]; counts['reserved_same_exception'] += 1
        reserved.append({'ref':n,'layer':pb,'status':results[0][0]})
for n in REFS:
    for mask in range(16):
        for arm in (1,2):
            expected = color(b,target[n,0])
            for bit,pb in ((8,8),(1,5),(4,7),(2,6)):
                if mask&bit:
                    v = color(b,target[n,pb],32 if pb==7 and arm==2 else 16); m = v[:,:,3]>0; expected[m] = v[m]
            actual = np.asarray(b.composite(n,mask,arm)[0])
            assert np.array_equal(expected,actual)
            assert label(actual[:,:,3]>0,np.ones((3,3)))[1] == 1
            counts['partial_RGBA_exact'] += 1
    for mask in (0,15):
        bb,ff = bodies[n]; expected = color(b,bb)
        if mask: m=ff>0; expected[m] = color(b,ff,16)[m]
        assert np.array_equal(expected,np.asarray(b.composite(n,mask,1)[0]))

head45 = parts(a,5,45)
source_tail = [sig(p)for p in head45[-2:]]
expected_sig = [(0,6,-9,-22),(0,1,4,-20),(0,31,-12,-38),(0,30,10,-4)]
assert source_tail == expected_sig[:2]
head_proof = []
for n in REFS:
    ps = parts(b,5,n)
    assert [sig(p)for p in ps] == expected_sig
    assert np.array_equal(render(b,n,5,ps),target[n,5])
    assert not np.array_equal(target[n,5],a.layer(45,5)[0])
    assert [p['record_offset']for p in ps[:2]] == [p['record_offset']for p in parts(b,5,45)[-2:]]
    assert [p['record_offset']for p in ps] == [p['record_offset']for p in parts(b,5,204)]
    assert [f['index']for f in a.banks[0]['frames']if f['offset']==a.banks[0]['frames'][n]['offset']] == [n]
    assert [f['index']for f in b.banks[0]['frames']if f['offset']==b.banks[0]['frames'][n]['offset']] == [n]
    head_proof.append({'ref':n,'record_signatures':expected_sig,'record_addresses':[p['record_offset']for p in ps],'first_two_alias_parent45_tail':True,'four_new_heads_share_records_only':True,'all_rendered_head_pixels_match_new_target':True,'head_bitmap45_not_copied':True,'independent_graphics_stream':True})
assert raw(a,0,45) == raw(b,0,45)
for pb in PBS:
    assert [sig(p)for p in parts(a,pb,45)] == [sig(p)for p in parts(b,pb,45)]
    assert np.array_equal(a.layer(45,pb)[0],b.layer(45,pb)[0])
nativep = S/'victory_components_native_checks.json'
native = js(nativep); assert native['passed']
resource = native['resources']['PL00_U.ARC']; assert resource['candidate_sha256']==sha(new)
checks = next(q for q in resource['banks']if q['bank']==0)['native_decoder_checks']
for n in REFS:
    q = next(q for q in checks if q['frame']==n)
    assert q['decoded_sha256']==sha(raw(b,0,n)) and q['buffer_outside_and_unused_tail_preserved']

O.mkdir(exist_ok=True); sheets = []
def board(items,name,columns,scale=5):
    boxes = [im.getbbox()for _,im in items if im.getbbox()]
    x0=min(z[0]for z in boxes)-3; y0=min(z[1]for z in boxes)-3
    x1=max(z[2]for z in boxes)+3; y1=max(z[3]for z in boxes)+3
    cw=(x1-x0)*scale+10; ch=(y1-y0)*scale+25
    image=Image.new('RGB',(cw*columns,ch*((len(items)+columns-1)//columns)),'#263345');draw=ImageDraw.Draw(image)
    for i,(title,im)in enumerate(items):
        x=i%columns*cw; y=i//columns*ch
        pic=im.crop((x0,y0,x1,y1)).resize(((x1-x0)*scale,(y1-y0)*scale),Image.Resampling.NEAREST)
        image.paste(pic,(x+5,y+22),pic);draw.text((x+5,y+3),title,fill='white')
    p=O/name;image.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes()),'same_origin':True,'no_opaque_clipping':True})
for n in REFS:
    board([(f'{n} {title}',ar.composite(n,mask,1)[0])for ar,mask,title in ((a,0,'old base'),(b,0,'new base'),(a,15,'old fourth'),(b,15,'new fourth'))],f'full_{n:03}.png',4)
    board([(f'{n} {title}',b.composite(n,mask,2)[0])for mask,title in ((1,'head'),(2,'body'),(4,'arms'),(8,'legs'),(10,'body+legs'))],f'partial_{n:03}.png',5)
assert counts['raw_checked']==508 and counts['non_target_raw_exact']==504
assert counts['target_layers_exact']==20 and counts['partial_RGBA_exact']==128
for path,h in tracked.items(): assert sha((ROOT/path).read_bytes())==h,path
report = {
    'passed':True,'scope':'기본/포스 승리204..207의 새 원화8셀→96고정등록→얼굴/손/동일행 다리→20층→실제자원 독립 읽기',
    'candidate':rel(newp),'candidate_sha256':sha(new),'parent':rel(oldp),'parent_sha256':sha(old),
    'target_manifest_sha256':sha((T/'manifest.json').read_bytes()),'counts':dict(counts),
    'source_quantization':quant,'source_registration':proof,'head_records':head_proof,
    'parent45_raw_layers_records_exact':True,'nonselected_shared_compositions':shared,'reserved':reserved,
    'other_entries_palette_audio_bank_boundaries_exact':True,
    'native_MIPS_existing_evidence':{'path':rel(nativep),'sha256':sha(nativep.read_bytes()),'four_decoded_hashes_match':True,'executed_here':False},
    'readback_sheets':sheets,'readback_actually_viewed':False,'inputs':tracked,'producer_functions_called':False,
    'runtime_verified':False,'user_accepted':False,'overall_complete':False,
    'limits':['대상128 RGBA와 비대상raw/층/조립을 대조했으며 제작자7296 전조합을 재실행하지 않았다.','새 MIPS/브라우저/실기는 실행하지 않고 현재후보와 기존 원MIPS4 decoded hash를 결속했다.','B02 및 B01의206 반려 원화는 제작 출처로 사용하지 않았다. 원화8셀은A204205·206_03·B01의207이며207만y−5 강체등록이다.'],
}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'report_sha256':sha((O/'report.json').read_bytes()),'counts':dict(counts)},ensure_ascii=False))
