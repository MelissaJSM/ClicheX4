from pathlib import Path
import sys,json,hashlib,io,base64
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,distance_transform_cdt
R=Path.cwd();W=R/'work/sprite_style_unification_20261107';S=W/'root_shibuki_hover';O=S/'body_layers_probe03';D=W/'zero_audit';sys.path.insert(0,str(R))
from scripts.export_x_consistency import Archive
from scripts.prepare_riko_ui import entry
from src.psx_player import composition_frame
from src.psx_static_effect import compose_static
from src.psx_ui_atlas import local_composition
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();tracked={}
def readimg(p):tracked[str(p.relative_to(R))]=sha(p);return np.array(Image.open(p))
def track(p):tracked[str(p.relative_to(R))]=sha(p)
p=W/'shibuki_audit/prepared_nova_strike_base01/PL00_U.ARC';track(p);a=Archive(p.read_bytes());meta=json.loads((O/'manifest.json').read_text(encoding='utf8'));track(O/'manifest.json');track(S/'prepare_body_layers03.py');proof=json.loads((D/'shibuki_base_hover_ownership01/report.json').read_text(encoding='utf8'));Y,X=np.indices((384,384));Y-=160;X-=160
assert sha(p)==meta['parent_sha256']
def box(r):x0,y0,x1,y1=r;return(X>=x0)&(X<x1)&(Y>=y0)&(Y<y1)
def comp(ls,m,arm=1):
 z=np.array(a.rgba(ls[0]))
 for bit,pb in((8,8),(1,5),(4,7),(2,6)):
  if m&bit:q=np.array(a.rgba(ls[pb],32 if pb==7 and arm==2 else 16));v=q[:,:,3]>0;z[v]=q[v]
 return z
def static(jf,p=None):
 c=composition_frame(a.c,12,jf)if p is None else{'parts':[p]};px,size,bb,_=compose_static(entry(a.data,0x10206),local_composition(c));z=np.zeros((384,384),np.uint8)
 if px:z[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]=np.frombuffer(px,np.uint8).reshape(size[1],size[0])
 return z,c
