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
S=B/'root_nana_vehicle';T=S/'joint_targets03';P=S/'packed_vehicle03';O=D/'nana_base_vehicle13_independent01'
PBS=(0,5,6,7,8);REFS=tuple(range(162,175));RESERVED={105,*range(175,183)}
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
oldp=B/'root_nana_return/packed_return03/PL00_U.ARC';newp=P/'PL00_U.ARC'
old,new=blob(oldp),blob(newp);a,b=Archive(old),Archive(new)
assert sha(old)=='6823c51d79f45beb3eeee8a9a2ec4a73aa1e067c5e1465d4325d6e4cf8c8ebf9'
assert sha(new)=='29f7b9a054ede30562bc4c3a88da96f70a909ad05262b3fd184c566e980454db'
meta=js(T/'manifest.json');assert meta['parent_sha256']==sha(old) and meta['refs']==list(REFS)
registered={};quant=[]
for suffix in ('a01','b01'):
 regdir=S/f'registered_{suffix}';reg=js(regdir/'manifest.json');ap=S/f'art_{suffix}/generated.png'
 assert sha(blob(ap))==reg['source_sha256'] and reg['parent_sha256']==sha(old)
 source=Image.open(ap).convert('RGBA');assert list(source.size)==reg['source_size'];
 for q in reg['frames']:
  form=q['form'];n=q['ref'];start=16 if form=='fourth'else 0
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
  assert sha(z.tobytes())==q['indices_sha256']and np.array_equal(z,png(regdir/f'{form}_{n:03}_indices.png'))
  assert sha(color(a,z,start).tobytes())==q['rgba_sha256']and q['body_translation']==[0,0]and not q['bbox_rescale']
  registered[n,form]=z;quant.append({'form':form,'ref':n,'fixed96_source_vote_exact':True,'source_crop':q['source_crop'],'whole_body_shift':[0,0]})
assert len(registered)==8
KEYS=(162,166,170,174);DY={162:0,163:1,164:3,165:-1,166:0,167:1,168:3,169:-1,170:0,171:1,172:2,173:-1,174:0}
faces={162:(-18,-12,-9,-4),166:(-17,-14,-8,-6),170:(-16,-18,-7,-10),174:(-12,-22,-3,-14)}
hands={162:(-22,-1,-13,3),166:(-22,-2,-14,6),170:(-19,-7,-10,-2),174:(-17,-10,-8,-4)}
leg_start={162:6,166:5,170:1,174:-4};head_bottom={162:-5,166:-7,170:-11,174:-14}
def rect(q):
 x0,y0,x1,y1=q;return (X>=x0)&(X<x1)&(Y>=y0)&(Y<y1)
base_layers={};provenance=[]
for n in KEYS:
 bs=registered[n,'base'].copy();fs=registered[n,'fourth'].copy();face=rect(faces[n]);hand=rect(hands[n])
 if n==174:bs[face]=fs[face]
 else:fs[face]=bs[face]
 fs[hand]=bs[hand];donor=fs.copy();links=[];extent=[]
 for y in range(160+leg_start[n],190):
  for gap in spans((bs[y]>0)&(fs[y]==0)):
   candidates=[]
   for sy in (y,y-1,y+1):
    for sr in spans(donor[sy]>0):
     lo=min(int(sr[0]),int(gap[0]));hi=max(int(sr[-1]),int(gap[-1]));ext=max(int(sr[0])-lo,hi-int(sr[-1]))
     if ext<=3 and hi-lo+1<=max(3,2*len(sr)):candidates.append((abs(sy-y),ext,sy,sr,lo,hi))
   assert candidates
   _,ext,sy,sr,lo,hi=min(candidates,key=lambda c:c[:2]);dest=np.arange(lo,hi+1);sx=sr[np.rint(np.linspace(0,len(sr)-1,len(dest))).astype(int)]
   fs[y,dest]=donor[sy,sx];extent.append(ext)
   links.extend({'dst':[int(x-160),y-160],'src':[int(xx-160),sy-160],'index':int(donor[sy,xx])}for x,xx in zip(dest,sx))
 q=next(q for q in meta['sources']if q['ref']==n);assert links==q['leg_registration']
 assert np.array_equal(fs,png(T/f'fourth_registered_{n:03}.png'))
 outside=[[int(x-160),int(y-160),int(bs[y,x])]for y,x in np.argwhere((bs>0)&(fs==0))];assert outside==q['base_outer_shared_cells']
 full=np.where(fs,fs,bs).astype(np.uint8);owner=np.full(bs.shape,6,np.uint8)
 owner[Y>=leg_start[n]]=8;owner[(X>=-1)&(Y>=head_bottom[n]-2)]=8;owner[Y<=head_bottom[n]]=5
 owner[rect((hands[n][0],hands[n][1]-2,-4,hands[n][3]+1))]=7;owner[face]=5
 dif=((full!=bs)|np.array([a.words[i]!=a.words[16+i]for i in range(16)])[full])&(full>0)
 ls={0:bs,**{pb:np.where(dif&(owner==pb),full,0).astype(np.uint8)for pb in PBS[1:]}}
 base_layers[n]=(ls,owner,full)
 provenance.append({'ref':n,'face_source':'fourth'if n==174 else'base','new_hand_shared':True,'leg_source_links':len(links),'maximum_horizontal_extent':max(extent),'maximum_vertical_displacement':max(abs(q['dst'][1]-q['src'][1])for q in links),'previous_or_next_row_links':[q for q in links if q['dst'][1]!=q['src'][1]],'new_base_outer_cells':outside,'owner_reconstructed':True})
