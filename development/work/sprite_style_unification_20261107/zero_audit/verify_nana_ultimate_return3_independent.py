"""Nana Ultimate 귀환3 원화/실루엣/광선→실제ARC 독립 reader."""
from pathlib import Path
import collections,hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import binary_dilation,label
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;B=D.parent;N=B/'nana_audit'
sys.path[:0]=[str(ROOT),str(D)]
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from src.psx_player import bank_offsets,composition_frame
from verify_shibuki_ultimate_hurt13_independent import raw,parts,sig,tile,color,polygons
U=N/'ultimate_return_repaint';P=U/'packed_return_candidate_v1';T=U/'final_targets_v1';O=D/'nana_ultimate_return3_independent01'
PBS=(0,5,6,7,8);REFS={156,157,158};RESERVED={105,*range(175,183)}
sha=lambda x:hashlib.sha256(x).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();tracked={}
def readb(p):
 z=p.read_bytes();tracked[rel(p)]=sha(z);return z
def readj(p):return json.loads(readb(p))
def png(p):readb(p);return np.array(Image.open(p))
def shift(z,dy):
 out=np.zeros_like(z);y,x=np.nonzero(z);out[y+dy,x]=z[y,x];return out
def full(ar,n):
 z=ar.layer(n)[0].copy()
 for pb in(8,5,7,6):v=ar.layer(n,pb)[0];z[v>0]=v[v>0]
 return z
def quantize(cell,pal):
 rgba=np.array(cell.convert('RGBA'));rgb=rgba[:,:,:3].astype(np.float32);alpha=rgba[:,:,3].astype(np.float32)/255
 labels=np.empty(alpha.shape,np.uint8)
 for y in range(len(labels)):labels[y]=1+np.square(rgb[y,:,None,:]-pal[None,1:,:]).sum(2).argmin(1)
 green=(rgb[:,:,1]>rgb[:,:,0]+15)&(rgb[:,:,1]>rgb[:,:,2]+15)&(rgba[:,:,3]>=128);green[len(green)//2:]=False;labels[green]=14
 votes=np.stack([np.asarray(Image.fromarray(np.where(labels==i,alpha,0).astype(np.float32),'F').resize((96,128),Image.Resampling.BOX))for i in range(1,16)])
 coverage=np.asarray(Image.fromarray(alpha,'F').resize((96,128),Image.Resampling.BOX));small=1+votes.argmax(0).astype(np.uint8);small[coverage<.5]=0
 eyes=votes[13].copy();eyes[coverage<.5]=0;eyes[64:]=0
 if eyes.max()>.015:small[np.unravel_index(eyes.argmax(),eyes.shape)]=14
 z=np.zeros((384,384),np.uint8);z[96:224,112:208]=small;return z
def aura(z):
 m=z>0;inner=binary_dilation(m,np.ones((3,3)));outer=binary_dilation(m,np.ones((3,3)),iterations=2)
 return np.where(m,z,np.where(inner,7,np.where(outer,13,0))).astype(np.uint8)
oldp=N/'ultimate_victory_repaint/packed_victory_candidate_v1/PL02_U.ARC';newp=P/'PL02_U.ARC'
old,new=readb(oldp),readb(newp);a,b=Archive(old),Archive(new)
assert sha(old)=='b7dcf46dba35084265e8b32529d7a4d072108ed201a60ba4f17fcc71494aa1c5'
assert sha(new)=='493bf2706aae33b64c4ffe70be1576a7ed63b0a4f62c54e89ca5876131392e29'
lockpath=P/'INPUT_FROZEN.json';lock=readj(lockpath)
assert lock['candidate_sha256']==sha(new)and lock['parent_sha256']==sha(old)
for q in lock['files']:
 v=readb(ROOT/q['path']);assert sha(v)==q['sha256']and len(v)==q['size']
meta=readj(T/'manifest.json');cm=readj(U/'costume_pair_probe_v2/manifest.json');rm=readj(U/'body_registered_v1/registration.json')
assert meta['body_source_manifest_sha256']==sha((U/'costume_pair_probe_v2/manifest.json').read_bytes())
assert meta['parent_arc_sha256']==cm['parent_arc_sha256']==rm['parent_arc_sha256']==sha(old)
pal=lambda start:np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32)
sourceart=ROOT/rm['source_art_path'];readb(sourceart);assert sha(sourceart.read_bytes())==rm['source_art_sha256'];source=Image.open(sourceart).convert('RGBA')
fixed={}
for q in rm['frames']:
 f=q['form'];z=quantize(source.crop(q['source_crop']),pal(16 if f=='before'else 0))
 assert sha(z.tobytes())==q['native_sha256']and np.array_equal(z,png(U/'body_registered_v1'/f'{f}_156_indices.png'));fixed[f]=z
