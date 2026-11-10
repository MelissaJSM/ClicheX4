import gzip,sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R))
from scripts.prepare_nana_life_revision import PARENT,entry
S=R/'work/ver_rin_nana/checkpoints/before_nana_life_face_20261030/current_progress';s=gzip.decompress(S.read_bytes());vram=2569183;g=entry((PARENT/'modified.arc').read_bytes(),0x10206)
def hits(data,lo,hi):
 out=[];p=lo
 while(p:=s.find(data,p,hi))>=0:out.append(p);p+=1
 return out
report={'state_size':len(s),'texture_size':len(g),'ram':hits(g,0,vram),'pages':[]}
for page in range(len(g)//32768):
 b=g[page*32768:(page+1)*32768];row=max(range(256),key=lambda y:len(set(b[y*128:(y+1)*128])));cand=hits(b[row*128:(row+1)*128],vram,vram+1048576);bases=[]
 for pos in cand:
  base=pos-row*2048
  if vram<=base and base+255*2048+128<=vram+1048576 and all(s[base+y*2048:base+y*2048+128]==b[y*128:(y+1)*128]for y in range(256)):bases.append(base)
 report['pages'].append({'page':page,'ram':hits(b,0,vram),'bases':bases,'xy':[[int((p-vram)%2048//2),int((p-vram)//2048)]for p in bases]})
(S.parent/'probe.json').write_text(json.dumps(report,indent=2)+'\n','utf8');print(report)
