"""PL00 호버 실제부분소유/원사격/제트 읽기. 원화/자원/로직 변경 없음."""
from pathlib import Path
import collections,hashlib,json,struct,sys
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import distance_transform_cdt
R=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent;H=W/'shibuki_audit';O=D/'shibuki_base_hover_ownership01';assert not O.exists()
sys.path[:0]=[str(R),str(D)]
from scripts.export_x_consistency import Archive,animation_map
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from src.psx_player import composition_frame,bank_offsets
from src.psx_static_effect import compose_static
from src.psx_ui_atlas import local_composition,tile_pixels
from verify_shibuki_ultimate_hurt13_independent import raw,parts,sig,tile
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(R).as_posix();off=lambda x:x-0x80010000+2048;tracked={};PBS=(0,5,6,7,8);REFS=set(range(221,231));KEYS=(221,223,225,227,229)
def blob(p):
 v=p.read_bytes();tracked[rel(p)]=sha(v);return v
def js(p):return json.loads(blob(p))
def bbox(z):
 y,x=np.nonzero(z);return None if not len(x)else[int(x.min()-160),int(y.min()-160),int(x.max()-159),int(y.max()-159)]
def coords(z):return[[int(x-160),int(y-160)]for y,x in np.argwhere(z)]
def static(ar,pb,n,ps=None):
 c=composition_frame(ar.c,pb,n)if ps is None else{'parts':ps};pixels,size,bb,_=compose_static(entry(ar.data,0x10206),local_composition(c));z=np.zeros((384,384),np.uint8)
 if len(pixels):z[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]=np.frombuffer(pixels,np.uint8).reshape(size[1],size[0])
 return z,c
def neutral(z,rgba=(40,220,240,190)):
 out=np.zeros((384,384,4),np.uint8);out[z>0]=rgba;return Image.fromarray(out)
bp=H/'prepared_nova_strike_base01/PL00_U.ARC';a=Archive(blob(bp));assert sha(a.data)=='36d4d0293abc77052c476e0495f4f4542ca75471c7a149f200e4bdb8f4e1bd4e'
original,_=read_disc(R/'MegaMan X4.bin',('PL00_U.ARC','PL02_U.ARC','SLUS_005.61'));u=Archive(original['PL00_U.ARC']);u2=Archive(original['PL02_U.ARC']);assert sha(u.data)=='92b2a3209ad6603cf519616dc580400434271f87e8e7129495430c04d0d1c35a'
disc=R/'out/ver_buki_riko/sprite_style_unification_20261107_v28/shibuki_riko.bin';current,_=read_disc(disc,('PL00_U.ARC','SLUS_005.61'));br=Archive(current['PL00_U.ARC']);oe=original['SLUS_005.61'];ce=current['SLUS_005.61']
for n in REFS:
 assert raw(a,0,n)==raw(br,0,n)
 for pb in PBS:assert np.array_equal(a.layer(n,pb)[0],br.layer(n,pb)[0])and[sig(p)for p in parts(a,pb,n)]==[sig(p)for p in parts(br,pb,n)]
codes=[]
for name,lo,hi in [('dispatcher',0x80023e70,0x80023ed0),('air_move',0x800339e0,0x80033b00),('hover_check',0x8003751c,0x800375b0),('hover_main_and_movement',0x800388f0,0x80038e90),('hover_jet',0x800b2ad0,0x800b2c8c),('muzzle',0x80092e2c,0x80092f08),('lemon',0x80092314,0x800924f8),('shoot_animation',0x80038524,0x800385ec),('shoot_air',0x80037338,0x800373d8),('partial_renderer',0x8002588c,0x80025ce0)]:
 code=ce[off(lo):off(hi)];assert code==oe[off(lo):off(hi)],name;codes.append({'name':name,'start':lo,'end':hi,'bytes':code.hex(),'sha256':sha(code),'original_US_exact':True})
