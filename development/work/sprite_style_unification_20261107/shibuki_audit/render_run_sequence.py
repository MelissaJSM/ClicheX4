"""실행표 원순서/유지 호출을 이용한 정적 이미지 재생. 실제 게임 녹화 아님."""
from pathlib import Path
import sys,json,hashlib
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from PIL import Image,ImageDraw
from scripts.export_x_consistency import Archive
out=H/'prepared_run_complete03';a=Archive((out/'PL02_U.ARC').read_bytes())
meta=ROOT/'work/sprite_consistency_20261105/playback/manifest.json';d=json.loads(meta.read_text('utf8'))
anim=next(x for x in d['characters']['shibuki']['forms']['ultimate_before']['animations']if x['id']==8)
seq=[(x['frame_ref'],x['duration_calls'])for x in anim['steps']]
ims=[];times=[]
for ref,calls in seq:
 panel=Image.new('RGBA',(1024,576),(26,32,43,255));draw=ImageDraw.Draw(panel)
 for i,(label,mask,add)in enumerate([('jacket RUN',15,0),('jacket SHOT',15,1),('swimsuit RUN',0,0),('swimsuit SHOT',0,1)]):
  x=i%2*512;y=i//2*288;idle=a.composite(0,mask)[0].crop((112,128,208,192)).resize((384,256),Image.Resampling.NEAREST);im=a.composite(ref+add,mask)[0].crop((112,128,208,192)).resize((384,256),Image.Resampling.NEAREST)
  panel.alpha_composite(im,(x,y+24));draw.text((x+5,y+4),f'{label} ref {ref+add:03} / {calls} calls',fill='white')
 ims.append(panel.convert('RGB'));times.append(round(calls*1000/60))
ims[0].save(out/'run_shot_sequence.webp',save_all=True,append_images=ims[1:],duration=times,loop=0,lossless=True)
(out/'sequence.json').write_text(json.dumps({'source_metadata_sha256':hashlib.sha256(meta.read_bytes()).hexdigest(),'animation_id':8,'sequence':seq,'shoot_refs_policy':'same moving pose +1; shot dwell uses moving pose call duration for visual review','timer_calls_per_second_assumption':60,'actual_game_capture':False,'external_physics_not_simulated':True},ensure_ascii=False,indent=2)+'\n','utf8')
