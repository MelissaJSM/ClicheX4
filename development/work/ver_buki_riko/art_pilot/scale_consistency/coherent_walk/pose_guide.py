"""New authored joint diagram, not game imagery or final sprite artwork."""
import json,math
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse
P=Path(__file__).parent
xs=[-16,-12,-6,-2,2,6,12,16,11,5,-2,-8,-12,-15]
ys=[21]*8+[18,16,15,17,18,20]
dy=[0,1,0,-1,-1,0,0]*2
def joint(a,b,l1,l2,bend):
    dx,dy=b[0]-a[0],b[1]-a[1];d=math.hypot(dx,dy)
    assert d<=l1+l2
    t=(l1*l1-l2*l2+d*d)/(2*d);h=math.sqrt(max(0,l1*l1-t*t))
    return [a[0]+t*dx/d+bend*h*(-dy/d),a[1]+t*dy/d+bend*h*dx/d]
fig,axs=plt.subplots(4,4,figsize=(12,12),facecolor='#282b35')
rows=[]
for i,ax in enumerate(axs.flat):
    ax.set_aspect('equal');ax.set_xlim(-28,28);ax.set_ylim(30,-34);ax.axis('off');ax.set_facecolor('#282b35')
    if i>=14:continue
    hip=[0,3+dy[i]];shoulder=[-2,-6+dy[i]]
    nearfoot=[xs[i],ys[i]];farfoot=[xs[(i+7)%14],ys[(i+7)%14]]
    nrw=[-xs[i]*.5,5-3*abs(xs[i])/16+dy[i]]
    frw=[-xs[(i+7)%14]*.5,5-3*abs(xs[(i+7)%14])/16+dy[i]]
    near=[hip,joint(hip,nearfoot,11,14,1),nearfoot]
    far=[hip,joint(hip,farfoot,11,14,1),farfoot]
    na=[shoulder,joint(shoulder,nrw,6,7,-1),nrw]
    fa=[shoulder,joint(shoulder,frw,6,7,-1),frw]
    for pts,c,w in [(far,'#697888',5),(fa,'#697888',4),([hip,shoulder],'#20bbbf',8),(near,'#f4f6ff',5),(na,'#f4f6ff',4)]:
        ax.plot(*zip(*pts),c=c,lw=w,solid_capstyle='round')
    for foot,c in [(farfoot,'#697888'),(nearfoot,'#f4f6ff')]:ax.plot([foot[0]-3,foot[0]+1],[foot[1]+2]*2,c=c,lw=4)
    ax.add_patch(Ellipse((-6,-16+dy[i]),20,18,facecolor='#9ed195',edgecolor='#dce9e1'))
    ax.plot([-14,-11],[-16+dy[i]]*2,c='#9b5faf',lw=3)
    ax.axhline(24,c='#454955',lw=.7)
    rows.append({'phase':i,'hip':hip,'shoulder':shoulder,'near_leg':near,'far_leg':far,'near_arm':na,'far_arm':fa,'whole_body_dy':dy[i]})
fig.subplots_adjust(0,0,1,1,wspace=0,hspace=0)
fig.savefig(P/'pose_guide.png',dpi=128)
(P/'pose_guide.json').write_text(json.dumps({'kind':'authored technical pose guide, not final artwork','poses':rows},indent=2))
