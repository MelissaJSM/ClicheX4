from inspect_fit import *
def run():
 a=np.load(D/'base_sample.npz')['pixels'];h,w=a.shape
 safe=[original(n)[2] for n in BODY[2:]];best=None;winner=None
 for by in range(-25,-14):
  for bx in range(-25,-14):
   canvas=np.zeros((192,192),np.uint8);canvas[96+by:96+by+h,96+bx:96+bx+w]=a
   poses=[np.array(Image.fromarray(canvas).rotate(i*45,Image.Resampling.NEAREST,center=(96,96))) for i in range(8)]
   coords=[np.nonzero(p) for p in poses]
   for y in range(-4,5):
    for x in range(-4,5):
     bads=[int(np.count_nonzero(~s[yy+y,xx+x])) for (yy,xx),s in zip(coords,safe)]
     choice=(sum(bads)*10000+abs(x)+abs(y)+abs(bx+20)+abs(by+20),bx,by,x,y,bads)
     if best is None or choice<best:best=choice;winner=poses
 print(best);np.savez(D/'rotations.npz',**{str(n):np.roll(np.roll(p,best[4],0),best[3],1) for n,p in zip(BODY[2:],winner)})
 (D/'pivot.json').write_text(json.dumps({'base_position':list(best[1:3]),'translation':list(best[3:5]),'outside':best[5]}),'utf8')
if __name__=='__main__':run()
