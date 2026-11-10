exec((__import__('pathlib').Path(__file__).with_name('fit_native.py')).read_text(encoding='utf-8').split("prior=json")[0])
im=Image.open(P/'run_source_10.png').convert('RGBA');a=np.array(im);scale=.14;h,w=math.ceil(im.height*scale),math.ceil(im.width*scale);head=np.array(Image.open(master))[:19,12:35];common=geometry[19][2];options=[]
for px in (.5,.25,.75,.125,.875):
 for py in (.5,.25,.75,.125,.875):
  xs=np.minimum(((np.arange(w)+px)/scale).astype(int),im.width-1);ys=np.minimum(((np.arange(h)+py)/scale).astype(int),im.height-1);pixels=a[ys[:,None],xs[None,:]];mask=pixels[:,:,3]>=128;rgb=pixels[:,:,:3].astype(np.int32);ix=np.zeros((h,w),dtype=np.uint8);ix[mask]=np.argmin(((rgb[mask,None]-colors[None])**2).sum(2),1)+1
  eyes=(ix==5)&(rgb[:,:,0]>rgb[:,:,1]+20)&(rgb[:,:,2]>rgb[:,:,0]+10)&(np.indices(ix.shape)[0]<h*.48);ey,ex=np.nonzero(eyes)
  if not len(ex):continue
  use=ey<=ey.min()+1;ex=ex[use];ey=ey[use];hx=round(ex.mean()-6);hy=round(ey.mean()-12.5);native=np.zeros((96,96),dtype=np.uint8);native[24:24+h,24:24+w]=ix;native[24:24+hy+19,24:50]=0;native[24+hy:24+hy+19,24+hx:24+hx+23]=head;yy,xx=np.nonzero(native);bx0,by0,bx1,by1=int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1);sprite=native[by0:by1,bx0:bx1];hh,ww=sprite.shape;lh=[24+hx-bx0,24+hy-by0]
  for head_x in (-12,-13,-11):
   x=head_x-lh[0];y=24-hh;bad=int(np.sum((sprite!=0)&~common[64+y:64+y+hh,64+x:64+x+ww]));options.append((bad*100+abs(px-.5)+abs(py-.5)+abs(head_x+12),bad,px,py,x,y,sprite,lh,ix,ex.mean(),ey.mean()))
best=min(options,key=lambda q:q[0]);_,bad,px,py,x,y,sprite,lh,ix,ex,ey=best
print('best',bad,px,py,x,y,'head',[x+lh[0],y+lh[1]])
if bad:raise ValueError('Cannot normalize without changing anatomy')
save_image(ix.tobytes(),(w,h),words,P/'probe_run_10.png')
r=json.loads((P/'fit_probe.json').read_text());r['run10'].update({'phase':[px,py],'world_origin':[x,y],'eye_world':[float(x+ex),float(y+ey)]});(P/'fit_probe.json').write_text(json.dumps(r,indent=2),encoding='utf-8')
