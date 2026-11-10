"""Read current basic/Fourth hover bodies with the required legs bit enabled."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive,page
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 d=W/'root_nana_hover';assert not d.exists();d.mkdir()
 src=W/'root_nana_shot87/packed_settle01/PL00_U.ARC';assert sha(src)=='8951948879773266cae0bebd408b411f4806b5652257bba3c50df0212b3c6e10';a=Archive(src.read_bytes());rows=[]
 for n in range(221,231):
  for label,mask,idle_mask in [('base_legs',8,0),('fourth',15,15)]:
   im=a.composite(n,mask)[0];im.save(d/f'{label}_{n:03}.png');idle=a.composite(0,idle_mask)[0]
   page([(f'{label} current {n}',im)],idle,d/f'compare_{label}_{n:03}.png',cols=1,scale=5)
   rows.append({'ref':n,'form':label,'mask':mask,'bbox':im.getbbox(),'rgba_sha256':hashlib.sha256(im.tobytes()).hexdigest()})
 for label,frames in [('pose_inputs',[(221,8),(221,15),(223,8),(223,15)]),('style_inputs',[(0,0),(0,15),(37,0),(37,15)])]:
  sheet=Image.new('RGBA',(1152,1152))
  for i,(n,mask)in enumerate(frames):
   im=a.composite(n,mask)[0];crop=im.crop((112,112,208,208));assert np.count_nonzero(np.array(crop)[:,:,3])==np.count_nonzero(np.array(im)[:,:,3]);sheet.alpha_composite(crop.resize((576,576),Image.Resampling.NEAREST),(i%2*576,i//2*576))
  sheet.save(d/f'{label}.png')
 r={'input':{'path':src.relative_to(ROOT).as_posix(),'sha256':sha(src)},'scope':'나나 기본 상체+다리파츠8 및 포스15 호버10의 원화 입력 조사','cases':rows,'crop':[112,112,208,208],'native_cell':96,'image_reference_scale':6,'pose_order':[[221,8],[221,15],[223,8],[223,15]],'style_order':[[0,0],[0,15],[37,0],[37,15]],'notes':['호버는 다리파츠8을 요구하므로 기본층0 단독 반신을 완성 자세로 사용하지 않는다.','현재 그림의 세부 차이를 조사하는 입력이며 새 원화/게임수정이 아니다.','정본 사랑이·실제 원발사점·추진발 연결은 후속 별도 검증 대상이다.'],'new_art_generated':False,'game_changed':False}
 (d/'input_audit.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'directory':str(d),'cases':len(rows)}))
if __name__=='__main__':main()
