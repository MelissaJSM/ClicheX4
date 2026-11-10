from fit_ground import *
im=Image.open(D/'generated_lunge_v3.png');worlds={};records=[]
scale=float(sys.argv[1]) if len(sys.argv)>1 else .13
for k,(x,y,x1,y1) in enumerate([(0,0,768,550),(768,0,1536,550),(0,550,768,1024),(768,550,1536,1024)]):
 a,head=normalize(im.crop((x,y,x1,y1)),scale);h,w=a.shape
 tx=-30-head[0];ty=24-h;world=np.zeros((192,192),dtype=np.uint8);world[96+ty:96+ty+h,96+tx:96+tx+w]=a
 worlds[k]=world;records.append({'frame':k,'head_world':[tx+head[0],ty+head[1]],'size':[w,h],
 'foot_y':int(np.nonzero(world)[0].max()-96),'outside':{n:int(np.count_nonzero((world!=0)&~geometry[n][2])) for n in (111,113,115,117,119,121,123,125,127)},
 'components':[len(c) for c in component(world!=0)]})
review(worlds,records,D/'lunge_fit_review.png');np.savez(D/'lunge_worlds.npz',**{str(n):w for n,w in worlds.items()});(D/'lunge_registration.json').write_text(json.dumps(records,indent=2));print(json.dumps(records))
