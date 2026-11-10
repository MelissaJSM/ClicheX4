"""PL00 새호버 사격5의 고정원화10셀·의미팔·총구와80부분을 독립 계산한다."""
from pathlib import Path
import sys,json,hashlib,collections
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,binary_dilation
R=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent;S=W/'root_shibuki_hover';H=W/'shibuki_audit';O=D/'shibuki_base_hover_shots01'
assert not O.exists();sys.path[:0]=[str(R),str(D)]
from scripts.export_x_consistency import Archive
from verify_shibuki_ultimate_hurt13_independent import color
hb=lambda v:hashlib.sha256(v).hexdigest();rel=lambda p:p.relative_to(R).as_posix();tracked={};PBS=(0,5,6,7,8);REFS=(222,224,226,228,230)
def blob(p):v=p.read_bytes();tracked[rel(p)]=hb(v);return v
def js(p):return json.loads(blob(p))
def png(p):blob(p);return np.array(Image.open(p))
Y,X=np.indices((384,384));Y-=160;X-=160
def box(v):x0,y0,x1,y1=v;return(X>=x0)&(X<x1)&(Y>=y0)&(Y<y1)
def compose(ls,m,arm=1):
 out=color(a,ls[0])
 for bit,pb in((8,8),(1,5),(4,7),(2,6)):
  if m&bit:z=color(a,ls[pb],32 if pb==7 and arm==2 else 16);v=z[:,:,3]>0;out[v]=z[v]
 return out
def coords(mask):return[[int(x)-160,int(y)-160]for y,x in np.argwhere(mask)]
old=H/'prepared_nova_strike_base01/PL00_U.ARC';a=Archive(blob(old));assert hb(a.data)=='36d4d0293abc77052c476e0495f4f4542ca75471c7a149f200e4bdb8f4e1bd4e'
bodymeta=js(S/'body_layers_probe04/manifest.json');bodyrows={x['ref']:x for x in bodymeta['frames']};shotmeta=js(S/'shot_composed01/manifest.json');shotrows={x['ref']:x for x in shotmeta['records']};reg=js(S/'shot_registered01/manifest.json');gunmeta=js(S/'shot_inputs01/manifest.json');proof=js(D/'shibuki_base_hover_ownership01/report.json');assert proof['parent_sha256']==hb(a.data)if 'parent_sha256'in proof else True
source_proof=js(D/'shibuki_base_hover_layers03_read01/report.json');assert hb(blob(D/'shibuki_base_hover_layers03_read01/report.json'))=='1e40958b92f5b4d1140336d81056cd90bf2a24f188d95adba0a2c191500b01c5'
js(S/'body_layers_probe04/text_correction.json')
base04={}
for n in(221,223,225,227,229):
 base04[n]={pb:png(S/f'body_layers_probe04/layer{pb}_{n}.png')for pb in PBS}
 for pb in PBS:
  assert np.array_equal(base04[n][pb],png(S/f'body_layers_probe03/layer{pb}_{n}.png'))
  assert hb(base04[n][pb].tobytes())==bodyrows[n]['layer_hashes'][str(pb)]
registered={};source_checks=[]
for row in reg['records']:
 n,form=row['ref'],row['form'];src=R/row['source'];assert hb(blob(src))==row['source_sha256'];im=Image.open(src).convert('RGBA');cell=np.array(im.crop(row['source_crop']).resize((96,96),Image.Resampling.NEAREST));start=0 if form=='base_legs'else 16
 pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.int32)
 q=(np.square(cell[:,:,:3].astype(np.int32)[:,:,None,:]-pal[None,None,1:]).sum(3).argmin(2)+1).astype(np.uint8);q[cell[:,:,3]<128]=0;z=np.zeros((384,384),np.uint8);z[112:208,112:208]=q
 p=S/f'shot_registered01/{form}_{n}_source_indices.png';assert hb(blob(p))==row['output_sha256']and np.array_equal(z,png(p));registered[n,form]=z
 source_checks.append({'ref':n,'form':form,'source':row['source'],'source_sha256':row['source_sha256'],'crop':row['source_crop'],'fixed_grid':96,'world_origin':160,'indices_sha256':hb(z.tobytes())})
