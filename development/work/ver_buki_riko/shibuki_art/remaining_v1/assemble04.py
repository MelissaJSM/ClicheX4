"""신규 원화와 수용된 파츠로 남은 동작의 편집용 160x160 마스터를 만든다."""
import json,sys,struct
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.extract_zero import save_image
from scripts.discover_inputs import psx_arc
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices
d=Path(__file__).parent;a=d/'production04';a.mkdir(exist_ok=True);plan=json.loads((d/'plan.json').read_text());art=json.loads((d/'native04/art.json').read_text());pal=art['palette_words'];SIZE=(160,160);ORIGIN=(80,80)
parent=ROOT/'out/ver_buki_riko/shibuki_low_hp_20261026T151338348062Z';arc=(parent/'modified.arc').read_bytes();orig=(ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/original.arc').read_bytes()
def entries(arc):
 es=psx_arc(arc)
 return [arc[e['offset']:e['offset']+e['size']] for t in (2,3) for e in es if int(e['type'],16)==t]
g,c=entries(arc);og,oc=entries(orig);bank=graphics_bank(g,0,allow_bank_aliases=True);ob=graphics_bank(og,0,allow_bank_aliases=True)
def compose(n,original=False,tiles=None):
 gg,cc,bb=(og,oc,ob) if original else (g,c,bank);f=bb['frames'][n];raw=decode_stream(gg,f['offset'],f['limit'],f['tile_count']*128).data;cp=composition_frame(cc,0,n)
 if tiles is not None:cp={**cp,'parts':[q for q in cp['parts'] if q['tile'] in tiles]}
 pix,size,bounds,_=compose_indices(raw,f['tile_count'],cp,allowed_cluts={0,2});v=np.frombuffer(pix,np.uint8).reshape(size[1],size[0])%16;out=np.zeros(SIZE,np.uint8);yy,xx=np.nonzero(v);out[yy+bounds[1]+80,xx+bounds[0]+80]=v[yy,xx];return out
def native(n):
 im=np.array(Image.open(d/'native04'/f'frame_{n:03d}.png'));out=np.zeros(SIZE,np.uint8);out[40:120,32:128]=im;return out
def move(x,dx=0,dy=0):
 out=np.zeros_like(x);yy,xx=np.nonzero(x);assert np.all((xx+dx>=0)&(xx+dx<160)&(yy+dy>=0)&(yy+dy<160));out[yy+dy,xx+dx]=x[yy,xx];return out
def over(bg,fg):
 out=bg.copy();out[fg!=0]=fg[fg!=0];return out
def outline(v,color=6):
 mask=v!=0;p=np.pad(mask,1);edge=(p[:-2,1:-1]|p[2:,1:-1]|p[1:-1,:-2]|p[1:-1,2:])&~mask;out=v.copy();out[edge]=color;return out
fxmap=np.array([0,1,2,5,4,5,6,7,9,9,10,11,6,14,8,2],np.uint8)
targets={r['frame']:native(r['frame']) for r in art['frames']}; groups=[]
def putgroup(n,aliases=None,writable=None,kind='body',effects=None,translations=None):
 aliases=aliases or [k for bi,k in plan['groups'][n]['aliases']];parts={k:plan['groups'][k]['parts'] for k in aliases};alltiles={q['tile'] for ps in parts.values() for q in ps};w=sorted(alltiles if writable is None else writable)
 groups.append({'frame':n,'aliases':aliases,'writable':w,'kind':kind,'effect_tiles':sorted(effects or []),'translations':translations or {str(k):[0,0] for k in aliases},'budget':plan['groups'][n]['budget'],'tile_count':plan['groups'][n]['tile_count'],'part_slots':{str(k):[q['index'] for q in ps if q['tile'] in w] for k,ps in parts.items()}})

# Body translations are taken from original composition records, not guessed timings.
for n in (89,95,98,162,166,170):
 aliases=[k for bi,k in plan['groups'][n]['aliases']];primary=n
 if n==89:aliases=[88,89]
 translations={str(n):[0,0]}
 for k in aliases:
  if k==n:continue
  old=plan['groups'][n]['parts'];other=plan['groups'][k]['parts'];diff=[]
  for q in old:
   matches=[v for v in other if v['tile']==q['tile'] and v['flags']==q['flags']]
   if len(matches)==1:diff.append([matches[0]['x']-q['x'],matches[0]['y']-q['y']])
  assert diff and all(v==diff[0] for v in diff),(n,k,diff)
  translations[str(k)]=diff[0];targets[k]=move(targets[n],*diff[0])
 putgroup(n,aliases,plan['groups'][n]['base_tiles'],'body',set(plan['groups'][88]['base_tiles'])-set(plan['groups'][89]['base_tiles']) if n==89 else [],translations)
for n in (90,91,94,97,100,101,102,103,104,174,204,205,206,207,231,233,234):putgroup(n)
targets[232]=targets[231].copy();targets[232]=move(targets[232],dy=1);putgroup(232)
targets[93]=compose(37);putgroup(93)
# All ordinary animation endpoints reuse the accepted idle rather than a new approximation.
targets[142]=compose(0);putgroup(142)
targets[141]=compose(0);putgroup(141,writable=list(range(7)),effects=[7])
targets[136]=targets[135].copy();putgroup(135);putgroup(136,writable=list(range(7)),effects=[7]);putgroup(137,writable=list(range(7)),effects=[7]);putgroup(138)
targets[139]=move(targets[138],dy=-1);putgroup(139)
targets[140]=np.where(compose(0)!=0,9,0).astype(np.uint8);putgroup(140,writable=list(range(8)),effects=[8])
# Materialisation silhouettes have the new ears/hair/body, retaining original energy timing.
targets[133]=outline(targets[133]);putgroup(133)
targets[130]=over(fxmap[compose(129,True)],np.where(targets[133]!=0,9,0).astype(np.uint8));putgroup(130)
targets[131]=np.where(targets[133]!=0,9,0).astype(np.uint8);putgroup(131,[131,132],list(range(8,16)),effects=list(range(8)));groups[-1]['part_slots']['132']=[];targets[132]=np.zeros(SIZE,np.uint8)
targets[134]=over(fxmap[compose(129,True)],targets[133]);putgroup(134)
# Return pose is composited inside the original ring, no stretching of the human body.
putgroup(156);targets[157]=outline(outline(move(targets[156],dy=-1),14),6);putgroup(157)
targets[158]=over(fxmap[compose(159,True)],move(targets[158],dy=-10));putgroup(158)
# Original special damage effects sampled outside their original body; body now has one common pose.
for n in (235,236):
 original=compose(n,True);wanted=(original==8) if n==235 else (original==5);fx=np.where(wanted,9 if n==235 else 6,0).astype(np.uint8)
 # Do not retain white highlights that belonged to the original face/armor.
 oldbody=compose(234,True)!=0;p=np.pad(oldbody,1);mask=p[1:-1,1:-1]|p[:-2,1:-1]|p[2:,1:-1]|p[1:-1,:-2]|p[1:-1,2:];fx[mask]=0
 targets[n]=over(fx,targets[234]);putgroup(n)
# Charged soul-body disappearance silhouettes reuse the accepted idle silhouette.
for n,color in ((208,8),(209,14)):
 targets[n]=np.where(compose(0)!=0,color,0).astype(np.uint8);putgroup(n)
src=targets[209];targets[210]=src[:, :].copy();targets[210][:,:]=0
ys,xs=np.nonzero(src);cx=80;xx=np.rint((xs-cx)*.45+cx).astype(int);targets[210][ys,xx]=np.where(xx<cx,6,14);putgroup(210)
# Nova entry shares its torso between animation variants; original armor remains untouched.
targets[213]=targets[100].copy();targets[214]=targets[213].copy();putgroup(213,[213,214])
targets[215]=targets[101].copy();targets[216]=targets[215].copy();putgroup(215,[215,216])
targets[217]=outline(targets[217]);putgroup(217)
targets[220]=over(fxmap[compose(219,True)],targets[217]);putgroup(220)
# Air-hover normal/firing pairs keep the approved air bodies and forearm cannon art.
for n,source in ((221,39),(223,37),(225,45),(227,47),(229,41)):
 targets[n]=compose(source);targets[n+1]=compose(source+1);putgroup(n,[n,n+1],kind='pair')
# Ride-armor head-only slots are limited to one 16x16 tile. Purpose-sized icon from approved head.
idle=np.array(Image.open(d.parent/'standing_buster_v1/parent_000.png'));head=idle[16:36,32:54];small=np.array(Image.fromarray(head).resize((14,15),Image.Resampling.NEAREST));headtile=np.zeros((16,16),np.uint8);headtile[0:15,1:15]=small
for n in (184,193,195,196,199):
 aliases=[k for bi,k in plan['groups'][n]['aliases']];translations={};parts=plan['groups'][n]['parts'];q=parts[0];w=[q['tile']];targets[n]=np.zeros(SIZE,np.uint8);targets[n][80+q['y']:96+q['y'],80+q['x']:96+q['x']]=headtile
 for k in aliases:
  v=plan['groups'][k]['parts'][0];dx=v['x']-q['x'];dy=v['y']-q['y'];translations[str(k)]=[dx,dy]
  targets[k]=move(targets[n],dx,dy) if k!=198 else np.zeros(SIZE,np.uint8)
 putgroup(n,aliases,w,'head',translations=translations)
 if n==196:groups[-1]['part_slots']['198']=[]
# Non-body effect streams only change color indices, preserving original shape/part layout.
for n in (126,128,129,159,160,211,212,218,219):putgroup(n,kind='effect')
selected={k for r in groups for k in r['aliases']};assert selected==set(plan['remaining_frames']),(set(plan['remaining_frames'])-selected,selected-set(plan['remaining_frames']))
for n,t in targets.items():save_image(t.tobytes(),SIZE,pal,a/f'frame_{n:03d}.png')
manifest={'frames':[{'frame':n,'image':f'frame_{n:03d}.png'} for n in sorted(targets)],'groups':groups,'palette_words':pal,'canvas_size':SIZE,'origin':ORIGIN,'effect_index_mapping':fxmap.tolist(),'source_inventory':plan['source_inventory'],'parent':str(parent.relative_to(ROOT)),'remaining_frames':plan['remaining_frames'],'head_slot_constraint':'one tile 16x16, human head only; body not resized','placeholder_frames_preserved':plan['placeholder_frames']}
(a/'art.json').write_text(json.dumps(manifest,indent=2));print('groups',len(groups),'targets',len(targets),'refs',len(selected))
