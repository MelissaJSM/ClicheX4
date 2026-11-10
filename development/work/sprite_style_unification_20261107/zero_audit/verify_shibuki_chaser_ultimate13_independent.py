"""Ultimate 체이서8 생성셀→공통층65→실제 ARC 독립 읽기. 제작 함수 미호출."""
from pathlib import Path
import collections,hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;H=D.parent/'shibuki_audit'
sys.path[:0]=[str(ROOT),str(D)]
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from src.psx_player import bank_offsets,composition_frame
from verify_shibuki_ultimate_hurt13_independent import raw,parts,sig,tile,color,polygons
P=H/'prepared_chaser_ultimate01';T=H/'chaser_ultimate_targets01';O=D/'shibuki_chaser_ultimate13_independent01'
PBS=(0,5,6,7,8);REFS=set(range(162,175));KEYS=(162,166,170,174);RESERVED={105,*range(175,183)}
GROUPS=((162,163,164,165),(166,167,168,169),(170,171,172,173),(174,))
DY={162:0,163:1,164:3,165:-1,166:0,167:1,168:3,169:-1,170:0,171:1,172:2,173:-1,174:0}
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();tracked={};counts=collections.Counter()
def blob(p):
 z=p.read_bytes();tracked[rel(p)]=sha(z);return z
def js(p):return json.loads(blob(p))
def png(p):blob(p);return np.array(Image.open(p))
def shift(z,dy):
 out=np.zeros_like(z);yy,xx=np.nonzero(z);assert not len(yy)or min(yy+dy)>=0 and max(yy+dy)<384
 out[yy+dy,xx]=z[yy,xx];return out
assert not O.exists(),'고유 출력폴더 필요'
oldp=H/'prepared_standing_fire_ultimate01/PL02_U.ARC';newp=P/'PL02_U.ARC';old,new=blob(oldp),blob(newp);a,b=Archive(old),Archive(new)
assert sha(old)=='1f271aeaee7c65a938a6a09116bc8b2317f7f138465f563d4c6cc1f3704ee1ad'
assert sha(new)=='2b8faa71d3a94bc6d52ac0e389c6121d530d6455e664ad852061c43c77789b5c'
proposal=js(P/'proposal.json');lock=js(P/'PREPARED_LOCK.json');source=js(P/'INPUT_LOCK.json');producer=js(P/'verification.json')
for p,h in lock['files'].items():assert sha(blob(P/p))==h,p
for p,h in lock['source_scripts'].items():assert sha(blob(H/p))==h,p
assert sha(blob(P/'INPUT_LOCK.json'))==proposal['target_lock_sha256']=='28aac47d6324becaccb69f80537691d4767242bdb643338057fcde680bc87609'
for p,h in source['files'].items():assert sha(blob(ROOT/p))==h,p
assert len(source['files'])==297 and source['candidate_sha256']==sha(new)and source['parent_sha256']==sha(old)
meta=js(T/'manifest.json');assert meta['parent_sha256']==sha(old)and set(meta['refs'])==REFS
for p,h in meta['source_files'].items():assert sha(blob(ROOT/p))==h,p
original=Archive(blob(H/'chaser_sources01/original_ultimate.ARC'));registered={};samples={};quant=[]
for page,ns in((1,(162,166)),(2,(170,174))):
 sd=H/f'chaser_ultimate_inputs{page:02}';nd=H/f'chaser_ultimate_native{page:02}';rm=js(nd/'report.json');art=sd/'generated.png'
 assert sha(blob(art))==js(sd/'generation_receipt.json')['sha256']==rm['source_sha256']
 im=Image.open(art).convert('RGBA');assert im.width==im.height;full=np.array(im.resize((192,192),Image.Resampling.NEAREST))
 for col,(form,pal)in enumerate((('before',16),('after',0))):
  rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[pal:pal+16]],np.int32)
  for row,n in enumerate(ns):
   cell=full[row*96:(row+1)*96,col*96:(col+1)*96];ind=(1+np.square(cell[:,:,:3].astype(np.int32)[:,:,None]-rgb[None,None,1:]).sum(3).argmin(2)).astype(np.uint8);ind[cell[:,:,3]<128]=0
   z=np.zeros((384,384),np.uint8);z[112:208,112:208]=ind
   assert np.array_equal(z,png(nd/f'{form}_{n:03}_indices.png'))and np.array_equal(cell,png(nd/f'{form}_{n:03}_sample_rgba.png'))
   registered[form,n]=z;samples[form,n]=cell;counts['generated_cells_requantized']+=1;quant.append({'ref':n,'form':form,'source':rel(art),'source_size':list(im.size),'canvas192_cell96_exact':True})