before,initial=fixed['before'].copy(),fixed['after'].copy()
local=ROOT/cm['local_art'];readb(local);assert sha(local.read_bytes())==cm['local_art_sha256']
localfixed=quantize(Image.open(local).convert('RGBA').crop(cm['local_fixed_source_crop']),pal(0));donor=np.zeros_like(localfixed);donor[:,4:]=localfixed[:,:-4]
assert np.array_equal(donor,png(U/'costume_pair_probe_v2/waist_donor_156.png'))
boundary=[]
for q in cm['original_source_boundary']:
 cell=np.array(source.crop(q['source_native_sample_rect']));opaque=cell[:,:,3]>=128;rgb=np.median(cell[:,:,:3][opaque],axis=0)
 idx=1+np.square(pal(0)[1:]-rgb).sum(1).argmin();x,y=q['world']
 assert int(opaque.sum())==q['opaque_samples']==30 and len(cell)*len(cell[0])==q['total_samples']==64
 assert rgb.tolist()==q['sample_median_rgb']and int(idx)==q['index']==1 and before[y+160,x+160]==0
 before[y+160,x+160]=idx;boundary.append({'world':[x,y],'source_opaque':30,'total':64,'index':1})
wm=polygons([cm['waist_polygon']]);mask=polygons([cm['costume_polygon']]);after_source=initial.copy();after_source[wm]=donor[wm]
assert np.count_nonzero(after_source!=initial)==cm['replaced_waist_pixels']==40
after=np.where(before==15,13,before).astype(np.uint8);after[mask]=after_source[mask]
for x,y in cm['donor_leg_excluded_from_costume']:assert not mask[y+160,x+160]
assert np.array_equal(after_source,png(U/'costume_pair_probe_v2/after_source_156.png'))
body={}
for form,z in(('before',before),('after',after)):
 assert np.array_equal(z,png(U/'costume_pair_probe_v2'/f'{form}_156.png'))and sha(z.tobytes())==cm[form+'_sha256']
 assert label(z>0,np.ones((3,3)))[1]==1;body[form,156]=z
assert not np.any((after>0)&(before==0))
histp=ROOT/meta['historical_arc'];hist=Archive(readb(histp));assert sha(hist.data)==meta['historical_arc_sha256']
energy=hist.layer(159)[0];assert np.count_nonzero(energy)==1875 and sha(energy.tobytes())==meta['historical_energy_sha256']
assert np.array_equal(energy,a.layer(159)[0])and np.array_equal(energy,png(T/'original_energy159_indices.png'))
mapping=np.array([0,5,6,7,8,5,6,7,8,9,8,9,13,13,9,9],np.uint8)
assert np.array_equal(aura(shift(full(a,156),-1)),full(a,157))
oldmoved=shift(full(a,156),-10);assert np.array_equal(np.where(oldmoved>0,mapping[oldmoved%16],energy),full(a,158))
effects=[]
for form in('before','after'):
 moved=shift(body[form,156],-1);body[form,157]=aura(moved)
 fx=np.where(moved==0,body[form,157],0).astype(np.uint8);q=next(q for q in meta['rules']if q['ref']==157 and q['form']==form)
 assert np.count_nonzero(fx)==q['aura_pixels']and np.array_equal(fx,png(T/f'{form}_aura157.png'))
 assert np.array_equal(body[form,157][moved>0],moved[moved>0])
 moved=shift(body[form,156],-10);body[form,158]=np.where(moved>0,mapping[moved%16],energy).astype(np.uint8)
 q2=next(q for q in meta['rules']if q['ref']==158 and q['form']==form)
 assert q2['mapping']==mapping.tolist()and np.count_nonzero(energy*(moved==0))==q2['visible_energy_outside_body']
 assert np.array_equal(body[form,158][moved==0],energy[moved==0])
 effects.append({'form':form,'157_Chebyshev_aura':q['aura_pixels'],'158_historical_energy':1875,'158_visible_energy':q2['visible_energy_outside_body']})
