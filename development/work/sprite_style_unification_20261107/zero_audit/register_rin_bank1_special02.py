"""새 원화의 눈 표본을 보존하고 뇌신격 검기 접점을 비교한다."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
D=Path(__file__).parent/'rin_extension';A=D/'bank1_special02';O=D/'bank1_special02_registered_v1';assert not O.exists();O.mkdir()
sha=lambda b:hashlib.sha256(b).hexdigest();info=json.loads((A/'inputs.json').read_text('utf8'));arc=(ROOT/info['actual_input_arc']).read_bytes();assert sha(arc)==info['archive_sha256'];pal=info['palette_words'];black=struct.unpack_from('<16H',entry(arc,9),13*32);fxpal=struct.unpack_from('<16H',entry(arc,9),5*32)
probe=json.loads((A/'anchor_probe_v1/registration.json').read_text('utf8'));timeline=json.loads((D/'bank1_special228_review/report.json').read_text('utf8'))
rows=[];items={k:[]for k in('normal','black')};effects={k:[]for k in items};contacts=[]
def roi(a,box,values):
 x0,y0,x1,y1=box;yy,xx=np.where(np.isin(a[y0:y1,x0:x1],values));return {'bbox':[int(xx.min()+x0),int(yy.min()+y0),int(xx.max()+x0+1),int(yy.max()+y0+1)]if len(xx)else None,'pixels':len(xx)}
for f in info['frames']:
 n=f['ref'];src=A/'anchor_probe_v1'/f'b1_{n:03}_indices.png';a=np.array(Image.open(src));z=a.copy();ops=[]
 if n==119:
  vote=next(q for q in probe['119_eye_vote_candidates']if q['xy']==[135,154]);assert vote=={'xy':[135,154],'cyan_weight':92,'winner':3,'winner_weight':99};assert a[154,135]==3
  z[154,135]=15;ops.append({'operation':'semantic_eye_palette_vote','xy':[135,154],'before':3,'after':15,'source_cyan_weight':92,'winner_weight':99,'source_cell':[22,50],'reason':'원화의 청록 눈을 양자화 다수결이 남색 윤곽으로 바꾼 한 셀만 실제 원화 색상 표본으로 보존'})
 p=O/f'b1_{n:03}_indices.png';Image.fromarray(z).save(p);old=render(arc,1,5,n)[0]
 for name,words in [('normal',pal),('black',black)]:items[name].extend([(f'b1 {n} old',rgba(old,words)),(f'b1 {n} new',rgba(z,words))])
 pairs=list(dict.fromkeys((r['body'],r['effect'])for ts in timeline['timelines'].values()for r in ts if r['body']==n))
 for nn,e in pairs:
  fx=render(arc,1,5,e)[0]
  for name,words in [('normal',pal),('black',black)]:
   for label,b in [('old',old),('new',z)]:
    im=rgba(b,words);im.alpha_composite(rgba(fx,fxpal));effects[name].append((f'{nn}+{e} {label}',im))
 rows.append({'key':f'b1_{n:03}','bank':1,'ref':n,'source_native':str(src.relative_to(ROOT)),'source_native_sha256':sha(src.read_bytes()),'whole_translation':next(q['translation']for q in probe['records']if q['key']==f'b1_{n:03}'),'operations':ops,'output_sha256':sha(p.read_bytes()),'old_head_override':False,'manually_invented_colors':False})
 contacts.append({'ref':n,'hand_roi':[110,156,135,168],'old_cuff':roi(old,[110,156,135,168],[8,9,10,11]),'new_cuff':roi(z,[110,156,135,168],[8,9,10,11]),'old_wrist_skin':roi(old,[110,156,135,168],[12,13,14]),'new_wrist_skin':roi(z,[110,156,135,168],[12,13,14]),'effect_pairs':pairs,'old_floor':int(np.where(old>0)[0].max()),'new_floor':int(np.where(z>0)[0].max())})
for name,words in [('normal',pal),('black',black)]:
 page(items[name],rgba(render(arc,0,0,147)[0],words),O/(name+'_comparison.png'),cols=2,scale=5)
 page(effects[name],rgba(render(arc,0,0,147)[0],words),O/(name+'_effects_comparison.png'),cols=2,scale=5)
 frames=[np.array(Image.open(O/f'b1_{n:03}_indices.png'))for n in(108,110,112,119)];board=Image.new('RGB',(840,4*240),'#64717b');dr=ImageDraw.Draw(board)
 for i,n in enumerate((108,110,112,119)):
  for j,(label,b)in enumerate([('old',render(arc,1,5,n)[0]),('new',frames[i])]):
   p=rgba(b,words).crop((112,150,147,168)).resize((420,216),Image.Resampling.NEAREST);board.paste(p,(j*420,i*240+20),p);dr.text((j*420+4,i*240+3),f'{n} {label} ROI112,150..147,168',fill='white')
 board.save(O/(name+'_hand_detail.png'))
(O/'registration.json').write_text(json.dumps({'source_arc_sha256':sha(arc),'source_generated_sha256':sha((A/'generated.png').read_bytes()),'records':rows,'scope':'뇌신격 낮은 찌르기4원화와 원래 전신이 정확 같은 사본8참조. 새 머리·옷·손발을 고정배율로 등록하며 눈119 한 셀은 실제 원화 청록 표본을 보존한다. 원검기/시간표/팔레트는 유지한다.','runtime_verified':False,'user_accepted':False},ensure_ascii=False,indent=2)+'\n','utf8')
(O/'contacts.json').write_text(json.dumps({'records':contacts,'native_timeline_evidence':str((D/'bank1_special228_review/report.json').relative_to(ROOT)),'effect_palette':5,'runtime_verified':False},ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(contacts))
