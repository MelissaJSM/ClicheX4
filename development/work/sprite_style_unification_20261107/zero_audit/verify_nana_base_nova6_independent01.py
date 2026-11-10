"""기본/포스 노바 새6셀→부분소유/원효과→30층/최종ARC 독립 reader."""
from pathlib import Path
import collections,hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import binary_dilation,binary_fill_holes,distance_transform_edt,label
R=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent;N=W/'nana_audit';U=N/'base_nova_repaint';sys.path[:0]=[str(R),str(D)]
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from src.psx_player import bank_offsets,composition_frame
from verify_shibuki_ultimate_hurt13_independent import raw,parts,sig,tile,color
P=U/'packed_nova_candidate_v1';O=D/'nana_base_nova6_independent01';assert not O.exists()
PBS=(0,5,6,7,8);REFS={213,214,215,216,217,220};RESERVED={105,*range(175,183)}
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(R).as_posix();tracked={};counts=collections.Counter()
def blob(p):
 v=p.read_bytes();tracked[rel(p)]=sha(v);return v
def js(p):return json.loads(blob(p))
def png(p):blob(p);return np.array(Image.open(p))
def equal(z,p):assert np.array_equal(z,png(p)),str(p)
Y,X=np.indices((384,384));Y-=160;X-=160
def box(x0,y0,x1,y1):return(X>=x0)&(X<x1)&(Y>=y0)&(Y<y1)
def composite(ls,mask,arm=1):
 out=color(a,ls[0])
 for bit,pb in((8,8),(1,5),(4,7),(2,6)):
  if mask&bit:z=color(a,ls[pb],32 if pb==7 and arm==2 else 16);m=z[:,:,3]>0;out[m]=z[m]
 return out
