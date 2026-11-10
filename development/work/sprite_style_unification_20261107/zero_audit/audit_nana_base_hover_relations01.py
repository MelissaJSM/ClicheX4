"""기본/포스 호버 원점·원효과와 등록8표시 읽기. 게임/제작 입력은 쓰지 않는다."""
from pathlib import Path
import hashlib,json,struct,sys
import numpy as np
from PIL import Image,ImageDraw
import capstone
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent
sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,animation_map
from scripts.prepare_riko_ui import entry
from src.psx_player import composition_frame
from src.psx_static_effect import compose_static
from src.psx_ui_atlas import local_composition,tile_pixels
O=D/'nana_base_hover_relations01';O.mkdir(exist_ok=False)
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();off=lambda a:a-0x80010000+2048
inputs={}
def blob(p):
 b=p.read_bytes();inputs[rel(p)]=sha(b);return b
def js(p):return json.loads(blob(p))
def write(n,v):(O/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
def bbox(a):
 y,x=np.nonzero(a);return None if not len(x)else[int(x.min()-160),int(y.min()-160),int(x.max()+1-160),int(y.max()+1-160)]
def coords(a):
 y,x=np.nonzero(a);return [[int(xx-160),int(yy-160)]for yy,xx in zip(y,x)]
def psig(c):return[(p['flags'],p['tile'],p['x'],p['y'])for p in c['parts']]
def static(ar,bank,n):
 c=composition_frame(ar.c,bank,n);b,s,bb,_=compose_static(entry(ar.data,0x10206),local_composition(c))
 z=np.zeros((384,384),np.uint8);z[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]=np.frombuffer(b,np.uint8).reshape(s[1],s[0]);return z,c
def board(rows,name,cols=4):
 cw,ch=288,330;out=Image.new('RGB',(cw*cols,ch*((len(rows)+cols-1)//cols)),'#263345');dr=ImageDraw.Draw(out)
 for i,(text,im)in enumerate(rows):
  x,y=i%cols*cw,i//cols*ch;dr.text((x+4,y+3),text,fill='white');im=im.crop((126,124,194,198)).resize((272,296),Image.Resampling.NEAREST);out.paste(im,(x+8,y+27),im)
 out.save(O/name)
orig,_=read_disc(ROOT/'MegaMan X4.bin',['PL00_U.ARC','PL02_U.ARC','SLUS_005.61'])
disc=ROOT/'out/ver_rin_nana/sprite_style_unification_20261107_v39/rin_nana.bin'
now,_=read_disc(disc,['PL00_U.ARC','PL02_U.ARC','SLUS_005.61'])
pp=W/'root_nana_shot87/packed_settle01/PL00_U.ARC';cur=Archive(blob(pp));assert cur.data==now['PL00_U.ARC']
assert sha(cur.data)=='8951948879773266cae0bebd408b411f4806b5652257bba3c50df0212b3c6e10'
ars={'us_base':Archive(orig['PL00_U.ARC']),'us_ultimate':Archive(orig['PL02_U.ARC']),'current_base':cur,'current_ultimate':Archive(now['PL02_U.ARC'])}
oe,ce=orig['SLUS_005.61'],now['SLUS_005.61'];cs=capstone.Cs(capstone.CS_ARCH_MIPS,capstone.CS_MODE_MIPS32|capstone.CS_MODE_LITTLE_ENDIAN)
codes=[]
for name,lo,hi in [('air_move',0x800339e0,0x80033b00),('hover_check',0x8003751c,0x800375b0),('hover_start',0x80038970,0x800389dc),('hover_end',0x80038d38,0x80038d88),('hover_jet',0x800b2ad0,0x800b2c8c),('muzzle',0x80092e2c,0x80092f08),('lemon',0x80092314,0x800924f8)]:
 b=ce[off(lo):off(hi)];assert b==oe[off(lo):off(hi)]
 p=O/f'{name}_mips.txt';p.write_text('\n'.join(f'{i.address:08x} {i.mnemonic} {i.op_str}'for i in cs.disasm(b,lo))+'\n','utf8');codes.append({'name':name,'range':[hex(lo),hex(hi)],'sha256':sha(b),'original_US_exact':True,'disassembly':rel(p)})
ren=ce[off(0x800257bc):off(0x8002588c)];assert sha(ren)=='46c1fe4c8c01be08e49c733c24e99fe7e4e2416b93a2dc50585a3503854038c5'
blob(ROOT/'scripts/ultimate_costume_renderer.py')
for f in ['player_check.c','player_special.c','object_update.c']:blob(ROOT/'work/research/decomp/src/main'/f)
jetrows=[];jetarr={};seq=[];tiles=set()
for n,aid in [(221,33),(223,34),(225,35),(227,36),(229,32)]:
 addr=struct.unpack_from('<I',oe,off(0x8011bf40+aid*4))[0];assert oe[off(addr):off(addr+12)]==ce[off(addr):off(addr+12)]
 steps=[list(struct.unpack_from('<bbbB',oe,off(addr+i*4)))for i in range(3)];seq.append({'refs':[n,n+1],'animation':aid,'steps':steps})
 jetarr[n]=[]
 for _,_,_,f in steps:
  z,c=static(ars['us_base'],12,f);ts=sorted({p['page']*256+p['tile']for p in c['parts']});tiles.update(ts);checks={}
  for k,a in ars.items():
   zz,cc=static(a,12,f);assert np.array_equal(z,zz)and psig(c)==psig(cc)
   for t in ts:assert tile_pixels(entry(a.data,0x10206),t)==tile_pixels(entry(ars['us_base'].data,0x10206),t)
   checks[k]={'records_semantic_exact':True,'record_offsets':[q['record_offset']for q in cc['parts']],'whole_tiles_exact':True}
  jetarr[n].append(z);np.save(O/f'jet_{f:02}.npy',z)
  jetrows.append({'frame':f,'refs':[n,n+1],'parts':c['parts'],'tiles':ts,'opaque':int((z>0).sum()),'bbox':bbox(z>0),'indexed_sha256':sha(z.tobytes()),'archives':checks})
origins=[]
for n in (222,224,226,228,230):
 a=off(0x8011b230+n*2);assert oe[a:a+2]==ce[a:a+2];x,y=struct.unpack_from('<bb',oe,a);origins.append({'ref':n,'direction0':[x,y],'direction1':[-x,y],'US_RN39_exact':True})
assert oe[off(0x80108768):off(0x80108768+96)]==ce[off(0x80108768):off(0x80108768+96)]
lemonptr=struct.unpack_from('<I',oe,off(0x8011bf40+21*4))[0];assert oe[off(lemonptr):off(lemonptr+28)]==ce[off(lemonptr):off(lemonptr+28)]
lemon=[]
for i in range(7):
 step=list(struct.unpack_from('<bbbB',oe,off(lemonptr+i*4)));z,c=static(ars['us_base'],1,step[3]);ts=sorted({p['page']*256+p['tile']for p in c['parts']})
 for a in ars.values():
  zz,cc=static(a,1,step[3]);assert np.array_equal(z,zz)and psig(c)==psig(cc)
  for t in ts:assert tile_pixels(entry(a.data,0x10206),t)==tile_pixels(entry(ars['us_base'].data,0x10206),t)
 lemon.append({'step':step,'opaque':int((z>0).sum()),'bbox':bbox(z>0),'parts':c['parts'],'tiles':ts,'all_four_archives_exact':True})
layerrows=[]
for n in range(221,231):
 layers=[]
 for pb in (0,5,6,7,8):
  z,m=cur.layer(n,pb);layers.append({'bank':pb,'opaque':int((z>0).sum()),'bbox':bbox(z>0),'parts':m['parts'],'paired_next_layer_exact':bool(np.array_equal(z,cur.layer(n+1 if n%2 else n-1,pb)[0]))})
 f=cur.banks[0]['frames'][n];layerrows.append({'ref':n,'tile_count':f['tile_count'],'raw_owners':[q['index']for q in cur.banks[0]['frames']if q['offset']==f['offset']],'layers':layers})
# Coordinate diagnostics use actual visible green/skin colors. Skin ROIs are labelled
# color extents, not an inferred fist joint. No pixels are edited.
pal=np.array(cur.rgba(np.arange(48,dtype=np.uint8).reshape(1,48)))
greens={tuple(pal[0,14,:3])}
skin=set(tuple(pal[0,i,:3])for i in [10,11,12,26,27,28,42,43,44])
yy,xx=np.indices((384,384));X,Y=xx-160,yy-160
def color_mask(arr,colors):return np.any(np.stack([np.all(arr[:,:,:3]==c,axis=2)for c in colors]),axis=0)&(arr[:,:,3]>0)
def metrics(im):
 a=np.asarray(im);al=a[:,:,3]>0;eyes=color_mask(a,greens)&(Y<0);sk=color_mask(a,skin)
 return {'bbox':bbox(al),'eye_green_coords':coords(eyes),'bottom_y':int(np.where(al)[0].max()-160),'lower_left_bbox_y_ge8':bbox(al&(Y>=8)&(X<0)),'lower_right_bbox_y_ge8':bbox(al&(Y>=8)&(X>=0)),'skin_left_roi_x_lt_minus5_y_lt8':bbox(sk&(X<-5)&(Y<8)),'skin_right_roi_x_gt4_y_lt8':bbox(sk&(X>4)&(Y<8))}
registration=[];tabs=[]
for reg in ['registered01','registered02']:
 p=W/'root_nana_hover'/reg;manifest=js(p/'manifest.json');blob(ROOT/manifest['source'])
 for q in manifest['frames']:
  n,mask,form=q['ref'],q['mask'],q['form'];ip=p/f'{form}_{n}_rgba.png';blob(ip);new=Image.open(ip).convert('RGBA');old=cur.composite(n,mask)[0]
  row={'ref':n,'mask':mask,'form':form,'registration':rel(p),'source_sha256':manifest['source_sha256'],'old':metrics(old),'new':metrics(new),'jet_contacts':[]}
  items=[]
  for label,body in [('old',old),('new fixed',new)]:
   items.append((f'{n} {form} {label}',body));a=np.asarray(body)[:,:,3]>0
   for k,z in enumerate(jetarr[n]):
    out=np.zeros((384,384,4),np.uint8);out[z>0]=[40,220,240,200];im=Image.fromarray(out);im.alpha_composite(body)
    row['jet_contacts'].append({'body':label,'phase':k,'body_jet_overlap':int(((z>0)&a).sum()),'effect_alpha_bbox':bbox(z>0)})
    items.append((f'{n} {label} jet phase{k}',im))
  board(items,f'{form}_{n}_jet_contacts.png',4);registration.append(row)
 for f in ['comparison_1.png','comparison_2.png']:blob(p/f)
ua,ur=animation_map(oe);ca,cr=animation_map(ce);aids=sorted({i for n in range(221,231)for i in cr[n]})
for i in aids:assert ua[i]==ca[i]
for f in ['nana_ultimate_hover_relations01/conclusions.json','nana_ultimate_hover_muzzle01/report.json']:blob(D/f)
out={'passed':True,'scope':'RN39 기본/포스 호버 원코드·효과·8등록표시 독립 읽기. 새패킹/실기/전체수용 아님.','parent':rel(pp),'parent_sha256':sha(cur.data),'disc':rel(disc),'disc_PL00_exact':True,'arc_hashes':{k:sha(a.data)for k,a in ars.items()},'US_exe_sha256':sha(oe),'current_exe_sha256':sha(ce),'code':codes,'renderer_sha256':sha(ren),'ordinary_renderer':'Ultimate engine+37=0이면 player+0xA7 mask 그대로. mask8=legs bank8,mask15=8/5/7/6 순서. Ultimate hover override를 PL00에 적용하지 않는다.','reachability':'원 player_check_air_move는 input_locked=0,air_action=0,X일 때 hover검사. player_check_hover는 armor_parts bit8와 pressed JUMP0x80 필요. 초기 timer180, 방향전환 구간40, jump재입력/만료 시 fall. 장면별 발동 실기는 미실행.','jet_origin':'visual0x21 객체는 player world x/y/facing 그대로. 별도 bank12/static0x10206/globalCLUT0x7802. 여기 청록은 중립진단색이며 게임색/드로우순서 캡처가 아니다.','jet_sequences':seq,'jet_frames':jetrows,'jet_total_parts':sum(len(r['parts'])for r in jetrows),'jet_tiles':sorted(tiles),'static_texture_full_entry_hashes':{k:sha(entry(a.data,0x10206))for k,a in ars.items()},'muzzle_origins':origins,'shot_type0_offset':list(struct.unpack_from('<hh',oe,off(0x80108768))),'first7_lemon_effects':lemon,'layers':layerrows,'registration':registration,'metric_limits':'녹색 눈 색표본과 피부색 ROI의 실제 보이는 범위. 피부색이 귀/목과 겹칠 수 있으므로 손 관절 확정값으로 부르지 않음. 전체 bbox/최저점만으로 다리를 강제로 옮기지 않음.','player_original_sequences':[ca[i]for i in aids],'new_MIPS_execution':False,'runtime_executed':False,'producer_functions_called':False,'source_requantization':False,'visual_review':'후속 visual.json에 직접 열람 범위 기록','inputs':inputs}
write('report.json',out)
print(json.dumps({'report_sha256':sha((O/'report.json').read_bytes()),'jets':len(jetrows),'parts':out['jet_total_parts'],'tiles':sorted(tiles),'registration':registration},ensure_ascii=False))
