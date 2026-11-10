"""Reconstruct current hurt layers from their current bodies without editing ARC."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
from src.psx_player import graphics_bank,composition_frame,decode_stream,compose_indices
D=Path(__file__).parent/'rin_extension';P=D/'prepared_wall_followup_v2/PL01_U.ARC';O=D/'hurt_rules97';O.mkdir(exist_ok=True)
arc=P.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(arc)=='289370272eb51e377435e3fea0591921f4497fe3774d1f41e1d15d4d76d22ca2'
g,c=entry(arc,2),entry(arc,3);bank=graphics_bank(g,0);pal=struct.unpack_from('<64H',entry(arc,9));black=list(pal);black[:16]=struct.unpack_from('<16H',entry(arc,9),13*32)
a={n:render(arc,0,0,n)[0]for n in range(135,146)};pred={135:a[135],139:a[139]};overlays={};parts={}
def compose_parts(n,selected):
 f=bank['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;comp=composition_frame(c,0,n);comp={**comp,'parts':selected}
 px,size,bounds,_=compose_indices(raw,f['tile_count'],comp,allowed_cluts={0,2});v=np.frombuffer(px,np.uint8).reshape(size[1],size[0]);world=np.zeros((384,384),np.uint8);world[160+bounds[1]:160+bounds[3],160+bounds[0]:160+bounds[2]]=v;return world
def dilate(mask,radius,manhattan=False):
 pad=np.pad(mask,radius);result=np.zeros_like(mask)
 for dy in range(-radius,radius+1):
  for dx in range(-radius,radius+1):
   if manhattan and abs(dx)+abs(dy)>radius:continue
   result|=pad[radius+dy:radius+dy+384,radius+dx:radius+dx+384]
 return result
def flash(body):
 mask=body>0;expanded=dilate(mask,1);return np.where(expanded,np.where(mask&(body!=11),10,11),0).astype(np.uint8)
for base,refs,count in [(135,[136,137],10),(139,[140,141],10)]:
 bc=composition_frame(c,0,base)
 for n in refs:
  q=composition_frame(c,0,n);sem=lambda ps:[(x['flags'],x['tile'],x['x'],x['y'])for x in ps]
  assert sem(q['parts'][:count])==sem(bc['parts'])
  ov=compose_parts(n,q['parts'][count:]);overlays[n]=ov;pred[n]=np.where(ov%16!=0,ov,a[base]);parts[n]={'body_parts':count,'effect_parts':len(q['parts'])-count,'effect_cluts':sorted({p['clut']for p in q['parts'][count:]}),'effect_world_sha256':sha(ov.tobytes())}
pred[138]=flash(a[135]);pred[142]=flash(a[139])
mask=a[139]>0;inside=mask.copy()
for dx,dy in [(-1,0),(1,0),(0,-1),(0,1)]:inside&=np.roll(np.roll(mask,dx,1),dy,0)
pred[143]=np.where(mask,np.where(inside,47,37),0).astype(np.uint8)
light=np.array([0,7,8,9,8,9,10,9,10,11,11,11,13,14,11,11],np.uint8);pred[144]=light[a[139]]
near=dilate(mask,1,True)&~mask;far=dilate(mask,2,True)&~mask&~near;ring=np.where(near,37,np.where(far,38,0)).astype(np.uint8);pred[145]=np.where(ring>0,ring,pred[144]);overlays[145]=ring
results=[]
for n in range(135,146):
 delta=pred[n]!=a[n];ys,xs=np.where(delta);results.append({'ref':n,'rule_matches_current':not np.any(delta),'different_pixels':int(delta.sum()),'difference_bbox':[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]if len(xs)else None,'current_palette_indices':np.unique(a[n]).tolist(),'stream_shared_refs':[f['index']for f in bank['frames']if f['offset']==bank['frames'][n]['offset']],'tile_count':bank['frames'][n]['tile_count'],'part_count':len(composition_frame(c,0,n)['parts'])})
for form,words in [('normal',pal),('black',black)]:
 for k in range(0,11,4):
  items=[]
  for n in range(135+k,min(146,139+k)):items.extend([(f'{n} actual',rgba(a[n],words)),(f'{n} reconstructed',rgba(pred[n],words))])
  page(items,rgba(render(arc,0,0,147)[0],words),O/f'{form}_{k//4:02}.png',cols=4,scale=4)
j={'source':str(P.relative_to(ROOT)),'source_sha256':sha(arc),'scope':'새 원화 전에 현재 몸체로 기존 파생효과를 독립 재구성한 읽기 검사. 패킹/자원변경 없음.','all_rules_exact':all(q['rule_matches_current']for q in results),'results':results,'separate_layers':parts,'light_mapping144':light.tolist(),'spark_source_preserved_in_planned_patch':True,'old_library_caution':'src.psx_hurt.edit_hurt_stream은 원작 spark0/8만 허용한다. 현재 린은0/11이므로 현재 자원에 그대로 호출하면 거부된다. 현재 효과층은 다시 채색하지 않고 바이트/좌표를 보호한다.','body_silhouette_rules':{'138':'135의8방향1px확장·외곽11/내부10','142':'139의8방향1px확장·외곽11/내부10','143':'139의4방향경계CLUT2index5·내부15','144':'139에기존LIGHT_MAP','145':'144+139의맨해튼1px/2px고리CLUT2index5/6'},'actual_gameplay':False,'visually_reviewed':True,'actually_viewed_sheets':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p.read_bytes())}for p in sorted(O.glob('*.png'))],'visual_observations':['일반·레드6시트에서 기존 몸체와 재구성 효과가 같은 위치·외곽으로 이어지는 것을 확인했다.','몸체135/139의 머리·얼굴·커프·가슴 안쪽은 대기보다 단순하며 새 원화가 필요하다. 기존 효과는 복원 규칙이 확인됐으므로 새로운 신체 외곽에 맞춰 같이 갱신할 수 있다.','CLUT2가 검게 보이는 시트는 저장 팔레트 미리보기 한계이다. 현재 게임에서 검정 전기가 표시된다는 증거로 삼지 않는다.']}
(O/'report.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'rules_exact':j['all_rules_exact'],'results':results}))
