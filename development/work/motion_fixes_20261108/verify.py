from pathlib import Path
import sys,json,shutil
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[1];sys.path.insert(0,str(ROOT))
from common import sha,write
from scripts.export_x_consistency import Archive
from scripts.prepare_riko_ui import entry
from src.psx_player import bank_offsets,composition_frame
PBS=(0,5,6,7,8);reports=[]
review=ROOT/'out/motion_fixes_20261108_review';review.mkdir(exist_ok=True)
for mode,selected in [('ver_rin_nana',set(range(33,55))|set(range(67,85))),('ver_buki_riko',set(range(68,85,2)))]:
 w=H/mode
 for name in ('PL00','PL02'):
  a=Archive((w/(name+'_U.ARC')).read_bytes());b=Archive((w/(name+'_fixed.ARC')).read_bytes());same=changed=0
  for n in range(237):
   for pb in PBS:
    if n in {105,*range(175,183)}:continue
    old=a.layer(n,pb)[0];new=b.layer(n,pb)[0]
    if n not in selected:assert np.array_equal(old,new),(mode,name,n,pb);same+=1
    else:
     changed+=int(np.any(old!=new))
     if mode=='ver_rin_nana':assert np.array_equal(new,np.array(Image.open(w/f'body_registration/{name}_layer{pb}_{n:03}.png')))
  assert a.p==b.p
  reports.append({'mode':mode,'resource':name,'unselected_layers_exact':same,'changed_layers':changed,'palette_exact':True})
  # All partial armor masks use the same registered layer geometry. Inspect alpha
  # containment in Ultimate pre/post costumes where only the head overlay is used.
  if name=='PL02':
   for n in sorted(selected):
    after=np.array(b.composite(n,0)[0]);before=np.array(b.composite(n,15)[0]);assert np.all((after[:,:,3]==0)|(before[:,:,3]>0)),(mode,n,'coat fails to cover body')
  for form,mask in ([('base',0),('fourth',15)] if name=='PL00' else [('ultimate_before',15),('ultimate_after',0)]):
   refs=([0]*8+[33,35,37,39,41,43,45,47,49,51,53]+[0]*8+[67,69]+[71,75]*5+[77,79,81,83]+[0]*8) if mode=='ver_rin_nana' else [0]*8+[68,70]+[72,76]*5+[78,80,82,84]+[0]*8
   frames=[]
   for n in refs:
    im=Image.new('RGB',(768,340),(31,38,50));d=ImageDraw.Draw(im)
    for k,aa in enumerate((a,b)):
     crop=aa.composite(n,mask)[0].crop((112,120,208,200)).resize((384,320),Image.Resampling.NEAREST);im.paste(crop,(k*384,20),crop);d.text((k*384+8,4),f'{form} {n}: '+('before' if k==0 else 'adjusted'),fill='white')
    frames.append(im)
   frames[0].save(review/f'{mode}_{form}.gif',save_all=True,append_images=frames[1:],duration=80,loop=0,disposal=2)
rn=H/'ver_rin_nana';old=Archive((rn/'PL01_U.ARC').read_bytes());new=Archive((rn/'PL01_fixed.ARC').read_bytes());digests=[]
for n in (46,47,48):
 a=old.layer(n)[0];b=new.layer(n)[0];yy,xx=np.indices(a.shape);region=(xx-160>=3)&(xx-160<=35)&(yy-160>=-7)&(yy-160<=np.where(xx-160<7,2,10))
 assert np.array_equal(a[~region],b[~region]);digests.append(sha(b.tobytes()))
assert len(set(digests))==3
shutil.copyfile(rn/'rin_flutter/review.png',review/'rin_dash.png');shutil.copyfile(rn/'rin_flutter/preview.gif',review/'rin_dash.gif')
shutil.copyfile(H/'ver_buki_riko/riko_inverted_trial.png',review/'riko_black_clothing.png')
for mode,folder,files in [('ver_rin_nana','body_registration',['base_air','base_dash','base_shot','fourth_dash','ultimate_before_dash','ultimate_after_dash']),('ver_buki_riko','wrist_registration',['base','fourth','ultimate_before','ultimate_after'])]:
 for file in files:shutil.copyfile(H/mode/folder/(file+'.png'),review/(mode+'_'+file+'.png'))
write(H/'static_validation.json',{'passed':True,'resources':reports,'rin_tail_frames_distinct':3,'rin_head_body_outside_tail_exact':True,'ultimate_pre_post_alpha_containment':True,'simulation_note':'GIF는 자세 연결 비교용으로 80ms 고정 재생. 실제 엔진 타이밍의 실행 증거는 별도 runtime 기록만 해당.','palette_timing_source_exe_unchanged':True})
html='<!doctype html><meta charset="utf-8"><title>동작 수정 비교</title><style>body{background:#151d29;color:#eef2fa;font:17px sans-serif;margin:30px}img{max-width:100%;image-rendering:pixelated}article{margin:35px 0}</style><h1>2026-11-08 동작 수정 비교</h1><p>왼쪽 이전 / 오른쪽 수정. GIF는 고정 간격의 자세 비교이며 실기 녹화가 아닙니다.</p>'
for p in sorted(review.glob('*')):
 if p.suffix in ('.png','.gif'):html+=f'<article><h2>{p.stem}</h2><img loading="lazy" src="{p.name}"></article>'
(review/'index.html').write_text(html,'utf8');print('static checks passed; review:',review)