wrapper=ce[off(0x800257bc):off(0x8002588c)];assert sha(wrapper)=='46c1fe4c8c01be08e49c733c24e99fe7e4e2416b93a2dc50585a3503854038c5';codes.append({'name':'accepted_costume_wrapper','start':0x800257bc,'end':0x8002588c,'bytes':wrapper.hex(),'sha256':sha(wrapper),'original_US_exact':False})
for p in(R/'scripts/ultimate_costume_renderer.py',R/'work/research/decomp/src/main/player_special.c',R/'work/research/decomp/src/main/player_check.c',R/'work/research/decomp/src/main/player_weapon.c',D/'shibuki_nova_hover_relations01/report.json',D/'nana_ultimate_hover_muzzle01/report.json'):blob(p)
users=collections.defaultdict(set)
for pb in range(len(bank_offsets(a.c))):
 for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
  for p in parts(a,pb,n):users[p['record_offset']].add((pb,n))
layers=[];pairs=[]
Y,X=np.indices((384,384));Y-=160;X-=160
for n in sorted(REFS):
 f=a.banks[0]['frames'][n];rows=[];outside={}
 for pb in PBS:
  z=a.layer(n,pb)[0];ps=parts(a,pb,n);us=u.layer(n,pb)[0];ts=sorted({p['tile']+p['page']*256 for p in ps})
  rows.append({'bank':pb,'opaque':int((z>0).sum()),'bbox':bbox(z>0),'indices_sha256':sha(z.tobytes()),'parts':ps,'unique_semantic_records':len({sig(p)for p in ps}),'consumed_tiles':[{'tile':t,'full256_sha256':sha(tile(a,n,t).tobytes())}for t in ts],'US_opaque':int((us>0).sum()),'US_bbox':bbox(us>0)})
  for p in ps:
   shared=sorted([list(v)for v in users[p['record_offset']]if not(v[0]in PBS and v[1]in REFS)])
   if shared:outside[str(p['record_offset'])]=shared
 visible={}
 for mask in(0,8,9,10,11,12,13,14,15):
  im=np.array(a.composite(n,mask)[0]);visible[str(mask)]={'opaque':int((im[:,:,3]>0).sum()),'bbox':bbox(im[:,:,3]>0),'lower_y_ge8_bbox':bbox((im[:,:,3]>0)&(Y>=8))}
 layers.append({'ref':n,'tile_count':f['tile_count'],'raw_owners':[v['index']for v in a.banks[0]['frames']if v['offset']==f['offset']],'layers':rows,'outside_record_owners':outside,'visible_masks':visible})
for n in KEYS:
 rows=[]
 for pb in PBS:
  z,q=a.layer(n,pb)[0],a.layer(n+1,pb)[0];rows.append({'bank':pb,'different_cells':int((z!=q).sum()),'difference_bbox':bbox(z!=q),'same_records':[sig(p)for p in parts(a,pb,n)]==[sig(p)for p in parts(a,pb,n+1)]})
 assert all(r['different_cells']==0 for r in rows if r['bank']in(5,6,8))
 # Effective legs at lower8 footprint remain equal through every valid hover mask and shot pair.
 footprint=a.layer(n,8)[0]>0;reference=np.array(a.composite(n,8)[0]);foot_exact=True
 for f in(n,n+1):
  for m in range(8,16):foot_exact&=np.array_equal(reference[footprint],np.array(a.composite(f,m)[0])[footprint])
 pairs.append({'refs':[n,n+1],'layers':rows,'layer8_world_exact':True,'lower8_footprint_RGBA_all_valid_masks_and_shot_exact':bool(foot_exact),'first_mask8_lowest_y':bbox(reference[:,:,3]>0)[3]-1})
