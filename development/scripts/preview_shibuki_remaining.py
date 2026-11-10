"""패치 ARC를 다시 읽어 전체 기본형 시트와 원본 순서의 동작 미리보기를 만든다."""
import argparse,json,struct,sys
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import psx_arc,sha256
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_sprite_batch import canvas_from_parts
from scripts.prepare_shibuki_remaining_plan import STUBS

def main():
 p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);args=p.parse_args();build=args.build.resolve()
 if not build.is_relative_to(ROOT/'out/ver_buki_riko'):raise ValueError('Expected isolated build')
 manifest=json.loads((build/'manifest.json').read_text());arc=(build/'modified.arc').read_bytes()
 if sha256(arc)!=manifest['modified_archive_sha256']:raise ValueError('ARC changed')
 es=psx_arc(arc);g,c,pal=[arc[e['offset']:e['offset']+e['size']] for t in (2,3,9) for e in es if int(e['type'],16)==t];palette=struct.unpack('<16H',pal[:32]);bank=graphics_bank(g,0,allow_bank_aliases=True)
 out=build/'sprite_review';out.mkdir(exist_ok=False);frames={};metrics=[]
 for n in range(237):
  if n in STUBS:continue
  f=bank['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;v=canvas_from_parts(raw,f['tile_count'],composition_frame(c,0,n))%16;im=save_image(v.tobytes(),(160,160),palette,out/f'frame_{n:03}.png').convert('RGBA');frames[n]=im;y,x=np.nonzero(v);metrics.append({'frame':n,'bbox':None if not len(x) else [int(x.min())-80,int(y.min())-80,int(x.max())+1-80,int(y.max())+1-80],'opaque_pixels':len(x)})
 sheet=Image.new('RGB',(12*160,19*180),(36,51,66));draw=ImageDraw.Draw(sheet)
 for i,n in enumerate(frames):
  x=i%12*160;y=i//12*180;sheet.paste(frames[n],(x,y+20),frames[n]);draw.text((x+6,y+5),str(n),fill='white')
 sheet.save(out/'all_base_1x.png')
 selected=[0,37,89,90,95,97,100,101,102,103,104,130,133,134,135,137,138,142,156,158,162,166,170,174,184,204,205,206,207,208,217,220,221,222,231,233,234,235,236]
 sheet=Image.new('RGB',(8*240,5*280),(36,51,66));draw=ImageDraw.Draw(sheet)
 for i,n in enumerate(selected):
  im=frames[n].crop((40,35,120,115)).resize((240,240),Image.Resampling.NEAREST);x=i%8*240;y=i//8*280;sheet.paste(im,(x,y+30),im);draw.text((x+6,y+8),str(n),fill='white')
 sheet.save(out/'remaining_review_3x.png')
 inv=json.loads((ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/inventory.json').read_text());animations=[]
 for aid in [2,3,35,39,40,65,69,73,91,95,96,97,98,99,100,101,102,103,104,105,106]:
  a=inv['animations'][aid];pics=[];dur=[]
  for step in a['steps']:
   n=step['frame']
   if n not in frames:continue
   bg=Image.new('RGB',(160,160),(36,51,66));bg.paste(frames[n],(0,0),frames[n]);pics.append(bg.resize((480,480),Image.Resampling.NEAREST));dur.append(max(20,round((step['duration_ticks']+1)*1000/60)))
  if pics:pics[0].save(out/f'animation_{aid:03}.gif',save_all=True,append_images=pics[1:],duration=dur,loop=0,disposal=2);animations.append(aid)
 (out/'review.json').write_text(json.dumps({'source_arc_sha256':sha256(arc),'frames':metrics,'placeholders_preserved':sorted(STUBS),'preview_only_not_runtime_evidence':True,'gif_time_basis':'duration_ticks+1 at nominal 60 Hz; renderer preview, runtime unchanged','animations':animations},indent=2));print(json.dumps({'output':str(out),'frames':len(frames),'animations':animations}))
if __name__=='__main__':main()
