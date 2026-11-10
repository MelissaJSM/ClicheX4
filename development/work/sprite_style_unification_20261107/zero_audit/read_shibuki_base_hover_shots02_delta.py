"""01 독립근거를 보존하고02의3셀 팔소유 정정만 별도 검증한다."""
from pathlib import Path
import json,hashlib,sys
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
R=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent;S=W/'root_shibuki_hover';PREV=D/'shibuki_base_hover_shots01';O=D/'shibuki_base_hover_shots02_delta01';assert not O.exists();sys.path[:0]=[str(R),str(D)]
from scripts.export_x_consistency import Archive
from verify_shibuki_ultimate_hurt13_independent import color
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();hb=lambda v:hashlib.sha256(v).hexdigest();rel=lambda p:p.relative_to(R).as_posix();files={}
def track(p):files[rel(p)]=sha(p);return p
def read(p):track(p);return json.loads(p.read_text('utf8'))
def png(p):track(p);return np.array(Image.open(p))
r=read(PREV/'report.json');assert sha(PREV/'report.json')=='0b98a7d07250b13ea7359c075ad8ea68e05bb50273d82e4d8f6b57886edc2961'
for p,h in r['inputs'].items():assert sha(R/p)==h,p
priorlock=read(PREV/'READER_LOCK.json')
for p,h in priorlock['files'].items():assert sha(R/p)==h,p
meta=read(S/'shot_composed02/manifest.json');rows={q['ref']:q for q in meta['records']}
for p in(S/'compose_shots01.py',S/'compose_shots02.py'):track(p)
c1=(S/'compose_shots01.py').read_text('utf8');c2=(S/'compose_shots02.py').read_text('utf8');assert c1.replace("out=D/'shot_composed01'","out=D/'shot_composed02'").replace("arm&((f==9)|np.isin(b,(12,13)))","arm&np.isin(b,(12,13))")==c2
p=W/'shibuki_audit/prepared_nova_strike_base01/PL00_U.ARC';a=Archive(track(p).read_bytes());assert hb(a.data)==r['parent_sha256'];PBS=(0,5,6,7,8);expected={222:[],224:[[-18,-6]],226:[],228:[],230:[[-6,-2],[-7,-1]]};oldlayers={};newlayers={};diffrows=[];condition_rows=[]
def compose(ls,m,arm):
 z=color(a,ls[0])
 for bit,pb in((8,8),(1,5),(4,7),(2,6)):
  if m&bit:v=color(a,ls[pb],32 if pb==7 and arm==2 else 16);k=v[:,:,3]>0;z[k]=v[k]
 return z
for n,coords in expected.items():
 old={pb:png(S/f'shot_composed01/layer{pb}_{n}.png')for pb in PBS};new={pb:png(S/f'shot_composed02/layer{pb}_{n}.png')for pb in PBS};fourth=png(S/f'shot_registered01/fourth_{n}_source_indices.png');region=np.zeros((384,384),bool)
 for x,y in coords:region[y+160,x+160]=True
 for pb in PBS:
  target=old[pb].copy()
  if pb==7:
   assert not old[pb][region].any() and np.all(fourth[region]==9);target[region]=fourth[region]
  assert np.array_equal(new[pb],target),(n,pb);assert sha(S/f'shot_composed02/layer{pb}_{n}.png')==rows[n]['layer_hashes'][str(pb)]
  diffrows.append({'ref':n,'layer':pb,'changed_cells':int((new[pb]!=old[pb]).sum())})
 guard=png(S/f'shot_inputs01/{n}_gun_guard.png')>0;assert not(guard&region).any()
 for m in range(8,16):
  for arm in(1,2):
   oz,nz=compose(old,m,arm),compose(new,m,arm);changed=np.any(oz!=nz,axis=2);expect=region if m&4 else np.zeros_like(region)
   assert np.array_equal(changed,expect);assert not np.any(oz[:,:,3]!=nz[:,:,3]);assert int(label(nz[:,:,3]>0,np.ones((3,3)))[1])==1
   assert np.array_equal(oz[guard],nz[guard]);condition_rows.append({'ref':n,'mask':m,'arm':arm,'changed_RGBA_pixels':int(changed.sum()),'components8':1})
 oldlayers[n]=old;newlayers[n]=new
assert sum(q['changed_cells']for q in diffrows)==3 and sum(q['changed_RGBA_pixels']for q in condition_rows)==24
O.mkdir(exist_ok=False);sheets=[]
for n in(224,230):
 out=Image.new('RGB',(4*240,2*340),'#c6d0d7');dr=ImageDraw.Draw(out);crop=(126,128,182,189)
 for row,m in enumerate((8,15)):
  for col,(name,ls)in enumerate((('01',oldlayers[n]),('02',newlayers[n]))):
   im=Image.fromarray(compose(ls,m,1));p=im.crop(crop).resize((224,244),Image.Resampling.NEAREST);x=col*480;y=row*340;dr.text((x+3,y+3),f'{n} mask{m} {name}',fill='black');out.paste(p,(x+2,y+30),p)
   localcrop=(137,149,153,160)if n==224 else(148,152,160,166);local=im.crop(localcrop).resize(((localcrop[2]-localcrop[0])*14,(localcrop[3]-localcrop[1])*14),Image.Resampling.NEAREST);out.paste(local,(x+244,y+50),local)
 p=O/f'delta_{n}.png';out.save(p);sheets.append({'path':rel(p),'sha256':sha(p),'scales':[4,14]})
for n in(224,230):track(S/f'shot_composed02/comparison_{n}.png')
for p in(Path(__file__),D/'verify_shibuki_ultimate_hurt13_independent.py',R/'scripts/export_x_consistency.py'):track(p)
for p,h in files.items():assert sha(R/p)==h,p
report={'passed':True,'scope':'shot01의3셀의상소유오류를02가최소변경으로정정했는지증분검사','prior_report':{'path':rel(PREV/'report.json'),'sha256':sha(PREV/'report.json')},'prior_final_lock':{'path':rel(PREV/'READER_LOCK.json'),'sha256':sha(PREV/'READER_LOCK.json')},'source_code_change':'출력폴더명과shared_skin을arm&base12/13으로제한하는1식외동일','changed_cells':expected,'layer_deltas':diffrows,'conditions':condition_rows,'checks':{'layers_compared':25,'changed_layers':2,'changed_index_cells':3,'partial_conditions':80,'changed_RGBA_pixels_total':24,'all80_same_alpha_and_single_component':True,'base_mask8_unchanged':True,'face_lower_gun_unchanged':True,'actualFourth9_from_same_source':True,'all_other_indices_exact':True},'original01_inputs_unchanged':True,'sheets':sheets,'inputs':files,'actually_viewed':False,'source_or_resource_modified':False,'producer_functions_imported_or_called':False,'new_art_generated':False,'new_MIPS_execution':False,'ARC_created':False,'runtime_verified':False,'limits':['04非사격과原source10再양자화는이전01독립근거를재사용했다.','02의3색인변화는arm7선택마스크에서만표시되며실제기본mask8그림은그대로다.','패킹·공유원시·GPU·게임실기는이번진단범위밖이다.']}
report['limits'][0]='04 비사격과 원화10셀 재양자화는 이전01 독립근거를 재사용했다.'
with(O/'report.json').open('x',encoding='utf8')as f:f.write(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'report_sha256':sha(O/'report.json'),'checks':report['checks']}))
