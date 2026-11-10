"""오른손103/104 두 ARC를 생성원화부터 별도 reader로 검사한다."""
from pathlib import Path
import sys,json,collections
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).parent;sys.path.insert(0,str(D))
import verify_checkpoint20_x_candidates as r
H=r.H;ROOT=r.ROOT;PBS=r.PBS;REFS=(103,104);O=D/'rising_right_independent';O.mkdir(exist_ok=True)
HEAD={103:[(-16,-22),(3,-22),(3,-14),(10,-13),(12,-5),(9,6),(7,15),(1,16),(1,12),(-3,10),(-4,5),(-11,3),(-16,-5)],104:[(-16,-26),(2,-26),(2,-18),(7,-16),(11,-11),(13,8),(8,16),(5,15),(4,10),(0,8),(-2,1),(-11,-3),(-16,-7)]}
FACE={103:(-11,-7,1,1),104:(-11,-11,1,-4)}
DECO={103:[(3,-14),(9,-14),(12,-10),(12,-4),(10,-3),(8,-6),(4,-7),(2,-11)],104:[(1,-18),(8,-18),(11,-14),(10,-7),(6,-8),(5,-11),(1,-12)]}
Y,X=np.indices((384,384));x=X-160;y=Y-160
def poly(points):
 im=Image.new('1',(384,384));ImageDraw.Draw(im).polygon([(px+160,py+160)for px,py in points],fill=1);return np.array(im,bool)
def sampled(path,box,words,start,alpha,largest=False):
 r.read(path);im=Image.open(path).convert('RGBA');assert im.size==(1536,1024)
 v=np.array(im.crop(box).resize((64,64),Image.Resampling.NEAREST));rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in words[start+1:start+16]],np.int32)
 q=(1+((v[:,:,:3].astype(np.int32)[:,:,None]-rgb[None,None])**2).sum(3).argmin(2)).astype(np.uint8);q[v[:,:,3]<alpha]=0
 removed=0
 if largest:
  labs,n=label(q>0,np.ones((3,3)));sizes=np.bincount(labs.ravel());sizes[0]=0;k=int(sizes.argmax());removed=int(np.count_nonzero(q)-sizes[k]);assert sizes[k]>=900 and removed in(19,13);q[labs!=k]=0
 z=np.zeros((384,384),np.uint8);z[124:188,128:192]=q;return z,removed
def base_targets(a,S):
 report=r.js(S/'report.json');targets={};proof=[]
 rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words],np.int32)
 lut={i:1+int(np.argmin(((rgb[17:32]-rgb[i])**2).sum(1)))for i in range(1,16)}
 for n in REFS:
  row=next(z for z in report['rows']if z['ref']==n);assert list(map(tuple,row['head_polygon']))==HEAD[n]and list(map(tuple,row['ornament_polygon']))==DECO[n]
  sources=[]
  for i,form in enumerate(('base','fourth')):
   if n==103:path=H/'rising_air_hand_fix_inputs01/page01/generated_rejected104.png';box=(0,i*512,512,(i+1)*512);alpha=128
   else:path=H/'rising104_height_edit01/generated.png';box=(i*768,128,(i+1)*768,896);alpha=224
   z,removed=sampled(path,box,a.words,i*16,alpha,n==104);assert np.array_equal(z,r.arr(H/'rising_right_hand_native05'/f'{form}_{n}_indices.png'));sources.append(z)
   proof.append({'ref':n,'form':form,'generated_sha256':r.sha(r.read(path)),'fixed_crop':box,'alpha_threshold':alpha,'disconnected_background_removed':removed,'native_source_exact':True})
  base,full=sources;fx0,fy0,fx1,fy1=FACE[n];face=(x>=fx0)&(x<fx1)&(y>=fy0)&(y<fy1);deco=poly(DECO[n]);common=poly(HEAD[n])&(np.isin(base,[0,2,5,8,14,15])|(face&np.isin(base,[7,10,11,12,13])))&~deco
  full=full.copy();full[common]=0;missing=(base>0)&(full==0)&~common;marks=[]
  for py,px in zip(*np.where(missing)):
   src=int(base[py,px]);dst={1:2,4:11,10:10,11:11,12:9,13:9,15:1}.get(src,lut[src])
   if py-160>=10 and src in(2,3,5,6,8,9,14):dst={2:2,3:3,5:5,6:3,8:4,9:5,14:5}[src]
   full[py,px]=dst;marks.append([int(px)-160,int(py)-160,src,dst])
  assert marks==row['contour_material_mapping']
  owner=np.full(base.shape,6,np.uint8);owner[(y>=11)&(x<=6)]=8
  arms=poly([(2,-5),(9,-5),(10,3),(8,9),(1,7),(0,2)])|poly([(-14,0),(-8,0),(-7,7),(-10,11),(-16,9)])if n==103 else poly([(1,-33),(10,-33),(12,-19),(9,-13),(2,-13),(2,-20)])|poly([(-16,-5),(-9,-5),(-9,0),(-7,4),(-7,9),(-15,10),(-17,5)])
  owner[arms]=7;owner[deco]=5
  assert np.array_equal(owner,r.arr(S/f'{n:03}_owner.png'))
  r.read(S/f'{n:03}_common_mask.png');assert np.array_equal(common,np.array(Image.open(S/f'{n:03}_common_mask.png'))>0)
  for pb in PBS:
   v=base if pb==0 else np.where(owner==pb,full,0).astype(np.uint8);assert np.array_equal(v,r.arr(S/f'{n:03}_bank{pb}_indices.png'));targets[n,pb]=v
 return targets,proof
