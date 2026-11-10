"""전체 생성 자세를 원래 CLUT/고정 배율로 변환하고 접지만 맞춘다."""
import argparse,json,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page
from scripts.prepare_rin_run import quantize
from scripts.prepare_sprite_style_unification import WORK,write
from src.psx_disc import file_hash

def main():
 p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args();d=a.directory.resolve()
 assert d.is_relative_to(WORK) and (d/'generated.png').is_file()
 info=json.loads((d/'inputs.json').read_text('utf8'));source=ROOT/info['source_bin'];assert file_hash(source)==info['source_sha256']
 arc=Archive(read_disc(source,(info['archive'],))[0][info['archive']]);start=info['palette_row']
 colors=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in arc.words[start+1:start+16]],np.int32)
 im=Image.open(d/'generated.png').convert('RGBA');cw,ch=im.width/info['columns'],im.height/info['rows']
 assert abs(cw/ch-info['native_cell'][0]/info['native_cell'][1])<.001
 scale=info['native_cell'][0]/cw;out=d/'native';assert not out.exists();out.mkdir();records=[];items=[]
 for f in info['frames']:
  x,y=f['cell'];crop=im.crop((round(x*cw),round(y*ch),round((x+1)*cw),round((y+1)*ch)))
  v=quantize(crop,colors,scale);assert v.shape==tuple(reversed(info['native_cell']))
  target=np.zeros((384,384),np.uint8);x0,y0,x1,y1=info['crop'];target[y0:y1,x0:x1]=v
  ref=f['ref'];mask=15 if info['form']=='ultimate_after' and 217<=ref<=230 else info['mask']
  old=arc.composite(ref,mask,2)[0];current=arc.rgba(target,start);newbox=current.getchannel('A').getbbox();assert newbox
  # A uniform translation retains every authored pixel; do not squash each pose.
  dx=0;dy=old.getchannel('A').getbbox()[3]-newbox[3]
  assert abs(dy)<=6,(ref,dy)
  if dy:target=np.roll(target,dy,axis=0)
  revised=arc.rgba(target,start);Image.fromarray(target).save(out/f'{ref:03}_indices.png');revised.save(out/f'{ref:03}.png')
  items.extend([(f'{ref:03} before',old),(f'{ref:03} detailed',revised)])
  records.append({'ref':ref,'scale':scale,'translate':[dx,dy],'before':old.getchannel('A').getbbox(),'after':revised.getchannel('A').getbbox(),
                  'new_art_pixels':int((target>0).sum()),'old_head_or_body_overwritten':False})
 for i in range(0,len(items),8):page(items[i:i+8],arc.composite(0,info['mask'],2)[0],out/f'comparison_{i//8:02}.png',cols=2,scale=4)
 write(out/'registration.json',{'source_art_sha256':file_hash(d/'generated.png'),'fixed_scale':scale,'native_palette_row':start,'frames':records,'applied':False})
 print(json.dumps({'native':str(out),'count':len(records),'scale':scale}))
if __name__=='__main__':main()