Y,X=np.indices((384,384));Y-=160;X-=160
contacts=js(H/'chaser_ultimate_contacts01/report.json');joint=js(H/'chaser_ultimate_common01/report.json');edge=js(H/'chaser_ultimate_common02/report.json')
assert edge['source_report_sha256']==sha(blob(H/'chaser_ultimate_common01/report.json'))
for q in contacts['rows']:
 form,n=q['form'],q['ref'];z=registered[form,n].copy()
 for e in q['gold_source_samples']:
  x,y=e['xy'];assert samples[form,n][y+48,x+48].tolist()==e['source_RGBA']and z[y+160,x+160]==e['nearest_index'];assert e['semantic_index']==7
  z[y+160,x+160]=7;counts['gold_source_samples']+=1
 if n==166:z=shift(z,-1)
 else:
  mask=(Y>=10)&(X>=3)&(X<=11)&(z>0);assert int(mask.sum())==q['movement']['source_pixels']==33
  part=np.where(mask,z,0);z[mask]=0;moving=shift(part,1);assert not np.any((moving>0)&(z>0));z[moving>0]=moving[moving>0]
 assert np.array_equal(z,png(H/f'chaser_ultimate_contacts01/{form}_{n:03}_indices.png'))and sha(z.tobytes())==q['indices_sha256'];registered[form,n]=z
rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words],np.int32)
lut=np.r_[0,1+np.square(rgb[17:32,None]-rgb[None,1:16]).sum(2).argmin(1)].astype(np.uint8)
back=np.r_[0,1+np.square(rgb[1:16,None]-rgb[None,17:32]).sum(2).argmin(1)].astype(np.uint8);assert lut.tolist()==joint['before16_to_after0']
masters={};joints=[]
for n in KEYS:
 q=next(q for q in joint['rows']if q['ref']==n);before=registered['before',n].copy();after=registered['after',n].copy()
 for e in q['gold_source_samples']:
  x,y=e['xy'];assert samples['before',n][y+48,x+48].tolist()==e['RGBA']and before[y+160,x+160]==e['old']and e['new']==7
  before[y+160,x+160]=7;counts['gold_source_samples']+=1
 bx,by=q['braid_x_ge_y_lt'];head=(Y<q['head_y_lt'])|((X>=bx)&(Y<by))
 legs=(((Y>=5)&(X<3))|(Y>=9))if n==162 else((((Y>=6)&(X<3))|(Y>=10))if n==166 else((((Y>=10)&(X<3))|((Y>=14)&(X<=8))|(Y>=17))if n==170 else Y>=14))
 hand=polygons([q['hand_polygon']])&np.isin(before,[10,12,13]);common=head|legs|hand;after[common]=lut[before][common]
 for name,z in [('head',head),('legs',legs),('hand',hand),('common',common)]:assert np.array_equal(z,png(H/f'chaser_ultimate_common01/{n:03}_{name}_mask.png')>0)
 for form,z in [('before',before),('after',after)]:assert np.array_equal(z,png(H/f'chaser_ultimate_common01/{form}_{n:03}_indices.png'))
 overlaps=[]
 if n==170:
  assert before[176,171]==0 and after[176,171]==15;before[176,171]=back[15];counts['new_donor_outline_registered']+=1
  for form,z in [('before',before),('after',after)]:
   mask=(Y>=16)&(X>=2)&(X<=10)&(z>0);assert mask.sum()==35;part=np.where(mask,z,0);z[mask]=0;moving=shift(part,-1);overlap=(moving>0)&(z>0);assert overlap.sum()==9
   rows=[[int(x)-160,int(y)-160,int(z[y,x]),int(moving[y,x])]for y,x in zip(*np.nonzero(overlap))]
   eq=next(q for q in next(r for r in edge['rows']if r['ref']==n)['registrations']if q.get('form')==form);assert rows==eq['overlap_rows'];z[moving>0]=moving[moving>0];overlaps.append({'form':form,'moved_pixels':35,'occluded_joint_pixels':9,'rows':rows})
 assert not np.any((after>0)&(before==0))
 for form,z in [('before',before),('after',after)]:assert np.array_equal(z,png(H/f'chaser_ultimate_common02/{form}_{n:03}_indices.png'))
 diff=np.any(color(a,before,16)!=color(a,after,0),axis=2);ls={0:after,5:np.where(diff,before,0).astype(np.uint8),**{pb:np.zeros_like(before)for pb in (6,7,8)}}
 for pb,z in ls.items():assert np.array_equal(z,png(H/f'chaser_ultimate_common02/{n:03}_bank{pb}_indices.png'))
 masters[n]=ls;joints.append({'ref':n,'common_masks_reconstructed':True,'moved_ankle':overlaps,'source_only_no_old_body_copy':True})
