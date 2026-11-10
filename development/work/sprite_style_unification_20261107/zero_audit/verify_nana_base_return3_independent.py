"""나나 기본/포스 귀환3: 새 원화/효과/소유→실제자원 독립 읽기."""
from pathlib import Path
import collections,hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,binary_dilation,distance_transform_edt
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;B=D.parent
sys.path[:0]=[str(ROOT),str(D)]
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from src.psx_player import bank_offsets,composition_frame
from verify_shibuki_ultimate_hurt13_independent import raw,parts,sig,tile,color,render
S=B/'root_nana_return';T=S/'joint_targets03';P=S/'packed_return03';O=D/'nana_base_return3_independent01'
PBS=(0,5,6,7,8);REFS=(156,157,158);RESERVED={105,*range(175,183)}
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();tracked={}
def blob(p):
 b=p.read_bytes();tracked[rel(p)]=sha(b);return b
def js(p):return json.loads(blob(p))
def png(p):blob(p);return np.array(Image.open(p))
def shift(z,dy):
 out=np.zeros_like(z);y,x=np.nonzero(z);assert not len(y)or min(y+dy)>=0 and max(y+dy)<384;out[y+dy,x]=z[y,x];return out
def aura(z):
 m=z>0;return np.where(m,z,np.where(binary_dilation(m),13,np.where(binary_dilation(m,iterations=2),7,0))).astype(np.uint8)
def spans(row):
 xs=np.flatnonzero(row);return []if not len(xs)else np.split(xs,np.flatnonzero(np.diff(xs)>1)+1)