ua,ur=animation_map(oe);ca,cr=animation_map(ce);ids=sorted({i for n in REFS for i in cr[n]})
for i in ids:assert ua[i]==ca[i]
jets=[];jetseq=[];jetarrays={};jettiles=set();jetcontacts=[]
for n,aid in((221,33),(223,34),(225,35),(227,36),(229,32)):
 addr=struct.unpack_from('<I',oe,off(0x8011bf40+aid*4))[0];assert oe[off(addr):off(addr+12)]==ce[off(addr):off(addr+12)];steps=[list(struct.unpack_from('<bbbB',oe,off(addr+i*4)))for i in range(3)];jetseq.append({'refs':[n,n+1],'animation':aid,'steps':steps});jetarrays[n]=[]
 for _,_,_,frame in steps:
  z,c=static(a,12,frame);uz,uc=static(u,12,frame);z2,c2=static(u2,12,frame);assert np.array_equal(z,uz)and np.array_equal(z,z2)and[sig(p)for p in c['parts']]==[sig(p)for p in uc['parts']]==[sig(p)for p in c2['parts']]
  ts=sorted({p['tile']+p['page']*256 for p in c['parts']});jettiles.update(ts)
  for t in ts:assert tile_pixels(entry(a.data,0x10206),t)==tile_pixels(entry(u.data,0x10206),t)==tile_pixels(entry(u2.data,0x10206),t)
  jets.append({'frame':frame,'refs':[n,n+1],'parts':c['parts'],'tiles':ts,'opaque':int((z>0).sum()),'bbox':bbox(z>0),'US_PL00_PL02_current_semantic_and_full_tiles_exact':True,'indices_sha256':sha(z.tobytes())});jetarrays[n].append((frame,z))
  lower=a.layer(n,8)[0]>0;distance=distance_transform_cdt(~lower,metric='chessboard');partcontact=[]
  for i,p in enumerate(c['parts']):
   zz,_=static(a,12,frame,[p]);m=zz>0;v=int(distance[m].min());near=(distance==v)&m
   partcontact.append({'part':i,'effect_bbox':bbox(m),'nearest_lower8_chebyshev_distance':v,'overlap_lower8':int((m&lower).sum()),'nearest_effect_cells':coords(near)[:20],'nearest_coordinate_list_truncated':int(near.sum())>20})
  jetcontacts.append({'ref':n,'shot_ref':n+1,'jet_frame':frame,'parts':partcontact,'metric_limit':'하체8 전체와의 최소거리. 각발목/뒤꿈치의완전접점판정이아니며효과중립색합성은실기아님.'})
muzzles=[]
for n in(222,224,226,228,230):
 at=off(0x8011b230+n*2);assert oe[at:at+2]==ce[at:at+2];x,y=struct.unpack_from('<bb',oe,at);muzzles.append({'ref':n,'table_address':hex(0x8011b230+n*2),'direction0':[x,y],'direction1':[-x,y],'first_effect_table_origin_plus_type0':True})
assert oe[off(0x80108768):off(0x80108768+96)]==ce[off(0x80108768):off(0x80108768+96)];type0=list(struct.unpack_from('<hh',oe,off(0x80108768)))
lp=struct.unpack_from('<I',oe,off(0x8011bf40+21*4))[0];assert oe[off(lp):off(lp+28)]==ce[off(lp):off(lp+28)];lemon=[];first=None
for i in range(7):
 step=list(struct.unpack_from('<bbbB',oe,off(lp+i*4)));z,c=static(a,1,step[3]);uz,uc=static(u,1,step[3]);assert np.array_equal(z,uz)and[sig(p)for p in c['parts']]==[sig(p)for p in uc['parts']]
 ts=sorted({p['tile']+p['page']*256 for p in c['parts']})
 for t in ts:assert tile_pixels(entry(a.data,0x10206),t)==tile_pixels(entry(u.data,0x10206),t)
 lemon.append({'step':step,'opaque':int((z>0).sum()),'bbox':bbox(z>0),'parts':c['parts'],'tiles':ts,'source_full_tiles_exact':True})
 if first is None:first=z
assert int((first>0).sum())==188
O.mkdir(exist_ok=False);sheets=[]
def board(name,rows,scale=4):
 bs=[im.getbbox()for row in rows for _,im in row if im.getbbox()];bb=(min(v[0]for v in bs)-3,min(v[1]for v in bs)-3,max(v[2]for v in bs)+3,max(v[3]for v in bs)+3);w,h=bb[2]-bb[0],bb[3]-bb[1];cw,ch=w*scale+10,h*scale+25;out=Image.new('RGB',(cw*len(rows[0]),ch*len(rows)),'#263345');dr=ImageDraw.Draw(out)
 for y,row in enumerate(rows):
  for x,(caption,im)in enumerate(row):
   dr.text((x*cw+3,y*ch+3),caption,fill='white');pic=im.crop(bb).resize((w*scale,h*scale),Image.Resampling.NEAREST);out.paste(pic,(x*cw+5,y*ch+22),pic)
 p=O/name;out.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes()),'crop':bb,'integer_scale':scale})
