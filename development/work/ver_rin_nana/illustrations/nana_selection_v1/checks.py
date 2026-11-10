"""선택 이름/린/작은 도트/자원 범위 및 내부 투명 구멍 검사. 디스크 쓰기 없음."""
import json,sys
from collections import deque
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_selection_portrait import ART,sources,verify,entry,replace_entry,composition_frame
from scripts.build_nana_selection_portrait import validate
art=ART/'native04';repro=ART/'repro04';m,records,original=sources();edited={n:(art/n).read_bytes()for n in original};ix=(art/'indices.bin').read_bytes();pal=(art/'palette.bin').read_bytes();verify(original,edited,ix,pal);results=[]
def reject(label,action):
 try:action()
 except ValueError as e:results.append({'case':label,'rejected':True,'reason':str(e)})
 else:raise AssertionError(label)
def alter(name,e,off):
 d=edited.copy();a=bytearray(entry(d[name],e));a[off]^=1;d[name]=replace_entry(d[name],e,bytes(a));return d
for label,n,e,off in [('rin_small','ST0E_U1.ARC',0x10102,0),('nana_small','ST0E_U1.ARC',0x10102,90112),('rin_palette','COL0E_U1.ARC',5,160+2),('selection_small_palette','COL0E_U1.ARC',5,512+2)]:
 reject(label,lambda n=n,e=e,off=off:verify(original,alter(n,e,off),ix,pal))
p=entry(edited['ST0E_U1.ARC'],10)
for label,b,f in [('rin_visible_part',1,1),('name_position',1,7),('nana_small_position',2,0),('rin_small_position',0,0)]:
 off=composition_frame(p,b,f)['parts'][0]['record_offset']+2
 reject(label,lambda off=off:verify(original,alter('ST0E_U1.ARC',10,off),ix,pal))
badpal=bytearray(pal);badpal[2]^=1;d=edited.copy();cp=entry(d['COL0E_U1.ARC'],5);d['COL0E_U1.ARC']=replace_entry(d['COL0E_U1.ARC'],5,cp[:128]+badpal+cp[160:]);reject('shared_name_palette',lambda:verify(original,d,ix,bytes(badpal)))
reject('obsolete_unprotected_palette_recipe',lambda:validate(ART/'native03',ART/'repro03'))
reject('unexpected_art_folder',lambda:validate(ROOT/'out',repro))
validate(art,repro)
# Flood transparency from the outside. Any remaining zero is an unwanted interior hole.
q=deque((x,y)for y in range(160)for x in range(192)if(x in(0,191)or y in(0,159))and not ix[y*192+x]);seen=set()
while q:
 x,y=q.popleft()
 if(x,y)in seen:continue
 seen.add((x,y))
 for nx,ny in((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
  if 0<=nx<192 and 0<=ny<160 and not ix[ny*192+nx]and(nx,ny)not in seen:q.append((nx,ny))
holes=ix.count(0)-len(seen)
if holes:raise AssertionError('Transparent interior holes')
report={'negative_checks':results,'passed':len(results),'internal_transparent_pixels':holes,'valid_recipe_verified':True,'disk_writes':False};(ART/'checks.json').write_text(json.dumps(report,indent=2)+'\n','utf8');print(json.dumps({'passed':len(results),'holes':holes}))
