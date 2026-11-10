from pathlib import Path
P=Path(__file__).parent
s=(P/'fit_coherent.py').read_text(encoding='utf-8')
s=s.replace("C=P/'coherent_walk'","C=P/'zero_based_rebuild'").replace('generated_final.png','generated_cycle.png').replace('scale=.17','scale=.19')
s=s.replace('sprite[:24+hy+18,:]=0','sprite[:24+hy+18,24+hx:24+hx+23]=0')
s=s.replace('range(-1,2)','range(-2,3)')
s=s.replace('range(-3,4)','range(-6,4)')
s=s.replace('hy=0','hy=3 if n==9 else 2 if n in (16,17) else 1 if n==10 else 0')
s=s.replace('choices.append((100*bad+3*abs(dx)+5*abs(dy),bad,x,y))','choices.append((100*bad+3*abs(dx)+5*abs(dy)+(10000 if n==9 and y+head_local[1]<-24 else 0),bad,x,y))')
s=s.replace('a=np.array(cell);yy,xx=np.nonzero(a[:,:,3]>=160);a=a[yy.min():yy.max()+1,xx.min():xx.max()+1]', '''a=np.array(cell)
    # Disconnected fragments at the cell edge belong to a neighboring cape.
    from collections import deque
    unseen=set(map(tuple,np.argwhere(a[:,:,3]>=160)));groups=[]
    while unseen:
        seed=unseen.pop();todo=deque([seed]);group=[seed]
        while todo:
            yy,xx=todo.popleft()
            for ddy,ddx in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
                point=(yy+ddy,xx+ddx)
                if point in unseen:unseen.remove(point);todo.append(point);group.append(point)
        groups.append(group)
    main=max(groups,key=len);keep=np.zeros(a.shape[:2],dtype=bool)
    for yy,xx in main:keep[yy,xx]=True
    a[~keep,3]=0
    yy,xx=np.nonzero(keep);a=a[yy.min():yy.max()+1,xx.min():xx.max()+1]''')
s=s.replace('ideal_y=24-hh',"original=np.array(Image.open(Q/f'original_{n:03d}.png'));oy,ox=np.nonzero(original[:,:,3] if original.ndim==3 else original);original_bottom=int(oy.max())+geometry[n][1][1];ideal_y=original_bottom+1-hh")
s=s.replace("recipe['source_art']={'generated_cycle.png':hashlib.sha256((C/'generated_cycle.png').read_bytes()).hexdigest(),'pose_guide.json':hashlib.sha256((C/'pose_guide.json').read_bytes()).hexdigest()}","recipe['source_art']={'generated_cycle.png':hashlib.sha256((C/'generated_cycle.png').read_bytes()).hexdigest(),'zero_full_cycle.png':hashlib.sha256((C/'zero_full_cycle.png').read_bytes()).hexdigest()}")
s=s.replace("'no waist/hip/arm layer compositing'","'no waist/hip/arm layer compositing'")
s=s.replace('generated_cycle.png','generated_cycle_compact.png')
s=s.replace('if bad:fails.append', '''if n in (9,17):
        ed=np.array(Image.open(C/'generated_fit.png').convert('RGBA').resize((128,72),Image.Resampling.NEAREST));em=ed[:,:,3]>=160;er=ed[:,:,:3].astype(np.int32);ei=np.zeros(em.shape,dtype=np.uint8);ei[em]=np.argmin(((er[em,None]-colors[None])**2).sum(2),1)+1
        key=0 if n==9 else 1;tile=ei[:,key*64:(key+1)*64]
        rects=[(8,1,25,12)] if n==9 else [(13,-2,26,11),(13,-18,29,-6)]
        for rx0,ry0,rx1,ry1 in rects:world[64+ry0:64+ry1,64+rx0:64+rx1]=tile[40+ry0:40+ry1,32+rx0:32+rx1]
        bad=int(np.sum((world!=0)&~safe))
    if bad:fails.append''')
exec(s)
import json,hashlib
recipe=json.loads((C/'recipe.json').read_text(encoding='utf-8'))
recipe['coherent_body']['method']='Original Zero pose-reference rebuild; uniform body sheet scale, fixed reference head and integer registration. Local generated rear-boot/cape corrections in 9/17; no waist cut or individual hip translation.'
recipe['coherent_body']['original_motion_exact_joint_match_proven']=False
recipe['source_art']['generated_fit.png']=hashlib.sha256((C/'generated_fit.png').read_bytes()).hexdigest()
recipe['coherent_body']['local_generated_edits']={'9':[[8,1,25,12]],'17':[[13,-2,26,11],[13,-18,29,-6]]}
(C/'recipe.json').write_text(json.dumps(recipe,ensure_ascii=False,indent=2),encoding='utf-8')
