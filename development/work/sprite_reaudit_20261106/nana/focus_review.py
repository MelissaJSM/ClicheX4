"""Read-only Nana detail sheets and material-layer comparisons."""
from prepare_review import *

def components(im):
 a=np.asarray(im)[:,:,3]>0;seen=set();groups=[]
 for y,x in zip(*np.nonzero(a)):
  p=(int(x),int(y))
  if p in seen:continue
  stack=[p];seen.add(p);pts=[]
  while stack:
   xx,yy=stack.pop();pts.append([xx-160,yy-160])
   for dy in(-1,0,1):
    for dx in(-1,0,1):
     nx,ny=xx+dx,yy+dy;q=(nx,ny)
     if 0<=nx<384 and 0<=ny<384 and a[ny,nx] and q not in seen:seen.add(q);stack.append(q)
  groups.append(pts)
 return sorted(groups,key=len,reverse=True)

def main():
 assert digest(SOURCE)==SHA
 with SOURCE.open('rb')as f:
  d=DiscReader(f,SOURCE.stat().st_size);rs={r['name'].split(';')[0]:r for r in d.inspect()['files']if not r['directory']};assets={n:d.read(rs[n]['lba'],rs[n]['size'])for n in('PL00_U.ARC','PL02_U.ARC')}
 a=Archive(assets['PL00_U.ARC']);u=Archive(assets['PL02_U.ARC']);out=OUT/'focus';out.mkdir(exist_ok=True);sheets=[];small=[];diff=[]
 for ref in range(237):
  if ref in(105,*range(175,183)):continue
  for mask in range(16):
   x=a.composite(ref,mask,1)[0];y=a.composite(ref,mask,2)[0]
   if x.tobytes()!=y.tobytes():diff.append([ref,mask])
 for num,refs in enumerate(([0,120,121],[122,123,124],[125,141,142],[0,156,157])):
  rows=[]
  for ref in refs:
   rows.append((f'ref {ref}',[(f'mask {m:X}',a.composite(ref,m)[0])for m in(0,2,8,15)]))
   for mask in(0,1,2,4,8,15):
    im=a.composite(ref,mask)[0];cs=components(im)
    small.append({'ref':ref,'mask':mask,'largest_size':len(cs[0])if cs else 0,'small_components':[c for c in cs if len(c)<=6]})
  sheets.append(grid(rows,out/f'partial_fragments_{num:02}.png',4))
 for name,refs in [('sleeves',[0,85,2,12,26,62]),('ladder_legs',[0,144,145,146,148,150]),('face_special',[0,95,98,100,104,231])]:
  rows=[(label,[(str(ref),arc.composite(ref,mask)[0])for ref in refs])for label,arc,mask in [('base',a,0),('fourth',a,15),('ultimate jacket',u,15),('ultimate swimsuit',u,0)]]
  sheets.append(grid(rows,out/f'{name}.png',4))
 # Reflow existing strips only; preserve every source pixel and label.
 for name,cols,per in [('selection_all',26,7),('save_all',16,8)]:
  src=Image.open(OUT/f'{name}.png');cw=src.width//cols
  for start in range(0,cols,per):
   p=out/f'{name}_{start//per:02}.png';src.crop((start*cw,0,min(cols,start+per)*cw,src.height)).save(p);sheets.append({'path':p.relative_to(ROOT).as_posix(),'source':f'{name}.png','original_columns':[start,min(cols,start+per)]})
 result={'source_sha256':SHA,'armtype_combinations_compared':228*16,'arm1_arm2_differences':diff,'sheets':sheets,'small_components':small,'new_art_pixels':False,'runtime_verified':False}
 write(OUT/'focus_manifest.json',result);assert digest(SOURCE)==SHA
 print(json.dumps({'armtype_differences':diff,'sheets':len(sheets)},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
