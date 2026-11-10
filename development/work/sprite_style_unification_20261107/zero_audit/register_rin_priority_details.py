"""Keep authored cyan-eye clusters during the native palette registration."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent;R=D/'rin_extension/detail_priority_singles';OUT=R/'registered_v2';assert not OUT.exists();OUT.mkdir()
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render,rgba
arc=(D/'rin_extension/prepared_air_continuation2_v2/PL01_U.ARC').read_bytes();pal=struct.unpack_from('<16H',entry(arc,9));black=struct.unpack_from('<16H',entry(arc,9),13*32);sha=lambda x:hashlib.sha256(x).hexdigest()
colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in pal[1:]],np.int32)
rois={'b0_061':(140,130,170,162),'b1_005':(150,125,174,155),'b1_183':(130,150,160,176)};records=[];targets={}
for key in ['b0_061','b0_174','b1_005','b1_183']:
 p=R/key;info=json.loads((p/'inputs.json').read_text('utf8'));reg=json.loads((p/'native/registration.json').read_text('utf8'));assert sha((p/'generated.png').read_bytes())==reg['source_art_sha256']
 a=np.array(Image.open(p/'native'/(key+'_indices.png')));out=a.copy();edits=[]
 if key in rois:
  im=Image.open(p/'generated.png').convert('RGBA');full=np.array(im);near=np.zeros(full.shape[:2],np.uint8)
  for y in range(im.height):near[y]=np.argmin(((full[y,:,:3].astype(np.int32)[:,None]-colors[None])**2).sum(2),axis=1)+1
  votes=np.stack([np.array(Image.fromarray(np.where(near==i,full[:,:,3],0).astype(np.uint8)).resize((96,96),Image.Resampling.BOX))for i in range(1,16)])
  dy=reg['records'][0]['translate'][1];x0,y0,x1,y1=rois[key]
  for yy,xx in np.argwhere(votes[14]>10):
   y,x=int(yy)+104+dy,int(xx)+112
   if x0<=x<x1 and y0<=y<y1 and a[y,x]>0 and np.isin(a[y-1:y+2,x-1:x+2],[12,13,14]).any():
    cyan=int(votes[14,yy,xx]);winner=int(votes[:,yy,xx].max())
    if cyan*2.3>winner and a[y,x]!=15:
     out[y,x]=15;edits.append({'x':x,'y':y,'before':int(a[y,x]),'after':15,'authored_cyan_weight':cyan,'old_winner_weight':winner,'weight':2.3})
 assert np.array_equal(a>0,out>0);assert set(out[a!=out]).issubset({15})
 dest=OUT/(key+'_indices.png');Image.fromarray(out).save(dest);targets[key]=out
 old=np.array(Image.open(p/(key+'_indices.png')))
 feet={}
 for name,v in [('old',old),('new',out)]:
  yy,xx=np.nonzero(v);last=int(yy.max());bx=np.flatnonzero((v[last-1:last+1]>0).any(0));feet[name]={'floor':last,'last2_rows_x':[int(bx.min()),int(bx.max())],'opaque_pixels':int(len(xx))}
 records.append({'key':key,'bank':int(key[1]),'ref':int(key.split('_')[1]),'source':str((p/'generated.png').relative_to(ROOT)),'source_sha256':reg['source_art_sha256'],'input_meta_sha256':sha((p/'inputs.json').read_bytes()),'target':str(dest.relative_to(ROOT)),'target_sha256':sha(dest.read_bytes()),'translate':reg['records'][0]['translate'],'native_size':[96,96],'registration_scale':reg['scale'],'eye_registration':edits,'old_head_overwrite':0,'alpha_unchanged_from_native_v1':True,'feet':feet})
for label,words in [('normal',pal),('black',black)]:
 sheet=Image.new('RGB',(1440,600*4),'#64717b');draw=ImageDraw.Draw(sheet)
 for row,key in enumerate(targets):
  b,n=int(key[1]),int(key.split('_')[1]);old=render(arc,b,b*5,n)[0]
  for col,(name,v)in enumerate([('idle147',render(arc,0,0,147)[0]),('previous',old),('new authored',targets[key])]):
   pic=rgba(v,words).crop((112,104,208,200)).resize((480,480),Image.Resampling.NEAREST);assert np.count_nonzero(np.array(pic.getchannel('A')))==np.count_nonzero(v)*25
   sheet.paste(pic,(col*480,row*600+50),pic);draw.text((col*480+4,row*600+10),key+' '+name,fill='white')
 sheet.save(OUT/(label+'_comparison.png'))
report={'source_arc_sha256':sha(arc),'frames':records,'native_old_alpha_preserved':False,'native_v1_alpha_preserved':True,'source_art_direct_registration':True,'shared_old_head_used':False,'game_applied':False,'limitations':['새 원화는 기존 몸체 외곽과 완전히 같지 않다. 프레임별 발끝 x범위와 세부 관절 접점을 확인한 뒤 패킹한다.','61/승리5의 청록 눈3셀은 실제 생성 원화의 색 분포를 가중 등록한 것이며 원래 머리 픽셀을 덮은 것이 아니다.']}
(OUT/'registration.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'frames':len(records),'eye_changes':{r['key']:r['eye_registration']for r in records}}))
