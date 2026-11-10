"""Inspect/recover original Frost source skin shades; no generated artwork."""
from prepare_review import *
from scripts.prepare_nana_pilot import normalize
from src.psx_player import composition_frame,decode_stream,bank_offsets,indexed_atlas
from src.psx_sprite_batch import pack_original_layout
from src.psx_compress import encode_stream,replace_stream
from src.psx_bank_repack import repack_graphics_bank
from scripts.prepare_riko_ui import replace_entry

def merged(arc,n,mask=15):
 a=arc.layer(n)[0].copy()
 for bit,b in((8,8),(1,5),(4,7),(2,6)):
  if mask&bit:
   layer=arc.layer(n,b)[0];a[layer>0]=layer[layer>0]
 return a
def largest(alpha):
 seen=np.zeros(alpha.shape,bool);groups=[];h,w=alpha.shape
 for sy,sx in zip(*np.nonzero(alpha)):
  if seen[sy,sx]:continue
  stack=[(int(sy),int(sx))];seen[sy,sx]=True;pts=[]
  while stack:
   y,x=stack.pop();pts.append((y,x))
   for dy in(-1,0,1):
    for dx in(-1,0,1):
     yy,xx=y+dy,x+dx
     if 0<=yy<h and 0<=xx<w and alpha[yy,xx]and not seen[yy,xx]:seen[yy,xx]=True;stack.append((yy,xx))
  groups.append(pts)
 return max(groups,key=len)
