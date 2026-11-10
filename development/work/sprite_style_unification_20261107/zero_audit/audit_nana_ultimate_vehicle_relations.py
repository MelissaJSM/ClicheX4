"""Ultimate 차량 원US/역사4키/현재후폼 별칭 의미 독립 읽기."""
from pathlib import Path
import json,hashlib,sys
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;B=D.parent;N=B/'nana_audit';O=D/'nana_ultimate_vehicle_relations01'
sys.path[:0]=[str(ROOT),str(D)]
from scripts.export_x_consistency import Archive
from scripts.c01_audio_build import read_disc
from verify_shibuki_ultimate_hurt13_independent import raw,parts,sig
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();tracked={}
def blob(p):
 v=p.read_bytes();tracked[rel(p)]=sha(v);return v
def js(p):return json.loads(blob(p))
def png(p):blob(p);return np.array(Image.open(p))
def merged(a,n,mask):
 z=a.layer(n,0)[0].copy()
 for bit,pb in((8,8),(1,5),(4,7),(2,6)):
  if mask&bit:
   v=a.layer(n,pb)[0];z[v>0]=v[v>0]
 return z
def shift(z,dy):
 out=np.zeros_like(z);out[max(dy,0):min(384,384+dy)]=z[max(-dy,0):min(384,384-dy)];return out
def bbox(z):
 y,x=np.nonzero(z);return [int(x.min()-160),int(y.min()-160),int(x.max()+1-160),int(y.max()+1-160)]if len(x)else None
H=ROOT/'work/ver_rin_nana/nana_ultimate_armor';V=H/'vehicle_packed_v4';norm=ROOT/'work/overhaul_20261105/sprites/nana_preultimate/normalized'
paths={'current':N/'ultimate_special_finish_repaint/packed_special_candidate_v1/PL02_U.ARC','previous':N/'ultimate_recoil_repaint/packed_recoil_candidate_v1/PL02_U.ARC','historical_vehicle':V/'PL02_U.ARC','overhaul_baseline':ROOT/'work/overhaul_20261105/sprites/ver_rin_nana/baseline/PL02_U.ARC'}
arcs={k:Archive(blob(p))for k,p in paths.items()};cur=arcs['current'];previous=arcs['previous'];hist=arcs['historical_vehicle'];baseline=arcs['overhaul_baseline']
assert sha(cur.data)=='56a3aeb489229d85bb72205bd14f866b4444ff5daa8e1bc7f91c82e9b3c46fc0'
assets,_=read_disc(ROOT/'MegaMan X4.bin',('PL00_U.ARC','PL02_U.ARC'))
arcs['original_US_PL00']=Archive(assets['PL00_U.ARC']);arcs['original_US_PL02']=Archive(assets['PL02_U.ARC'])
PBS=(0,5,6,7,8);REFS=range(162,175);GROUPS=((162,163,164,165),(166,167,168,169),(170,171,172,173),(174,));DY={162:0,163:1,164:3,165:-1,166:0,167:1,168:3,169:-1,170:0,171:1,172:2,173:-1,174:0}
for n in REFS:
 assert raw(cur,0,n)==raw(previous,0,n)
 for pb in PBS:assert [sig(q)for q in parts(cur,pb,n)]==[sig(q)for q in parts(previous,pb,n)]
relations=[]
for tag,a in arcs.items():
 for group in GROUPS:
  master=group[0]
  for n in group[1:]:
   row={'archive':tag,'source':master,'target':n,'dx':0,'dy':DY[n],'layers':{},'forms':{}}
   for pb in PBS:
    x,y=shift(a.layer(master,pb)[0],DY[n]),a.layer(n,pb)[0]
    row['layers'][str(pb)]={'changed':int((x!=y).sum()),'alpha_changed':int(((x>0)!=(y>0)).sum()),'bbox':bbox(x!=y),'source_parts':[sig(q)for q in parts(a,pb,master)],'target_parts':[sig(q)for q in parts(a,pb,n)]}
   for form,mask in(('before',15),('after',0)):
    x,y=shift(merged(a,master,mask),DY[n]),merged(a,n,mask);diff=x!=y
    row['forms'][form]={'changed':int(diff.sum()),'alpha_changed':int(((x>0)!=(y>0)).sum()),'bbox':bbox(diff),'delta_cells':[[int(xx-160),int(yy-160),int(x[yy,xx]),int(y[yy,xx])]for yy,xx in np.argwhere(diff)]}
   relations.append(row)
recipe=js(V/'recipe.json');normalization=js(norm/'normalization.json');plan=js(norm.parent/'production_plan.json');history=[];derivations=[]
for n in REFS:
 z=png(V/f'ultimate_{n:03}.png');full=np.zeros((384,384),np.uint8);full[80:240,80:240]=z
 assert np.array_equal(full,merged(hist,n,15))
 nz=png(norm/f'{n:03}.png')
 history.append({'ref':n,'historical_png':rel(V/f'ultimate_{n:03}.png'),'historical_indexed_exact':True,'current_before_equals_historical':bool(np.array_equal(full,merged(cur,n,15))),'current_after_equals_normalized':bool(np.array_equal(nz,merged(cur,n,0))),'registration':next(q for q in recipe['registration']if q['frames'][0]==n),'own_generated_report':next((q for q in normalization['reports']if q['frame']==n),None),'alias_derived_record':next((q for q in normalization['aliases_derived']if q['frame']==n),None)})
