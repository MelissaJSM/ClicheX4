"""정본총과 새 소매/맨팔 사이 손만 새로 잇는 원화 입력."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,write
def main():
 m=json.loads((D/'a_inputs_v1/manifest.json').read_text('utf8'));a=Archive((ROOT/m['parent_arc']).read_bytes());out=D/'hand98_inputs_v1';assert not (out/'manifest.json').exists();out.mkdir(exist_ok=True);target=Image.new('RGBA',(1536,1024));guide=target.copy();style=target.copy();proof=[]
 for i,(form,start,mask)in enumerate((('before',16,15),('after',0,0))):
  p=D/f'contacts_probe_v1/{form}_098_indices.png';z=np.array(Image.open(p));im=a.rgba(z,start).crop((112,96,208,224)).resize((768,1024),Image.Resampling.NEAREST);target.alpha_composite(im,(i*768,0));guide.alpha_composite(im,(i*768,0));dr=ImageDraw.Draw(guide);dr.rectangle((i*768+25*8,56*8,i*768+36*8,66*8),outline=(0,220,255,255),width=3);dr.text((i*768+40,40),f'{form}98: connect one skin hand / forearm to FIXED pistol',fill=(0,220,255,255));style.alpha_composite(a.composite(91,mask)[0].crop((112,96,208,224)).resize((768,1024),Image.Resampling.NEAREST),(i*768,0));proof.append({'form':form,'source':p.relative_to(ROOT).as_posix(),'source_sha256':digest(p),'world_crop':[-48,-64,48,64],'edit_world_box':[-23,-8,-12,2]})
 target.save(out/'edit_target.png');guide.save(out/'edit_guide.png');style.save(out/'hand_style.png');write(out/'manifest.json',{'refs':[98],'scope':'배치고정 정본85모듈에 새손/전완 국소원화 연결. 앞진단의 끊김은 최종에 사용하지 않음.','frames':proof,'files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p)}for p in sorted(out.iterdir())if p.is_file()]});print(out)
if __name__=='__main__':main()
