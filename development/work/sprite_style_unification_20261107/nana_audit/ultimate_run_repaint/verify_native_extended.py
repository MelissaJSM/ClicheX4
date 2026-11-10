"""이동32 후보의 전228참조·부분16마스크·팔2·총구 및 거부 검증."""
from pathlib import Path
import sys,json,copy
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sys.path[:0]=[str(D),str(ROOT),str(D.parent/'native_restore'),str(D.parent/'base_run_repaint')]
from preview_restore import Archive,sha,digest,write,need
from pack_cycle import raw,PLACEHOLDERS
from scripts.export_x_consistency import DRAW_ORDER
from scripts.discover_inputs import psx_arc
from scripts.prepare_shibuki_ultimate_production import records
from src.psx_player import composition_frame,bank_offsets,indexed_atlas
import pack_native as producer
FINAL='49da59790a3ad45c6b5a99f78e4786c135d8d017baa67ff55c07373a26f7fbe9'
def composed(a,layers,mask,arm):
 out=np.array(a.rgba(layers[0]))
 for bit,pb in DRAW_ORDER:
  if mask&bit:
   part=np.array(a.rgba(layers[pb],32 if pb==7 and arm==2 else 16));visible=part[:,:,3]>0;out[visible]=part[visible]
 return out
def main():
 out=D/'packed_run_diagnostic_v1';td=D/'joint_native_targets_v1';a=producer.validate_source((D.parent/'ultimate_dash_repaint/packed_dash_candidate_v1/PL02_U.ARC').read_bytes());b=Archive((out/'PL02_U.ARC').read_bytes());need(sha(b.data)==FINAL,'Candidate')
 meta=json.loads((td/'manifest.json').read_text('utf8'));targets={(n,pb):np.array(Image.open(td/f'layer{pb}_{n:03}.png'))for n in producer.REFS for pb in producer.PBS};producer.validate_targets(targets,meta)
 fire=json.loads((D/'firing_inputs_v1/manifest.json').read_text('utf8'));windows={r['ref']:r['window_world']for r in fire['frames']}
 images=selected=nonselected=muzzles=layers=nonlayers=0;frames=[]
 for n in range(237):
  if n in PLACEHOLDERS:continue
  old={pb:a.layer(n,pb)[0]for pb in producer.PBS};new={pb:b.layer(n,pb)[0]for pb in producer.PBS};expected={pb:targets.get((n,pb),old[pb])for pb in producer.PBS}
  for pb in producer.PBS:need(np.array_equal(new[pb],expected[pb]),f'Layer {n}/{pb}');layers+=1;nonlayers+=(n,pb)not in targets
  for arm in(1,2):
   for mask in range(16):
    actual=np.array(b.composite(n,mask,arm)[0]);want=composed(a,expected,mask,arm);need(np.array_equal(actual,want),f'RGBA {n}/{mask}/{arm}')
    images+=1;selected+=n in producer.REFS;nonselected+=n not in producer.REFS
    if n in windows:
     x0,y0,x1,y1=windows[n];sl=np.s_[y0+160:y1+160,x0+160:x1+160]
     need(np.array_equal(actual[sl],np.array(a.composite(n,mask,arm)[0])[sl]),f'Muzzle {n}/{mask}/{arm}');muzzles+=1
  if n in producer.REFS:frames.append({'ref':n,'before_rgba_sha256':sha(np.array(b.composite(n,15)[0]).tobytes()),'after_rgba_sha256':sha(np.array(b.composite(n,0)[0]).tobytes()),'tile_count':b.banks[0]['frames'][n]['tile_count']})
 rawcount=nonraw=0
 for gb,bank in enumerate(a.banks):
  need((bank['base'],bank['end'])==(b.banks[gb]['base'],b.banks[gb]['end']),'Graphics bank boundary')
  for n in range(len(bank['frames'])):
   rawcount+=1
   if gb==0 and n in producer.REFS:continue
   need(raw(a,gb,n)==raw(b,gb,n),f'Other raw {gb}/{n}');nonraw+=1
 need(bank_offsets(a.c)==bank_offsets(b.c),'Composition bank boundary');parts=0;gpu=0
 for pb in range(len(bank_offsets(a.c))):
  for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
   if(n,pb)in targets:continue
   need(records(a.c,pb,n)==records(b.c,pb,n),f'Other composition {pb}/{n}');parts+=1
 for n in producer.REFS:
  count=b.banks[0]['frames'][n]['tile_count'];need(count==32,'Buffer');atlas=np.frombuffer(indexed_atlas(raw(b,0,n),count)[0],np.uint8).reshape(32,256)
  for pb in producer.PBS:
   for p in composition_frame(b.c,pb,n)['parts']:
    t=p['tile'];tile=atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
    if t%16==0:need(not tile[:,0].any(),'GPU first column')
    if p['flip_y']and t//16==0:need(not tile[0].any(),'GPU flipY first row')
    gpu+=1
 pairs=[]
 for n in range(1,33,2):
  f,h=b.banks[0]['frames'][n:n+2];need(f['offset']==h['offset']and f['tile_count']==h['tile_count']==32,'Shared pair');pairs.append([n,n+1])
 layout=lambda data:[{k:v for k,v in e.items()if k!='sha256'}for e in psx_arc(data)]
 need(layout(a.data)==layout(b.data),'ARC layout');check=bytearray(a.data)
 for e in psx_arc(a.data):
  if int(e['type'],16)in(2,3):check[e['offset']:e['offset']+e['size']]=b.data[e['offset']:e['offset']+e['size']]
 need(check==b.data,'Other entries')
 rejected=[]
 def reject(name,call):
  try:call()
  except(ValueError,KeyError,TypeError):rejected.append(name)
  else:raise ValueError('Bad input accepted: '+name)
 bad=bytearray(a.data);bad[-1]^=1;reject('wrong_parent',lambda:producer.validate_source(bytes(bad)))
 reject('existing_output',lambda:producer.validate_output(out));reject('outside_output',lambda:producer.validate_output(ROOT/'unauthorized_candidate'))
 for name,mut in [('manifest_parent',lambda m:m.update(source_arc_sha256='0'*64)),('duplicate_ref',lambda m:m['frames'].__setitem__(0,m['frames'][1])),('target_hash',lambda m:m['frames'][0]['layers'].update({'0':'0'*64}))]:
  m=copy.deepcopy(meta);mut(m);reject(name,lambda m=m:producer.validate_targets(targets,m))
 t=dict(targets);t.pop((1,0));reject('missing_target',lambda:producer.validate_targets(t,meta))
 for name,value in [('pixel_mutation',targets[1,0].copy()),('wrong_shape',np.zeros((383,384),np.uint8)),('wrong_depth',targets[1,0].astype(np.uint16)),('invalid_palette',targets[1,0].copy())]:
  if name=='pixel_mutation':value[160,160]^=1
  if name=='invalid_palette':value[0,0]=16
  t=dict(targets);t[1,0]=value;reject(name,lambda t=t:producer.validate_targets(t,meta))
 t=dict(targets);t[1,0]=t[1,0].copy();t[1,0][0,0]=1;m=copy.deepcopy(meta);m['frames'][0]['layers']['0']=sha(t[1,0].tobytes());reject('outside_window',lambda:producer.validate_targets(t,m))
 rebuilt,_=producer.build(a,targets,meta);need(rebuilt==b.data,'Reproduction')
 write(out/'extended_verification.json',{'passed':True,'parent_sha256':sha(a.data),'candidate_sha256':FINAL,'selected_refs':list(producer.REFS),
  'raw_checked':rawcount,'nonselected_raw_exact':nonraw,'layers_checked':layers,'nonselected_layers_exact':nonlayers,
  'nonselected_compositions_exact':parts,'rgba_combinations_checked':images,'selected_combinations_checked':selected,'unchanged_combinations_checked':nonselected,
  'original_muzzle_rgba_checked':muzzles,'gpu_parts':gpu,'paired_streams':pairs,'frames':frames,'directory_layout_unchanged':True,
  'palette_audio_other_entries_exact':True,'negative_cases':rejected,'reproduced_identical':True,'runtime_verified':False,'native_mips_verified':False,
  'scope':'228 유효 참조×16 표시마스크×팔형2 직접 대조. 정상 Ultimate은 획득전15/획득후0이며 다른 마스크는 구조 회귀이다. 게임 실기는 이 검사에 포함하지 않는다.'})
 print(json.dumps({'passed':True,'rgba':images,'muzzles':muzzles,'raw':rawcount,'nonraw':nonraw,'gpu':gpu,'rejections':len(rejected)}),flush=True)
if __name__=='__main__':main()
