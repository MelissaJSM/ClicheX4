"""낙봉파 잔여 몸체/구체를 당시 원화 기록과 실제 최신 표시로 분리한다."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).parent;ROOT=D.parents[2];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.c01_audio_build import read_disc
from src.psx_player import graphics_bank,decode_stream,composition_frame
R=D/'rin_extension';P=R/'prepared_arrival01/PL01_U.ARC';O=R/'burst_remaining_probe01';O.mkdir(exist_ok=True)
H=ROOT/'work/ver_rin_nana/style_revision/v4_special';read=lambda p:json.loads(p.read_text('utf8'));sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
arc=P.read_bytes();assert sha(arc)=='adf3b9475dd95cad5ff53ba627e4461dc9cb7ec18d202482b59744b0587c0322'
hist=read(H/'assembled_rise_burst_thrust_dashslash/verification.json');g=entry(arc,2);ps=entry(arc,3);pal=struct.unpack_from('<16H',entry(arc,9));rows=[];bodies={};effects={}
refs=[177,178,179,180,181,186,187,188,189]
for n in refs:
 source=101 if n==177 else 186 if n==187 else n;folder=H/('thrust'if n==177 else 'burst');rec=read(folder/'registered.json')['frames'][str(source)];path=folder/rec['file'];assert sha(path.read_bytes())==rec['sha256']
 b=np.zeros((384,384),np.uint8);small=np.array(Image.open(path));x,y,r,bt=rec['bounds'];assert small.shape==(bt-y,r-x);dx=hist['burst_contact_registration'][str(186 if n==187 else n)]['translate_x'];b[160+y:160+bt,160+x+dx:160+r+dx]=small
 aura=hist['embedded_charge_aura'].get(str(n),{}).get('world_pixels',[]);fx=np.zeros_like(b);combined=b.copy()
 for x,y,v in aura:fx[160+y,160+x]=v;combined[160+y,160+x]=v
 actual=render(arc,1,5,n)[0];assert np.array_equal(actual,combined),(n,int(np.count_nonzero(actual!=combined)))
 bodies[n]=b;effects[n]=fx;Image.fromarray(b).save(O/f'b1_{n:03}_body_indices.png');Image.fromarray(fx).save(O/f'b1_{n:03}_effect_indices.png')
 f=graphics_bank(g,1)['frames'][n];c=composition_frame(ps,5,n);raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
 rows.append({'ref':n,'body_source':rel(path),'body_source_sha256':sha(path.read_bytes()),'source_bounds':rec['bounds'],'original_registration_dx':dx,'body_bbox':rgba(b,pal).getbbox(),'effect_pixels':len(aura),'effect_over_body_pixels':int(np.count_nonzero((fx>0)&(b>0))),'parent_reconstruction_exact':True,'tile_count':f['tile_count'],'raw_sha256':sha(raw),'parts':c['parts'],'shared_refs':[h['index']for h in graphics_bank(g,1)['frames']if h['offset']==f['offset']]})
baseline_path=ROOT/read(R/'rin294_components.json')['source_bin'];baseline=read_disc(baseline_path,('PL01_U.ARC',))[0]['PL01_U.ARC']
def normalized(a):
 yy,xx=np.nonzero(a)
 if not len(xx):return None
 x,y,r,b=int(xx.min()),int(yy.min()),int(xx.max())+1,int(yy.max())+1
 return (sha(a[y:b,x:r].tobytes()),r-x,b-y),(x,y)
matches=[]
for bi,pb,total in[(0,0,254),(1,5,190)]:
 for n in range(total):
  if bi==1 and 42<=n<=49:continue
  a=render(baseline,bi,pb,n)[0];norm=normalized(a)
  if norm is None:continue
  for source,b in bodies.items():
   target=normalized(b)
   if norm[0]==target[0]:
    dx,dy=target[1][0]-norm[1][0],target[1][1]-norm[1][1];assert np.array_equal(np.roll(np.roll(a,dy,0),dx,1),b)
    matches.append({'target':source,'source_ref':f'b{bi}_{n:03}','dx':dx,'dy':dy,'full_body_exact_after_translation':True})
for form,row in [('normal',0),('black',13)]:
 words=struct.unpack_from('<16H',entry(arc,9),row*32)
 for page,start in enumerate(range(0,len(refs),3)):
  ids=refs[start:start+3];sheet=Image.new('RGB',(1536,len(ids)*400),'#313b4d');draw=ImageDraw.Draw(sheet)
  for iy,n in enumerate(ids):
   for ix,(tag,z)in enumerate([('idle147',render(arc,0,0,147)[0]),('current',render(arc,1,5,n)[0]),('authored body',bodies[n]),('protected effect',effects[n])]):
    pic=rgba(z,words).crop((112,112,208,208)).resize((384,384),Image.Resampling.NEAREST);sheet.paste(pic,(ix*384,iy*400+16),pic);draw.text((ix*384+4,iy*400+3),f'{n} {tag}',fill='white')
  sheet.save(O/f'{form}_separation_{page:02}.png')
j={'source':rel(P),'source_sha256':sha(arc),'historical_verification':rel(H/'assembled_rise_burst_thrust_dashslash/verification.json'),'historical_verification_sha256':sha((H/'assembled_rise_burst_thrust_dashslash/verification.json').read_bytes()),'refs':rows,'baseline_arc_sha256':sha(baseline),'exact_translation_matches':matches,'runtime_verified':False,'scope':'당시 승인된 우리 캐릭터 원화에서 구체 합성 전 몸체를 복원하고 구체 원픽셀을 재합성해 최신9표시를 정확히 재현한다. 효과는 imagegen 입력에서 제외한다.'}
(O/'inventory.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'rows':[{k:r[k]for k in('ref','body_bbox','effect_pixels','effect_over_body_pixels','tile_count','shared_refs')}for r in rows],'exact_matches':matches},ensure_ascii=False))