oldp=W/'root_nana_hover/packed_hover_final01/PL00_U.ARC';newp=P/'PL00_U.ARC';old,new=blob(oldp),blob(newp);a,b=Archive(old),Archive(new)
assert sha(old)=='9c1ff453a2308ddc40f39e5790de0aa6a5cf41dda43165b0fa16808f8c3a643c'
assert sha(new)=='94cf560530c87ac11a03c029a9b6e98be44c06ea6d30d6c5ce66204c8a8e3cb3'
lock=js(P/'INPUT_FROZEN.json');assert lock['candidate_sha256']==sha(new)and lock['parent_sha256']==sha(old)and len(lock['files'])==159
for q in lock['files']:assert sha(blob(R/q['path']))==q['sha256'],q['path']
ver=js(P/'verification.json');pr=js(P/'proposal.json');sourcever=js(P/'source_verification.json')
# 각96고정셀 전체에서 고해상도 색인별 alpha 면적투표를 직접 계산한다.
registered={};source_cells=[]
for page in('a','b'):
 m=js(U/f'{page}_registered_v1/manifest.json');art=R/m['source_art'];assert sha(blob(art))==m['source_art_sha256'];im=Image.open(art).convert('RGBA')
 for q in m['frames']:
  form,n=q['form'],q['ref'];start=16 if form=='fourth'else 0;cell=np.array(im.crop(q['source_crop']));rgb=cell[:,:,:3].astype(np.float32);alpha=cell[:,:,3].astype(np.float32)/255
  pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32);indices=np.empty(alpha.shape,np.uint8)
  for yy in range(len(indices)):indices[yy]=1+np.square(rgb[yy,:,None]-pal[None,1:]).sum(2).argmin(1)
  green=(rgb[:,:,1]>rgb[:,:,0]+15)&(rgb[:,:,1]>rgb[:,:,2]+15)&(cell[:,:,3]>=128);green[len(green)//2:]=False;indices[green]=14
  def area(z):return np.array(Image.fromarray(z.astype(np.float32),'F').resize((96,96),Image.Resampling.BOX))
  votes=np.stack([area(np.where(indices==i,alpha,0))for i in range(1,16)]);coverage=area(alpha);native=(1+votes.argmax(0)).astype(np.uint8);native[coverage<.5]=0
  eyes=votes[13].copy();eyes[coverage<.5]=0;eyes[48:]=0
  if eyes.max()>.015:native[np.unravel_index(eyes.argmax(),eyes.shape)]=14
  z=np.zeros((384,384),np.uint8);z[112:208,112:208]=native;assert sha(z.tobytes())==q['target_sha256'];equal(z,U/f'{page}_registered_v1/{form}_{n:03}_indices.png');registered[form,n]=z
  source_cells.append({'ref':n,'form':form,'source_crop':q['source_crop'],'indices_sha256':sha(z.tobytes())})
assert len(source_cells)==6
common=js(U/'common_layers_probe_v1/manifest.json');masters={};ownership=[]
for q in common['frames']:
 n=q['ref'];base=registered['base',n].copy();fourth=registered['fourth',n].copy()
 if n==213:
  m=box(-3,10,11,20)&(base>0);cut=np.where(m,base,0).astype(np.uint8);assert int(m.sum())==65 and sha(cut.tobytes())==q['rigid_moves'][0]['source_sha256'];base[m]=0;shift=np.roll(cut,-1,axis=0);base[shift>0]=shift[shift>0]
 shared=np.zeros(base.shape,bool)
 for bounds in q['shared_boxes']:shared|=box(*bounds)
 fourth[shared]=base[shared];donor=fourth.copy()
 for e in q['same_scanline_fourth_links']:
  x,y=e['destination'];sx,sy=e['source'];assert y==sy and abs(x-sx)<=2 and donor[sy+160,sx+160]==e['index']>0;fourth[y+160,x+160]=donor[sy+160,sx+160];counts['preparation_same_row_links']+=1
 full=np.where(fourth,fourth,base).astype(np.uint8);owner=np.full(base.shape,6,np.uint8);owner[(Y<-7)&(X>=(-7 if n==213 else -3))]=5;owner[(Y>=3)|((X>=10)&(Y>=-10))]=8
 if n==213:owner[box(-13,-8,-4,2)|box(5,-4,12,4)]=7
 else:owner[box(-12,-24,-3,-11)|box(6,-3,13,5)]=7
 owner[box(*q['shared_boxes'][0])]=5
 paldiff=np.array([a.words[i]!=a.words[i+16]for i in range(16)])[full];diff=((full!=base)|((fourth>0)&paldiff))&(full>0)
 ls={0:base,**{pb:np.where(diff&(owner==pb),full,0).astype(np.uint8)for pb in PBS[1:]}}
 for name,z in(('base',base),('fourth',fourth),('full',full),('owner',owner),('shared_mask',shared.astype(np.uint8)*255)):equal(z,U/f'common_layers_probe_v1/{name}_{n:03}_indices.png')
 for pb,z in ls.items():equal(z,U/f'common_layers_probe_v1/layer{pb}_{n:03}.png')
 before={pb:z.copy()for pb,z in ls.items()};bounds=[-12,-24,4,-8]if n==213 else[-8,-24,8,-8];m=(ls[5]>0)&~box(*bounds);assert not ls[8][m].any();ls[8][m]=ls[5][m];ls[5][m]=0
 assert np.array_equal(composite(ls,15),composite(before,15))and np.array_equal(ls[0],before[0]);assert int(m.sum())==(84 if n==213 else 58)
 hm=js(U/'preparation_effect_probe_v2/manifest.json');hq=next(p for p in hm['frames']if p['key']==n);actual=[[int(x-160),int(y-160),int(before[5][y,x])]for y,x in np.argwhere(m)];assert actual==hq['moved_head5_to_veil_leg8']
 ownership.append({'ref':n,'moved_cells':int(m.sum()),'source_owner':5,'destination_owner':8,'outside_head_bounds':bounds,'full_base_fourth_exact':True});masters[n]=ls
uspath=W/'shibuki_audit/chaser_sources01/original_base.ARC';usdata=blob(uspath);assert sha(usdata)=='92b2a3209ad6603cf519616dc580400434271f87e8e7129495430c04d0d1c35a';us=Archive(usdata)
fxmask=(us.layer(213,0)[0]==0)&(us.layer(214,0)[0]>0);fx=np.where(fxmask,us.layer(214,0)[0],0).astype(np.uint8);assert int(fxmask.sum())==124;equal(fx,U/'preparation_effect_probe_v2/effect214_indices.png')
for pb in PBS:
 z=a.layer(213,pb)[0].copy();z[fxmask]=fx[fxmask]if pb==0 else 0;assert np.array_equal(z,a.layer(214,pb)[0])
target={}
for n in(213,214,215,216):
 for pb,z0 in masters[213 if n<215 else 215].items():
  z=z0.copy()
  if n==214:z[fxmask]=fx[fxmask]if pb==0 else 0
  target[n,pb]=z;equal(z,U/f'preparation_effect_probe_v2/layer{pb}_{n}.png')
dash=js(U/'dash_layers_probe_v1/manifest.json');base=registered['base',217].copy();fourth=registered['fourth',217].copy();shared=np.zeros(base.shape,bool)
for bounds in dash['shared_boxes']:shared|=box(*bounds)
fourth[shared]=base[shared];donor=fourth.copy()
for e in dash['same_scanline_fourth_links']:
 x,y=e['destination'];sx,sy=e['source'];assert y==sy and abs(x-sx)<=2 and donor[sy+160,sx+160]==e['index']>0;fourth[y+160,x+160]=donor[sy+160,sx+160];counts['dash_same_row_links']+=1
assert counts['dash_same_row_links']==11
full=np.where(fourth,fourth,base).astype(np.uint8);br=binary_dilation(base>0)&(base==0);fr=binary_dilation(full>0)&(full==0);bz=base.copy();fz=full.copy();bz[br]=9;fz[fr]=9;assert not((bz>0)&(fz==0)).any()
owner=np.full(base.shape,6,np.uint8);owner[(X>=4)|((X>=-5)&(Y<4))]=8;owner[box(-22,-12,-6,4)]=5;owner[box(-20,3,-8,12)|box(-8,0,-3,4)]=7
_,nearest=distance_transform_edt(full==0,return_indices=True);owner[fr]=owner[tuple(nearest[:,fr])]
paldiff=np.array([a.words[i]!=a.words[i+16]for i in range(16)])[fz];diff=((fz!=bz)|paldiff)&(fz>0);ls={0:bz,**{pb:np.where(diff&(owner==pb),fz,0).astype(np.uint8)for pb in PBS[1:]}}
assert np.array_equal(composite(ls,15),color(a,fz,16))
for name,z in(('base_body',base),('fourth_source',fourth),('fourth_union',full),('base_ring',br.astype(np.uint8)*255),('fourth_ring',fr.astype(np.uint8)*255),('owner',owner)):equal(z,U/f'dash_layers_probe_v1/{name}_217.png')
for pb,z in ls.items():equal(z,U/f'dash_layers_probe_v1/layer{pb}_217.png');target[217,pb]=z
oldbody=np.roll(a.layer(217,0)[0],1,axis=0);old220=a.layer(220,0)[0];om=oldbody>0;assert np.array_equal(old220[om],oldbody[om]);background=old220.copy();background[om]=0;background[om&binary_fill_holes(old220>0)]=9
bodybase=np.roll(bz,1,axis=0);outbase=background.copy();outbase[bodybase>0]=bodybase[bodybase>0];equal(background,U/'dash_layers_probe_v1/effect220_background_indices.png')
for pb in PBS:
 if pb:assert np.array_equal(a.layer(220,pb)[0],np.roll(a.layer(217,pb)[0],1,axis=0))
 z=outbase if pb==0 else np.roll(ls[pb],1,axis=0);target[220,pb]=z;equal(z,U/f'dash_layers_probe_v1/layer{pb}_220.png')
keep=~om&(bodybase==0);assert np.array_equal(outbase[keep],old220[keep]);assert(int((base>0).sum()),int((full>0).sum()),int(br.sum()),int(fr.sum()))==(653,684,120,116)
for q in ver['targets']:
 z=target[q['ref'],q['bank']];assert sha(blob(R/q['path']))==q['file_sha256']and sha(z.tobytes())==q['indices_sha256']
assert len(old)==len(new)and a.p==b.p
oe,ne=psx_arc(old),psx_arc(new);assert[(x['type'],x['offset'],x['size'])for x in oe]==[(x['type'],x['offset'],x['size'])for x in ne]
allow=np.zeros(len(old),bool)
for e in oe:
 if int(e['type'],16)in(2,3):allow[e['offset']:e['offset']+e['size']]=True
assert not np.any((np.frombuffer(old,np.uint8)!=np.frombuffer(new,np.uint8))&~allow)
assert bank_offsets(a.g,allow_aliases=True)==bank_offsets(b.g,allow_aliases=True)and bank_offsets(a.c)==bank_offsets(b.c)
for gb,(ab,bb)in enumerate(zip(a.banks,b.banks)):
 assert(ab['base'],ab['end'],len(ab['frames']))==(bb['base'],bb['end'],len(bb['frames']))
 if gb:assert a.g[ab['base']:ab['end']]==b.g[bb['base']:bb['end']]
 for af,bf in zip(ab['frames'],bb['frames']):
  n=af['index'];assert n==bf['index'];counts['raw_checked']+=1
  if gb==0 and n in REFS:assert bf['tile_count']==32
  else:assert raw(a,gb,n)==raw(b,gb,n)and af['tile_count']==bf['tile_count'];counts['non_target_raw_exact']+=1
reserved=[]
for n in range(237):
 for pb in PBS:
  if n in RESERVED:
   try:b.layer(n,pb)
   except(ValueError,IndexError)as e:
    try:a.layer(n,pb)
    except(ValueError,IndexError)as e2:assert(type(e),str(e))==(type(e2),str(e2))
    else:raise AssertionError('new invalid layer')
    reserved.append([n,pb,'same_exception']);continue
   assert np.array_equal(b.layer(n,pb)[0],a.layer(n,pb)[0]);reserved.append([n,pb,'exact']);continue
  assert np.array_equal(b.layer(n,pb)[0],target[n,pb]if n in REFS else a.layer(n,pb)[0]),(n,pb);counts['target_layers_exact'if n in REFS else'non_target_layers_exact']+=1
for pb in range(len(bank_offsets(a.c))):
 for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
  op,bp=parts(a,pb,n),parts(b,pb,n)
  if pb in PBS and n in REFS:
   for p in bp:
    t=p['tile']+p['page']*256;assert 0<=t<b.banks[0]['frames'][n]['tile_count']and p['unknown_flags']==0;z=tile(b,n,t)
    assert not(t%16==0 and z[:,0].any())and not(p['flip_y']and t//16==0 and z[0].any());counts['GPU_parts']+=1
  else:assert[sig(q)for q in op]==[sig(q)for q in bp];counts['non_target_compositions_exact']+=1
groups=[]
for n in sorted(REFS):
 og=[q['index']for q in a.banks[0]['frames']if q['offset']==a.banks[0]['frames'][n]['offset']];ng=[q['index']for q in b.banks[0]['frames']if q['offset']==b.banks[0]['frames'][n]['offset']]
 assert og==ng and set(ng)<=REFS;groups.append({'ref':n,'owners':ng,'tiles':b.banks[0]['frames'][n]['tile_count']})
 for mask in range(16):
  for arm in(1,2):
   expected=composite({pb:target[n,pb]for pb in PBS},mask,arm);actual=np.array(b.composite(n,mask,arm)[0]);assert np.array_equal(expected,actual);counts['target_partial_RGBA_exact']+=1
   if n==214:assert np.array_equal(actual[fxmask],color(a,fx)[fxmask]);counts['effect214_RGBA_conditions']+=1
assert len({tuple(q['owners'])for q in groups})==4
native=js(U/'native_components_v1_native_checks.json');assert native['passed'];nr=native['resources']['PL00_U.ARC'];assert nr['candidate_sha256']==sha(new)and nr['GPU_part_edge_checks']==114
for row in nr['banks'][0]['native_decoder_checks']:assert row['decoded_sha256']==sha(raw(b,0,row['frame']))
assert [counts[k]for k in('raw_checked','non_target_raw_exact','target_layers_exact','non_target_layers_exact','non_target_compositions_exact','GPU_parts','target_partial_RGBA_exact','effect214_RGBA_conditions')]==[508,502,30,1110,1757,114,192,32],counts
O.mkdir(exist_ok=False);sheets=[]
def sheet(name,rows,scale=4):
 boxes=[im.getbbox()for row in rows for _,im in row if im.getbbox()];crop=(min(z[0]for z in boxes)-3,min(z[1]for z in boxes)-3,max(z[2]for z in boxes)+3,max(z[3]for z in boxes)+3);w,h=crop[2]-crop[0],crop[3]-crop[1];cw,ch=w*scale+10,h*scale+25;out=Image.new('RGB',(cw*len(rows[0]),ch*len(rows)),'#263345');dr=ImageDraw.Draw(out)
 for y,row in enumerate(rows):
  for x,(caption,im)in enumerate(row):
   dr.text((x*cw+3,y*ch+3),caption,fill='white');v=im.crop(crop).resize((w*scale,h*scale),Image.Resampling.NEAREST);out.paste(v,(x*cw+5,y*ch+22),v)
 p=O/name;out.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes()),'crop':crop,'integer_scale':scale})