target={}
for n in sorted(REFS):
 bef,aft=body['before',n],body['after',n];assert not np.any((aft>0)&(bef==0))
 target[n,0]=aft;target[n,5]=np.where((bef!=aft)|(bef==15),bef,0).astype(np.uint8)
 for pb in(6,7,8):target[n,pb]=np.zeros_like(aft)
 for pb in PBS:assert np.array_equal(target[n,pb],png(T/f'layer{pb}_{n:03}.png'))and sha(target[n,pb].tobytes())==meta['targets'][str(n)][str(pb)]

counts = collections.Counter()
assert len(old) == len(new) and a.p == b.p
ae, be = psx_arc(old), psx_arc(new)
assert [(q['type'], q['offset'], q['size']) for q in ae] == [(q['type'], q['offset'], q['size']) for q in be]
allow = np.zeros(len(old), bool)
for q in ae:
    if int(q['type'], 16) in (2, 3):
        allow[q['offset']:q['offset']+q['size']] = True
assert not np.any((np.frombuffer(old, np.uint8) != np.frombuffer(new, np.uint8)) & ~allow)
assert bank_offsets(a.g, allow_aliases=True) == bank_offsets(b.g, allow_aliases=True)
assert bank_offsets(a.c) == bank_offsets(b.c)
for gb, (ab, bb) in enumerate(zip(a.banks, b.banks)):
    assert (ab['base'], ab['end'], len(ab['frames'])) == (bb['base'], bb['end'], len(bb['frames']))
    if gb:
        assert a.g[ab['base']:ab['end']] == b.g[bb['base']:bb['end']]
        counts['other_graphics_banks_byte_exact'] += 1
    for f, g in zip(ab['frames'], bb['frames']):
        n = f['index']
        assert n == g['index']
        counts['raw_checked'] += 1
        if gb == 0 and n in REFS:
            assert g['tile_count'] == 32
        else:
            assert raw(a, gb, n) == raw(b, gb, n) and f['tile_count'] == g['tile_count']
            counts['non_target_raw_exact'] += 1
for n in range(237):
    if n in RESERVED:
        continue
    for pb in PBS:
        want = target[n, pb] if n in REFS else a.layer(n, pb)[0]
        assert np.array_equal(b.layer(n, pb)[0], want), (n, pb)
        counts['target_layers_exact' if n in REFS else 'non_target_layers_exact'] += 1

