"""새호버10 입력을 잠그고 원15jet 위치와 비교. 입력 그림/자원 불변."""
from pathlib import Path
import collections,hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import distance_transform_cdt,label
R=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent;S=W/'root_shibuki_hover';H=W/'shibuki_audit';A=D/'shibuki_base_hover_ownership01';O=D/'shibuki_base_hover_contacts01';assert not O.exists()
sys.path[:0]=[str(R),str(D)]
from scripts.export_x_consistency import Archive
from scripts.prepare_riko_ui import entry
from src.psx_player import composition_frame
from src.psx_static_effect import compose_static
from src.psx_ui_atlas import local_composition
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(R).as_posix();tracked={};KEYS=(221,223,225,227,229)
def blob(p):
 v=p.read_bytes();tracked[rel(p)]=sha(v);return v
def js(p):return json.loads(blob(p))
def img(p):blob(p);return np.array(Image.open(p))
def bbox(mask):
 y,x=np.nonzero(mask);return None if not len(x)else[int(x.min()-160),int(y.min()-160),int(x.max()-159),int(y.max()-159)]
def color(z,start):return ar.rgba(z,start)
def static(frame,ps=None):
 c=composition_frame(ar.c,12,frame)if ps is None else{'parts':ps};px,size,bb,_=compose_static(entry(ar.data,0x10206),local_composition(c));z=np.zeros((384,384),np.uint8)
 if len(px):z[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]=np.frombuffer(px,np.uint8).reshape(size[1],size[0])
 return z,c
source=H/'prepared_nova_strike_base01/PL00_U.ARC';ar=Archive(blob(source));assert sha(ar.data)=='36d4d0293abc77052c476e0495f4f4542ca75471c7a149f200e4bdb8f4e1bd4e'
previous=js(A/'report.json');assert sha(blob(A/'report.json'))=='4a09339f0f6e270c89d75963c9676b38fdc896abe51abd4ecb8bb302fe5191af'
js(A/'conclusions.json');js(A/'READ_LOCK.json')
for page in(1,2):
 m=js(S/f'registered_neutral{page:02}/manifest.json');assert m['source_sha256']==sha(blob(S/f'art{page:02}_generated.png'))
m229=js(S/'reach229_registered01/manifest.json');assert m229['source_sha256']==sha(blob(R/m229['source']))
new={};old={};frames=[];Y,X=np.indices((384,384));Y-=160;X-=160
for n in KEYS:
 for form,mask,start in(('base_legs',8,0),('fourth',15,16)):
  p=S/(f'registered_neutral{1 if n<225 else 2:02}/{form}_{n}_nearest_indices.png'if n!=229 else f'reach229_registered01/{form}_local_indices.png')
  z=img(p);assert z.shape==(384,384)and z.dtype==np.uint8 and z.max()<16;new[n,form]=z;old[n,form]=np.array(ar.composite(n,mask)[0]);om=old[n,form][:,:,3]>0
  if n!=229:
   m=js(p.parent/'manifest.json');q=next(v for v in m['frames']if v['ref']==n and v['form']==form and v['method']=='nearest');assert sha(z.tobytes())==q['indices_sha256']
  frames.append({'ref':n,'form':form,'path':rel(p),'file_sha256':sha(p.read_bytes()),'indices_sha256':sha(z.tobytes()),'new_bbox':bbox(z>0),'old_bbox':bbox(om),'new_pixels':int((z>0).sum()),'old_pixels':int(om.sum()),'components8':int(label(z>0,np.ones((3,3)))[1]),'new_lowest_y':bbox(z>0)[3]-1,'old_lowest_y':bbox(om)[3]-1,'lower_y_ge8_new_bbox':bbox((z>0)&(Y>=8)),'lower_y_ge8_old_bbox':bbox(om&(Y>=8)),'lower_rows':[{'y':y,'new_x':np.flatnonzero(z[y+160]>0).astype(int).tolist(),'old_x':np.flatnonzero(om[y+160]).astype(int).tolist()}for y in range(4,29)]})
for q in frames:
 for row in q['lower_rows']:
  row['new_x']=[v-160 for v in row['new_x']];row['old_x']=[v-160 for v in row['old_x']]
jetarrays={};contacts=[]
for n in KEYS:
 seq=next(q for q in previous['jets']['sequences']if q['refs'][0]==n);jetarrays[n]=[]
 for step in seq['steps']:
  jf=step[3];z,c=static(jf);saved=R/rel(A/f'jet_{jf:02}.npy');blob(saved);assert np.array_equal(z,np.load(saved));jetarrays[n].append((jf,z))
  for form in('base_legs','fourth'):
   for state in('old','new'):
    m=(old[n,form][:,:,3]>0)if state=='old'else(new[n,form]>0);m&=Y>=8;dist=distance_transform_cdt(~m,metric='chessboard')
    pmetrics=[]
    for i,p in enumerate(c['parts']):
     zz,_=static(jf,[p]);em=zz>0;d=int(dist[em].min());near=em&(dist==d);pmetrics.append({'part':i,'effect_bbox':bbox(em),'minimum_lower_yge8_distance':d,'overlap_pixels':int((em&m).sum()),'nearest_effect_coordinates':[[int(x-160),int(y-160)]for y,x in np.argwhere(near)][:30],'list_truncated':int(near.sum())>30})
    contacts.append({'ref':n,'form':form,'state':state,'jet_frame':jf,'parts':pmetrics,'limit':'Y>=8 전체하체 최소거리이며 각 신발의 정확한 접점 판정이 아니다. 원점 고정 정적 진단이다.'})