def bbox(z):y,x=np.nonzero(z);return[int(x.min()-160),int(y.min()-160),int(x.max()-159),int(y.max()-159)]if len(x)else None
rows=[];pictures=[]
RESULT_DIR=D/'shibuki_base_hover_layers03_read01';assert not RESULT_DIR.exists()
for f in meta['frames']:
 n=f['ref'];page=1 if n<225 else 2
 bp=S/(f'registered_neutral{page:02}/base_legs_{n:03}_nearest_indices.png'if n!=229 else'reach229_registered01/base_legs_local_indices.png');fp=S/(f'registered_neutral{page:02}/fourth_{n:03}_nearest_indices.png'if n!=229 else'reach229_registered01/fourth_local_indices.png');b,fr=readimg(bp),readimg(fp);assert sha(bp)==f['base_source_sha256']and sha(fp)==f['fourth_source_sha256']
 ls={pb:readimg(O/f'layer{pb}_{n:03}.png')for pb in(0,5,6,7,8)};owner=readimg(O/f'owner_{n:03}.png');lower=fr.copy()
 if n==223:
  region=(X>=7)&(Y>=18);donor=np.where(region,lower,0);lower[region]=0;yy,xx=np.nonzero(donor);lower[yy-1,xx]=donor[yy,xx]
 legmask=(Y>=f['leg_cut_y'])&~((X>=10)&(Y<8));assert np.array_equal(ls[8],np.where(legmask,lower,0));assert np.array_equal(ls[0],np.where(legmask,0,b))
 for pb in(5,6,7):assert np.array_equal(ls[pb],np.where(owner==pb,fr,0))
 for pb,z in ls.items():assert hashlib.sha256(z.tobytes()).hexdigest()==f['layer_hashes'][str(pb)]
 assert np.all((sum((ls[pb]>0).astype(int)for pb in(5,6,7,8)))<=1)
 face=box(f['shared_face']);armwin=box(f['arm_ownership_windows'][0])|box(f['arm_ownership_windows'][1]);assert not ls[5][armwin].any();assert not any(ls[p][face].any()for p in(5,6,7,8))
 comps=[];sharedlegs=np.array(a.rgba(ls[8],16));v=legmask
 for m in range(8,16):
  for arm in(1,2):
   c=comp(ls,m,arm);assert np.array_equal(c[v],sharedlegs[v]);assert np.array_equal(c[face],np.array(a.rgba(b))[face]);lab,k=label(c[:,:,3]>0,np.ones((3,3)));sizes=np.bincount(lab.ravel())[1:];comps.append([m,arm,int(k),sizes.tolist()])
 contacts=[];seq=next(x for x in proof['jets']['sequences']if x['refs'][0]==n);panels=[]
 for step in seq['steps']:
  jf=step[3];jz,jc=static(jf);assert np.array_equal(jz,np.load(D/f'shibuki_base_hover_ownership01/jet_{jf:02}.npy'))
  for state,alpha in [('parent',a.layer(n,8)[0]>0),('sourceFourth',fr>0),('newCommon',ls[8]>0)]:
   mask=alpha&(Y>=8);dist=distance_transform_cdt(~mask,metric='chessboard');data=[]
   for pp in jc['parts']:
    zz,_=static(jf,pp);em=zz>0;data.append([int(dist[em].min()),int((em&mask).sum())])
   contacts.append({'jet':jf,'state':state,'parts_distance_overlap':data})
  for mask in(8,15):
   z=np.zeros((384,384,4),np.uint8);z[jz>0]=(32,208,232,180);im=Image.fromarray(z);im.alpha_composite(Image.fromarray(comp(ls,mask)));panels.append((f'{n} mask{mask} jet{jf}',im))
 out=Image.new('RGB',(840,660),'#263345');dr=ImageDraw.Draw(out)
 for i,(cap,im)in enumerate(panels):
  x=i//2;y=i%2;dr.text((x*280+6,y*330+3),cap,fill='white');pic=im.crop((130,128,185,191)).resize((275,315),Image.Resampling.NEAREST);out.paste(pic,(x*280+2,y*330+18),pic)
 buf=io.BytesIO();out.save(buf,format='WEBP',lossless=True);pictures.append({'name':f'memory_jets_{n}','webp':base64.b64encode(buf.getvalue()).decode()})
 rows.append({'ref':n,'source_reconstruction_exact':True,'face_common_exact':True,'high_arms_not_head5':True,'bbox_new_8':bbox(comp(ls,8)[:,:,3]>0),'bbox_new_15':bbox(comp(ls,15)[:,:,3]>0),'lower_bbox':bbox(ls[8]>0),'leg_changed_from_Fourth_pixels':int(((lower!=fr)&legmask).sum()),'mask8_15_both_arm_types_components':comps,'jets':contacts,'new_part8_all_masks_exact':True,'owner229_5_4':int(owner[164,165])if n==229 else None})
for p,h in tracked.items():assert sha(R/p)==h


track(Path(__file__));track(D/'shibuki_base_hover_ownership01/report.json')
for jf in range(15):track(D/f'shibuki_base_hover_ownership01/jet_{jf:02}.npy')
for n in(221,223,225,227,229):
 for name in('comparison','partial'):track(O/f'{name}_{n}.png')
