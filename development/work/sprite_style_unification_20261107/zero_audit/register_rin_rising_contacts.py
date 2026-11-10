"""Anchor the newly authored rising-slash hands, with local boot registration."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
D=Path(__file__).parent/'rin_extension';P=D/'rising_rear01';O=D/'rising_registered_contacts_v1'
assert not O.exists();O.mkdir()
arc=(D/'prepared_rear_continuation2_v1/PL01_U.ARC').read_bytes()
assert hashlib.sha256(arc).hexdigest()=='a565e55fb422764432b03fe60d53430fcd5ede2aa95829a655a9c22bcc902c4d'
assert hashlib.sha256((P/'generated.png').read_bytes()).hexdigest()=='541661aaad1cae0cb822480e40614a2a6128f6969c482e03b0340f117fcebeb4'
pal=struct.unpack_from('<16H',entry(arc,9));black=struct.unpack_from('<16H',entry(arc,9),13*32)
items={f:[]for f in('normal','black')};rows=[]
for n,undo in [(148,0),(150,0),(152,1),(154,-1)]:
 old=render(arc,1,5,n)[0];generic=np.array(Image.open(P/f'native/b1_{n:03}_indices.png'))
 a=np.roll(generic,undo,axis=0);new=a.copy();scope=np.zeros_like(a,bool);method='No local movement'
 if n==152:
  # Toe is one pixel too low; move the newly drawn boot up, leaving calf intact.
  x0,y0,x1,y1=139,180,148,188;cut=a[y0:y1,x0:x1].copy();new[y0:y1,x0:x1]=0
  new[y0-1:y1-1,x0:x1]=cut;scope[y0-1:y1,x0:x1]=True
  method='New boot region [139,180,148,188] translated (0,-1); no head/hand movement.'
 if n==154:
  # Keep the uppermost seam row while lowering the newly drawn boot one pixel.
  # The seam is copied from the same new source, never old artwork or flat fill.
  x0,y0,x1,y1=140,181,149,188;cut=a[y0:y1,x0:x1].copy();new[y0:y1,x0:x1]=0
  new[y0+1:y1+1,x0:x1]=cut;new[y0,x0:x1]=cut[0];scope[y0:y1+1,x0:x1]=True
  method='New boot region [140,181,149,188] translated (0,+1); same-art top seam row retained.'
 assert np.array_equal(new[~scope],a[~scope])
 assert np.array_equal(new[0:174],a[0:174])
 assert np.nonzero(old)[0].max()==np.nonzero(new)[0].max()
 Image.fromarray(new).save(O/f'b1_{n:03}_indices.png');Image.fromarray(scope.astype(np.uint8)*255).save(O/f'b1_{n:03}_contact_scope.png')
 centers=[]
 for v in(old,new):
  yy,xx=np.nonzero(np.isin(v[120:132,141:155],range(7,12)));centers.append([float(xx.mean()+141),float(yy.mean()+120)])
 delta=(np.array(centers[1])-centers[0]).tolist();assert max(map(abs,delta))<0.5
 row={'key':f'b1_{n:03}','bank':1,'ref':n,'wholebody_generic_shift_undone':[0,undo],'wholebody_translation_from_fixed_cell':[0,0],'local_registration':method,'local_changed_pixels':int(np.count_nonzero(a!=new)),'glove_bright_center_before':centers[0],'glove_bright_center_after':centers[1],'glove_bright_center_delta':delta,'original_floor_y':int(np.nonzero(old)[0].max()),'registered_floor_y':int(np.nonzero(new)[0].max()),'head_and_high_hand_exact_from_unshifted_new_art':True,'old_body_pixels_copied':0,'indices_sha256':hashlib.sha256((O/f'b1_{n:03}_indices.png').read_bytes()).hexdigest()};rows.append(row)
 for form,words in [('normal',pal),('black',black)]:
  items[form].extend([(f'{n} old',rgba(old,words)),(f'{n} new fixed-cell',rgba(a,words)),(f'{n} contacts',rgba(new,words))])
  rgba(new,words).save(O/f'b1_{n:03}_{form}.png')
for form,words in [('normal',pal),('black',black)]:page(items[form],rgba(render(arc,0,0,147)[0],words),O/f'{form}_comparison.png',cols=3,scale=5)
(O/'registration.json').write_text(json.dumps({'records':rows,'source_generated':str((P/'generated.png').relative_to(ROOT)),'source_generated_sha256':hashlib.sha256((P/'generated.png').read_bytes()).hexdigest(),'scope':'용염인 새4몸체. 범용 발맞춤의 전신 y이동을 취소하고 손/머리 원점을 유지한다.152/154 부츠만 새원화 내부에서1px 정합. 불꽃은 이 파일에 포함하지 않는다.','root_review_pending':True,'user_accepted':False,'runtime_verified':False},ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'out':str(O),'records':rows}))
