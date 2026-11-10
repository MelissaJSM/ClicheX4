"""새 상체를 고정하고 재작화된 하체 및 한 픽셀 발 접점만 등록한다."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
D=Path(__file__).parent/'rin_extension';A=D/'followthrough_contacts_fix01';O=D/'followthrough_registered_v1';assert not O.exists();O.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
info=json.loads((A/'inputs.json').read_text('utf8'));P=ROOT/info['actual_input_arc'];arc=P.read_bytes();assert sha(P)==info['archive_sha256'];pal=info['palette_words'];black=struct.unpack_from('<16H',entry(arc,9),13*32)
assert sha(A/'generated.png')=='7e66e058b6c6ad73c2495e49c899501182f5dea2c7344ab5013ef6d5a8faeadc'
regions={'b1_146':(150,170,200,195),'b1_156':(154,167,175,195),'b1_158':(140,170,192,195),'b0_197':(138,162,165,191)}
contacts={'b1_146':[((159,180,174,190),(1,-1),False),((184,182,196,190),(-1,-1),False)],'b1_156':[((158,177,170,190),(1,1),True)],'b1_158':[((176,179,191,191),(-1,0),False)],'b0_197':[((143,175,155,190),(1,-1),False)]}
items={k:[]for k in('normal','black')};rows=[]
for f in info['frames']:
 key=f['key'];p=A/(key+'_source_indices.png');npth=A/'native_fixed'/(key+'_indices.png');base=np.array(Image.open(p));new=np.array(Image.open(npth));z=base.copy();x0,y0,x1,y1=regions[key];mask=np.zeros(z.shape,bool);mask[y0:y1,x0:x1]=True;z[mask]=new[mask];ops=[]
 for box,(dx,dy),keep in contacts[key]:
  x0,y0,x1,y1=box;cut=z[y0:y1,x0:x1].copy();z[y0:y1,x0:x1]=0;z[y0+dy:y1+dy,x0+dx:x1+dx]=cut
  if keep:z[y0,x0:x1]=cut[0]
  ops.append({'box':box,'translation':[dx,dy],'retain_source_top_seam_row':keep})
 assert np.array_equal(z[~mask],base[~mask]),key
 old=render(arc,f['bank'],f['bank']*5,f['ref'])[0];assert np.nonzero(z)[0].max()==np.nonzero(old)[0].max(),key
 out=O/(key+'_indices.png');Image.fromarray(z).save(out)
 for form,words in [('normal',pal),('black',black)]:
  pic=rgba(z,words);pic.save(O/(form+'_'+key+'.png'));items[form].extend([(key+' old',rgba(old,words)),(key+' long leg source',rgba(base,words)),(key+' corrected',pic)])
 rows.append({'key':key,'bank':f['bank'],'ref':f['ref'],'source_native':rel(p),'source_native_sha256':sha(p),'lower_source_native':rel(npth),'lower_source_native_sha256':sha(npth),'lower_region':regions[key],'contact_translations':ops,'output_sha256':sha(out),'old_bounds':rgba(old,pal).getbbox(),'new_bounds':rgba(z,pal).getbbox(),'floor_y':int(np.nonzero(z)[0].max()),'outside_lower_region_exact_from_new_upper_art':True,'old_head_or_body_override':False,'invented_color':False,'wholebody_scale':False})
for form,words in [('normal',pal),('black',black)]:page(items[form],rgba(render(arc,0,0,147)[0],words),O/(form+'_comparison.png'),cols=3,scale=5)
(O/'registration.json').write_text(json.dumps({'source_arc':rel(P),'source_arc_sha256':sha(P),'source_generated_sha256':sha(A/'generated.png'),'original_new_art_sha256':sha(D/'followthrough01/generated.png'),'records':rows,'scope':'용염인 준비/회복146156158 및 사다리진입197. 새 머리·손·상의 고정, 별도 재작화한 무릎/종아리/부츠를 국소 등록. 실제 발 접점은 같은 새 원화의 부츠1px 이동으로 정합.197=212 정확 사본 확대 예정.','candidate_only':True,'root_review_pending':True,'runtime_verified':False,'user_accepted':False},ensure_ascii=False,indent=2)+'\n','utf8');print(O)
