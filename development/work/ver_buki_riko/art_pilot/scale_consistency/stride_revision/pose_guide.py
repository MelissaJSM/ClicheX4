from pathlib import Path
import json,math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=Path(__file__).parent
foot_x=[-9,-14,-8,-4,0,4,9,12,12,9,5,1,-2,-5]
bob=[0,1,1,0,-1,-1,-1]*2
foot_y=[17,20,20,21,22,20,16,12,8,8,9,12,14,17]
records=[];fig,axs=plt.subplots(4,4,figsize=(16,12.8),dpi=100)
for i,ax in enumerate(axs.flat):
 ax.set(xlim=(-20,20),ylim=(29,-3));ax.set_aspect('equal');ax.axis('off')
 if i>=14:continue
 foot=np.array([foot_x[i],foot_y[i]],dtype=float);ankle=foot+np.array([2,-2]);d=np.linalg.norm(ankle);L1,L2=9,13
 assert abs(L1-L2)<d<L1+L2
 a=(L1*L1-L2*L2+d*d)/(2*d);h=math.sqrt(L1*L1-a*a);v=ankle/d;perp=np.array([-v[1],v[0]]);candidates=[a*v+h*perp,a*v-h*perp];knee=min(candidates,key=lambda q:q[0])
 ax.plot([0,knee[0]],[0,knee[1]],color='#edb28c',lw=14,solid_capstyle='round');ax.plot([knee[0],ankle[0]],[knee[1],ankle[1]],color='#a0b5dc',lw=15,solid_capstyle='round');ax.plot([ankle[0],ankle[0],foot[0]-2],[ankle[1],foot[1],foot[1]],color='#6076ad',lw=12,solid_capstyle='round')
 ax.scatter([0,knee[0],ankle[0]],[0,knee[1],ankle[1]],s=26,color='#28304b',zorder=4)
 records.append({'phase':i,'hip':[0,0],'knee':knee.tolist(),'ankle':ankle.tolist(),'foot_center':foot.tolist(),'bone_lengths':[9,13],'whole_body_dy':bob[i]})
fig.subplots_adjust(left=0,right=1,top=1,bottom=0,wspace=0,hspace=0);fig.savefig(P/'kinematic_guide.png',transparent=True);plt.close(fig)
(P/'kinematic_guide.json').write_text(json.dumps({'kind':'Authored kinematic diagram; not game artwork','native_cell':[40,32],'columns':4,'rows':4,'frames':records,'target_plant_speed':2,'plant_phases':[1,2,3,4],'original_ticks':[2,3,2,2,2,3,2]*2},indent=2),encoding='utf-8')