target={};aliases=[]
for g in GROUPS:
 k=g[0]
 for n in g:
  pd={}
  for pb in PBS:
   z=shift(masters[k][pb],DY[n]);assert np.array_equal(z,png(T/f'{n:03}_bank{pb}_indices.png'))and sha(z.tobytes())==meta['targets'][str(n)][str(pb)]
   assert np.array_equal(original.layer(n,pb)[0],shift(original.layer(k,pb)[0],DY[n]));pd[str(pb)]=int((a.layer(n,pb)[0]!=shift(a.layer(k,pb)[0],DY[n])).sum());target[n,pb]=z
  aliases.append({'ref':n,'master':k,'dy':DY[n],'original_US_5layers_exact':True,'parent_layer_differences':pd,'new_5layers_exact':True,'historical_after_differences_not_called_original_alias':True})
assert len(old)==len(new)and a.p==b.p
oe,ne=psx_arc(old),psx_arc(new);assert [(q['type'],q['offset'],q['size'])for q in oe]==[(q['type'],q['offset'],q['size'])for q in ne];allow=np.zeros(len(old),bool)
for q in oe:
 if int(q['type'],16)in (2,3):allow[q['offset']:q['offset']+q['size']]=True
assert not np.any((np.frombuffer(old,np.uint8)!=np.frombuffer(new,np.uint8))&~allow)
assert bank_offsets(a.g,allow_aliases=True)==bank_offsets(b.g,allow_aliases=True)and bank_offsets(a.c)==bank_offsets(b.c)
for gb,(ab,bb)in enumerate(zip(a.banks,b.banks)):
 assert(ab['base'],ab['end'],len(ab['frames']))==(bb['base'],bb['end'],len(bb['frames']))
 if gb:assert a.g[ab['base']:ab['end']]==b.g[bb['base']:bb['end']]
 for af,bf in zip(ab['frames'],bb['frames']):
  n=af['index'];assert n==bf['index'];counts['raw_checked']+=1
  if gb==0 and n in REFS:assert 0<bf['tile_count']<=32
  else:assert raw(a,gb,n)==raw(b,gb,n)and af['tile_count']==bf['tile_count'];counts['non_target_raw_exact']+=1
reserved=[]
for n in range(237):
 for pb in PBS:
  if n in RESERVED:
   try:b.layer(n,pb)
   except(ValueError,IndexError)as ex:
    try:a.layer(n,pb)
    except(ValueError,IndexError)as ex2:assert type(ex)==type(ex2)and str(ex)==str(ex2)
    else:raise AssertionError('new invalid layer')
    reserved.append([n,pb,'same_exception']);continue
   assert np.array_equal(b.layer(n,pb)[0],a.layer(n,pb)[0]);reserved.append([n,pb,'exact']);continue
  assert np.array_equal(b.layer(n,pb)[0],target[n,pb]if n in REFS else a.layer(n,pb)[0]),(n,pb)
  counts['target_layers_exact'if n in REFS else'non_target_layers_exact']+=1