assert len(source_checks)==10
# 수용된34 총열의 실제색인을 읽는다. PL00는CLUT0/16총색이달라0층고정이필수다.
gm=png(R/gunmeta['master_mask_path'])>0;assert hb(blob(R/gunmeta['master_mask_path']))==gunmeta['master_mask_sha256']
master=np.where(gm,a.layer(34,0)[0],0).astype(np.uint8)
assert int(gm.sum())==71 and int((master>0).sum())==60
assert np.array_equal(color(a,master)[gm],np.array(a.composite(34,0)[0])[gm])
wrong_clut_pixels=int(np.any(color(a,master)[gm]!=color(a,master,16)[gm],axis=1).sum());assert wrong_clut_pixels==60
assert np.array_equal(master,png(S/'shot_inputs01/master_indices.png'))
origins={q['ref']:q['direction0']for q in proof['muzzles']};changes={222:[[-32,-29,-8,1],[-10,-6,-5,1]],224:[[-33,-19,-10,2],[-11,-7,-5,2]],226:[[-24,-14,-9,3],[-11,-6,-4,3]],228:[[-24,-14,-9,6],[-11,-6,-5,6]],230:[[-29,-30,-9,2],[-11,-7,-5,2]]}
clears={222:[-32,-14,-17,-5],224:[-33,-14,-19,-4],226:[-24,-15,-10,-6],228:[-24,-15,-7,-6],230:[-29,-16,-14,-7]};arm_y={222:-7,224:-6,226:-5,228:-5,230:-7};allrows=[];layers={};counters=collections.Counter()
for n in REFS:
 before=base04[n-1];face=box(bodyrows[n-1]['shared_face']);edit=np.logical_or.reduce([box(v)for v in changes[n]])&~face;assert np.array_equal(edit,png(S/f'shot_composed01/edit_{n}.png')>0)
 mx,my=origins[n];dx,dy=mx+24,my+10;gun=np.roll(np.roll(master,dy,axis=0),dx,axis=1);guard=np.roll(np.roll(gm,dy,axis=0),dx,axis=1)
 assert np.array_equal(gun,png(S/f'shot_inputs01/{n}_gun_indices.png'))and np.array_equal(guard,png(S/f'shot_inputs01/{n}_gun_guard.png')>0)
 assert next(q for q in gunmeta['frames']if q['ref']==n)['muzzle']==origins[n]
 src={form:registered[n,form].copy()for form in('base_legs','fourth')};clear=box(clears[n])&~face
 removed={form:int(((z>0)&clear).sum())for form,z in src.items()}
 for z in src.values():z[clear]=0
 arm=edit&(Y>=arm_y[n]);shared=arm&((src['fourth']==9)|np.isin(src['base_legs'],(12,13)))
 out={pb:z.copy()for pb,z in before.items()};out[0][edit]=src['base_legs'][edit]
 for pb in(5,6,7):out[pb][edit]=0
 out[7][arm&~shared]=src['fourth'][arm&~shared];out[0][guard]=gun[guard]
 for pb in(5,6,7,8):out[pb][guard]=0
 target={pb:png(S/f'shot_composed01/layer{pb}_{n}.png')for pb in PBS}
 for pb in PBS:
  assert np.array_equal(out[pb],target[pb]);assert hb(blob(S/f'shot_composed01/layer{pb}_{n}.png'))==shotrows[n]['layer_hashes'][str(pb)];counters['target_layers_reconstructed']+=1
  assert np.array_equal(out[pb][~(edit|guard)],before[pb][~(edit|guard)])
 assert np.array_equal(out[8],before[8]);assert np.array_equal(out[0][face&~guard],before[0][face&~guard])
 assert int(shared.sum())==shotrows[n]['skin_common']
 # 실제 불투명 의상층은 서로 겹치지 않는지, 새 사격팔의 상부가head5로 남는지 검사한다.
 assert np.all(sum((out[pb]>0).astype(np.uint8)for pb in(5,6,7,8))<=1)
 assert not any(out[pb][edit].any()for pb in(5,6))
 states=[];contact=[];normal=color(a,gun);lower=(before[8]>0);bodycut=bodyrows[n-1]['leg_cut_y'];below=(Y>=bodycut)&~((X>=10)&(Y<8))
 for mask in range(8,16):
  for armtype in(1,2):
   z=compose(out,mask,armtype);bz=compose(before,mask,armtype)
   assert np.array_equal(z[face&~guard],bz[face&~guard])and np.array_equal(z[below],bz[below])and np.array_equal(z[guard],normal[guard])
   k=int(label(z[:,:,3]>0,np.ones((3,3)))[1]);assert k==1,(n,mask,armtype,k)
   assert np.array_equal(z[shared&~guard],compose(out,8)[shared&~guard]);counters['partial_combinations']+=1;counters['gun_guards_exact']+=1
   states.append([mask,armtype,k])
 for form,mask in(('base_legs',8),('fourth',15)):
  z=compose(out,mask);non_gun=(z[:,:,3]>0)&~guard
  touch4=binary_dilation(gun>0,np.array([[0,1,0],[1,1,1],[0,1,0]],bool))&non_gun;touch8=binary_dilation(gun>0,np.ones((3,3),bool))&non_gun
  contact.append({'form':form,'four_connected_touch_cells':coords(touch4),'eight_connected_touch_cells':coords(touch8)})
 # 얼굴 guard 안은 명시적으로 총의 우선권이며 피부/눈 전체보존과 혼동하지 않는다.
 changedface=(face&guard)&np.any(compose(out,8)!=compose(before,8),axis=2)
 allrows.append({'ref':n,'body_ref':n-1,'edit_windows':changes[n],'face_window':bodyrows[n-1]['shared_face'],'removed_generated_cannon_pixels':removed,'arm_bank7_min_y':arm_y[n],'common_skin_semantic_cells':int(shared.sum()),'shared_base_transparent_cells':coords(shared&(src['base_legs']==0)),'shared_base_values':dict(zip(*[v.tolist()for v in np.unique(src['base_legs'][shared],return_counts=True)])),'face_gun_guard_cells':coords(face&guard),'face_changed_only_within_guard':coords(changedface),'muzzle_origin':origins[n],'master_translation':[dx,dy],'canonical_opaque':60,'canonical_transparent_guard':11,'gun_body_contacts':contact,'layer_changed_cells':{str(pb):int((out[pb]!=before[pb]).sum())for pb in PBS},'lower8_exact':True,'full_lower_RGBA_exact_all16':True,'face_outside_guard_RGBA_exact_all16':True,'no_head5_or_torso6_opaque_inside_arm_edit':True,'partial_states':states})
 layers[n]=out
