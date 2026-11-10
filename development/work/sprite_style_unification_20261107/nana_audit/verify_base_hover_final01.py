"""최종 기본/포스 호버: 고정등록→50층 독립재구성, 실제 ARC/원FX 읽기 감사."""
from pathlib import Path
import collections,hashlib,json,struct,sys
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,binary_dilation
N=Path(__file__).resolve().parent;W=N.parent;ROOT=W.parents[1];R=W/'root_nana_hover';S=N/'base_hover_shot_support01';D=W/'zero_audit';O=N/'base_hover_final_independent01'
sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
from scripts.prepare_riko_ui import entry
from scripts.discover_inputs import psx_arc
from scripts.c01_audio_build import read_disc
from src.psx_player import bank_offsets,composition_frame,decode_stream,indexed_atlas
from src.psx_ui_atlas import local_composition,tile_pixels
from src.psx_static_effect import compose_static
need=lambda ok,msg:None if ok else (_ for _ in ()).throw(ValueError(msg))
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();tracked={};counts=collections.Counter()
def blob(p):
 v=p.read_bytes();tracked[rel(p)]=sha(v);return v
def js(p):return json.loads(blob(p))
def png(p):blob(p);return np.array(Image.open(p))
def eq(x,y,why):need(np.array_equal(x,y),why)
def raw(ar,gb,n):
 f=ar.banks[gb]['frames'][n];return decode_stream(ar.g,f['offset'],f['limit'],f['tile_count']*128).data