for i,ns in enumerate(((213,214),(215,216),(217,220))):sheet(f'readback_{i+1}.png',[[(f'{n} old base',a.composite(n,0)[0]),(f'{n} new base',b.composite(n,0)[0]),(f'{n} old Fourth',a.composite(n,15)[0]),(f'{n} new Fourth',b.composite(n,15)[0])]for n in ns],3 if i==2 else 5)
sheet('partial_preparation.png',[[(f'{n} mask{mask}',b.composite(n,mask)[0])for mask in(1,2,4,8,15)]for n in(213,215)],5)
sheet('partial_dash.png',[[(f'217 mask{mask}',b.composite(217,mask)[0])for mask in(1,2,4,8,15)]],5)
for p,h in tracked.items():assert sha((R/p).read_bytes())==h,p
report={'passed':True,'scope':'Nana 기본/포스 Nova6의 생성6셀→공통손/같은행하체/소유→원효과/30층/실제ARC 독립 읽기','candidate':rel(newp),'candidate_sha256':sha(new),'parent_sha256':sha(old),'counts':dict(counts),'generated_fixed_cells_direct_requantized':source_cells,'preparation213_boot_local_translation':[0,-1],'rear_veil_ownership':ownership,'effect214':{'original_US_external_pixels':124,'parent_5layers_rule_reproduced':True,'new_body_and_armor_occlusion_rule_exact':True,'RGBA_conditions':32,'whole_original_effect_tiles_copied':False},'alias216_215_all5_exact':True,'dash217':{'new_base_body_pixels':653,'new_fourth_union_pixels':684,'new_Manhattan1_index9_ring':[120,116],'common_hand_boxes':dash['shared_boxes'],'same_row_source_links':11},'effect220':{'parent_body_y1_rule_exact':True,'removed_oldbody_region_pixels':int(om.sum()),'parent_external_effect_pixels':int(((old220>0)&~om).sum()),'new_body_occludes_external_effect':int(((old220>0)&~om&(bodybase>0)).sum()),'outside_oldbody_and_newbody_world_indices_exact':True,'whole_effect_raw_exact':False,'new_armor_layers_y1_exact':True},'energy218219_raw_5layers_records_exact':True,'entry_bank_boundaries_palette_audio_exact':True,'stream_groups':groups,'reserved_layers':reserved,'native_producer6_raw_hashes_bound':True,'new_MIPS_execution':False,'readback_sheets':sheets,'actually_viewed':False,'inputs':tracked,'producer_functions_called':False,'resources_modified':False,'runtime_verified':False,'limits':['생성6고정셀은직접면적투표재양자화. 의미공통창/같은행표본은기록된선택범위와실제원화값을검사했다.','초기common_v1과최종preparation_v2의베일소유변경을구분하며전체그림이동일해도부분상태는변경이다.','220은새몸+1y와기존몸내부envelope9복원 정책이며전체FXraw보존이아니다.','원MIPS/재현거부/원순서/실기는다른범위이며이reader는새실행하지않는다.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'passed':True,'report_sha256':sha((O/'report.json').read_bytes()),'counts':dict(counts)}))
