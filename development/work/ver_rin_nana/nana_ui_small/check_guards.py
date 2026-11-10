"""UI 공유 영역과 잘못된 제작 입력의 거부를 실제 검사한다. 디스크 쓰기 없음."""
import copy,json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_ui_small import read_sources,verify,entry,replace_entry
from scripts.build_nana_ui_small import validate
from src.psx_player import composition_frame
from scripts.project import digest

base=ROOT/'work/ver_rin_nana/nana_ui_small';art=base/'v1';other=base/'repro_v1'
m,arc,records,originals=read_sources();edited={n:(art/n).read_bytes()for n in originals}
verify(originals,edited,arc);results=[]
def reject(label,action):
 try:action()
 except ValueError as e:results.append({'case':label,'rejected':True,'reason':str(e)})
 else:raise AssertionError('Unsafe UI input accepted: '+label)
def corrupt_resource(name,off):
 q=edited.copy();a=bytearray(q[name]);a[off]^=1;q[name]=bytes(a);return q
def corrupt_entry(name,e,off):
 q=edited.copy();a=bytearray(entry(q[name],e));a[off]^=1;q[name]=replace_entry(q[name],e,bytes(a));return q
cases=[('rin_texture','ST0E_U1.ARC',0x10102,16),('portrait_texture','ST0E_U1.ARC',0x10102,40960+16),('selection_effect_palette','COL0E_U1.ARC',5,17*32+2),('rin_palette','COL0E_U1.ARC',5,2)]
for label,n,e,off in cases:reject(label,lambda n=n,e=e,off=off:verify(originals,corrupt_entry(n,e,off),arc))
parts=entry(edited['ST0E_U1.ARC'],10);o=composition_frame(parts,2,9)['parts'][0]['record_offset']+2
reject('selection_effect_position',lambda:verify(originals,corrupt_entry('ST0E_U1.ARC',10,o),arc))
menu=edited['MOJIPAT.ARC']
for label,off in [('save_rin_palette',6788+10*32+2),('save_armor_palette',6788+9*32+2),('save_armor_position',composition_frame(menu,2,45)['parts'][0]['record_offset']+2),('save_body_palette',6788+8*32+2)]:
 reject(label,lambda off=off:verify(originals,corrupt_resource('MOJIPAT.ARC',off),arc))
bad1=base/'negative_a';bad2=base/'negative_b'
shutil.copytree(art,bad1);shutil.copytree(other,bad2)
recipe=json.loads((art/'recipe.json').read_text('utf8'))
for key,value in [('kind','wrong'),('parent_sha256','0'*64),('parent_arc_sha256','0'*64),('master_sha256','0'*64),('palette_sha256','0'*64),('mapping',{}),('files',[]),('verification',{})]:
 r=copy.deepcopy(recipe);r[key]=value
 for d in(bad1,bad2):(d/'recipe.json').write_text(json.dumps(r),'utf8')
 reject('recipe_'+key,lambda:validate(bad1,bad2))
for d in(bad1,bad2):shutil.copyfile(art/'recipe.json',d/'recipe.json')
for d in(bad1,bad2):
 p=d/'MOJIPAT.ARC';b=bytearray(p.read_bytes());b[-1]^=1;p.write_bytes(b)
reject('prepared_file_hash',lambda:validate(bad1,bad2))
for d in(bad1,bad2):shutil.copyfile(art/'MOJIPAT.ARC',d/'MOJIPAT.ARC')
(bad1/'extra.bin').write_bytes(b'test');reject('different_reproduction_file_set',lambda:validate(bad1,bad2))
report={'checks':results,'passed':len(results),'disk_writes':False,'valid_recipe_verified':True}
(base/'guard_checks.json').write_text(json.dumps(report,indent=2)+'\n','utf8');print(json.dumps({'passed':len(results)}))
