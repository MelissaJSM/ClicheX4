"""Register accepted new Rin keys; preserve native animation and unrelated references."""
from pathlib import Path
from collections import defaultdict
import sys,json,hashlib,struct,importlib.util
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent;OUT=D/'rin_extension/prepared_keys_v1';ART=ROOT/'work/sprite_style_unification_20261107/rin/locomotion01'
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.overhaul_sprites_audit import render,rgba
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices,indexed_atlas,bank_offsets
from src.psx_frame_edit import frame_coverage
spec=importlib.util.spec_from_file_location('rear_packer',D/'riko_restore/pack_rear_head.py');packer=importlib.util.module_from_spec(spec);spec.loader.exec_module(packer)
SHA='e6dbffce1b3f3fa4842c4092c6a4de09109db1bd5569864d4959cb7ec92849e2';BINSHA='f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720';ARTSHA='a41a67e43c7d10b6ef02c865af57f33a71d655ee0957d54763d9f116c954b5cb';ALIASES={8:8,14:14,49:49,95:95,97:95,99:95,101:95}
PNG_HASHES={8:'499cdf9895eb564a034fea8ff2ee975277be5a23181b407cc095bb862b7b6f24',14:'ecb6a52e492b894c641ae8fc04470f8c4a156a99e9b2f941c72975bb6b5fc1b4',49:'a2c669bdfa333138a9b9a3927b6563fb5ee4cce19f4b0e189393f3a1288916e0',95:'4561f091bd515090c9c46f00e27e4b40848aaaff897075059e5358fef282261b'}
def sha(b):return hashlib.sha256(b).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def get_targets():
 need(sha((ART/'generated.png').read_bytes())==ARTSHA,'Authored image changed');info=json.loads((ART/'inputs.json').read_text('utf8'));need(info['archive_sha256']==SHA and info['source_sha256']==BINSHA,'Art source changed');reg=json.loads((ART/'native/registration.json').read_text('utf8'));need(reg['source_art_sha256']==ARTSHA and reg['scale']==.125,'Registration changed')
 for k,digest in PNG_HASHES.items():need(sha((ART/'native'/f'b0_{k:03d}_indices.png').read_bytes())==digest,'Registered native art changed')
 targets={n:np.array(Image.open(ART/'native'/f'b0_{k:03d}_indices.png'))for n,k in ALIASES.items()}
 for n,w in targets.items():need(w.shape==(384,384)and w.dtype==np.uint8 and w.max()<=15,'Invalid native image')
 return targets
def raster_safe(raw,tiles,cp):
 cov,sz,bb=frame_coverage(raw,tiles,cp);a=np.zeros((384,384),bool);a[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]=np.array([bool(v)for v in cov]).reshape(sz[1],sz[0]);return a
