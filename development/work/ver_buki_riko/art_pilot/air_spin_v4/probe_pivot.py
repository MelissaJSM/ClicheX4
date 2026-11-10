from inspect_fit import *
def run():
 a=np.load(D/'base_sample.npz')['pixels'];h,w=a.shape
 safe=[original(n)[2] for n in BODY[2:]];best=None;winner=None
 for cy,cx in ((96,96),(96.5,96.5),(96,96.5),(96.5,96)):
  for by in range(-23,-14):
   for bx in range(-23,-14):
    canvas=np.zeros((192,192),np.uint8);canvas[96+by:96+by+h,96+bx:96+bx+w]=a
    poses=[np.array(Image.fromarray(canvas).rotate(i*45,Image.Resampling.NEAREST,center=(cx,cy))) for i in range(8)]
    bads=[int(np.count_nonzero((p!=0)&~s)) for p,s in zip(poses,safe)]
    choice=(sum(bads)*10000+abs(bx+16)+abs(by+17),bx,by,cx,cy,bads)
    if best is None or choice<best:best=choice;winner=poses
 print(best);np.savez(D/'rotations.npz',**{str(n):p for n,p in zip(BODY[2:],winner)})
 (D/'pivot.json').write_text(json.dumps({'base_position':list(best[1:3]),'translation':[0,0],'pivot_world':[best[3]-96,best[4]-96],'outside':best[5]}),'utf8')
if __name__=='__main__':run()
