"""현재 네 캡슐 뱅크의 실루엣/원점/타일 경계를 읽기 전용 감사한다."""
from pathlib import Path
import hashlib,json,sys
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import binary_fill_holes,binary_dilation
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import DiscReader
from src.psx_player import graphics_bank,composition_frame,decode_stream,indexed_atlas

def bbox(a):
 y,x=np.where(a);return [int(x.min()-160),int(y.min()-160),int(x.max()-160),int(y.max()-160)] if len(x) else None
def main():
 data=(H/'PL02_U.ARC').read_bytes();arc=Archive(data)
 body,_=arc.composite(0,0);bodya=np.array(body)[:,:,3]>0;filled=binary_fill_holes(bodya)
 records=[];unsafe=[]
 for gb in range(10,14):
  b=graphics_bank(arc.g,gb,allow_bank_aliases=True)
  for n in range(12):
   a,meta=arc.layer(n,gb+8,gb);mask=a>0;f=b['frames'][n]
   raw=decode_stream(arc.g,f['offset'],f['limit'],f['tile_count']*128).data
   atlas=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256)
   for q in composition_frame(arc.c,gb+8,n)['parts']:
    t=q['tile'];p=atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
    if t%16==0 and p[:,0].any():unsafe.append({'bank':gb,'frame':n,'tile':t,'axis':'U','part':q})
    if q['flip_y'] and t//16%16==0 and p[0].any():unsafe.append({'bank':gb,'frame':n,'tile':t,'axis':'V','part':q})
   records.append({'bank':gb,'frame':n,'pixels':int(mask.sum()),'bbox':bbox(mask),'tile_count':f['tile_count'],
                   'whole_body_exact':bool(np.array_equal(mask,filled)) if n==5 else None,
                   'outer_1px_ring_exact':bool(np.array_equal(mask,binary_dilation(filled)&~filled)) if n in (9,10) else None})
   if n==5:assert np.array_equal(mask,filled)
   if n in (9,10):assert np.array_equal(mask,binary_dilation(filled)&~filled)
 assert not unsafe,unsafe
 frames=[1,4,5,6,7,8,9,10]
 board=Image.new('RGB',(len(frames)*190,420),'#263642');d=ImageDraw.Draw(board)
 for col,n in enumerate(frames):
  for row,bmask in enumerate((15,0)):
   im,_=arc.composite(0,bmask);a,_=arc.layer(n,18,10)
   rgba=np.array(im);rgba[a>0]=[120,240,255,255]
   out=Image.fromarray(rgba).crop((128,124,192,188)).resize((192,192),Image.Resampling.NEAREST)
   board.paste(out,(col*190,row*210+18),out)
   d.text((col*190+3,row*210+2),f'ref{n} / body mask{bmask}',fill='white')
 board.save(H/'body_ghost_overlap.png')
 oldpath=ROOT/'MegaMan X4.bin'
 with oldpath.open('rb') as f:
  disc=DiscReader(f,oldpath.stat().st_size);r=next(x for x in disc.inspect()['files'] if x['name']=='PL02_U.ARC;1');olddata=disc.read(r['lba'],r['size'])
 old=Archive(olddata);oldbody,_=old.composite(0,15);oldalpha=np.array(oldbody)[:,:,3]>0
 oldstats=[]
 for n in (5,9,10):
  a,_=old.layer(n,18,10);ma=a>0
  oldstats.append({'frame':n,'pixels':int(ma.sum()),'bbox':bbox(ma),'outside_body_pixels':int((ma&~oldalpha).sum()),'body_pixels_uncovered':int((oldalpha&~ma).sum())})
 out={'passed':True,'source_arc_sha256':hashlib.sha256(data).hexdigest(),'body_ref':0,'body_alpha_pixels':int(bodya.sum()),'body_bbox':bbox(bodya),
      'filled_holes':int(filled.sum()-bodya.sum()),'records':records,'unsafe_uv_parts':unsafe,'original_us_arc_sha256':hashlib.sha256(olddata).hexdigest(),
      'original_effect_comparison':oldstats,'preview':'body_ghost_overlap.png',
      'conclusion':'네 캡슐 모두 후반 몸체는 동일815px 실루엣이고 끝의1px바깥링도 동일한몸체에서 유도되어 있음. 현 정적자원에서 후반 원점/크기 불일치를 재현하지 못함.',
      'limitations':['겹침 미리보기는 효과를 단색청록으로 표시한 정적분석이다. 실제 CLUT/반투명 합성과 게임 캡처가 아니다.','초기재킷 위 획득예정 수영복 윤곽이 보이는 것은 변신연출일 수 있어 결함으로 단정하지 않았다.','현재 캡슐 장면 실기 재현은 수행하지 않았다.']}
 (H/'geometry_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n','utf8')
 print(json.dumps({'passed':True,'banks':4,'frames':48,'unsafe_uv_parts':len(unsafe),'original':oldstats}))
if __name__=='__main__':main()