def ultimate_targets(a,S):
 report=r.js(S/'report.json');targets={};proof=[];rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words],np.int32);lut=np.r_[0,1+(((rgb[17:32,None]-rgb[None,1:16])**2).sum(2)).argmin(1)].astype(np.uint8);assert lut.tolist()==report['palette_lut']
 for n in REFS:
  sources=[];path=H/('rising_ultimate_prepare103/generated.png'if n==103 else'rising_ultimate_right_retry02/generated.png');dn='rising_ultimate_prepare103_native01'if n==103 else'rising_ultimate_right_native02'
  for col,form,start in((0,'before',16),(1,'after',0)):
   z,_=sampled(path,(col*768,128,(col+1)*768,896),a.words,start,128);assert np.array_equal(z,r.arr(H/dn/f'{form}_{n}_indices.png'));sources.append(np.roll(z,int(n==103),0))
  before,fresh=sources;after=fresh.copy();fx0,fy0,fx1,fy1=FACE[n];face=(x>=fx0)&(x<fx1)&(y>=fy0)&(y<fy1);head=(poly(HEAD[n])|poly(DECO[n]))&(np.isin(before,[0,1,2,4,5,7,8,14,15])|face)
  head&=~((x>=1)&(x<=7)&(y>=-3)&(y<=7))if n==103 else~((x>=2)&(y<=-18))
  palms=(((x>=1)&(x<=6)&(y>=-3)&(y<=2))|((x>=-14)&(x<=-8)&(y>=1)&(y<=5)))if n==103 else(((x>=1)&(x<=7)&(y<=-25))|((x>=-16)&(x<=-10)&(y>=-5)&(y<=0)))
  common=head|(y>=11)|(palms&np.isin(before,[10,11,12,13]));after[common]=lut[before][common];extra=(after>0)&(before==0);coords=[[int(px)-160,int(py)-160,int(after[py,px])]for py,px in zip(*np.where(extra))];assert coords==([]if n==103 else[[-14,-2,15]])
  for px,py,val in coords:assert np.array_equal(rgb[val],rgb[16+val]);before[py+160,px+160]=val
  assert np.array_equal(before,r.arr(S/f'before_{n}_indices.png'))and np.array_equal(after,r.arr(S/f'after_{n}_indices.png'))
  r.read(S/f'{n}_common_mask.png');assert np.array_equal(common,np.array(Image.open(S/f'{n}_common_mask.png'))>0)
  same=np.all(r.color(before,a.words,16)==r.color(after,a.words),2)
  for pb in PBS:targets[n,pb]=after if pb==0 else np.where(same,0,before).astype(np.uint8)if pb==5 else np.zeros_like(after)
  proof.append({'ref':n,'generated_sha256':r.sha(r.read(path)),'native_two_costumes_source_exact':True,'common_mask_independently_rebuilt':True,'source_edge_added_before':coords,'whole_translation_y':int(n==103)})
 return targets,proof