extra=[]
for n in(221,223,225,227,229):
 ls={pb:readimg(O/f'layer{pb}_{n}.png')for pb in(0,5,6,7,8)}
 f=next(x for x in meta['frames']if x['ref']==n)
 hand=np.zeros((384,384),bool)
 for r in f['shared_hand_windows']:hand|=box(r)
 page=1 if n<225 else 2
 bp=S/(f'registered_neutral{page:02}/base_legs_{n}_nearest_indices.png'if n!=229 else'reach229_registered01/base_legs_local_indices.png')
 fp=S/(f'registered_neutral{page:02}/fourth_{n}_nearest_indices.png'if n!=229 else'reach229_registered01/fourth_local_indices.png')
 b,fr=readimg(bp),readimg(fp);selected=hand&(np.isin(b,(10,11,12,13))|(fr==9))
 assert np.array_equal(comp(ls,8)[selected],comp(ls,15)[selected])
 entry={'ref':n,'shared_hand_semantic_cells':int(selected.sum()),'shared_hand_mask8_15_RGBA_exact':True}
 if n==223:
  region=(X>=7)&(Y>=18);source=(fr>0)&region;dest=np.zeros_like(source);dest[:-1]=source[1:];overlap=dest&~region&(fr>0)
  entry['shoe_registration']={'moved_opaque':int(source.sum()),'overlap_old_upper_row':[[int(x-160),int(y-160),int(fr[y,x])]for y,x in np.argwhere(overlap)],'source_lower_alpha':int(((fr>0)&((Y>=7)&~((X>=10)&(Y<8)))).sum()),'new_lower_alpha':int((ls[8]>0).sum()),'meaning':'새신발38셀의동일색인1행이동.목적지윗행8셀을가리므로전체하체픽셀수보존이동이아니다.새원화재생성/늘림은없음.'}
 extra.append(entry)
for p,h in tracked.items():assert sha(R/p)==h
RESULT_DIR.mkdir(exist_ok=False)
sheets=[]
for pic in pictures:
 path=RESULT_DIR/(pic['name']+'.webp');path.write_bytes(base64.b64decode(pic['webp']));sheets.append({'path':str(path.relative_to(R)),'sha256':sha(path),'composition':'기존layer0/5/6/7/8의mask8/15와원15jet원점.청록단색은정적점유진단이며실제FX색/반투명아님.'})
# 원래 비교판에 빠진 mask11 및 arm2 mask15도 별도 읽기판으로 보존한다.
out=Image.new('RGB',(560,1650),'#b9c4cb');dr=ImageDraw.Draw(out)
for row,n in enumerate((221,223,225,227,229)):
 ls={pb:np.array(Image.open(O/f'layer{pb}_{n}.png'))for pb in(0,5,6,7,8)}
 for col,(m,arm)in enumerate(((11,1),(15,2))):
  im=Image.fromarray(comp(ls,m,arm));dr.text((col*280+3,row*330+3),f'{n} mask{m} arm{arm}',fill='black');pic=im.crop((130,128,185,191)).resize((275,315),Image.Resampling.NEAREST);out.paste(pic,(col*280,row*330+15),pic)
path=RESULT_DIR/'mask11_arm2.webp';out.save(path,format='WEBP',lossless=True);sheets.append({'path':str(path.relative_to(R)),'sha256':sha(path),'composition':'mask11 arm1 및 mask15 arm2 실제CLUT 조합'})
report={'passed':True,'scope':'Root PL00호버 새공통몸25층의출처/소유/80부분조합과원15jet 정적접점 읽기','parent_sha256':sha(p)if False else meta['parent_sha256'],'manifest_sha256':sha(O/'manifest.json'),'producer_script_sha256':sha(S/'prepare_body_layers03.py'),'frames':rows,'hand_and_registration_details':extra,'sheets':sheets,'inputs':tracked,'producer_functions_imported_or_called':False,'art_or_resource_modified':False,'new_art_generated':False,'native_packed':False,'MIPS_execution':False,'runtime_verified':False,'actually_viewed':False,'limits':['전체8연결성분1은미술품질판정자체가아니다.','jet최소거리는Y>=8전체하체에서잰진단으로개별신발의물리접점증명은아니다.','사격5와최종ARC/원MIPS/실기는미제작후속이다.']}
(RESULT_DIR/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(RESULT_DIR/'INPUT_LOCK.json').write_text(json.dumps({'files':tracked,'reader':str(Path(__file__).relative_to(R)),'no_source_writes':True},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'passed':True,'report_sha256':sha(RESULT_DIR/'report.json'),'input_lock_sha256':sha(RESULT_DIR/'INPUT_LOCK.json'),'sheets':len(sheets),'extra':extra}))