pairs=[]
for n in KEYS:
 zb,zf=new[n,'base_legs'],new[n,'fourth'];ab,af=zb>0,zf>0;rgba_b=np.array(color(zb,0));rgba_f=np.array(color(zf,16));diff=np.any(rgba_b!=rgba_f,axis=2)
 pairs.append({'ref':n,'alpha_different':int((ab!=af).sum()),'alpha_difference_bbox':bbox(ab!=af),'lower_yge8_alpha_different':int(((ab!=af)&(Y>=8)).sum()),'lower_yge8_RGBA_different':int((diff&(Y>=8)).sum()),'lower_yge8_RGBA_difference_bbox':bbox(diff&(Y>=8)),'both_opaque_color_differences_yge8':int((diff&ab&af&(Y>=8)).sum()),'not_yet_common_layer8':bool((diff&(Y>=8)).any())})
O.mkdir(exist_ok=False)
(O/'INPUT_LOCK.json').write_text(json.dumps({'inputs':tracked,'reader':{'path':rel(Path(__file__)),'sha256':sha(Path(__file__).read_bytes())},'source_only_read':True},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
sheets=[]
def board(name,rows,scale=4,crop=None):
 if crop is None:
  bs=[im.getbbox()for row in rows for _,im in row if im.getbbox()];crop=(min(v[0]for v in bs)-3,min(v[1]for v in bs)-3,max(v[2]for v in bs)+3,max(v[3]for v in bs)+3)
 w,h=crop[2]-crop[0],crop[3]-crop[1];cw,ch=w*scale+12,h*scale+25;out=Image.new('RGB',(cw*len(rows[0]),ch*len(rows)),'#263345');dr=ImageDraw.Draw(out)
 for y,row in enumerate(rows):
  for x,(caption,im)in enumerate(row):
   dr.text((x*cw+3,y*ch+3),caption,fill='white');pic=im.crop(crop).resize((w*scale,h*scale),Image.Resampling.NEAREST);out.paste(pic,(x*cw+6,y*ch+22),pic)
 p=O/name;out.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes()),'crop':list(crop),'integer_scale':scale})
for n in KEYS:
 rows=[]
 for form,start in(('base_legs',0),('fourth',16)):
  for state in('old','new'):
   row=[]
   for jf,jz in jetarrays[n]:
    rgba=np.zeros((384,384,4),np.uint8);rgba[jz>0]=(32,208,232,180);im=Image.fromarray(rgba);im.alpha_composite(Image.fromarray(old[n,form])if state=='old'else color(new[n,form],start));row.append((f'{n} {form} {state} jet{jf}',im))
   rows.append(row)
 board(f'jets_{n}.png',rows,5)
 board(f'feet_{n}.png',rows,7,(140,164,185,197))
board('bodies.png',[[(f'{n} old mask8',Image.fromarray(old[n,'base_legs'])),(f'{n} new base_legs',color(new[n,'base_legs'],0)),(f'{n} old mask15',Image.fromarray(old[n,'fourth'])),(f'{n} new Fourth',color(new[n,'fourth'],16))]for n in KEYS],4)
for p,h in tracked.items():assert sha((R/p).read_bytes())==h,p
report={'scope':'Root 새 시부키 PL00 호버10 등록 후보의 원15제트 정적 접점/크기/공통하체 읽기','source_arc':rel(source),'source_arc_sha256':sha(ar.data),'input_lock_sha256':sha((O/'INPUT_LOCK.json').read_bytes()),'frames':frames,'form_comparison':pairs,'jet_contacts':contacts,'sheets':sheets,'producer_functions_called':False,'new_quantization_performed':False,'input_art_or_resource_modified':False,'MIPS_execution':False,'runtime_verified':False,'actually_viewed':False,'limits':['원점160/384창에서 등록된 후보 자체를 읽었다. 원화 재양자화나 픽셀 수정은 수행하지 않았다.','청록 제트는 원15위상 알파/원점의 중립색 합성이며 실기색상/반투명·그리기순서 재현이 아니다.','최저Y/하체최소거리만으로 개별 양발 접점이나 미술 수용을 단정하지 않는다.','기본/포스 공통하체8은 기존 정책이며 현재 독립 생성 두 형태의 차이는 후속 정합 대상이다.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'report_sha256':sha((O/'report.json').read_bytes()),'input_lock_sha256':sha((O/'INPUT_LOCK.json').read_bytes()),'frames':[{k:q[k]for k in('ref','form','new_bbox','old_bbox','new_lowest_y','old_lowest_y')}for q in frames],'pairs':pairs}))
