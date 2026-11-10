"""새 사다리 원화의 고정1/8·기존CLUT 등록과 접점 비교. 전신 bbox 재조정 없음."""
from pathlib import Path
import sys,json,struct,argparse
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scipy.ndimage import label
from scripts.export_x_consistency import Archive,page
from scripts.prepare_shibuki_run_cycle import quantize
from native_pose_pack import need,sha,write

def features(v):
 y,x=np.nonzero(v);lab,num=label(np.isin(v,[12,13]),np.ones((3,3)));skin=[]
 for k in range(1,num+1):
  yy,xx=np.nonzero(lab==k)
  if len(xx)>=2:skin.append({'pixels':len(xx),'bbox_world_exclusive':[int(xx.min()-160),int(yy.min()-160),int(xx.max()+1-160),int(yy.max()+1-160)]})
 return {'opaque':len(x),'bbox_world_exclusive':[int(x.min()-160),int(y.min()-160),int(x.max()+1-160),int(y.max()+1-160)],'index12_13_components_unclassified':skin}

def main():
 p=argparse.ArgumentParser();p.add_argument('--page',type=int,required=True,choices=(1,2,3));p.add_argument('--source',type=Path,required=True);p.add_argument('--source-cell',type=int,default=512);p.add_argument('--sha256',required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args();source=args.source.resolve();out=args.output.resolve();need(source.is_relative_to(H)and out.is_relative_to(H),'Outside task');need(sha(source.read_bytes())==args.sha256,'Source image changed');need(not out.exists(),'Output exists')
 keys={1:[143,144,146],2:[149,151,153],3:[154,183]}[args.page];im=Image.open(source).convert('RGBA');cell_size=args.source_cell;need(im.size==(len(keys)*cell_size,2*cell_size),'Source dimensions must retain a fixed equal square-cell grid');data=(H/'prepared_wall_front01/PL00_U.ARC').read_bytes();need(sha(data)=='db508292c2746b5c4a12e60e9cf28f5ebe558e7998788c3d1d5440a4f8fd481a','Checkpoint changed');a=Archive(data);out.mkdir();rows=[];images={0:[],15:[]};layers={}
 for row,(name,mask,start)in enumerate((('base',0,0),('fourth',15,16))):
  words=struct.unpack_from('<16H',a.p,start*2);rgb=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in words],np.int32)
  for col,n in enumerate(keys):
   cell=im.crop((col*cell_size,row*cell_size,(col+1)*cell_size,(row+1)*cell_size));v=quantize(cell,(64,64),rgb,128);canvas=np.zeros((384,384),np.uint8);canvas[128:192,128:192]=v;layers[mask,n]=canvas;Image.fromarray(canvas).save(out/f'{name}_{n:03}_indices.png');pic=a.rgba(canvas,start);pic.save(out/f'{name}_{n:03}.png');images[mask].extend([(f'{n} current',a.composite(n,mask)[0]),(f'{n} new fixed scale',pic)]);rows.append({'ref':n,'form':name,'cell':[col,row],'new':features(canvas),'old':features(a.layer(n)[0])if mask==0 else None})
 for mask,name in((0,'base'),(15,'fourth')):page(images[mask],a.composite(0,mask)[0],out/f'{name}_comparison.png',cols=2,scale=4)
 overlap=[{'ref':n,'base_pixels_outside_fourth':int(np.count_nonzero((layers[0,n]>0)&(layers[15,n]==0))),'fourth_pixels_outside_base':int(np.count_nonzero((layers[15,n]>0)&(layers[0,n]==0)))}for n in keys]
 write(out/'registration.json',{'source_image':source.relative_to(ROOT).as_posix(),'source_sha256':args.sha256,'fixed_scale':64/cell_size,'actual_source_cell_size':cell_size,'native_origin':[160,160],'source_cell_origin':[32,32],'native_alpha_threshold':128,'new_full_art_registered':True,'old_coarse_head_body_overwrite':False,'wholebody_bbox_rescale':False,'rows':rows,'cross_costume_overlap':overlap,'input_art_only_not_packed':True,'hand_foot_contacts_pending_review':True,'runtime_verified':False});print(json.dumps({'rows':rows,'overlap':overlap}))

if __name__=='__main__':main()