def fit_windows(parts,n,raw,tiles,target):
 cp=composition_frame(parts,0,n);bad=int(np.count_nonzero((target>0)&~raster_safe(raw,tiles,cp)));edits=[]
 if not bad:return parts,edits
 need(n in (8,49),'Unexpected uncovered frame')
 # First try a whole sampling row: the old head spans two adjoining tiles.
 row_candidates=[]
 rows=defaultdict(list)
 for p in cp['parts']:rows[p['y']].append(p)
 for row,ps in rows.items():
  for dx in range(-8,9):
   if not dx:continue
   trial=bytearray(parts)
   for p in ps:trial[p['record_offset']+2]=(p['x']+dx)&255
   cand=composition_frame(trial,0,n);cost=int(np.count_nonzero((target>0)&~raster_safe(raw,tiles,cand)))
   if cost:continue
   bb=compose_indices(raw,tiles,cand)[2];sz=(bb[2]-bb[0],bb[3]-bb[1]);want=target[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]
   try:packer.edit_visible_set(raw,tiles,[(cand,want.tobytes(),sz)])
   except ValueError:continue
   row_candidates.append(((abs(dx)*len(ps),abs(dx),row),bytes(trial),ps,dx))
 if row_candidates:
  _,trial,ps,dx=min(row_candidates,key=lambda q:q[0]);needed=list(ps)
  for p in ps:
   reduced=bytearray(trial);reduced[p['record_offset']+2]=p['x']&255;cand=composition_frame(reduced,0,n)
   if np.any((target>0)&~raster_safe(raw,tiles,cand)):continue
   _,sz,bb,_=compose_indices(raw,tiles,cand);want=target[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]
   try:packer.edit_visible_set(raw,tiles,[(cand,want.tobytes(),sz)])
   except ValueError:continue
   trial=bytes(reduced);needed.remove(p)
  return trial,[{'ref':n,'record_offset':p['record_offset'],'tile':p['tile'],'before':[p['x'],p['y']],'after':[p['x']+dx,p['y']]}for p in needed]
 for step in range(4):
  best=None
  for p in cp['parts']:
   _,_,oldbb,_=compose_indices(raw,tiles,cp);empty=not np.any(np.frombuffer(indexed_atlas(raw,tiles)[0],np.uint8).reshape(-1,256)[p['tile']//16*16:p['tile']//16*16+16,p['tile']%16*16:p['tile']%16*16+16]);missing=np.argwhere((target>0)&~raster_safe(raw,tiles,cp))
   dxs=range(-2,3)if not empty else sorted(set(int(x)-160-p['x']-k for y,x in missing for k in (0,1,8,15)))
   dys=range(-2,3)if not empty else sorted(set(int(y)-160-p['y']-k for y,x in missing for k in (0,1,8,15)))
   for dy in dys:
    for dx in dxs:
     if not(dx or dy):continue
     trial=bytearray(parts);trial[p['record_offset']+2]=(p['x']+dx)&255;trial[p['record_offset']+3]=(p['y']+dy)&255;cand=composition_frame(trial,0,n);cost=int(np.count_nonzero((target>0)&~raster_safe(raw,tiles,cand)))
     if cost>=bad:continue
     bb=compose_indices(raw,tiles,cand)[2];sz=(bb[2]-bb[0],bb[3]-bb[1]);want=target[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]
     try:packer.edit_visible_set(raw,tiles,[(cand,want.tobytes(),sz)])
     except ValueError:continue
     key=(cost,abs(dx)+abs(dy),abs(dy),p['record_offset'],dx,dy)
     if best is None or key<best[0]:best=(key,bytes(trial),p,dx,dy)
  need(best is not None,f'No lossless local window solution {n}')
  key,parts,p,dx,dy=best;edits.append({'ref':n,'record_offset':p['record_offset'],'tile':p['tile'],'before':[p['x'],p['y']],'after':[p['x']+dx,p['y']+dy]});cp=composition_frame(parts,0,n);bad=key[0]
  if bad==0:break
 need(bad==0,'Remaining uncovered authored pixels');return parts,edits
def build(arc,targets):
 need(sha(arc)==SHA,'Wrong source ARC');expected=get_targets();need(set(targets)==set(ALIASES),'Target selection')
 for n,w in targets.items():need(np.array_equal(w,expected[n]),'Target differs from registered new art')
 g,c=entry(arc,2),entry(arc,3);newc=c;bank=graphics_bank(g,0);windows=[];replacements={}
 for n in ALIASES:
  f=bank['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;newc,edits=fit_windows(newc,n,raw,f['tile_count'],targets[n]);windows+=edits
 for n in ALIASES:
  f=bank['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;cp=composition_frame(newc,0,n);_,sz,bb,_=compose_indices(raw,f['tile_count'],cp);w=targets[n];need(not np.any((w>0)&~raster_safe(raw,f['tile_count'],cp)),'Uncovered target');small=w[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]];new=packer.edit_visible_set(raw,f['tile_count'],[(cp,small.tobytes(),sz)]);a=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256);b=np.frombuffer(indexed_atlas(new,f['tile_count'])[0],np.uint8).reshape(-1,256)
  for p in cp['parts']:
   t=p['tile'];yy,xx=t//16*16,t%16*16
   if t%16==0:need(not np.any((a[yy:yy+16,xx]==0)&(b[yy:yy+16,xx]>0)),'New GPU first-column alpha')
   if p['flip_y']and t//16%16==0:need(not np.any((a[yy,xx:xx+16]==0)&(b[yy,xx:xx+16]>0)),'New GPU flipped-first-row alpha')
  replacements[n]=new
 ng,layout=packer.repack_raw(g,0,replacements);out=replace_entry(replace_entry(arc,2,ng),3,newc);need(replace_entry(replace_entry(out,2,g),3,c)==arc,'Other entries changed');need(bank_offsets(g,allow_aliases=True)==bank_offsets(ng,allow_aliases=True),'Bank boundaries');allowed={q['record_offset']+k for q in windows for k in (2,3)};need(all(i in allowed for i,(a,b)in enumerate(zip(c,newc))if a!=b),'Non-window composition change')
 counts={'raw':0,'display':0,'non_target_raw_exact':0,'non_target_display_exact':0};changes=[]
 for bi in (0,1):
  ob=graphics_bank(g,bi);nb=graphics_bank(ng,bi)
  for of,nf in zip(ob['frames'],nb['frames']):
   n=of['index'];is_target=bi==0 and n in targets;need(of['tile_count']==nf['tile_count']<=32,'Tile count');ar=decode_stream(g,of['offset'],of['limit'],of['tile_count']*128).data;br=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data;counts['raw']+=1
   if not is_target:need(ar==br,'Unrelated raw');need(composition_frame(c,bi*5,n)==composition_frame(newc,bi*5,n),'Unrelated composition');counts['non_target_raw_exact']+=1
   if bi==1 and 42<=n<=49:continue
   before=render(arc,bi,bi*5,n)[0];after=render(out,bi,bi*5,n)[0];want=targets[n]if is_target else before;need(np.array_equal(want,after),'Readback mismatch');counts['display']+=1
   if not is_target:counts['non_target_display_exact']+=1
   else:changes.append({'ref':n,'changed_pixels':int(np.count_nonzero(before!=after)),'alpha_added':int(np.count_nonzero((before==0)&(after>0))),'alpha_removed':int(np.count_nonzero((before>0)&(after==0)))})
 return out,{'counts':counts,'window_edits':windows,'bank_layout':layout,'changes':changes,'all_new_art_pixels_exact':True,'no_old_head_overlay':True,'original_palette_audio_effects_timing_exact':True,'native_tile_counts_preserved':True,'new_gpu_boundary_alpha':0}
def boards(arc,out):
 for name,row in [('normal',0),('black',13)]:
  pal=struct.unpack_from('<16H',entry(arc,9),row*32);ns=[147]+list(ALIASES);board=Image.new('RGB',(800,428*len(ns)),'#64717b');draw=ImageDraw.Draw(board)
  for y,n in enumerate(ns):
   for x,(label,a)in enumerate([('before',arc),('new art readback',out)]):
    im=rgba(render(a,0,0,n)[0],pal).crop((120,112,200,192)).resize((400,400),Image.Resampling.NEAREST);board.paste(im,(x*400,y*428+28),im);draw.text((x*400+5,y*428+6),f'{n} {label}',fill='white')
  board.save(OUT/f'{name}_readback.png')
  for page in range(2):board.crop((0,page*4*428,800,(page+1)*4*428)).save(OUT/f'{name}_readback_{page}.png')
def main():
 parent=ROOT/'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin';need(sha(parent.read_bytes())==BINSHA,'Parent BIN');arc=read_disc(parent,('PL01_U.ARC',))[0]['PL01_U.ARC'];targets=get_targets();out,proof=build(arc,targets);again,_=build(arc,targets);need(out==again,'Reproduction');reject=[]
 for case in ('parent','missing_ref','palette_16','body_pixel'):
  aa=arc;tt={n:v.copy()for n,v in targets.items()}
  if case=='parent':aa=bytes([arc[0]^1])+arc[1:]
  elif case=='missing_ref':tt.pop(97)
  elif case=='palette_16':tt[8][144,150]=16
  else:tt[49][180,150]^=1
  try:build(aa,tt)
  except ValueError as exc:reject.append({'case':case,'error':str(exc)})
  else:raise ValueError('Invalid input accepted')
 OUT.mkdir(exist_ok=True);(OUT/'PL01_U.ARC').write_bytes(out);boards(arc,out);report={'source_bin':str(parent.relative_to(ROOT)),'source_bin_sha256':BINSHA,'source_arc_sha256':SHA,'resource':str((OUT/'PL01_U.ARC').relative_to(ROOT)),'after_sha256':sha(out),'new_art_source_sha256':ARTSHA,'references':list(ALIASES),'authored_key_aliases':ALIASES,'verification':proof,'reproducible':True,'rejections':reject,'game_changed':False,'runtime_verified':False};(OUT/'proposal.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'after_sha256':sha(out),'proof':proof}))
if __name__=='__main__':main()
