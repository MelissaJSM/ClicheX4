"""새 벽 원화를 고정1/8 축척과 기존 CLUT로 등록하는 비교 후보."""
from pathlib import Path
import sys,json,struct
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page
from scripts.prepare_shibuki_run_cycle import quantize
from native_pose_pack import SOURCE,SOURCE_SHA,sha,need,write
from src.psx_disc import file_hash

def main():
 need(file_hash(SOURCE)==SOURCE_SHA,'Source changed');a=Archive(read_disc(SOURCE,('PL00_U.ARC',))[0]['PL00_U.ARC']);source=H/'wall_detail_inputs01';out=H/'wall_detail_native01';need(not out.exists(),'Output exists');out.mkdir()
 src_hashes={'generated_page01.png':'8347d300959ae4bf752d6c1b457efad9462d586cd65475d918ff865c69fd052f','generated_page02.png':'7a7772833fabc314bc5bf85d5e1acb42f2ccdfb8fe37da064c3c89f6ba829489'};rows=[];images={0:[],15:[]}
 for p,refs in((1,[55,57,59]),(2,[61,63,65])):
  path=source/f'generated_page{p:02}.png';need(sha(path.read_bytes())==src_hashes[path.name],'Generated image changed');im=Image.open(path).convert('RGBA');need(im.size==(1536,1024),'Unexpected generated dimensions')
  for r,(name,mask,start)in enumerate((('base',0,0),('fourth',15,16))):
   words=struct.unpack_from('<16H',a.p,start*2);rgb=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in words],np.int32)
   for col,n in enumerate(refs):
    crop=im.crop((col*512,r*512,(col+1)*512,(r+1)*512));v=quantize(crop,(64,64),rgb,128);canvas=np.zeros((384,384),np.uint8);canvas[120:184,128:192]=v
    Image.fromarray(canvas).save(out/f'{name}_{n:03}_indices.png');pic=a.rgba(canvas,start);pic.save(out/f'{name}_{n:03}.png');images[mask].extend([(f'{name} current {n}',a.composite(n,mask)[0]),(f'{name} new {n}',pic)])
    y,x=np.nonzero(canvas);ey,ex=np.nonzero((canvas==7)&(np.indices(canvas.shape)[0]<160))if start==0 else(np.array([]),np.array([]));rows.append({'ref':n,'form':name,'source_file':path.name,'cell':[col,r],'fixed_scale':.125,'translation_canvas':[128,120],'alpha_threshold':128,'palette_word_start':start,'opaque_pixels':len(x),'bbox_world':[int(x.min())-160,int(y.min())-160,int(x.max()+1)-160,int(y.max()+1)-160],'gold_pixels_world':[[int(i)-160,int(j)-160]for j,i in zip(ey,ex)],'old_head_or_body_overwrite':False})
 for mask,label in((0,'base'),(15,'fourth')):page(images[mask],a.composite(0,mask)[0],out/f'{label}_comparison.png',cols=2,scale=4)
 write(out/'registration.json',{'source_bin_sha256':SOURCE_SHA,'generated_sha256':src_hashes,'records':rows,'source_alpha_preserved':True,'native_index_transparency_threshold':128,'runtime_verified':False,'registered_art_only_not_packed':True,'fixed_scale_no_bbox_resize':True,'unresolved':'Exact palms/feet and cross-costume overlap must be evaluated before packing.'})
 print(json.dumps({'records':[(r['form'],r['ref'],r['bbox_world'])for r in rows]}))

if __name__=='__main__':main()