shared = []
for pb in range(len(bank_offsets(a.c))):
    allparts = {n: parts(a, pb, n) for n in range(composition_frame(a.c, pb, 0)['bank_frame_count'])}
    selected_addresses = {q['record_offset'] for n in REFS if n in allparts and pb in PBS for q in allparts[n]}
    for n, op in allparts.items():
        bp = parts(b, pb, n)
        if pb in PBS and n in REFS:
            # 158은 몸체와 긴 빛줄기를 함께 그린다. 타일32 제한과
            # 조립 파츠수를 혼동하지 않고 파서 및 실제 GPU 검사로 확인.
            assert 0 < len(bp) <= 256
            for q in bp:
                t = q['tile'] + q['page'] * 256
                assert 0 <= t < 32 and q['unknown_flags'] == 0
                v = tile(b, n, t)
                assert not (t % 16 == 0 and v[:, 0].any())
                assert not (q['flip_y'] and t // 16 == 0 and v[0].any())
                counts['GPU_parts_checked'] += 1
        else:
            assert [sig(q) for q in op] == [sig(q) for q in bp]
            counts['non_target_compositions_exact'] += 1
            overlaps = sorted(selected_addresses & {q['record_offset'] for q in op})
            if overlaps:
                shared.append({'bank': pb, 'ref': n, 'shared_parent_record_offsets': overlaps,
                               'entire_composition_semantics_exact': True})
assert raw(a, 0, 89) == raw(b, 0, 89)
for n in sorted(REFS):
    for mask in range(16):
        for arm in (1, 2):
            expected = color(b, target[n, 0])
            for bit, pb in ((8, 8), (1, 5), (4, 7), (2, 6)):
                if mask & bit:
                    v = color(b, target[n, pb], 32 if pb == 7 and arm == 2 else 16)
                    m = v[:, :, 3] > 0
                    expected[m] = v[m]
            assert np.array_equal(expected, np.asarray(b.composite(n, mask, arm)[0]))
            counts['partial_RGBA_exact'] += 1
    assert np.array_equal(color(b, body['before', n], 16), np.asarray(b.composite(n, 15)[0]))
    assert np.array_equal(color(b, body['after', n]), np.asarray(b.composite(n, 0)[0]))

nativep=U/'native_components_v1_native_checks.json';native=readj(nativep);assert native['passed']
nr=native['resources']['PL02_U.ARC'];assert nr['candidate_sha256']==sha(new)
checks=next(q for q in nr['banks']if q['bank']==0)['native_decoder_checks']
for n in REFS:
 q=next(q for q in checks if q['frame']==n);assert q['decoded_sha256']==sha(raw(b,0,n))and q['buffer_outside_and_unused_tail_preserved']
O.mkdir(exist_ok=True);sheets=[]
for n in sorted(REFS):
 panels=[(a,15,'old before'),(b,15,'new before'),(a,0,'old after'),(b,0,'new after')]
 pics=[ar.composite(n,mask)[0]for ar,mask,_ in panels];boxes=[p.getbbox()for p in pics]
 x0=min(p[0]for p in boxes)-6;y0=min(p[1]for p in boxes)-5;x1=max(p[2]for p in boxes)+6;y1=max(p[3]for p in boxes)+5
 cw=(x1-x0)*5+12;ch=(y1-y0)*5+28;im=Image.new('RGB',(cw*4,ch),'#263345');dr=ImageDraw.Draw(im)
 for col,(pic,(_,_,title))in enumerate(zip(pics,panels)):
  pic=pic.crop((x0,y0,x1,y1)).resize(((x1-x0)*5,(y1-y0)*5),Image.Resampling.NEAREST);im.paste(pic,(col*cw+6,24),pic);dr.text((col*cw+6,4),f'{n} {title}',fill='white')
 p=O/f'readback_{n:03}.png';im.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes()),'original_crop':[x0,y0,x1,y1],'no_opaque_pixels_clipped':True})
assert counts['raw_checked']==512 and counts['non_target_raw_exact']==509
assert counts['target_layers_exact']==15 and counts['non_target_layers_exact']==1125 and counts['partial_RGBA_exact']==96
for p,h in tracked.items():assert sha((ROOT/p).read_bytes())==h,p
report={'passed':True,'scope':'새귀환2원화+국소의상1셀 독립재양자화·첫원화경계1셀→156/157/158 15층→ARC',
 'candidate':rel(newp),'candidate_sha256':sha(new),'parent_sha256':sha(old),'input_lock_sha256':sha(lockpath.read_bytes()),'locked_inputs':len(lock['files']),
 'target_manifest_sha256':sha((T/'manifest.json').read_bytes()),'counts':dict(counts),'new_art_fixed_cells_reconstructed':3,
 'original_boundary_sample':boundary,'local_waist_source_pixels':40,'local_waist_translation':[4,0],'donor_leg38_excluded':True,
 'parent_before157158_rule_reconstructed':True,'new_effects':effects,'no_old_body_alpha_or_guard_cell_copied':True,
 'shared_non_target_records':shared,'other_entries_bank_boundaries_palette_audio_exact':True,
 'parts_counts':{str(n):{str(pb):{'old':len(parts(a,pb,n)),'new':len(parts(b,pb,n))}for pb in PBS}for n in sorted(REFS)},
 'native_MIPS_existing_evidence':{'path':rel(nativep),'sha256':sha(nativep.read_bytes()),'new3_decoded_hashes_exact':True,'executed_here':False},
 'readback_sheets':sheets,'readback_actually_viewed':False,'inputs':tracked,'producer_functions_called':False,'runtime_verified':False,
 'limitations':['대상96RGBA 및비대상1125층/팔레트보존을확인.제작자7296전조합검사는반복하지않았다.',
                '새MIPS실행/원순서브라우저재생/실제귀환실기/사용자수용은별도다.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'counts':dict(counts),'report_sha256':sha((O/'report.json').read_bytes())}))