target={};bodies={};aliases=[]
for n in REFS:
 k=162 if n<166 else 166 if n<170 else 170 if n<174 else 174;dy=DY[n];ls,owner,full=base_layers[k]
 q=next(q for q in meta['frames']if q['ref']==n);assert q['source_key']==k and q['translation']==[0,dy]
 for pb in PBS:
  expected=shift(ls[pb],dy);target[n,pb]=expected
  assert np.array_equal(expected,png(T/f'layer{pb}_{n:03}.png'))and sha(expected.tobytes())==q['layer_hashes'][str(pb)]
  assert np.array_equal(a.layer(n,pb)[0],shift(a.layer(k,pb)[0],dy)),(n,pb,'parent alias')
 assert np.array_equal(np.roll(owner,dy,0),png(T/f'owner_{n:03}.png'))
 bodies[n]=(target[n,0],shift(full,dy));aliases.append({'ref':n,'source_key':k,'dy':dy,'parent_all5layers_exact':True})
counts = collections.Counter()
assert len(old)==len(new) and a.p==b.p
ae,be = psx_arc(old),psx_arc(new)
assert [(q['type'],q['offset'],q['size'])for q in ae] == [(q['type'],q['offset'],q['size'])for q in be]
allow = np.zeros(len(old),bool)
for q in ae:
    if int(q['type'],16) in (2,3): allow[q['offset']:q['offset']+q['size']] = True
assert not np.any((np.frombuffer(old,np.uint8)!=np.frombuffer(new,np.uint8))&~allow)
assert bank_offsets(a.g,allow_aliases=True)==bank_offsets(b.g,allow_aliases=True)
import struct
old_starts,new_starts=bank_offsets(a.c),bank_offsets(b.c)
assert new_starts[:6]==old_starts[:6]and new_starts[6]==old_starts[6]+40 and new_starts[7:]==old_starts[7:]
lo,hi=old_starts[6:8];consumed=set(range(lo,lo+composition_frame(a.c,6,0)['bank_frame_count']*4));end=lo
for n in range(composition_frame(a.c,6,0)['bank_frame_count']):
 for q in parts(a,6,n):consumed.update(range(q['record_offset'],q['record_offset']+4));end=max(end,q['record_offset']+4)
assert not consumed.intersection(range(hi-40,hi)) and end<=hi-40
scratch=bytearray(a.c);scratch[lo+40:hi]=a.c[lo:hi-40];struct.pack_into('<I',scratch,24,lo+40)
for pb in range(len(old_starts)):
 for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
  assert [(q['flags'],q['tile'],q['x'],q['y'])for q in composition_frame(a.c,pb,n)['parts']]==[(q['flags'],q['tile'],q['x'],q['y'])for q in composition_frame(scratch,pb,n)['parts']]