O.mkdir(exist_ok=False);sheets=[]
crop=(126,128,182,189)
for n in REFS:
 rows=[]
 for mask,arm in((8,1),(15,1),(11,1),(15,2)):
  rows.append([(f'new body {n-1} m{mask} a{arm}',Image.fromarray(compose(base04[n-1],mask,arm))),(f'new shot {n} m{mask} a{arm}',Image.fromarray(compose(layers[n],mask,arm))),(f'parent shot {n} m{mask} a{arm}',a.composite(n,mask,arm)[0])])
 out=Image.new('RGB',(3*290,4*330),'#e8e5dd');dr=ImageDraw.Draw(out)
 for row,items in enumerate(rows):
  for col,(caption,im)in enumerate(items):
   dr.text((col*290+3,row*330+3),caption,fill='black');pic=im.crop(crop).resize((280,305),Image.Resampling.NEAREST);out.paste(pic,(col*290+2,row*330+22),pic)
 p=O/f'composition_{n}.png';out.save(p);sheets.append({'path':rel(p),'sha256':hb(p.read_bytes()),'integer_scale':5,'crop_world':[v-160 for v in crop]})
# 15원jet은 이전body03에서원점검사되었으며이번하체exact를통해접점유지를검증한다.
for n in REFS:
 seq=next(q for q in proof['jets']['sequences']if q['refs'][1]==n)
 for step in seq['steps']:
  jf=step[3];jp=D/f'shibuki_base_hover_ownership01/jet_{jf:02}.npy';blob(jp);jet=np.load(jp)
  assert np.array_equal(layers[n][8],base04[n-1][8]);counters['unchanged_lower_jet_pairs']+=1
for p in(Path(__file__),S/'compose_shots01.py',S/'register_shots01.py',S/'register_neutral.py',S/'prepare_body_layers04.py',R/'scripts/export_x_consistency.py',D/'verify_shibuki_ultimate_hurt13_independent.py'):blob(p)
for n in REFS:
 for what in('comparison','partial'):blob(S/f'shot_composed01/{what}_{n}.png')
for p,h in tracked.items():assert hb((R/p).read_bytes())==h,p
report={'passed':True,'scope':'Shibuki PL00 비사격body04→사격5국소팔/고정총의 독립 재계산과 부분소유 진단','parent_sha256':hb(a.data),'body04_pixels_equal_independently_checked_body03':True,'source_registered_fixed_cells':source_checks,'counts':dict(counters),'frames':allrows,'sheets':sheets,'inputs':tracked,'cannon_palette':{'actual':0,'if_incorrectly_using_CLUT16_different_pixels':wrong_clut_pixels,'policy':'불투명60전체색이CLUT16에서달라공통0에정본을넣고overlay에서는guard71을비워야한다.'},'reader_assumption_correction':'첫진단은Ultimate와같이총CLUT0/16이동일하다고잘못가정해중단됐다.후보오류가아니며실제PL00색인/CLUT0조건으로판독기를수정했다.후보/입력은미변경.','actually_viewed':False,'producer_functions_imported_or_called':False,'input_pixels_or_resources_modified':False,'new_art_generated':False,'ARC_created':False,'new_MIPS_execution':False,'runtime_verified':False,'limits':['이것은25사격층의 등록후보 읽기이며최종50층 ARC/공유/저장/원MIPS 검사를 대신하지 않는다.','80조합은mask8..15×arm1/2이다. 실제PL00원호버다리bit8조건과기본8/포스15에따른진단이다.','원 총구5값과수용34의60+11 정본을결속한다.원US개별총통전체형상exact를주장하지않는다.','얼굴은총guard밖exact이다. 총guard에겹친얼굴창은총을앞에두는정책으로분리한다.','15jet원점은이전독립근거이며이번새실행은없다.하체8과전체하체RGBA exact이므로기존body04의접점관계는유지한다.','8연결성분1은손목형태나의상색미술수용を自動証明しない。']}
report['limits'][-1]='8연결성분1은 손목형태나 의상색의 미술수용을 자동 증명하지 않는다.'
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(O/'INPUT_LOCK.json').write_text(json.dumps({'files':tracked,'source_inputs_unchanged':True},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'report_sha256':hb((O/'report.json').read_bytes()),'counts':dict(counters),'face_guard_changes':[{k:r[k]for k in('ref','face_changed_only_within_guard','shared_base_transparent_cells')}for r in allrows]}))
