import gzip,sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R))
from scripts.prepare_nana_life_revision import PARENT,entry
from src.psx_ui_atlas import tile_pixels
S=R/'work/ver_rin_nana/checkpoints/before_nana_life_face_20261030/current_progress';s=gzip.decompress(S.read_bytes());vram=2569183;g=entry((PARENT/'modified.arc').read_bytes(),0x10206);out=[];common=None
for t in [657,658,659,660,662,663,665,667,669,670,672,673,675,676]:
 rows=[g[((t//16)*16+y)*128+(t%16)*8:((t//16)*16+y)*128+(t%16)*8+8]for y in range(16)];r=max(range(16),key=lambda n:len(set(rows[n])));p=vram;hits=[]
 while(p:=s.find(rows[r],p,vram+1048576))>=0:
  b=p-r*2048
  if vram<=b and b+15*2048+8<=vram+1048576 and all(s[b+y*2048:b+y*2048+8]==rows[y]for y in range(16)):hits.append(b)
  p+=1
 bases={b-(t//16%16)*16*2048-(t%16)*8 for b in hits};common=bases if common is None else common&bases
 out.append({'tile':t,'hits':hits,'xy':[[int((b-vram)%2048//2),int((b-vram)//2048)]for b in hits]})
report={'tiles':out,'common_page2_bases':list(common)};(S.parent/'tile_probe.json').write_text(json.dumps(report,indent=2)+'\n','utf8');print({'matches':{q['tile']:len(q['hits'])for q in out},'common_page2_bases':list(common)})