for pb in range(len(bank_offsets(a.c))):
 for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
  op,bp=parts(a,pb,n),parts(b,pb,n)
  if pb in PBS and n in REFS:
   for q in bp:
    t=q['tile']+q['page']*256;assert 0<=t<b.banks[0]['frames'][n]['tile_count']and q['unknown_flags']==0;z=tile(b,n,t)
    assert not(t%16==0 and z[:,0].any())and not(q['flip_y']and t//16==0 and z[0].any());counts['GPU_parts']+=1
  else:assert [sig(q)for q in op]==[sig(q)for q in bp];counts['non_target_compositions_exact']+=1
groups=[]
for n in sorted(REFS):
 owners=[q['index']for q in b.banks[0]['frames']if q['offset']==b.banks[0]['frames'][n]['offset']]
 oo=[q['index']for q in a.banks[0]['frames']if q['offset']==a.banks[0]['frames'][n]['offset']]
 assert oo==owners and set(owners)<=REFS;groups.append({'ref':n,'owners':owners,'old_tiles':a.banks[0]['frames'][n]['tile_count'],'new_tiles':b.banks[0]['frames'][n]['tile_count']})
components=[]
for n in sorted(REFS):
 for mask in range(16):
  for arm in (1,2):
   exp=color(b,target[n,0])
   for bit,pb in ((8,8),(1,5),(4,7),(2,6)):
    if mask&bit:v=color(b,target[n,pb],32 if pb==7 and arm==2 else 16);m=v[:,:,3]>0;exp[m]=v[m]
   act=np.array(b.composite(n,mask,arm)[0]);assert np.array_equal(exp,act);counts['partial_RGBA_exact']+=1;cc=label(act[:,:,3]>0,np.ones((3,3)))[1];components.append(int(cc));assert cc==1
assert counts['raw_checked']==512 and counts['non_target_raw_exact']==499 and counts['target_layers_exact']==65 and counts['non_target_layers_exact']==1075
assert counts['partial_RGBA_exact']==416 and counts['GPU_parts']==174
O.mkdir(exist_ok=False);sheets=[]
def sheet(name,rows):
 crop=(126,126,194,192);cw,ch=280,288;im=Image.new('RGB',(cw*len(rows[0]),ch*len(rows)),'#263345');dr=ImageDraw.Draw(im)
 for y,row in enumerate(rows):
  for x,(caption,pic)in enumerate(row):
   bb=pic.getbbox();assert crop[0]<=bb[0]and crop[1]<=bb[1]and crop[2]>=bb[2]and crop[3]>=bb[3]
   dr.text((x*cw+3,y*ch+3),caption,fill='white');v=pic.crop(crop).resize((272,264),Image.Resampling.NEAREST);im.paste(v,(x*cw+3,y*ch+22),v)
 p=O/name;im.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes())})
for n in KEYS:
 sheet(f'comparison_{n}.png',[[(f'{n} old before',a.composite(n,15)[0]),(f'{n} new before',b.composite(n,15)[0]),(f'{n} old after',a.composite(n,0)[0]),(f'{n} new after',b.composite(n,0)[0])]])
 sheet(f'partial_{n}.png',[[(f'{n} mask{mask}',b.composite(n,mask)[0])for mask in(0,1,2,4,8,15)]])
for i,g in enumerate(GROUPS):sheet(f'alias_{i}.png',[[(f'{n} before Y{DY[n]:+}',b.composite(n,15)[0])for n in g],[(f'{n} after Y{DY[n]:+}',b.composite(n,0)[0])for n in g]])
for p,h in tracked.items():assert sha((ROOT/p).read_bytes())==h,p
report={'passed':True,'scope':'Ultimate 체이서4새몸체×전후+9Y파생 13참조 독립읽기','candidate':rel(newp),'candidate_sha256':sha(new),'parent_sha256':sha(old),'input_lock_sha256':sha((P/'INPUT_LOCK.json').read_bytes()),'locked_inputs':len(source['files']),'counts':dict(counts),'generated8_requantization':quant,'joint_reconstruction':joints,'aliases':aliases,'stream_groups':groups,'all416_partial_single_component':True,'reserved_layers':reserved,'palette_audio_other_entries_all_bank_boundaries_exact':True,'readback_sheets':sheets,'actually_viewed':False,'inputs':tracked,'producer_functions_called':False,'new_MIPS_execution':False,'runtime_verified':False,'source_or_resource_modified':False,'overall_complete':False,'limits':['새생성8셀 고정표본/금색표본/공통머리·사지·손/162발+1·166전신-1·170발35셀-1(관절9셀가림)/후폼외곽1셀을독립재구성. 미술적수용과실제차량접점판정은별도.','원US Y별칭9는실제5층exact. 현재부모후폼의차이를새제작정책으로대체하며원PL02전체동일복사라하지않음.','원GPU정적타일경계174파트검사이며새MIPS실행/실제GPU/차량실기아님. 제작자원MIPS증거는별도.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'report_sha256':sha((O/'report.json').read_bytes()),'counts':dict(counts)}))
