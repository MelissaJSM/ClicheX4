"""Nana PL00 214의 원효과/역사합성 출처만 독립 읽기. 제작 함수 미호출."""
from pathlib import Path
import hashlib,json,struct,sys
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent;O=D/'nana_base_nova214_relations01';assert not O.exists();sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
from src.psx_player import composition_frame,decode_stream,indexed_atlas,compose_indices
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();inputs={};PBS=(0,5,6,7,8)
def read(p):
 b=p.read_bytes();inputs[rel(p)]=sha(b);return b
def bounds(z):
 y,x=np.nonzero(z);return None if not len(x)else[int(x.min()-160),int(y.min()-160),int(x.max()-159),int(y.max()-159)]
def coords(z):
 y,x=np.nonzero(z);return[[int(a-160),int(b-160)]for a,b in zip(x,y)]
def signature(p):return[p['flags'],p['tile'],p['x'],p['y']]
oldpath=ROOT/'work/overhaul_20261105/sprites/ver_rin_nana/baseline/PL00_U.ARC'
packedpath=ROOT/'work/overhaul_20261105/ui/nana_fourth_nova_v1/PL00_U.ARC'
currentpath=W/'root_nana_hover/packed_hover_final01/PL00_U.ARC'
old=Archive(read(oldpath));historic=Archive(read(packedpath));cur=Archive(read(currentpath));usdata=read_disc(ROOT/'MegaMan X4.bin',('PL00_U.ARC',))[0]['PL00_U.ARC'];us=Archive(usdata)
for path in ['scripts/overhaul_ui_nova_pack.py','scripts/overhaul_ui_nova_art.py','work/overhaul_20261105/ui/nana_fourth_nova_v1/proposal.json','work/overhaul_20261105/ui/nana_fourth_nova_v1/verification.json']:read(ROOT/path)
arc_mask=(old.layer(213,0)[0]==0)&(old.layer(214,0)[0]>0)
native_mask=(us.layer(213,0)[0]==0)&(us.layer(214,0)[0]>0)
derived=cur.layer(213,0)[0].copy();derived[arc_mask]=old.layer(214,0)[0][arc_mask]
rows=[]
for tag,a in [('original_US',us),('C04_parent',old),('C04_packed',historic),('latest',cur)]:
 layers=[]
 for b in PBS:
  x,y=a.layer(213,b)[0],a.layer(214,b)[0];layers.append({'bank':b,'differences':int((x!=y).sum()),'difference_box':bounds(x!=y),'indices213':np.unique(x[x>0]).tolist(),'indices214':np.unique(y[y>0]).tolist(),'parts213':composition_frame(a.c,b,213)['parts'],'parts214':composition_frame(a.c,b,214)['parts']})
 rows.append({'source':tag,'sha256':sha(a.data),'layers':layers})
currentproof=[]
for n in(213,214):
 for b in PBS:currentproof.append({'ref':n,'bank':b,'current_to_C04_packed_exact':bool(np.array_equal(cur.layer(n,b)[0],historic.layer(n,b)[0])),'C04_parent_to_US_exact':bool(np.array_equal(old.layer(n,b)[0],us.layer(n,b)[0]))})
