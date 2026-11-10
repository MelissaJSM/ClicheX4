"""국소 생성 원화의 파란 가죽 색인만 원래 새 신발 내부에 등록한다."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).parent;ROOT=D.parents[2];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_run import quantize
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import rgba,render
R=D/'rin_extension';S=R/'burst_shoe_edit01';A=R/'burst_charge01';P=R/'burst_charge_registered_v1';O=R/'burst_charge_registered_v2';O.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'));info=read(A/'inputs.json');oldreg=read(P/'registration.json');arc=(ROOT/info['source_arc']).read_bytes();pal=struct.unpack_from('<16H',entry(arc,9));colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in pal[1:]],np.int32)
assert sha(S/'generated.png')=='ddd35dc51e12faa45cfb4048c7ab17798b0058bcbe5bd463b673220b47a62069'
im=Image.open(S/'generated.png').convert('RGBA');assert im.size==(1536,1024);full=quantize(im,colors,1/8);rows=[];outputs={};Y,X=np.indices((384,384))
for rec in info['masters']:
 n=rec['ref'];cx,cy=rec['cell'];x0,y0,x1,y1=rec['world_crop'];z=np.zeros((384,384),np.uint8);z[y0:y1,x0:x1]=full[cy*64:(cy+1)*64,cx*96:(cx+1)*96]
 base=np.array(Image.open(P/f'b1_{n:03}_body_indices.png'));r=next(r for r in oldreg['records']if r['ref']==n);dx,dy=r['whole_body_translation'];z=np.roll(np.roll(z,dy,0),dx,1)
 # y173 is a conservative lower-shoe region in the pre-translation source.
 # Only blue leather source texels replace the old dark/desaturated interior.
 # Existing dark outline1, white highlight9..11, all alpha and body geometry remain.
 eligible=(Y>=173+dy)&(X>=130)&(X<193)&np.isin(base,(2,3,4,7,8))&np.isin(z,(4,5,6))
 result=base.copy();result[eligible]=z[eligible];changed=result!=base;assert changed.any() and np.array_equal(result>0,base>0)
 assert np.array_equal(result[~eligible],base[~eligible]);assert np.array_equal(result[base==1],base[base==1]);assert np.array_equal(result[np.isin(base,(9,10,11))],base[np.isin(base,(9,10,11))])
 changes=[{'world':[int(x),int(y)],'old_index':int(base[y,x]),'generated_index':int(z[y,x])}for y,x in np.argwhere(changed)]
 Image.fromarray(result).save(O/f'b1_{n:03}_body_indices.png');Image.fromarray((eligible*255).astype(np.uint8)).save(O/f'b1_{n:03}_source_mask.png');fx=np.array(Image.open(R/'burst_remaining_probe01'/f'b1_{n:03}_effect_indices.png'));combined=result.copy();combined[fx>0]=fx[fx>0];Image.fromarray(combined).save(O/f'b1_{n:03}_combined_indices.png');outputs[n]=(base,result)
 rows.append({'ref':n,'input_body_sha256':sha(P/f'b1_{n:03}_body_indices.png'),'generated_whole_canvas_scale':1/8,'same_whole_body_translation':[dx,dy],'source_color_cells':changes,'changed_pixels':int(changed.sum()),'alpha_and_geometry_exact':True,'dark_outer_contour_and_white_highlights_exact':True,'target_sha256':sha(O/f'b1_{n:03}_body_indices.png'),'combined_sha256':sha(O/f'b1_{n:03}_combined_indices.png')})
for form,row in [('normal',0),('black',13)]:
 words=struct.unpack_from('<16H',entry(arc,9),row*32);sheet=Image.new('RGB',(1440,1600),'#263142');dr=ImageDraw.Draw(sheet)
 for iy,n in enumerate(outputs):
  for ix,(tag,a)in enumerate([('idle147',render(arc,0,0,147)[0]),('v1 gray leather',outputs[n][0]),('v2 generated blue leather',outputs[n][1])]):
   p=rgba(a,words).crop((112,112,208,188)).resize((480,380),Image.Resampling.NEAREST);sheet.paste(p,(ix*480,iy*400+20),p);dr.text((ix*480+4,iy*400+4),f'{n} {tag}',fill='white')
 sheet.save(O/f'{form}_comparison.png')
q={'generated_source_sha256':sha(S/'generated.png'),'previous_registration_sha256':sha(P/'registration.json'),'records':rows,'scope':'새 국소 원화의 실제 파란 신발색만 같은좌표 기존 새 신발 내부에 등록. 폴리곤 윤곽·알파·대기 원화·포즈·명암의 흰 하이라이트와 어두운 외곽은 유지. 원종아리나 옛신발을 복사하지 않는다.','runtime_verified':False,'user_accepted':False}
(O/'registration.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps([{'ref':r['ref'],'changed':r['changed_pixels']}for r in rows]))
