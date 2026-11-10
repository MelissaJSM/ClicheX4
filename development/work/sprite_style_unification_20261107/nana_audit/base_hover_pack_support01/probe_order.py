"""그림/타일 고정 상태에서 head 기록 순열에 의한 저장공유 가능성 조사."""
from pathlib import Path
import sys,struct,json,hashlib,collections
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;W=N.parent;ROOT=W.parents[1];R=W/'root_nana_hover';H=W/'shibuki_audit'
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(H),str(R)]
from preview_restore import Archive,sha,digest,write,need
from scripts.prepare_shibuki_ultimate_production import records
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import bank_offsets,composition_frame,compose_indices
from src.psx_ui_atlas import local_composition
from pinned_head_pack import HeadPacker
REFS=tuple(range(221,231));GEOM=[(1,69,48),(2,69,64),(3,85,48),(4,85,64),(5,85,80),(6,101,64)]
def contains(a,b):return any(a[i:i+len(b)]==b for i in range(len(a)-len(b)+1))
def packed_sequences(rr):
 anchor=rr[0];chunks=[]
 for v in sorted(set(rr),key=lambda v:(-len(v),v)):
  if not any(contains(s,v)for s in chunks):chunks.append(v)
 merges=[]
 while len(chunks)>1:
  best=None
  for i,a in enumerate(chunks):
   for j,b in enumerate(chunks):
    if i==j:continue
    overlap=next((n for n in range(min(len(a),len(b)),0,-1)if a[-n:]==b[:n]),0)
    if not overlap:continue
    score=(overlap,-len(a)-len(b),-i,-j)
    if best is None or score>best[0]:best=(score,i,j,overlap)
  if best is None:break
  _,i,j,n=best;merged=chunks[i]+chunks[j][n:];chunks=[x for k,x in enumerate(chunks)if k not in(i,j)and not contains(merged,x)]+[merged];merges.append(n)
 ordered=sorted(chunks,key=lambda v:(-len(v),v));first=next((x for x in ordered if x[:len(anchor)]==anchor),None)
 return (first+sum((x for x in ordered if x!=first),())if first is not None else anchor+sum(ordered,())),merges
def reorder_same(a,n,new):
 old=records(a.c,5,n);tokens=tuple(old[i:i+4]for i in range(0,len(old),4))
 if new==tokens:return True
 if collections.Counter(new)!=collections.Counter(tokens):return False
 try:original,detail=a.layer(n,5)
 except ValueError:return False
 cp=composition_frame(a.c,5,n);parts=collections.defaultdict(list)
 for t,part in zip(tokens,cp['parts']):parts[t].append(part)
 reordered=[parts[t].pop(0)for t in new];cp=dict(cp,parts=reordered);f=a.banks[0]['frames'][n];raw=a.raw[(f['offset'],f['tile_count'])].data
 pix,size,bb,_=compose_indices(raw,f['tile_count'],local_composition(cp),allowed_cluts={0,1,2,3});z=np.zeros((384,384),np.uint8);small=np.frombuffer(pix,np.uint8).reshape(size[1],size[0]);yy,xx=np.nonzero(small);z[yy+bb[1]+160,xx+bb[0]+160]=small[yy,xx]
 return np.array_equal(z,original)
def main():
 audit=json.loads((R/'input_audit.json').read_text('utf8'));p=ROOT/audit['input']['path'];need(digest(p)==audit['input']['sha256'],'부모');a=Archive(p.read_bytes());starts=bank_offsets(a.c);count=composition_frame(a.c,5,0)['bank_frame_count'];capacity=(starts[6]-starts[5]-count*4)//4;rr=[tuple(records(a.c,5,n)[i:i+4]for i in range(0,len(records(a.c,5,n)),4))for n in range(count)];targets={}
 for n in REFS:targets[n]=np.array(Image.open(R/('body_layers_probe01'if n%2 else'shoot_layers_probe02')/f'layer5_{n}.png'))
 for n in REFS[::2]:
  _,partlists,_=HeadPacker.head_data([targets[q][80:240,80:240]for q in(n,n+1)],GEOM)
  for q,parts in zip((n,n+1),partlists):rr[q]=tuple(struct.pack('<BBbb',fl,t,x-80,y-80)for t,x,y,fl in parts)
 base,merges=packed_sequences(rr);print(json.dumps({'capacity_records':capacity,'baseline_records':len(base),'short_bytes':(len(base)-capacity)*4,'distinct_records':len(set(sum(rr,())))}),flush=True)
 keys={'byte':lambda r:r,'tile':lambda r:(r[1],r[0],r[2],r[3]),'yx':lambda r:(struct.unpack('<BBbb',r)[3],struct.unpack('<BBbb',r)[2],r[1],r[0]),'xy':lambda r:(struct.unpack('<BBbb',r)[2],struct.unpack('<BBbb',r)[3],r[1],r[0])};results=[];best=None
 for name,key in keys.items():
  for reverse in(False,True):
   variants=[];changed=[]
   for n,seq in enumerate(rr):
    v=tuple(sorted(seq,key=key,reverse=reverse))
    if n in REFS:v=seq # new geometry stays fixed for first experiment
    if v!=seq and not reorder_same(a,n,v):v=seq
    if v!=seq:changed.append(n)
    variants.append(v)
   packed,merges=packed_sequences(variants);r={'sort':name,'reverse':reverse,'packed_records':len(packed),'slack_bytes':(capacity-len(packed))*4,'changed_non_target_refs':changed};print(json.dumps(r),flush=True);results.append(r)
   if best is None or len(packed)<len(best[0]):best=(packed,variants,r)
 out=D/'order_probe01';out.mkdir(exist_ok=False);write(out/'report.json',{'parent_sha256':digest(p),'geometry':GEOM,'capacity_records':capacity,'baseline_records':len(base),'trials':results,'best':best[2],'new_art_changed':False,'game_written':False});write(out/'best_sequences.json',{'sequences':[[t.hex()for t in seq]for seq in best[1]],'packed':[t.hex()for t in best[0]]});print('saved '+digest(out/'report.json'))
if __name__=='__main__':main()
