"""현재 시부키 기본형 특수 자세를 같은 원점/확대율로 비교한다."""
import importlib.util
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('cov', ROOT/'scripts/audit_sprite_consistency_coverage.py')
cov=importlib.util.module_from_spec(spec);spec.loader.exec_module(cov)
OUT=Path(__file__).resolve().parent/'shibuki_specials'
OUT.mkdir(exist_ok=True)
binpath=ROOT/'out/ver_buki_riko/ultimate_costumes_swapped_20261105_v1/shibuki_riko.bin'
assert cov.file_sha(binpath)==cov.EXPECTED['ver_buki_riko'][1]
assets,_=cov.read_assets(binpath,['PL00_U.ARC'])
arc=assets['PL00_U.ARC']
ids=[0,85,95,96,97,98,99,100,101,102,103,104,231,232,233,234,235,236]
manifest={'source_bin':binpath.relative_to(ROOT).as_posix(),'source_sha256':cov.file_sha(binpath),
          'archive_sha256':cov.sha(arc),'palette':'entry9 first64colors, static preview; flash runtime palette not simulated',
          'current_game_tested':False,'art_modified':False,'frames':{}}
board=Image.new('RGB',(6*256,3*310),(29,34,42));dr=ImageDraw.Draw(board)
for i,n in enumerate(ids):
 im=cov.idle_image(arc,n,[0]);im.save(OUT/f'{n:03}.png')
 bbox=im.getbbox();a=np.asarray(im);opaque=a[:,:,3]>0
 colors,count=np.unique(a[opaque],axis=0,return_counts=True)
 manifest['frames'][str(n)]={'rgba_sha256':cov.sha(im.tobytes()),'bbox_world':[bbox[0]-160,bbox[1]-160,bbox[2]-160,bbox[3]-160],
  'size':[bbox[2]-bbox[0],bbox[3]-bbox[1]],'opaque_pixels':int(opaque.sum()),'colors_with_pixel_counts':[{'rgba':c.tolist(),'count':int(k)}for c,k in zip(colors,count)]}
 x=i%6*256;y=i//6*310
 pic=im.crop((128,118,192,190)).resize((256,288),Image.Resampling.NEAREST)
 board.paste(pic,(x,y+20),pic);dr.text((x+5,y+3),f'PL00 base {n} '+('IDLE'if n==0 else ''),fill='white')
board.save(OUT/'comparison_4x.png')
cov.write(OUT/'metadata.json',manifest)
print(json.dumps({'output':OUT.relative_to(ROOT).as_posix(),'frames':len(ids)},ensure_ascii=False))