rebalance={'before_bank6':[lo,hi],'after_bank6':[lo+40,hi],'head_gained_bytes':40,'last_consumed_record_byte':end,'tail40_not_referenced':True,'tail40_nonzero_bytes':sum(v!=0 for v in a.c[hi-40:hi]),'tail40_sha256':sha(a.c[hi-40:hi]),'all_original_records_after_pure_rebalance_exact':True,'only_directory_entry6_changed':True,'other_bank_absolute_starts_exact':True}
for pb in range(len(old_starts)):
 if pb not in PBS:
  end0=old_starts[pb+1]if pb+1<len(old_starts)else len(a.c)
  assert a.c[old_starts[pb]:end0]==b.c[new_starts[pb]:end0]

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


shared_groups=[]
for ns in ((162,163,164,165),(166,167,168,169),(170,171,172,173),(174,)):
 for ar in (a,b):assert len({ar.banks[0]['frames'][n]['offset']for n in ns})==1
 shared_groups.append({'refs':list(ns),'old_offset':a.banks[0]['frames'][ns[0]]['offset'],'new_offset':b.banks[0]['frames'][ns[0]]['offset'],'one_shared_raw_stream':True})
O.mkdir(exist_ok=True);sheets=[]
def board(items,name,columns,scale=5):
 boxes=[im.getbbox()for _,im in items if im.getbbox()];x0=min(q[0]for q in boxes)-3;y0=min(q[1]for q in boxes)-3;x1=max(q[2]for q in boxes)+3;y1=max(q[3]for q in boxes)+3
 cw=(x1-x0)*scale+10;ch=(y1-y0)*scale+25;im=Image.new('RGB',(cw*columns,ch*((len(items)+columns-1)//columns)),'#263345');dr=ImageDraw.Draw(im)
 for i,(title,pic)in enumerate(items):
  x=i%columns*cw;y=i//columns*ch;small=pic.crop((x0,y0,x1,y1)).resize(((x1-x0)*scale,(y1-y0)*scale),Image.Resampling.NEAREST);im.paste(small,(x+5,y+22),small);dr.text((x+5,y+3),title,fill='white')
 p=O/name;im.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes()),'same_origin':True,'no_opaque_clipping':True})

for n in KEYS:
 board([(f'{n} {title}',ar.composite(n,mask,1)[0])for ar,mask,title in((a,0,'old base'),(b,0,'new base'),(a,15,'old fourth'),(b,15,'new fourth'))],f'full_{n:03}.png',4,7)
 board([(f'{n} {title}',b.composite(n,mask,2)[0])for mask,title in((1,'head'),(2,'body'),(4,'arms'),(8,'legs'),(10,'body+legs'))],f'partial_{n:03}.png',5,6)
for group in ((162,163,164,165),(166,167,168,169),(170,171,172,173)):
 board([(f'{n} m{mask}',b.composite(n,mask,1)[0])for mask in(0,15)for n in group],f'alias_{group[0]:03}.png',4,5)
assert counts['raw_checked']==508 and counts['non_target_raw_exact']==495 and counts['target_layers_exact']==65 and counts['partial_RGBA_exact']==416
for p,h in tracked.items():assert sha((ROOT/p).read_bytes())==h,p
report={'passed':True,'scope':'?? ??/?? ??4?8?????96??/????????????????Y??9?65????ARC ????','candidate':rel(newp),'candidate_sha256':sha(new),'parent':rel(oldp),'parent_sha256':sha(old),'target_manifest_sha256':sha((T/'manifest.json').read_bytes()),'counts':dict(counts),'source_quantization':quant,'source_registration':provenance,'parent_and_new_aliases':aliases,'shared_raw_groups':shared_groups,'composition_rebalance':rebalance,'nonselected_shared_compositions':shared,'reserved':reserved,'entry_directory_length_other_entries_palette_audio_graphics_boundaries_exact':True,'composition_boundary_exception':'bank6 start only +40 inside fixed entry3; all other starts unchanged','readback_sheets':sheets,'readback_actually_viewed':False,'inputs':tracked,'producer_functions_called':False,'new_native_MIPS_performed':False,'runtime_verified':False,'user_accepted':False,'overall_complete':False,'limits':['416????RGBA?495???raw?1075?? ?? ????.???7296 ??? ???? ?? ???.','bank6 ?????40B?27??????? 0????? ???? ?? ???????????? ???? ????.','??directory? ?MIPS ?? ??? ?? ?? ???? ?? ? ?? ??? ???? ???.','????? ??? ????3/??1?? ??? ???? ??? ?? ?????.????????? ???.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'report_sha256':sha((O/'report.json').read_bytes()),'counts':dict(counts),'rebalance':rebalance},ensure_ascii=False))