for n in KEYS:
 board(f'ownership_{n}.png',[[('body0',a.rgba(a.layer(n,0)[0])),('head5',a.rgba(a.layer(n,5)[0],16)),('body6',a.rgba(a.layer(n,6)[0],16)),('arms7',a.rgba(a.layer(n,7)[0],16)),('legs8',a.rgba(a.layer(n,8)[0],16))],[(f'{n} mask8',a.composite(n,8)[0]),(f'{n+1} shot8',a.composite(n+1,8)[0]),(f'{n} mask15',a.composite(n,15)[0]),(f'{n+1} shot15',a.composite(n+1,15)[0]),('US mask15',u.composite(n,15)[0])]],5)
 rows=[]
 for form,mask in(('base legs',8),('Fourth',15)):
  row=[]
  for frame,z in jetarrays[n]:im=neutral(z);im.alpha_composite(a.composite(n,mask)[0]);row.append((f'{n} {form} jet{frame}',im))
  rows.append(row)
 board(f'jets_{n}.png',rows,5)
 for frame,z in jetarrays[n]:np.save(O/f'jet_{frame:02}.npy',z)
muzzle_rows=[]
for row in muzzles:
 n=row['ref'];x,y=row['direction0'];effect=np.roll(np.roll(first,y,axis=0),x,axis=1);ims=[]
 for title,ar,mask in(('current8',a,8),('current15',a,15),('US15',u,15)):
  im=neutral(effect,(255,210,20,160));im.alpha_composite(ar.composite(n,mask)[0]);dr=ImageDraw.Draw(im);dr.line((x+159,y+160,x+161,y+160),fill='#00eeff');dr.line((x+160,y+159,x+160,y+161),fill='#00eeff');ims.append((f'{n} {title} origin{x},{y}',im))
 muzzle_rows.append(ims)
board('muzzle_first_effect.png',muzzle_rows,5)
for p,h in tracked.items():assert sha((R/p).read_bytes())==h,p
report={'scope':'시부키 동결PL0036d4 기본/포스 호버221..230 부분소유/공유/원제트/원총구 읽기','parent':rel(bp),'parent_sha256':sha(a.data),'US_PL00_sha256':sha(u.data),'US_PL02_sha256':sha(u2.data),'code_disc':rel(disc),'code_disc_sha256':sha(disc.read_bytes()),'code_executable_sha256':sha(ce),'original_US_executable_sha256':sha(oe),'BR28_parent_hover50layers_raw_records_exact':True,'code_ranges':codes,'renderer':{'PL00_rule':'engine+37=0이면 player+A7 그대로,217..230 강제15 없음','minimum_hover_mask_bit':8,'valid_ordinary_partial_masks':list(range(8,16)),'overlay_order':[8,5,7,6],'overlay_bit_to_bank':{'8':8,'1':5,'4':7,'2':6},'CLUT':{'base0':'현재본체팔레트','5/6/8':'0x7843/index16','7_arm1':'0x7843/index16','7_arm2':'0x7844/index32'},'PL02_difference':'Ultimate에서만217..230강제15/upper0+lower5.이를PL00에이식하지않는다.'},'frames':layers,'pairs':pairs,'player_animation_ids':ids,'player_animations':[ca[i]for i in ids],'jets':{'visual_id':33,'composition_bank':12,'static_entry':'0x10206','clut':'0x7802','object_origin':'player x/y/facing 동일','sequences':jetseq,'frames':jets,'total_parts':sum(len(r['parts'])for r in jets),'whole_tiles':sorted(jettiles),'contact_metrics':jetcontacts},'muzzles':muzzles,'shot_type0_xy':type0,'lemon7':lemon,'first_lemon_pixels':188,'first_lemon_bbox':bbox(first>0),'readback_sheets':sheets,'inputs':tracked,'actually_viewed':False,'producer_functions_called':False,'art_or_resources_modified':False,'new_MIPS_execution':False,'runtime_verified':False,'new_art_accepted':False,'limits':['원코드바이트비교/정적복원으로실제게임이나후속새몸체접점수용을대체하지않는다.','본체0의하체부재는221/223기존분할정책이다.mask0은원진입조건상실제호버상태가아니다.','제트중립색/첫탄환중립색합성은원알파좌표진단이며원게임색상·그리기순서의실기캡처가아니다.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'report_sha256':sha((O/'report.json').read_bytes()),'pairs':pairs,'outside_record_owners':{str(r['ref']):r['outside_record_owners']for r in layers},'jet_frames':len(jets),'jet_tiles':sorted(jettiles),'muzzles':muzzles}))
