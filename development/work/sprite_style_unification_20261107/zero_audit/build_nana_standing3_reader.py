"""기존 독립 reader의 읽기 보존 검사를 재사용해 별도 정지3 검사기를 구성한다."""
from pathlib import Path
D=Path(__file__).parent
src=(D/'verify_nana_base_special4_independent.py').read_text('utf8')
head=src[:src.index('donorp=')]
head=head.replace('특수4','정지3').replace('root_nana_special','root_nana_standing').replace('joint_layers04','joint_layers06').replace('packed_special02','packed_standing03').replace('nana_base_special4_independent01','nana_base_standing3_independent01').replace('REFS={95,96,98,99}','REFS={88,89,97}')
head=head.replace("oldp=B/'root_nana_lowhp/packed_lowhp01/PL00_U.ARC'","oldp=B/'root_nana_special/packed_special02/PL00_U.ARC'")
head=head.replace('f2a968791b3411642a64bec9eb384a7f4b6a6d4e45be928a17b39262676f3648','87cc15efefedd475e0de972587995ad351d3ded1bd38a5c5096d5a3ab441748e').replace('ac1e35b7131d3909a93ea3466859aa9d7278c431d72defcb261b2b76cd1f6e16','f2a968791b3411642a64bec9eb384a7f4b6a6d4e45be928a17b39262676f3648')
head=head.replace('57d4627ed5a08b98f208cd8a27e40cee7979df1729940b6486f82504c15ebf3c','26765dc823179faae9a24b9102fbccb9aa8d511434e784931b0245a77d3a4711').replace('raw,parts,sig,tile,color,polygons','raw,parts,sig,tile,color,polygons,render')
body=r'''
oldbody88=np.roll(a.layer(89)[0],-1,1);effectmask=oldbody88!=a.layer(88)[0]
effect=np.where(effectmask,a.layer(88)[0],0).astype(np.uint8)
assert np.count_nonzero(effect)==83 and np.all(effect[effect>0]==12)
assert [[int(x-160),int(y-160),int(effect[y,x])]for y,x in np.argwhere(effectmask)]==meta['original88_effect']
for pb in PBS[1:]:assert np.array_equal(np.roll(a.layer(89,pb)[0],-1,1),a.layer(88,pb)[0])
target={};proof=[];bodies={};eyelids=[]
for entry in meta['source_registration']:
 n=entry['ref'];pair={form:registered[form,n].copy()for form in('base','fourth')}
 if n==97:
  for form in('base','fourth'):
   q=next(q for q in reg['frames']if q['ref']==n and q['form']==form)
   rgba=np.asarray(image.crop(q['source_crop']));rgb=rgba[:,:,:3].astype(np.float32);alpha=rgba[:,:,3].astype(np.float32)/255
   start=16 if form=='fourth'else 0;pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32)
   available=np.array([i for i in range(1,16)if i!=14]);indices=np.empty(alpha.shape,np.uint8)
   for y in range(len(indices)):indices[y]=available[np.square(rgb[y,:,None,:]-pal[None,available,:]).sum(2).argmin(1)]
   votes=np.array([np.asarray(Image.fromarray(np.where(indices==i,alpha,0).astype(np.float32),'F').resize((96,96),Image.Resampling.BOX))[38,44]for i in available])
   vote=int(available[votes.argmax()]);m=next(q for q in entry['eye_registration']if q['form']==form)
   assert vote==m['own_source_vote']
   assert np.allclose(votes,[m['source_area_votes'][str(int(i))]for i in available],rtol=0,atol=1e-8)
   v=vote if form=='base'else int(pair['base'][150,156]);assert pair[form][149,156]==pair[form][150,156]==14
   assert v==m['after'] and v in(10,11,12,13);pair[form][150,156]=v
   eyelids.append({'form':form,'own_authored_palette_vote':vote,'applied_new_base_face_pixel':v,'world':[-4,-10],'upper_eye_preserved':True})
 base,fourth=pair['base'],pair['fourth']
 shared=poly([[-20,-32],[-11,-32],[-9,-18],[-14,-17],[-20,-23]])if n==89 else poly([[-14,-14],[-8,-14],[-7,-5],[-13,-4]])
 assert int(shared.sum())==entry['shared_module_pixels'];fourth[shared]=base[shared]
 src=fourth.copy();region=(Y>=7)&(Y<=22)&(X>=-18)&(X<=16)
 if n==97:region&=(Y>=11)|(X<=7)
 links=[]
 for y in range(167,183):
  runs=spans((src[y]>0)&region[y]);groups={}
  for gap in spans((base[y]>0)&(fourth[y]==0)&region[y]):
   near=min(runs,key=lambda q:np.abs(q[:,None]-gap).min());groups.setdefault((int(near[0]),int(near[-1])),[]).append(gap)
  for(l,r),gaps in groups.items():
   lo=min(l,*(int(g[0])for g in gaps));hi=max(r,*(int(g[-1])for g in gaps));dest=np.arange(lo,hi+1)
   assert max(l-lo,hi-r)<=2 and len(dest)<=max(3,2*(r-l+1))
   sx=np.arange(l,r+1)[np.rint(np.linspace(0,r-l,len(dest))).astype(int)];fourth[y,dest]=src[y,sx]
   links.extend({'destination':[int(x-160),y-160],'source':[int(s-160),y-160],'index':int(src[y,s])}for x,s in zip(dest,sx))
 assert links==entry['leg_registration']
 own=np.full((384,384),6,np.uint8);own[(Y>=5)|((X>=8)&(Y>=-5))]=8
 if n==89:
  own[poly([[-20,-33],[-9,-33],[-6,-15],[0,-7],[-6,-2],[-13,-12]])]=7
  own[poly([[3,-8],[12,-7],[14,6],[7,8],[3,2]])]=7
  own[poly([[-9,-22],[7,-22],[12,-14],[7,-7],[-6,-7]])]=5
  own[(X>=6)&(X<=11)&(Y>=-14)&(Y<=-9)]=5
  own[poly([[9,-8],[12,-7],[16,-5],[17,7],[7,8],[7,-4]])]=8
 else:
  own[poly([[-14,-15],[-8,-15],[-7,-6],[5,-7],[7,2],[-8,4],[-14,-1]])]=7
  own[poly([[-8,-21],[5,-21],[10,-14],[7,-6],[-6,-6]])]=5
  own[(X>=6)&(X<=11)&(Y>=-14)&(Y<=-9)]=5
  own[poly([[10,-8],[12,-7],[17,-1],[17,7],[7,8],[7,-4]])]=8
  own[shared]=7
  for x,y in((9,-8),(8,-7)):own[y+160,x+160]=8
 full=np.where(fourth,fourth,base).astype(np.uint8);paldiff=np.array([a.words[i]!=a.words[i+16]for i in range(16)])[full]
 diff=((full!=base)|((fourth>0)&paldiff))&(full>0)
 ls={0:base,**{pb:np.where(diff&(own==pb),full,0).astype(np.uint8)for pb in PBS[1:]}}
 for n2,dx in(((88,-1),(89,0))if n==89 else((97,0),)):
  for pb,z in ls.items():
   v=np.roll(z,dx,1).copy()
   if n2==88 and pb==0:v[effectmask]=effect[effectmask]
   assert np.array_equal(v,png(T/f'layer{pb}_{n2:03}.png'));target[n2,pb]=v
   frame=next(q for q in meta['frames']if q['ref']==n2);assert sha(v.tobytes())==frame['layer_hashes'][str(pb)]
  assert np.array_equal(np.roll(own,dx,1),png(T/f'owner_{n2:03}.png'))
  # Overlay output comparison is performed below against independently built layers.
  if n2!=88:bodies[n2]=(base.copy(),fourth.copy())
 proof.append({'ref':n,'same_row_leg_links':len(links),'source_pixels_only':True,'new_base_hand_gun_shared':True,'ownership_reconstructed':True})
# 97最종은 완성색을 바꾸지 않고 두 베일 texel의 부분 소유만 바꿨다.
prior=S/'joint_layers05';priorlayers={pb:png(prior/f'layer{pb}_097.png')for pb in PBS}
allowed=np.zeros((384,384),bool);allowed[152,169]=True;allowed[153,168]=True
for pb in PBS:
 assert np.array_equal(priorlayers[pb][~allowed],target[97,pb][~allowed])
assert np.array_equal(priorlayers[0],target[97,0])
z1=color(a,priorlayers[0]);z2=color(a,target[97,0])
for pb in(8,5,7,6):
 for z,v in((z1,priorlayers[pb]),(z2,target[97,pb])):
  rgba=color(a,v,16);m=rgba[:,:,3]>0;z[m]=rgba[m]
assert np.array_equal(z1,z2)
'''
body=body.replace('97最종','97최종')
checks=src[src.index('counts=collections.Counter()'):src.index('groups=[]')]
checks=checks.replace('assert len(qs)<=16','assert 0<len(qs)<=256')
checks=checks.replace(' for mask in(0,15):',' for mask in (() if n==88 else (0,15)):')
tail=r'''
groups=[]
assert a.banks[0]['frames'][88]['offset']==a.banks[0]['frames'][89]['offset']
assert b.banks[0]['frames'][88]['offset']==b.banks[0]['frames'][89]['offset']
ps89,ps88=parts(b,0,89),parts(b,0,88)
assert [(q['flags'],q['tile'],q['x']-1,q['y'])for q in ps89]==[sig(q)for q in ps88[:len(ps89)]]
effectparts=ps88[len(ps89):];assert np.array_equal(render(b,88,0,effectparts),effect)
assert not({q['tile']for q in effectparts}&{q['tile']for pb in PBS for q in parts(b,pb,89)})
for pb in PBS[1:]:assert [(q['flags'],q['tile'],q['x']-1,q['y'])for q in parts(b,pb,89)]==[sig(q)for q in parts(b,pb,88)]
groups.append({'refs':[88,89],'shared32_tile_stream':True,'body_records_x_minus1':True,'effect83_in_separate_tiles':True,'effect_records_after_body':True,'effect_records':[sig(q)for q in effectparts]})
nativep=S/'standing_components_native_checks.json';native=js(nativep);assert native['passed']
nr=native['resources']['PL00_U.ARC'];assert nr['candidate_sha256']==sha(new)
checks=next(q for q in nr['banks']if q['bank']==0)['native_decoder_checks']
for n in REFS:
 q=next(q for q in checks if q['frame']==n);assert q['decoded_sha256']==sha(raw(b,0,n)) and q['buffer_outside_and_unused_tail_preserved']
O.mkdir(exist_ok=True);sheets=[]
def board(items,name,cols,scale):
 boxes=[im.getbbox()for _,im in items if im.getbbox()];x0=min(q[0]for q in boxes)-4;y0=min(q[1]for q in boxes)-4;x1=max(q[2]for q in boxes)+4;y1=max(q[3]for q in boxes)+4
 cw=(x1-x0)*scale+12;ch=(y1-y0)*scale+26;im=Image.new('RGB',(cw*cols,ch*((len(items)+cols-1)//cols)),'#263345');dr=ImageDraw.Draw(im)
 for i,(title,pic)in enumerate(items):
  x,y=i%cols*cw,i//cols*ch;v=pic.crop((x0,y0,x1,y1)).resize(((x1-x0)*scale,(y1-y0)*scale),Image.Resampling.NEAREST);im.paste(v,(x+6,y+22),v);dr.text((x+6,y+4),title,fill='white')
 p=O/name;im.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes()),'no_opaque_pixels_clipped':True})
for n in sorted(REFS):board([(f'{n} {title}',ar.composite(n,mask,1)[0])for ar,mask,title in((a,0,'old base'),(b,0,'new base'),(a,15,'old fourth'),(b,15,'new fourth'))],f'full_{n:03}.png',4,5)
for n in(89,97):board([(f'{n} {title}',b.composite(n,mask,2)[0])for mask,title in((1,'head'),(2,'body'),(4,'arms'),(8,'legs'),(10,'body legs'))],f'partial_{n:03}.png',5,5)
assert counts['raw_checked']==508 and counts['non_target_raw_exact']==505 and counts['partial_RGBA_exact']==96
for path,h in tracked.items():assert sha((ROOT/path).read_bytes())==h,path
report={'passed':True,'scope':'Nana 기본/포스89/97 새4셀→눈표본·손총·동일행다리·부분소유→88 원효과파생→15층 독립',
 'candidate':rel(newp),'candidate_sha256':sha(new),'parent_sha256':sha(old),'target_manifest_sha256':sha((T/'manifest.json').read_bytes()),
 'counts':dict(counts),'source_quantization':quant,'source_registration':proof,'eye_source_votes':eyelids,'shared_streams':groups,
 'nonselected_shared_compositions':shared,'veil_two_cells_owner8':[[9,-8],[8,-7]],'full97_RGBA_unchanged_from_joint05':True,
 'other_entries_palette_audio_bank_boundaries_exact':True,'native_MIPS_existing_evidence':{'path':rel(nativep),'sha256':sha(nativep.read_bytes()),'three_new_decoded_hashes_match':True,'executed_here':False},
 'readback_sheets':sheets,'readback_actually_viewed':False,'inputs':tracked,'producer_functions_called':False,'runtime_verified':False,
 'limitations':['대상96RGBA 및1125비대상층/팔레트 보존.제작자7296전조합검사는반복하지않았다.','새MIPS실행/원시간표브라우저재생/실기/사용자수용은별도다.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'report_sha256':sha((O/'report.json').read_bytes()),'counts':dict(counts)}))
'''
(D/'verify_nana_base_standing3_independent.py').write_text(head+body+checks+tail,'utf8')