for group in GROUPS[:3]:
 master=group[0];bodies=[merged(baseline,n,15)for n in group];overlays=[];bases=[]
 for n in group:
  z=np.zeros((384,384),np.uint8)
  for pb in(8,5,7,6):
   v=baseline.layer(n,pb)[0];z[v>0]=v[v>0]
  overlays.append(z);bases.append(baseline.layer(n,0)[0])
 common=np.all(np.stack(bodies)==bodies[0],axis=0);covered=np.all(np.stack(overlays)>0,axis=0)
 master_target=png(norm/f'{master:03}.png');shared=master_target.copy();shared[common&~covered]=bodies[0][common&~covered]
 for i,n in enumerate(group[1:],1):
  out=master_target.copy();out[bodies[i]!=bodies[0]]=bodies[i][bodies[i]!=bodies[0]];out[overlays[i]==0]=bases[i][overlays[i]==0]
  out[common]=shared[common];out[overlays[i]==0]=bases[i][overlays[i]==0]
  saved=png(norm/f'{n:03}.png')
  derivations.append({'ref':n,'master':master,'historical_unshifted_fallback_reconstructed_exact':bool(np.array_equal(out,saved)),'changed_vs_saved':int((out!=saved).sum()),'fallback_rule':'master未平行移動→元acquired表示がmasterと異なるセルを各frame値で戻す→overlay外base→共通セルcoherence','separate_generated_body':any(q['frame']==n for q in normalization['reports'])})
for q in derivations:q['fallback_rule']='마스터를 이동하지 않고 복사한 뒤 기존 acquired 표시의 서로 다른 셀/overlay 밖 원base를 되돌리고 공통셀을 맞춘 역사 파생'
frames=[]
for n in REFS:
 f=cur.banks[0]['frames'][n];record_shares=[]
 for pb in PBS:
  pp=parts(cur,pb,n);slots={q['record_offset']for q in pp}
  owners=[m for m in range(237)if m not in REFS and slots&{q['record_offset']for q in parts(cur,pb,m)}]
  if owners:record_shares.append({'bank':pb,'non_target_owners':owners,'records':pp})
 frames.append({'ref':n,'raw_owners':[q['index']for q in cur.banks[0]['frames']if q['offset']==f['offset']],'tile_count':f['tile_count'],'non_target_record_shares':record_shares})
for name in('prepare_nana_ultimate_vehicle.py','overhaul_sprites_costume.py','overhaul_sprites_costume_pack.py'):blob(ROOT/'scripts'/name)
tables=js(ROOT/'work/sprite_consistency_20261105/coverage/ver_rin_nana/x_animations.json')
used=[q for q in tables['animations']if any(s['frame']in REFS for s in q['steps'])]
O.mkdir(exist_ok=False);boards=[]
for group in GROUPS[:3]:
 master=group[0];box=(125,119,191,190);w,h=66,71;cw,ch=w*4+5,h*4+24
 board=Image.new('RGB',(cw*4,ch*2),'#263345');draw=ImageDraw.Draw(board)
 for row,(form,mask)in enumerate((('before',15),('after',0))):
  for col,n in enumerate(group):
   pic=cur.composite(n,mask)[0];bb=pic.getbbox();assert box[0]<=bb[0]and box[1]<=bb[1]and box[2]>=bb[2]and box[3]>=bb[3]
   x,y=col*cw,row*ch;draw.text((x+3,y+3),f'{n} {form} dy{DY[n]:+}',fill='white');im=pic.crop(box).resize((w*4,h*4),Image.Resampling.NEAREST);board.paste(im,(x+3,y+22),im)
 p=O/f'current_group_{master}.png';board.save(p);boards.append({'path':rel(p),'sha256':sha(p.read_bytes())})
for p,h in tracked.items():assert sha((ROOT/p).read_bytes())==h,p
report={'scope':'나나 Ultimate 차량162..174의 원US·역사원화·후폼정규화·현재공유를 읽기만 비교','current_sha256':sha(cur.data),'previous_vehicle_bytes_and_records_exact':True,'original_US_hashes':{k:sha(v)for k,v in assets.items()},'inputs':tracked,'relations':relations,'historical_provenance':history,'normalized_alias_reconstruction':derivations,'current_shared_frames':frames,'existing_animation_table_evidence':used,'boards':boards,'producer_functions_called':False,'native_MIPS_executed':False,'runtime_verified':False,'limits':['원US 원화와 현재 수용후폼의 차이를 구분한다. 신규13참조를 전부 원작동일복원으로 부르지 않는다.','원애니메이션 표는 기존추출 증거를 읽어 사용했으며 새EXE 실행/실기조작은 하지 않았다.','현재 역사후폼의 파생차이 존재는 신규4고유자세를 같은Y별칭으로 제작할 수 없다는 뜻이 아니다. 새공통정책 수용과 구분한다.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'report_sha256':sha((O/'report.json').read_bytes()),'current':[{'source':q['source'],'target':q['target'],'before':q['forms']['before']['changed'],'after':q['forms']['after']['changed']}for q in relations if q['archive']=='current'],'US':[{'source':q['source'],'target':q['target'],'before':q['forms']['before']['changed'],'after':q['forms']['after']['changed']}for q in relations if q['archive']=='original_US_PL02'],'alias_rebuild':derivations,'history_exact':[(q['ref'],q['current_before_equals_historical'],q['current_after_equals_normalized'])for q in history]},ensure_ascii=False))