def ps(ar,pb,n):return composition_frame(ar.c,pb,n)['parts']
def signature(parts):return[(p['flags'],p['tile'],p['x'],p['y'])for p in parts]
def tile(ar,n,t):
 f=ar.banks[0]['frames'][n];v=np.frombuffer(indexed_atlas(raw(ar,0,n),f['tile_count'])[0],np.uint8).reshape(-1,256);return v[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
PBS=(0,5,6,7,8);KEYS=(221,223,225,227,229);REFS=tuple(range(221,231));EMPTY=(128,129,132,140,159);RESERVED={105,*range(175,183)}
Y,X=np.indices((384,384));Y-=160;X-=160
def box(v):return(X>=v[0])&(Y>=v[1])&(X<v[2])&(Y<v[3])
def composite(ar,ls,mask,arm=2):
 im=ar.rgba(ls[0])
 for bit,pb in((8,8),(1,5),(4,7),(2,6)):
  if mask&bit:im.alpha_composite(ar.rgba(ls[pb],32 if pb==7 and arm==2 else 16))
 return im
need(not O.exists(),'새 독립 폴더')
P=R/'packed_hover_final01';newp=P/'PL00_U.ARC';new=blob(newp);oldp=W/'root_nana_shot87/packed_settle01/PL00_U.ARC';old=blob(oldp);a,b=Archive(old),Archive(new)
need(sha(new)=='9c1ff453a2308ddc40f39e5790de0aa6a5cf41dda43165b0fa16808f8c3a643c','후보 고정');need(sha(old)=='8951948879773266cae0bebd408b411f4806b5652257bba3c50df0212b3c6e10','부모 고정')
lock=js(P/'INPUT_LOCK.json');need(sha(blob(P/'INPUT_LOCK.json'))=='7238a32bc08ebd7abdb17d82b09381f4ac08d8660c8d02fc772025ccc681c56d'and len(lock['files'])==446,'446 잠금')
for q in lock['files']:need(sha(blob(ROOT/q['path']))==q['sha256'],'잠금입력 '+q['path'])
meta=js(R/'final_targets01/manifest.json');need(sha(blob(R/'final_targets01/manifest.json'))==lock['target_manifest_sha256'],'목표 manifest')
target={};owners={};reconstruction=[];pdiff=np.array([a.words[i]!=a.words[i+16]for i in range(16)])
# 고정등록 원화의 전체 정수이동부터 다시 읽고, 공통 얼굴/손/하체와 소유를 독립 적용한다.
alignment=js(R/'body_alignment01/manifest.json');aligned={}
for q in alignment['frames']:
 src=png(ROOT/q['source']);need(sha(blob(ROOT/q['source']))==q['source_sha256'],'등록 전 원화 해시');dx,dy=q['translation'];z=np.zeros_like(src);ys,xs=np.nonzero(src);z[ys+dy,xs+dx]=src[ys,xs]
 eq(z,png(R/f'body_alignment01/{q["form"]}_{q["ref"]}_indices.png'),'강체 정합');aligned[q['ref'],q['form']]=z;counts['rigid_registrations_reconstructed']+=1
for n,cut in zip(KEYS,(5,6,5,7,5)):
 base=aligned[n,'base_legs'];fourth=aligned[n,'fourth'].copy();top={221:-16,223:-15,225:-14,227:-14,229:-15}[n]
 face=box([-8,top,2,top+10]);palm=box([-14,-5,-4,4]);legs=(Y>=cut)&~((X>=8)&(Y<=10));fourth[face|palm|legs]=base[face|palm|legs]
 full=np.where(fourth,fourth,base);own=np.full(base.shape,6,np.uint8);own[(Y<=-6)&(X>=-10)]=5;own[(X>=5)&(Y<=10)]=5;own[(X<=-4)&(Y>=-6)&(Y<=3)]=7
 if n in(221,229):own[(X>=1)&(Y<=-18)]=7
 if n==223:own[box([8,-13,16,-6])]=7
 own[face]=5;own[palm]=7;own[legs]=8;diff=((full!=base)|pdiff[full])&(full>0)&~legs
 ls={0:np.where(legs,0,base).astype(np.uint8),8:np.where(legs,base,0).astype(np.uint8),**{p:np.where(diff&(own==p),full,0).astype(np.uint8)for p in(5,6,7)}}
 for p,z in ls.items():eq(z,png(R/f'body_layers_probe01/layer{p}_{n}.png'),'몸체 공통층 '+str((n,p)));target[n,p]=z
 eq(own,png(R/f'body_layers_probe01/owner_{n}.png'),'몸체 소유');owners[n]=own
 reconstruction.append({'ref':n,'registered_rigid_source_to_common_layers_exact':True})
# 정본 사랑이는 source85 실제 색인20개를 직접 읽는다.
cm=js(S/'inputs_a01/manifest.json');coords=cm['canonical_source_texels'];canonical_arc=Archive(blob(N/'ultimate_vehicle_repaint/packed_vehicle_candidate_v1/PL02_U.ARC'));need(sha(canonical_arc.data)=='94326933d0dd62ccd7a5904019cae9fd36fc068a6acde8941d6bf8ff363666ca','정본 출처 ARC');canonical_source=canonical_arc.layer(85)[0];gm=box([-22,-11,-14,-5])&np.isin(canonical_source,range(1,10))
actualcoords=[[int(x-160),int(y-160),int(canonical_source[y,x])]for y,x in np.argwhere(gm)];need(actualcoords==coords and len(coords)==20,'정본85 20texel')
originmap={222:(-27,-9),224:(-29,-8),226:(-20,-10),228:(-17,-10),230:(-24,-11)};guns={};skinmaps={}
for n,(ox,oy) in originmap.items():
 q=n-1;ls={p:target[q,p]for p in PBS};base=ls[0].copy();base[ls[8]>0]=ls[8][ls[8]>0];fourth=base.copy()
 for p in(8,5,7,6):fourth[ls[p]>0]=ls[p][ls[p]>0]
 masks={};gun=np.zeros_like(base)
 for x,y,v in coords:gun[y+oy+169,x+ox+183]=v
 for form,z in(('base_legs',base),('fourth',fourth)):
  if n<230:
   folder=S/'arm_joint_probe_v2';prefix=f'{form}_{n}';mask=png(folder/f'{prefix}_edit_mask.png')>0;piece=png(folder/f'{prefix}_arm_indices.png');eq(gun,png(folder/f'{prefix}_gun_indices.png'),'원총구 정본변환');skinmaps[n,form]=png(folder/f'{prefix}_skin_mask.png')>0
  else:
   donor=np.roll(png(R/f'registered03_fit01/{form}_230_indices.png'),-1,axis=1)
   mask=box([-35,-15,-3,3])&~((X>=-11)&(Y<=-9));mask|=box([-3,-6,1,-2]);mask|=box([-15,3,-5,6])
   piece=np.where(mask,donor,0).astype(np.uint8);piece[box([ox-2,oy-3,ox+10,oy+4])&mask]=0
   skin=mask&np.isin(donor,(10,11,12,13))&(X<=ox+9)&(Y>=oy)&(Y<=oy+5);piece[gun>0]=gun[gun>0];piece[skin]=donor[skin];mask|=gun>0;skinmaps[n,form]=skin
  z[mask]=piece[mask];masks[form]=mask
 hand=box([ox-2,oy-3,ox+10,oy+6]);fourth[hand]=base[hand];full=np.where(fourth,fourth,base);own=owners[q].copy();own[masks['base_legs']|masks['fourth']|hand]=7;legs=ls[8]>0;diff=((full!=base)|pdiff[full])&(full>0)&~legs
 out={0:np.where(legs,0,base).astype(np.uint8),8:ls[8],**{p:np.where(diff&(own==p),full,0).astype(np.uint8)for p in(5,6,7)}}
 for p,z in out.items():eq(z,png(R/f'shoot_layers_probe02/layer{p}_{n}.png'),'사격 재구성 '+str((n,p)));target[n,p]=z
 guns[n]=gun;reconstruction.append({'ref':n,'registered_arm_masks_to_body_common_hand_to_layers_exact':True,'source85_texels':20,'engine_origin':list(originmap[n]),'230_removes_old_hand_and_duplicate_barrel':n==230})
# 이번 변경의 실제 생성원화를 독립 area-vote 재양자화한다. 최초 전체10몸체 생성은 재양자화 범위 밖이다.
source=R/'rearfoot_edit01/generated.png';need(sha(blob(source))=='97ba28d207b3ac19e7fbce658897d5cc8d9eb879b86c139bd2b946192a8f409e','새발 원화');im=Image.open(source).convert('RGBA');foot_donors=[]
for form in(0,1):
 crop=im.crop((form*im.width//2,0,(form+1)*im.width//2,im.height));pix=np.array(crop);rgb=pix[:,:,:3].astype(np.float32);alpha=pix[:,:,3].astype(np.float32)/255;pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[form*16:form*16+16]],np.float32)
 labels=np.zeros(alpha.shape,np.uint8)
 for y in range(crop.height):labels[y]=1+((rgb[y,:,None,:]-pal[None,1:,:])**2).sum(2).argmin(1)
 green=(rgb[:,:,1]>rgb[:,:,0]+15)&(rgb[:,:,1]>rgb[:,:,2]+15)&(pix[:,:,3]>=128);green[crop.height//2:]=False;labels[green]=14
 votes=np.stack([np.array(Image.fromarray(np.where(labels==i,alpha,0).astype(np.float32),'F').resize((96,96),Image.Resampling.BOX))for i in range(1,16)]);coverage=np.array(Image.fromarray(alpha,'F').resize((96,96),Image.Resampling.BOX));small=1+votes.argmax(0).astype(np.uint8);small[coverage<.5]=0;eyes=votes[13].copy();eyes[coverage<.5]=0;eyes[48:]=0
 if eyes.max()>.015:small[np.unravel_index(eyes.argmax(),eyes.shape)]=14
 donor=np.zeros((384,384),np.uint8);donor[112:208,112:208]=small;eq(donor,png(R/f'rearfoot_registered01/donor_{form}.png'),'새발 생성 직접 재양자화');foot_donors.append(donor)
roi=box([-8,12,7,19]);legchanges=[]
for n in(229,230):
 original=target[n,8];z=original.copy();z[roi]=foot_donors[0][roi];need(np.count_nonzero(z!=original)==20,'신발20셀');eq(z[~roi],original[~roi],'신발범위밖 불변');eq(z,png(R/f'rearfoot_registered01/layer8_{n}.png'),'신발 등록');target[n,8]=z
 legchanges.append({'ref':n,'changed_cells':[[int(x-160),int(y-160),int(original[y,x]),int(z[y,x])]for y,x in np.argwhere(z!=original)],'outside_ROI_exact':True,'new_source_area_vote_reconstructed':True})
for q in meta['frames']:
 n=q['ref']
 for p in PBS:eq(target[n,p],png(R/f'final_targets01/layer{p}_{n}.png'),'최종50층 원출처');need(sha(target[n,p].tobytes())==q['layer_hashes'][str(p)],'최종층해시')
# 최종ARC 실제 해독. 이전지원 후보와의 표시 변화는229/230 layer8의20셀뿐이어야 한다.
prior=Archive(blob(N/'base_hover_pack_support01/candidate01/PL00_U.ARC'));increment=[]
for n in REFS:
 for p in PBS:
  z=b.layer(n,p)[0];eq(z,target[n,p],'최종ARC50 '+str((n,p)));d=int(np.count_nonzero(z!=prior.layer(n,p)[0]));need(d==(20 if n in(229,230)and p==8 else 0),'지원후보 변경영향');counts['target_layers_exact']+=1
  if d:increment.append({'ref':n,'layer':p,'changed_index_cells':d})
need(len(old)==len(new)and a.p==b.p,'길이/팔레트');entries=psx_arc(old);need([(e['type'],e['offset'],e['size'])for e in entries]==[(e['type'],e['offset'],e['size'])for e in psx_arc(new)],'ARC항목배치')
for e in entries:
 if int(e['type'],16)not in(2,3):s=slice(e['offset'],e['offset']+e['size']);need(old[s]==new[s],'외부항목exact')
need(bank_offsets(a.c)==bank_offsets(b.c)and bank_offsets(a.g,allow_aliases=True)==bank_offsets(b.g,allow_aliases=True),'모든은행경계')
for gb,(ab,bb)in enumerate(zip(a.banks,b.banks)):
 need((ab['base'],ab['end'])==(bb['base'],bb['end']),'그래픽경계')
 for af,bf in zip(ab['frames'],bb['frames']):
  n=af['index'];counts['raw_checked']+=1
  if gb or n not in REFS:need(raw(a,gb,n)==raw(b,gb,n)and af['tile_count']==bf['tile_count'],'비대상raw');counts['non_target_raw_exact']+=1
  else:need(bf['tile_count']==32,'32tile')
for n in KEYS:
 for ar in(a,b):
  fs=ar.banks[0]['frames'];need([f['index']for f in fs if f['offset']==fs[n]['offset']]==[n,n+1],'원사격짝공유')
 eq(target[n,8],target[n+1,8],'다리짝공유')
for n in range(237):
 if n in RESERVED:continue
 if n not in REFS:
  for p in PBS:eq(a.layer(n,p)[0],b.layer(n,p)[0],'비대상 표시층');counts['non_target_layers_exact']+=1
for p in range(len(bank_offsets(a.c))):
 for n in range(composition_frame(a.c,p,0)['bank_frame_count']):
  oldparts,newparts=ps(a,p,n),ps(b,p,n)
  if p in PBS and n in REFS:
   for q in newparts:
    t=q['tile']+q['page']*256;v=tile(b,n,t);need(0<=t<32 and not q['unknown_flags'],'GPU tile범위');need(not(t%16==0 and v[:,0].any())and not(q['flip_y']and t//16==0 and v[0].any()),'GPU원경계');counts['GPU_parts_checked']+=1
  elif p==5 and n in EMPTY:
   need(len(oldparts)==1 and not newparts and not tile(a,n,oldparts[0]['tile']).any(),'빈5기록 정확예외');counts['transparent_head_count0_exceptions']+=1
  else:need(signature(oldparts)==signature(newparts),'비대상 레코드');counts['non_target_records_exact']+=1
partial=[];muzzle=[]
for n in REFS:
 for mask in range(16):
  for arm in(1,2):
   expected=composite(a,{p:target[n,p]for p in PBS},mask,arm);actual=b.composite(n,mask,arm)[0];need(expected.tobytes()==actual.tobytes(),'부분RGBA');counts['partial_RGBA_exact']+=1
   if mask&8:need(label(np.asarray(actual)[:,:,3]>0,np.ones((3,3)))[1]==1,'유효호버1몸체');counts['valid_hover_single_body']+=1
   if n in guns:
    z=target[n,0].copy()
    for bit,p in((8,8),(1,5),(4,7),(2,6)):
     if mask&bit:z[target[n,p]>0]=target[n,p][target[n,p]>0]
    ox,oy=originmap[n];need(all(z[y+160,ox+161]==guns[n][y+160,ox+161]>0 for y in(oy-1,oy)),'두총구행');counts['muzzle_rows_conditions']+=1
    ongun=guns[n]>0;dif=ongun&(z!=guns[n]);need(np.isin(z[dif],(10,11,12,13)).all(),'정본가림은새손피부만')
 for mask in(8,15):partial.append({'ref':n,'mask':mask,'body_RGBA_sha256':sha(b.composite(n,mask)[0].tobytes())})
# 실제원US 탄환발사표와 독립FX의 전체 소비타일/15제트·7탄환을 재조립한다.
usdata=read_disc(ROOT/'MegaMan X4.bin',('SLUS_005.61','PL00_U.ARC'))[0];exe=usdata['SLUS_005.61'];us=Archive(usdata['PL00_U.ARC']);off=lambda addr:addr-struct.unpack_from('<I',exe,24)[0]+2048
for n,xy in originmap.items():need(struct.unpack_from('<bb',exe,off(0x8011b230+n*2))==xy,'원 signed 총구')
def effect(ar,p,n):
 cp=composition_frame(ar.c,p,n);pix,sz,bb,_=compose_static(entry(ar.data,0x10206),local_composition(cp));z=np.zeros((384,384),np.uint8);z[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]=np.frombuffer(pix,np.uint8).reshape(sz[1],sz[0]);return z,cp
jetmeta=js(D/'nana_ultimate_hover_relations01/conclusions.json');jets={};flash={}
for q in jetmeta['effect_frames']:
 i=q['effect_frame'];z,cp=effect(b,12,i);uz,ucp=effect(us,12,i);eq(z,uz,'原US제트15');need(signature(cp['parts'])==signature(ucp['parts']),'原US제트조립');need(sha(z.tobytes())==q['indexed_sha256'],'기존독립제트');jets[i]=z;counts['original_jet_phases_exact']+=1
for q in jetmeta['whole_tiles']:need(tile_pixels(entry(new,0x10206),q['tile'])==tile_pixels(entry(us.data,0x10206),q['tile']),'原제트 전체타일');counts['original_jet_whole_tiles_exact']+=1
for i in range(7):
 z,cp=effect(b,1,i);uz,ucp=effect(us,1,i);eq(z,uz,'원탄환7');need(signature(cp['parts'])==signature(ucp['parts']),'탄환조립');flash[i]=z;counts['original_projectile_phases_exact']+=1
need(np.count_nonzero(flash[0])==188,'첫188효과')
O.mkdir();sheets=[]
def board(items,name,cols,scale=5):
 boxes=[im.getbbox()for title,im in items if im.getbbox()];bb=(min(t[0]for t in boxes)-3,min(t[1]for t in boxes)-3,max(t[2]for t in boxes)+3,max(t[3]for t in boxes)+3);w,h=bb[2]-bb[0],bb[3]-bb[1];cw,ch=w*scale+10,h*scale+26;out=Image.new('RGB',(cw*cols,ch*((len(items)+cols-1)//cols)),'#273446');draw=ImageDraw.Draw(out)
 for j,(title,im)in enumerate(items):
  x,y=j%cols*cw,j//cols*ch;v=im.crop(bb).resize((w*scale,h*scale),Image.Resampling.NEAREST);out.paste(v,(x+5,y+22),v);draw.text((x+5,y+3),title,fill='white')
 p=O/name;out.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes()),'same_origin':True,'fixed_nearest_scale':scale,'world_crop':[v-160 for v in bb]})
for n in KEYS:
 items=[]
 for r in(n,n+1):
  for mask in(8,15):
   items.extend([(f'{r} m{mask} idle',b.composite(0,0 if mask==8 else 15)[0]),(f'{r} m{mask} parent',a.composite(r,mask)[0]),(f'{r} m{mask} final ARC',b.composite(r,mask)[0])])
 board(items,f'readback_{n}.png',6,5)
for n in KEYS:
 items=[]
 for r in(n,n+1):
  for mask in(8,15):
   for i in range((n-221)//2*3,(n-221)//2*3+3):
    fx=np.zeros((384,384,4),np.uint8);fx[jets[i]>0]=(60,155,220,255);im=Image.fromarray(fx);im.alpha_composite(b.composite(r,mask)[0]);items.append((f'{r} m{mask} neutral jet{i}',im))
 board(items,f'jet_{n}.png',6,4)
items=[]
for n,(ox,oy)in originmap.items():
 for mask in(8,15):
  z=np.roll(np.roll(flash[0],oy,0),ox,1);fx=np.zeros((384,384,4),np.uint8);fx[z>0]=(225,180,40,255);im=Image.fromarray(fx);body=b.composite(n,mask)[0];im.alpha_composite(body);ImageDraw.Draw(im).point((ox+160,oy+160),fill='#00ffff');items.append((f'{n} m{mask} muzzle {ox},{oy}',im));muzzle.append({'ref':n,'mask':mask,'origin':[ox,oy],'mouth_x':ox+1,'barrel_rows':[oy-1,oy],'first188_body_overlap':int(((z>0)&(np.asarray(body)[:,:,3]>0)).sum())})
board(items,'muzzle_10.png',5,5)
board([(f'{n} m{mask}',b.composite(n,mask)[0])for n in(229,230)for mask in range(8,16)],'last_pair_partial.png',8,4)
for p,h in tracked.items():need(sha((ROOT/p).read_bytes())==h,'읽기입력 불변 '+p)
report={'passed':True,'scope':'기본/포스 호버10 최종50층 독립출처재구성/ARC재독출·원총구/제트·부분조합·비대상 검증','candidate':rel(newp),'candidate_sha256':sha(new),'parent_sha256':sha(old),'input_lock_sha256':sha(blob(P/'INPUT_LOCK.json')),'locked_input_files':446,'counts':dict(counts),'source_reconstruction':reconstruction,'new_rearfoot_changes':legchanges,'incremental_vs_support_candidate':increment,'muzzle':muzzle,'readback_sheets':sheets,'readback_actually_viewed':False,'inputs':tracked,'producer_functions_called':False,'source_or_candidate_changed':False,'new_MIPS_executed':False,'gameplay_verified':False,'limits':['최초10몸체·8사격팔 원화 전체의 RGB 재양자화는 재실행하지 않았다. 고정등록 원화부터 공통화/소유/팔합성/정본20을 직접 재구성했다. 새229 신발 원화2셀은 직접 재양자화했다.','320부분 RGBA와160유효호버 단일몸체를 검사했다. 제작자7296 전체조합 검사를 본감사 실행으로 재계산해 보고하지 않는다.','원총구표/15제트/7탄환은 원US바이트와 정적재조립 대조이다. 중립색 효과판은 실제CLUT/반투명/렌더순서/시간표 실기가 아니다.','기존 지원count0 원MIPS26회와 별도 Root최종MIPS15는 각기 별도 근거이며 여기서는 새실행하지 않았다.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'report_sha256':sha((O/'report.json').read_bytes()),'counts':dict(counts),'sheets':len(sheets)}))
