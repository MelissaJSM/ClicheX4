from pack_arrival import *
td=D/'joint_targets01';m=read(td/'manifest.json');a=Archive((ROOT/m['parent_arc']).read_bytes())
for n in (133,134,135,136,137):
 z=np.array(Image.open(td/f'layer5_{n:03}.png'));ys,xs=np.nonzero(z);found=[]
 for ref in range(composition_frame(a.c,5,0)['bank_frame_count']):
  rr=records(a.c,5,ref);parts=list(struct.iter_unpack('<BBbb',rr))
  if not 1<=len(parts)<=3 or any(fl or t in(0,16)for fl,t,x,y in parts) or len({p[1]for p in parts})!=len(parts):continue
  cover=np.zeros(z.shape,bool)
  for fl,t,x,y in parts:cover[160+y:176+y,160+x:176+x]=True
  if (cover|~(z>0)).all():found.append({'ref':ref,'parts':parts,'record':rr.hex()})
 print(json.dumps({'target':n,'bbox':[int(xs.min()-160),int(ys.min()-160),int(xs.max()-160),int(ys.max()-160)],'candidates':found[:30]}))