def main(kind):
 P=H/f'prepared_rising_right_{kind}01';S=H/('rising_right_base_layers02'if kind=='base'else'rising_right_ultimate_shared02');filename='PL00_U.ARC'if kind=='base'else'PL02_U.ARC';q=r.js(P/'proposal.json');frozen=r.js(P/'INPUT_FROZEN.json')
 for name,h in frozen['files'].items():assert r.sha(r.read(P/name))==h
 r.check_lock(S);assert r.sha(r.read(S/'LOCK.json'))==q['source_art_manifest_sha256']
 old=r.read(ROOT/q['sequential_parent']['path']);new=r.read(ROOT/q['files'][filename]['path']);assert r.sha(old)==q['sequential_parent']['sha256']and r.sha(new)==q['files'][filename]['after'];a,b=r.Archive(old),r.Archive(new);targets,proof=base_targets(a,S)if kind=='base'else ultimate_targets(a,S)
 assert len(old)==len(new)and r.replace_entry(r.replace_entry(new,2,a.g),3,a.c)==old and a.p==b.p
 assert r.bank_offsets(a.g,allow_aliases=True)==r.bank_offsets(b.g,allow_aliases=True)and r.bank_offsets(a.c)==r.bank_offsets(b.c)
 count=collections.Counter();atlases={}
 for gb,(ab,bb)in enumerate(zip(a.banks,b.banks)):
  assert(ab['base'],ab['end'],len(ab['frames']))==(bb['base'],bb['end'],len(bb['frames']))
  for f,g in zip(ab['frames'],bb['frames']):
   aa=r.decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128);zz=r.decode_stream(b.g,g['offset'],g['limit'],g['tile_count']*128);assert aa.serialize()==a.g[aa.start:aa.end]and zz.serialize()==b.g[zz.start:zz.end];count['raw']+=1
   if gb==0 and f['index']in REFS:assert f['tile_count']==g['tile_count']==32;atlases[f['index']]=np.frombuffer(r.indexed_atlas(zz.data,32)[0],np.uint8).reshape(32,256)
   else:assert aa.data==zz.data and f['tile_count']==g['tile_count'];count['other_raw_exact']+=1
 sem=lambda cp:[(p['flags'],p['tile'],p['x'],p['y'])for p in cp['parts']]
 allowed=PBS if kind=='base'else(0,5)
 for pb in range(len(r.bank_offsets(a.c))):
  assert r.composition_frame(a.c,pb,0)['bank_frame_count']==r.composition_frame(b.c,pb,0)['bank_frame_count']
  for n in range(r.composition_frame(a.c,pb,0)['bank_frame_count']):
   ca,cb=r.composition_frame(a.c,pb,n),r.composition_frame(b.c,pb,n)
   if pb not in allowed or n not in REFS:assert sem(ca)==sem(cb);count['other_composition_records_exact']+=1
   if pb in PBS and n in REFS:
    for p in cb['parts']:
     t=p['tile'];assert 0<=t<32;tile=atlases[n][t//16*16:t//16*16+16,t%16*16:t%16*16+16];assert t%16!=0 or not tile[:,0].any();assert not p['flip_y']or not tile[0].any();count['gpu_parts']+=1
     if kind=='ultimate'and pb in(6,7,8):assert not tile.any();count['blank_reserved_parts']+=1
 for n in r.VALID:
  layers={}
  for pb in PBS:
   v=b.layer(n,pb)[0];count['layers']+=1
   if n in REFS:assert np.array_equal(v,targets[n,pb]);layers[pb]=v;count['authored_layers_exact']+=1
   else:assert np.array_equal(v,a.layer(n,pb)[0]);count['other_layers_exact']+=1
  if n not in REFS:continue
  for mask in range(16):
   for arm in(1,2):assert np.array_equal(np.array(b.composite(n,mask,arm)[0]),r.composite(layers,b.words,mask,arm));count['partial_RGBA']+=1
  for form,mask in(('base',0),('fourth',15))if kind=='base'else(('after',0),('before',15)):
   path=H/('rising_right_base_pack02'if kind=='base'else'rising_right_ultimate_pack01')/f'{form}_{n}.png';r.read(path);assert np.array_equal(np.array(Image.open(path)),r.composite(layers,b.words,mask,1));count['readback_PNG_exact']+=1
 assert count['raw']==(508 if kind=='base' else 512)and count['other_raw_exact']==count['raw']-2 and count['layers']==1140 and count['authored_layers_exact']==10
 for path,h in r.tracked.items():assert r.sha(path.read_bytes())==h
 out={'passed':True,'scope':'생성 원화의 실제 고정 셀 정규화·공통 머리/피부/의상 소유를 별도 재구성하고 103/104 신규10층·64부분조합을 출력 ARC에서 확인. 제작 함수 미호출. 실제게임/새원화 수용은 별도.','candidate_sha256':r.sha(new),'source_sha256':r.sha(old),'counts':dict(count),'source_reconstruction':proof,'only_graphics_composition_changed':True,'fixed_archive_bank_bounds':True,'palette_audio_static_other_entries_exact':True,'producer_functions_called':False,'runtime_verified':False,'source_files_unchanged':{r.rel(p):h for p,h in r.tracked.items()}}
 path=O/(kind+'.json');path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'kind':kind,'passed':True,'counts':dict(count),'report_sha256':r.sha(path.read_bytes())}))
if __name__=='__main__':
 for k in('base','ultimate'):main(k)
