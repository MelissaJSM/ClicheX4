"""생성 의상과 수용 몸을 정렬하고 부분 아머별 투명 레이어를 준비한다."""
import json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.extract_zero import save_image
from scripts.analyze_shibuki_armor import entries,PARENT
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_sprite_batch import canvas_from_parts
from scripts.prepare_shibuki_idle import breathe
d=Path(__file__).parent;out=d/'layers03';out.mkdir(exist_ok=False)
meta=json.loads((d/'candidate02/normalization.json').read_text());words=meta['palette_words'];es=entries((ROOT/PARENT/'modified.arc').read_bytes());g,c=es[2],es[3];bank=graphics_bank(g,0,allow_bank_aliases=True)
base={}
for n in (0,115,116,117,118,119):
 f=bank['frames'][n];base[n]=canvas_from_parts(decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data,f['tile_count'],composition_frame(c,0,n))
generated=np.array(Image.open(d/'candidate02/full_outfit_indexed.png'));target=generated.copy();filled=[]
# The engine draws overlays; it cannot erase the accepted base silhouette.
# Register only the few uncovered edge cells from nearby generated costume pixels.
yy,xx=np.indices(target.shape);clothing=yy>=75
for y,x in np.argwhere((base[0]>0)&(target==0)&clothing):
 coords=np.argwhere((generated>0)&clothing);dist=(coords[:,0]-y)**2+(coords[:,1]-x)**2;k=int(np.argmin(dist));sy,sx=coords[k]
 if dist[k]>9:raise ValueError(f'Costume silhouette too different at {x},{y}; new art required')
 target[y,x]=generated[sy,sx];filled.append({'x':int(x),'y':int(y),'source':[int(sx),int(sy)],'distance_squared':int(dist[k])})
regions={}
regions['leg']=(yy>=91)
regions['arm']=((xx<71)&(yy>=76)&(yy<92))|((xx>=85)&(yy>=80)&(yy<91))
regions['body']=(yy>=75)&(yy<91)&(xx>=70)&(xx<87)
# Preserve the accepted face and ears; replace only the side floral accessory.
regions['head']=(xx>=82)&(xx<90)&(yy>=62)&(yy<76)
layers={k:np.where(mask,target,0).astype(np.uint8) for k,mask in regions.items()}
# Head overlay must cover the old pink ornament; draw only new art within the same area.
for y,x in np.argwhere(regions['head']&(base[0]>0)&(layers['head']==0)):
 coords=np.argwhere((generated>0)&regions['head']);dist=(coords[:,0]-y)**2+(coords[:,1]-x)**2;k=int(np.argmin(dist));sy,sx=coords[k]
 if dist[k]>9:raise ValueError('Head ornament does not cover old accessory')
 layers['head'][y,x]=generated[sy,sx];filled.append({'x':int(x),'y':int(y),'source':[int(sx),int(sy)],'distance_squared':int(dist[k]),'kind':'head_edge_registration'})
covered=np.zeros((160,160),bool)
for k in ('body','arm','leg'):covered|=layers[k]>0
preserved_side_hair=(xx>=87)&(yy<80)
miss=np.argwhere((base[0]>0)&clothing&~covered&~preserved_side_hair)
if len(miss):raise ValueError('Uncovered costume pixels: '+repr(miss.tolist()))
metadata={'source_art':'candidate02','palette_words':words,'frames':[0,115,116,117,118,119],'edge_registration':filled,'face_and_ears_from_accepted_base':True,'canvas_size':[160,160],'origin':[80,80],'part_order':['leg','head','arm','body'],'layers':{},'game_applied':False}
basewords=list(np.frombuffer(es[9][:32],'<u2').astype(int));pictures={}
for n,delta in ((0,0),(115,1),(116,1),(117,1),(118,1),(119,-1)):
 ls={}
 for k,layer in layers.items():
  v=np.zeros_like(layer);v[55:103,61:109]=breathe(layer[55:103,61:109],delta)
  ls[k]=v
  save_image(v.tobytes(),(160,160),words,out/f'{k}_{n:03}.png')
  sy,sx=np.nonzero(v);metadata['layers'][f'{k}_{n}']={'pixels':len(sx),'bbox':[int(sx.min()),int(sy.min()),int(sx.max()+1),int(sy.max()+1)]}
 for mask in range(16):
  pic=save_image(base[n].tobytes(),(160,160),basewords,out/f'base_{n:03}.png').convert('RGBA')
  for bit,k in ((8,'leg'),(1,'head'),(4,'arm'),(2,'body')):
   if mask&bit:pic.alpha_composite(Image.open(out/f'{k}_{n:03}.png').convert('RGBA'))
  pic.save(out/f'frame_{n:03}_mask{mask:02}.png');pictures[n,mask]=pic
sheet=Image.new('RGB',(6*280,360),'#253546');draw=ImageDraw.Draw(sheet)
for i,mask in enumerate((0,1,2,4,8,15)):
 im=pictures[0,mask].crop((55,50,105,110)).resize((250,300),Image.Resampling.NEAREST);sheet.paste(im,(i*280+15,40),im);draw.text((i*280+10,15),['Base','Head','Body/cape','Arms','Legs','Full'][i],fill='white')
sheet.save(out/'partial_review.png')
seq=json.loads((ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/inventory.json').read_text())['idle_animation']['steps'];ims=[];duration=[]
for step in seq:
 pic=pictures[step['frame'],15];im=Image.new('RGB',(160,160),'#253546');im.paste(pic,(0,0),pic);ims.append(im.crop((55,50,105,110)).resize((400,480),Image.Resampling.NEAREST));duration.append(max(20,round((step['duration_ticks']+1)*1000/60)))
ims[0].save(out/'full_idle_preview.gif',save_all=True,append_images=ims[1:],duration=duration,loop=0,disposal=2)
(out/'layers.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8');print(json.dumps({'output':str(out),'registered_edge_pixels':len(filled),'layer_boxes':{k:v['bbox'] for k,v in metadata['layers'].items() if k.endswith('_0')}}))
