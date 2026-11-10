"""Candidate semantic registration of new heads, preserving source detail and feet."""
from pathlib import Path
import sys,json,hashlib,struct,collections
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
D=Path(__file__).parent/'rin_extension';S=D/'wall_followup01';O=D/'wall_followup_registered_v1';assert not O.exists();O.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();arc=(D/'prepared_victory_details_v1/PL01_U.ARC').read_bytes();assert hashlib.sha256(arc).hexdigest()=='1a4e16a126b551e5f9d291401a5b9249e66c84aa0252b929b2fd31fa541b143e';assert sha(S/'generated.png')=='bf9d790730fe4b6041a18f8b17e3d4afdd80f635c437a3ffc8bc7745806e8e3f'
pal=struct.unpack_from('<16H',entry(arc,9));black=struct.unpack_from('<16H',entry(arc,9),13*32)
# Semantic head polygons include their negative cells; gloves in front remain protected.
spec={
34:dict(poly=[(149,128),(168,128),(168,130),(175,130),(175,141),(165,141),(165,144),(162,145),(153,145),(149,142)],delta=(1,1),iris=(156,140),target_eye=(157,141)),
36:dict(poly=[(148,130),(167,130),(167,131),(174,131),(174,142),(166,142),(166,145),(162,147),(152,147),(148,143)],delta=(2,1),iris=(154,142),target_eye=(156,143)),
38:dict(poly=[(146,137),(163,137),(163,140),(171,140),(171,148),(164,148),(164,151),(158,153),(147,153),(144,150),(144,145)],delta=(-1,1),iris=(151,148),target_eye=(150,149)),
41:dict(poly=[(146,137),(165,137),(165,140),(174,140),(174,150),(166,150),(166,153),(158,155),(149,153),(146,149)],delta=(2,2),iris=(154,149),target_eye=(156,151)),
}
items={f:[]for f in('normal','black')};rows=[]
info=json.loads((S/'inputs.json').read_text('utf8'));reg=json.loads((S/'native/registration.json').read_text('utf8'));image=Image.open(S/'generated.png').convert('RGBA');cw=image.width/2
for n,s in spec.items():
 p=S/f'native/b0_{n:03}_indices.png';generic=np.array(Image.open(p));a=generic.copy();old=render(arc,0,0,n)[0];ix,iy=s['iris'];f=next(f for f in info['frames']if f['ref']==n);cx,cy=f['cell'];dy=next(f['translate'][1]for f in reg['records']if f['ref']==n)
 v=np.array(image.crop((round(cx*cw),round(cy*cw),round((cx+1)*cw),round((cy+1)*cw)))).astype(float);r,g,b,alpha=[v[:,:,k]for k in range(4)];ratio=np.divide(g,b,out=np.zeros_like(g),where=b>0);yy,xx=np.nonzero((alpha>=128)&(r<g*.6)&(g>90)&(ratio>.6)&(ratio<1.15));votes=collections.Counter(zip((112+xx*96/cw).astype(int).tolist(),(112+yy*96/cw+dy).astype(int).tolist()));assert votes[ix,iy]>=10
 a[iy,ix]=15
 maskim=Image.new('1',(384,384));ImageDraw.Draw(maskim).polygon(s['poly'],fill=1);mask=np.array(maskim,bool);dx,dy=s['delta'];movedmask=np.roll(np.roll(mask,dx,1),dy,0);source=np.zeros_like(a);source[mask]=a[mask];source=np.roll(np.roll(source,dx,1),dy,0);target=a.copy();target[mask]=0;target[movedmask]=source[movedmask]
 # Near-face hand of38 is drawn in front: preserve its new-art glove/forearm.
 protected=np.zeros_like(mask)
 if n==38:protected[143:159,140:146]=True;target[protected]=a[protected]
 scope=mask|movedmask;assert np.array_equal(target[~scope],a[~scope]);assert np.array_equal(target[166:],generic[166:]);assert target[s['target_eye'][1],s['target_eye'][0]]==15
 op=O/f'b0_{n:03}_indices.png';Image.fromarray(target).save(op);Image.fromarray(mask.astype(np.uint8)*255).save(O/f'b0_{n:03}_source_head_mask.png');Image.fromarray(protected.astype(np.uint8)*255).save(O/f'b0_{n:03}_foreground_mask.png')
 for form,words in [('normal',pal),('black',black)]:
  rgba(target,words).save(O/f'b0_{n:03}_{form}.png');items[form]+=[(f'{n} previous',rgba(old,words)),(f'{n} generic',rgba(generic,words)),(f'{n} eye-anchored new head',rgba(target,words))]
 rows.append({'key':f'b0_{n:03}','ref':n,'source_native':str(p.relative_to(ROOT)),'source_native_sha256':sha(p),'source_head_polygon':s['poly'],'source_head_delta':list(s['delta']),'source_iris':list(s['iris']),'source_cyan_votes':votes[ix,iy],'registered_iris':list(s['target_eye']),'old_body_copied_pixels':0,'feet_and_lower_body_exact_from_new_art':True,'wholebody_translation_from_generic':[0,0],'after_sha256':sha(op),'original_glove_anchors_pending':True})
for form,words in [('normal',pal),('black',black)]:page(items[form],rgba(render(arc,0,0,147)[0],words),O/f'{form}_comparison.png',cols=3,scale=5)
(O/'registration.json').write_text(json.dumps({'records':rows,'source_generated_sha256':sha(S/'generated.png'),'scope':'새 원화 머리만 의미 영역으로 이동해 눈 좌표를 정합한 중간 후보. 손/목 연결은 아직 실제 검토 필요. 원본/작업ARC 미변경.','root_review_pending':True,'runtime_verified':False,'user_accepted':False},ensure_ascii=False,indent=2)+'\n','utf8');print(str(O))