pp=composition_frame(us.c,0,214)['parts'];s213=[signature(p)for p in composition_frame(us.c,0,213)['parts']];f=us.banks[0]['frames'][214];raw=decode_stream(us.g,f['offset'],f['limit'],f['tile_count']*128).data;atlas=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256);contrib=[]
from src.psx_static_effect import compose_static
from src.psx_ui_atlas import local_composition
for p in pp:
 b,sz,bb,_=compose_indices(raw,f['tile_count'],local_composition({'parts':[p]}));z=np.zeros((384,384),np.uint8);z[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]=np.frombuffer(b,np.uint8).reshape(sz[1],sz[0]);m=z>0
 t=p['tile'];v=atlas[(t//16)*16:(t//16+1)*16,(t%16)*16:(t%16+1)*16]
 contrib.append({'part':p,'same_record_in213':signature(p)in s213,'opaque':int(m.sum()),'native_outer_mask_contribution':int((m&native_mask).sum()),'outside_native_outer_mask':int((m&~native_mask).sum()),'world_bbox':bounds(m),'indices':np.unique(z[m]).tolist(),'tile_full256_sha256':sha(v.tobytes())})
overlay_details={}
for b in PBS[1:]:
 a,z=cur.layer(213,b)[0],cur.layer(214,b)[0];diff=a!=z
 overlay_details[str(b)]={'difference_cells':int(diff.sum()),'all_difference_inside_historical_arc_mask':bool(np.all(~diff|arc_mask)),'214_equals213_with_arc_removed':bool(np.array_equal(z,np.where(arc_mask,0,a))),'changed_cells':[{'xy':xy,'old':int(a[xy[1]+160,xy[0]+160]),'new':int(z[xy[1]+160,xy[0]+160])}for xy in coords(diff)]}
O.mkdir(exist_ok=False);images=[]
def sheet(name,items,cols=4):
 box=(127,125,198,190);cw,ch=365,355;out=Image.new('RGB',(cols*cw,((len(items)+cols-1)//cols)*ch),'#253044');dr=ImageDraw.Draw(out)
 for i,(title,pic)in enumerate(items):
  x,y=i%cols*cw,i//cols*ch;im=pic.crop(box).resize((355,325),Image.Resampling.NEAREST);out.paste(im,(x+5,y+25),im);dr.text((x+5,y+3),title,fill='white')
 p=O/name;out.save(p);images.append({'path':rel(p),'sha256':sha(p.read_bytes())})
sheet('source_comparison.png',[(f'{tag} ref{n}',a.composite(n,0)[0])for n in(213,214)for tag,a in(('US',us),('C04 parent',old),('C04 packed',historic),('current',cur))])
sheet('effect_and_layers.png',[('US214 outer mask',us.rgba(np.where(native_mask,us.layer(214,0)[0],0))),('current213',cur.composite(213,0)[0]),('current214',cur.composite(214,0)[0]),('Fourth214',cur.composite(214,15)[0])]+[(f'US214 part{p["part"]["index"]} tile{p["part"]["tile"]}',us.rgba(np.where(native_mask,us.layer(214,0)[0],0)))for p in[]])
report={'scope':'Nana 기본/포스214의213대비119/34차이 출처만 읽기','archive_layers':rows,'C04_and_current_identity':currentproof,'historical_arc_rule':{'mask_pixels':int(arc_mask.sum()),'mask_bbox':bounds(arc_mask),'mask_indices':np.unique(old.layer(214,0)[0][arc_mask]).tolist(),'US_mask_exact':bool(np.array_equal(arc_mask,native_mask)),'US_values_exact':bool(np.array_equal(old.layer(214,0)[0][arc_mask],us.layer(214,0)[0][arc_mask])),'current214_reconstructed_from_current213_exact':bool(np.array_equal(derived,cur.layer(214,0)[0])),'current_body_overwritten_by_arc':int((arc_mask&(cur.layer(213,0)[0]>0)).sum()),'current_added_alpha_by_arc':int((arc_mask&(cur.layer(213,0)[0]==0)).sum()),'source_coords':coords(arc_mask)},'original214_parts':contrib,'overlay_derivation':overlay_details,'sheets':images,'actually_viewed':False,'new_MIPS_or_game_run':False,'source_or_candidate_changed':False,'producer_functions_called':False,'inputs':inputs}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'report_sha256':sha((O/'report.json').read_bytes()),'arc':{k:v for k,v in report['historical_arc_rule'].items()if k!='source_coords'},'parts':[{k:v for k,v in q.items()if k!='part'}|{'index':q['part']['index'],'tile':q['part']['tile']}for q in contrib],'overlays':{k:{kk:vv for kk,vv in v.items()if kk!='changed_cells'}for k,v in overlay_details.items()},'identities':currentproof}))