def main():
 assert digest(SOURCE)==SHA
 with SOURCE.open('rb')as f:
  d=DiscReader(f,SOURCE.stat().st_size);rs={r['name'].split(';')[0]:r for r in d.inspect()['files']};data={n:d.read(rs[n]['lba'],rs[n]['size'])for n in('PL00_U.ARC','PL02_U.ARC')}
 force,ult=Archive(data['PL00_U.ARC']),Archive(data['PL02_U.ARC']);src=ROOT/'work/ver_rin_nana/nana_ultimate_armor/frost_pose_v2/generated.png';assert digest(src)=='4a95d1d239a467eb10b96967207bca8a09fae15d4b09a9c122dae950299817fd'
 im=Image.open(src).convert('RGBA');pix=np.array(im);pts=largest(pix[:,:,3]>=192);mask=np.zeros(pix.shape[:2],bool)
 for y,x in pts:mask[y,x]=True
 pix[~mask,3]=0;sy,sx=np.nonzero(mask);box=(int(sx.min()),int(sy.min()),int(sx.max()+1),int(sy.max()+1));crop=Image.fromarray(pix).crop(box);assert crop.size==(560,804)
 rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in ult.words[16:32]],np.int32);v=normalize(crop,52,rgb,width=36);authored=np.zeros((384,384),np.uint8);authored[128:180,141:177]=v
 target=merged(ult,95);accepted=merged(force,95);yy,xx=np.indices(target.shape);lower=yy>=157
 alpha=target>0;inner=alpha.copy()
 for dy in(-1,0,1):
  for dx in(-1,0,1):inner&=np.roll(np.roll(alpha,dy,axis=0),dx,axis=1)
 wrong=lower&np.isin(accepted,(10,11,12,13))&np.isin(target,(1,2,3,4,14,15))&inner
 source_skin=np.isin(authored,(10,11,12,13))&lower;coords=np.argwhere(source_skin);new=target.copy();changes=[]
 for y,x in np.argwhere(wrong):
  # Nearest already-authored flesh shade, with reproducible source coordinate.
  dist=((coords-[y,x])**2).sum(1);sy,sx=coords[int(dist.argmin())];new[y,x]=authored[sy,sx]
  changes.append({'world':[int(x-160),int(y-160)],'before':int(target[y,x]),'after':int(new[y,x]),'authored_world':[int(sx-160),int(sy-160)],'distance_squared':int(dist.min())})
 out=OUT/'frost';out.mkdir(exist_ok=True);index=Image.fromarray(new);index.save(out/'candidate_095_indices.png');Image.fromarray(authored).save(out/'authored_095_indices.png');Image.fromarray((wrong*255).astype(np.uint8)).save(out/'material_mask.png')
 rows=[('current/reference',[('idle',ult.composite(0,15)[0]),('current95',ult.composite(95,15)[0]),('force95',force.composite(95,15)[0]),('authored before coverage',ult.rgba(authored,16))]),('candidate existing shades',[('idle',ult.composite(0,15)[0]),('95 corrected',ult.rgba(new,16)),('95 unchanged alpha',ult.rgba(np.where(alpha,1,0).astype(np.uint8),16))])]
 grid(rows,out/'material_review.png',5)
 write(out/'material.json',{'parent_sha256':SHA,'source_image':src.relative_to(ROOT).as_posix(),'source_sha256':digest(src),'registered_png': 'work/ver_rin_nana/nana_ultimate_armor/elemental_packed_v1/ultimate_095.png','source_crop':box,'source_size':[36,52],'source_placement_world':[-19,-32],'changed_count':len(changes),'changes':changes,'method':'only dark interior where current Fourth skin mask agrees; nearest existing authored skin shade','alpha_unchanged':bool(np.array_equal(new>0,target>0)),'exterior_unchanged':bool(np.array_equal(new[~inner],target[~inner])),'new_art_generated':False})
 # The 26-pixel diagnostic leaves a jagged black interior because the Fourth
 # leg bends differently. Register the authored right calf by scanline instead.
 revised=target.copy();changes2=[]
 def runs(row):
  xs=np.flatnonzero(row);return []if not len(xs)else np.split(xs,np.flatnonzero(np.diff(xs)>1)+1)
 for y in range(160,176):
  dr=runs(target[y]>0)[-1];sr=runs(authored[y]>0)[-1];skin=sr[np.isin(authored[y,sr],(10,11,12,13))]
  assert len(skin)>0 and len(dr)>=3
  for x in dr[1:-1]:
   if target[y,x]not in(1,2,3,4):continue
   fraction=(int(x)-int(dr[0]))/(int(dr[-1])-int(dr[0]));sx0=round(int(sr[0])+fraction*(int(sr[-1])-int(sr[0])));sx=int(skin[np.abs(skin-sx0).argmin()]);revised[y,x]=authored[y,sx]
   changes2.append({'world':[int(x-160),int(y-160)],'before':int(target[y,x]),'after':int(revised[y,x]),'authored_world':[sx-160,y-160],'target_leg_span_world':[int(dr[0])-160,int(dr[-1])-160],'authored_leg_span_world':[int(sr[0])-160,int(sr[-1])-160]})
 Image.fromarray(revised).save(out/'candidate_v2_095_indices.png')
 grid([('before',[('idle',ult.composite(0,15)[0]),('95 current',ult.composite(95,15)[0]),('authored native size',ult.rgba(authored,16))]),('right calf existing shades',[('idle',ult.composite(0,15)[0]),('95 revised',ult.rgba(revised,16)),('alpha exact',ult.rgba(np.where(alpha,1,0).astype(np.uint8),16))])],out/'material_review_v2.png',5)
 write(out/'material_v2.json',{'parent_sha256':SHA,'source_sha256':digest(src),'reused_authored_indexed_sha256':sha(authored.tobytes()),'changed_count':len(changes2),'changes':changes2,'method':'right-leg scanline registration using existing generated-source flesh indices; dark interior only, world Y0..15; silhouette row endpoints and boots unchanged','alpha_unchanged':bool(np.array_equal(revised>0,target>0)),'new_art_generated':False,'diagnostic_v1_rejected':'Fourth skin mask follows another bend and leaves dark speckling; v2 uses this same pose source'})
 print(json.dumps({'changed':len(changes),'bbox':box,'source_range':sorted(set(q['after']for q in changes))}),flush=True)
if __name__=='__main__':main()