Y,X=np.indices((384,384));Y-=160;X-=160
oldp=B/'root_nana_victory/packed_victory02/PL00_U.ARC';newp=P/'PL00_U.ARC'
old,new=blob(oldp),blob(newp);a,b=Archive(old),Archive(new)
assert sha(old)=='90c614a7996d65ff71381ccc1f673cbfa13b84eccafec83c2e919010310b9239'
assert sha(new)=='6823c51d79f45beb3eeee8a9a2ec4a73aa1e067c5e1465d4325d6e4cf8c8ebf9'
meta=js(T/'manifest.json');reg=js(S/'registered01/manifest.json');assert meta['parent_sha256']==reg['parent_sha256']==sha(old)
assert meta['refs']==list(REFS)
ap=S/'art01/generated.png';assert sha(blob(ap))==reg['source_sha256']=='a666e247f3575ec0ee332356dcdb7b7c8a414c07bc60b1ad4d8930b4cde35cae'
source=Image.open(ap).convert('RGBA');assert list(source.size)==reg['source_size'];registered={};quant=[]
for q in reg['frames']:
 form=q['form'];start=16 if form=='fourth'else 0
 pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32)
 rgba=np.array(source.crop(q['source_crop']));rgb=rgba[:,:,:3].astype(np.float32);alpha=rgba[:,:,3].astype(np.float32)/255
 indices=np.empty(alpha.shape,np.uint8)
 for y in range(len(indices)):indices[y]=1+np.square(rgb[y,:,None,:]-pal[None,1:,:]).sum(2).argmin(1)
 green=(rgb[:,:,1]>rgb[:,:,0]+15)&(rgb[:,:,1]>rgb[:,:,2]+15)&(rgba[:,:,3]>=128);green[len(green)//2:]=False;indices[green]=14
 votes=np.stack([np.asarray(Image.fromarray(np.where(indices==i,alpha,0).astype(np.float32),'F').resize((96,96),Image.Resampling.BOX))for i in range(1,16)])
 coverage=np.asarray(Image.fromarray(alpha,'F').resize((96,96),Image.Resampling.BOX));small=1+votes.argmax(0).astype(np.uint8);small[coverage<.5]=0
 eyes=votes[13].copy();eyes[coverage<.5]=0;eyes[48:]=0
 if eyes.max()>.015:small[np.unravel_index(eyes.argmax(),eyes.shape)]=14
 z=np.zeros((384,384),np.uint8);z[112:208,112:208]=small
 assert sha(z.tobytes())==q['indices_sha256']and np.array_equal(z,png(S/f'registered01/{form}_156_indices.png'))
 assert sha(color(a,z,start).tobytes())==q['rgba_sha256']and q['body_translation']==[0,0]and not q['bbox_rescale']
 registered[form]=z;quant.append({'form':form,'ref':156,'fixed96_source_vote_exact':True,'source_crop':q['source_crop'],'whole_body_shift':[0,0]})
assert len(registered)==2
base=registered['base'].copy();fourth=registered['fourth'].copy();face=(X>=-6)&(X<=1)&(Y>=-16)&(Y<=-9);fourth[face]=base[face]
donor=fourth.copy();links=[];extensions=[]
for y in range(164,183):
 for gap in spans((base[y]>0)&(fourth[y]==0)):
  sy=y;runs=spans(donor[sy]>0)
  if not runs:sy=y-1;runs=spans(donor[sy]>0)
  assert runs
  src=min(runs,key=lambda q:np.abs(q[:,None]-gap).min());lo=min(int(src[0]),int(gap[0]));hi=max(int(src[-1]),int(gap[-1]));extension=max(int(src[0])-lo,hi-int(src[-1]));assert extension<=3
  dest=np.arange(lo,hi+1);assert len(dest)<=max(3,len(src)*2);sx=src[np.rint(np.linspace(0,len(src)-1,len(dest))).astype(int)]
  fourth[y,dest]=donor[sy,sx];extensions.append(extension)
  links.extend({'dst':[int(x-160),y-160],'src':[int(xx-160),sy-160],'index':int(donor[sy,xx])}for x,xx in zip(dest,sx))
assert links==meta['leg_registration']
assert np.array_equal(fourth,png(T/'fourth_registered156.png'))
inherited=[[int(x-160),int(y-160),int(base[y,x])]for y,x in np.argwhere((base>0)&(fourth==0))];assert inherited==meta['base_outer_shared_cells']
full=np.where(fourth,fourth,base).astype(np.uint8);owner=np.full(base.shape,6,np.uint8)
owner[(Y>=4)|((X>=6)&(Y>=-6))]=8;owner[Y<=-7]=5;owner[(X>=-10)&(X<=3)&(Y>=-8)&(Y<=0)]=7;owner[face]=5
assert np.array_equal(aura(shift(a.layer(156)[0],-1)),a.layer(157)[0])
energy=a.layer(159)[0];assert np.count_nonzero(energy)==1875 and np.array_equal(energy,png(T/'original_energy159.png'))
assert sha(energy.tobytes())==meta['ascent_rule']['energy159_exact_sha256']
emap=np.array([0,5,6,7,8,5,6,7,8,9,8,9,13,13,9,9],np.uint8);assert meta['ascent_rule']['mapping']==emap.tolist()
body={156:(base,full),157:(aura(shift(base,-1)),aura(shift(full,-1))),158:tuple(np.where(shift(z,-10),emap[shift(z,-10)],energy).astype(np.uint8)for z in(base,full))}
target={};bodies={};effectproof=[]
for n,(bs,fs)in body.items():
 q=next(q for q in meta['frames']if q['ref']==n);dy={156:0,157:-1,158:-10}[n];assert q['translation']==[0,dy]
 owners=owner.copy()if not dy else np.roll(owner,dy,0)
 if n==157:
  # Match ownership of each aura pixel to its nearest actual new body texel.
  ni=distance_transform_edt(shift(full,-1)==0,return_distances=False,return_indices=True);owners=owners[tuple(ni)]
 assert np.array_equal(owners,png(T/f'owner_{n:03}.png'))
 assert not np.any((bs>0)&(fs==0))
 different=((bs!=fs)|np.array([a.words[i]!=a.words[16+i]for i in range(16)])[fs])&(fs>0)
 ls={0:bs,**{pb:np.where(different&(owners==pb),fs,0).astype(np.uint8)for pb in PBS[1:]}}
 for pb,z in ls.items():
  assert np.array_equal(z,png(T/f'layer{pb}_{n:03}.png'))and sha(z.tobytes())==q['layer_hashes'][str(pb)];target[n,pb]=z
 assert np.array_equal(fs,png(T/f'fourth_{n:03}_indices.png'));bodies[n]=(bs,fs)
 if n==157:
  for form,z,orig in [('base',bs,base),('fourth',fs,full)]:
   moved=shift(orig,-1);assert np.array_equal(z[moved>0],moved[moved>0]);effectproof.append({'ref':157,'form':form,'Manhattan_inner13_outer7':True,'aura_cells':int(np.count_nonzero((z>0)&(moved==0)))})
 if n==158:
  for form,z,orig in [('base',bs,base),('fourth',fs,full)]:
   moved=shift(orig,-10);assert np.array_equal(z[moved==0],energy[moved==0]);effectproof.append({'ref':158,'form':form,'parent159_energy':1875,'visible_energy_outside_new_body':int(np.count_nonzero(energy*(moved==0))),'no_old_body_or_alpha_clip':True})
proof={'new_face_shared':True,'leg_source_links':len(links),'max_extension':max(extensions),'previous_row_links':[q for q in links if q['src'][1]!=q['dst'][1]],'inherited_new_base_outer_cells':inherited,'owner03_reconstructed':True,'effects':effectproof}

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
            assert label(actual[:,:,3]>0,np.ones((3,3)))[1] == (1 if n in (156,157) else 24)
            counts['partial_RGBA_exact'] += 1
    for mask in (0,15):
        bb,ff = bodies[n]; expected = color(b,bb)
        if mask: m=ff>0; expected[m] = color(b,ff,16)[m]
        assert np.array_equal(expected,np.asarray(b.composite(n,mask,1)[0]))

source_tail=[sig(q)for q in parts(a,5,204)[-4:]]
expected_sig=[(0,6,-9,-22),(0,1,4,-20),(0,31,-12,-38),(0,30,10,-4),(0,29,-9,-38),(0,28,-12,-21)]
assert source_tail==expected_sig[:4]
heads=[]
for n in REFS:
 ps=parts(b,5,n);assert [sig(q)for q in ps]==expected_sig
 assert [q['record_offset']for q in ps[:4]]==[q['record_offset']for q in parts(b,5,204)[-4:]]
 assert [q['record_offset']for q in ps]==[q['record_offset']for q in parts(b,5,156)]
 assert np.array_equal(render(b,n,5,ps),target[n,5])and not np.array_equal(target[n,5],a.layer(204,5)[0])
 assert [f['index']for f in a.banks[0]['frames']if f['offset']==a.banks[0]['frames'][n]['offset']]==[n]
 assert [f['index']for f in b.banks[0]['frames']if f['offset']==b.banks[0]['frames'][n]['offset']]==[n]
 heads.append({'ref':n,'record_addresses':[q['record_offset']for q in ps],'signatures':expected_sig,'first4_share_parent204_records':True,'head204_bitmap_not_reused':True,'new_head_render_exact':True})
for n in (159,204):
 assert raw(a,0,n)==raw(b,0,n)
 for pb in PBS:
  assert np.array_equal(a.layer(n,pb)[0],b.layer(n,pb)[0])and [sig(q)for q in parts(a,pb,n)]==[sig(q)for q in parts(b,pb,n)]
nativep=S/'return_components_native_checks.json';native=js(nativep);assert native['passed']
nr=native['resources']['PL00_U.ARC'];assert nr['candidate_sha256']==sha(new)
checks=next(q for q in nr['banks']if q['bank']==0)['native_decoder_checks']
for n in REFS:
 q=next(q for q in checks if q['frame']==n);assert q['decoded_sha256']==sha(raw(b,0,n))and q['buffer_outside_and_unused_tail_preserved']
O.mkdir(exist_ok=True);sheets=[]
def board(items,name,columns,scale=5):
 boxes=[im.getbbox()for _,im in items if im.getbbox()];x0=min(q[0]for q in boxes)-3;y0=min(q[1]for q in boxes)-3;x1=max(q[2]for q in boxes)+3;y1=max(q[3]for q in boxes)+3
 cw=(x1-x0)*scale+10;ch=(y1-y0)*scale+25;im=Image.new('RGB',(cw*columns,ch*((len(items)+columns-1)//columns)),'#263345');dr=ImageDraw.Draw(im)
 for i,(title,pic)in enumerate(items):
  x=i%columns*cw;y=i//columns*ch;small=pic.crop((x0,y0,x1,y1)).resize(((x1-x0)*scale,(y1-y0)*scale),Image.Resampling.NEAREST);im.paste(small,(x+5,y+22),small);dr.text((x+5,y+3),title,fill='white')
 p=O/name;im.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes()),'same_origin':True,'no_opaque_clipping':True})
for n in REFS:
 board([(f'{n} {title}',ar.composite(n,mask,1)[0])for ar,mask,title in((a,0,'old base'),(b,0,'new base'),(a,15,'old fourth'),(b,15,'new fourth'))],f'full_{n:03}.png',4,4 if n==158 else 6)
 board([(f'{n} {title}',b.composite(n,mask,2)[0])for mask,title in((1,'head'),(2,'body'),(4,'arms'),(8,'legs'),(10,'body+legs'))],f'partial_{n:03}.png',5,3 if n==158 else 5)
assert counts['raw_checked']==508 and counts['non_target_raw_exact']==505 and counts['target_layers_exact']==15 and counts['partial_RGBA_exact']==96
for p,h in tracked.items():assert sha((ROOT/p).read_bytes())==h,p
report={'passed':True,'scope':'나나 기본/포스 귀환156 새2원화→고정등록/새얼굴·다리·베일소유→157/158 효과파생→15층 및 실제ARC 독립 읽기','candidate':rel(newp),'candidate_sha256':sha(new),'parent':rel(oldp),'parent_sha256':sha(old),'target_manifest_sha256':sha((T/'manifest.json').read_bytes()),'counts':dict(counts),'source_quantization':quant,'source_registration':proof,'head_records':heads,'parent159_and204_raw_layers_compositions_exact':True,'nonselected_shared_compositions':shared,'reserved':reserved,'other_entries_palette_audio_bank_boundaries_exact':True,'native_MIPS_existing_evidence':{'path':rel(nativep),'sha256':sha(nativep.read_bytes()),'three_decoded_hashes_match':True,'executed_here':False},'readback_sheets':sheets,'readback_actually_viewed':False,'inputs':tracked,'producer_functions_called':False,'runtime_verified':False,'user_accepted':False,'overall_complete':False,'limits':['대상96 부분RGBA와 비대상raw/층/조립을 독립검사했다. 제작자7296 전조합 재실행은 하지 않았다.','기존 원MIPS3 decoded hash를 현재후보에 결속했으며 새 MIPS/실기는 실행하지 않았다.','다리 정합은 같은행이 기본이나 바닥22행의2셀은 새 원화21행에서 가져온 예외다. 과거 몸체/옛알파를 복사한 것이 아니다.','157은 기본 현재부모의 Manhattan1/2 원식을 exact 재현한 뒤 새 양폼에 적용했다. 158은 현재159효과1875셀+새몸y−10이며 보이는 효과 픽셀과 가려진 효과를 구분했다.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'report_sha256':sha((O/'report.json').read_bytes()),'counts':dict(counts),'leg_links':len(links),'previous_row_links':proof['previous_row_links']},ensure_ascii=False))

