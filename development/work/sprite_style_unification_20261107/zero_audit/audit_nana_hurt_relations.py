"""Read-only body/effect/CLUT relationships for future Nana hurt art."""
from pathlib import Path
import collections,hashlib,json,struct,sys
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import binary_dilation,label
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
from src.psx_player import composition_frame,compose_indices,decode_stream,indexed_atlas
D=Path(__file__).parent;N=D.parent/'nana_audit';O=D/'nana_hurt_relations01';O.mkdir(exist_ok=True)
p=N/'rising_repaint/packed_base_candidate_v1/PL00_U.ARC';blob=p.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(blob)=='3bd156730cb932f2a97b43acc85f0d2209537c76cbab6d298c973438bc251b42'
a=Archive(blob);refs=[*range(106,115),*range(233,237)];PBS=(0,5,6,7,8)
def signature(p):return p['flags'],p['tile'],p['x'],p['y']
def render(n,parts):
 out=np.zeros((384,384),np.uint8)
 if not parts:return out
 f=a.banks[0]['frames'][n];raw=decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128).data
 pixels,size,box,_=compose_indices(raw,f['tile_count'],{'parts':parts},allowed_cluts={0,1,2,3})
 arr=np.frombuffer(pixels,np.uint8).reshape(size[1],size[0]);ys,xs=np.nonzero(arr);out[ys+box[1]+160,xs+box[0]+160]=arr[ys,xs]
 return out
def split(reference,n,pb):
 original=composition_frame(a.c,pb,reference)['parts'];curr=composition_frame(a.c,pb,n)['parts']
 remaining=collections.Counter(signature(p)for p in original);body=[];extra=[]
 for part in curr:
  key=signature(part)
  if remaining[key]:body.append(part);remaining[key]-=1
  else:extra.append(part)
 assert not any(remaining.values()),(reference,n,pb)
 return body,extra
result=[];panels=[];relations=[]
for n in refs:
 f=a.banks[0]['frames'][n];raw=decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128).data
 atlas=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256)
 owners=[x['index']for x in a.banks[0]['frames']if x['offset']==f['offset']]
 row={'ref':n,'stream_offset':f['offset'],'tiles':f['tile_count'],'shared_stream_owners':owners,'layers':{}}
 for pb in PBS:
  parts=composition_frame(a.c,pb,n)['parts'];pix=render(n,parts)
  row['layers'][str(pb)]={'parts':[{'record':r['index'],'tile':r['tile'],'world':[r['x'],r['y']],'clut':r['clut'],'flip_x':r['flip_x'],'flip_y':r['flip_y']}for r in parts],
    'raw_index_counts':{str(int(v)):int(c)for v,c in zip(*np.unique(pix[pix>0],return_counts=True))},'indexed_sha256':sha(pix.tobytes())}
  if pb==0:panels.append((f'{n} base actual CLUT',a.rgba(pix)))
 reference=106 if n in(107,108)else 110 if n==111 else None
 if reference is not None:
  deriv={'ref':n,'body_reference':reference,'layers':{}}
  for pb in PBS:
   body,fx=split(reference,n,pb);bp=render(n,body);fp=render(n,fx)
   assert np.array_equal(bp,render(reference,composition_frame(a.c,pb,reference)['parts']))
   fx_tiles=sorted({p['tile']for p in fx});tilehashes={str(t):sha(atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16].tobytes())for t in fx_tiles}
   deriv['layers'][str(pb)]={'body_records_exact':True,'extra_effect_records':[{'flags':p['flags'],'tile':p['tile'],'x':p['x'],'y':p['y'],'clut':p['clut']}for p in fx],'effect_tiles':fx_tiles,'tile_sha256':tilehashes,'effect_opaque_pixels':int(np.count_nonzero(fp))}
   if pb==0:
    a.rgba(bp).save(O/f'{n:03}_body.png');a.rgba(fp).save(O/f'{n:03}_effect.png');panels.append((f'{n} effect only CLUT',a.rgba(fp)))
  relations.append(deriv)
 result.append(row)
mask106=a.layer(106)[0]>0;flash=a.layer(109)[0]
assert np.array_equal(flash==13,mask106)
assert np.array_equal(flash==9,binary_dilation(mask106,iterations=1)&~mask106)
anims=json.loads((ROOT/'work/sprite_consistency_20261105/coverage/ver_rin_nana/x_animations.json').read_text('utf8'))
seqs=[]
for anim in anims['animations']:
 if not any(s['frame']in refs for s in anim['steps']):continue
 seqs.append({'id':anim['id'],'address':anim['address'],'steps':[{'position':s['position'],'frame':s['frame'],'calls':s['duration_calls_uninterrupted'],'event':s['event_signed'],'relative_step':s['relative_step']}for s in anim['steps']]})
for n in(235,236):
 row=next(r for r in result if r['ref']==n)
 row['notes']='현재 본체 조립은 CLUT0만 사용하고234와raw공유도없다. 표시 몸체는234와 같고 별도 제작한 나나 오라가 기본층에 함께 들어 있다.235/236을234+CLUT2효과로가정하지말것.'
historical=ROOT/'work/ver_rin_nana/nana_art/hurt_v1/production02'
invpath=ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/inventory.json'
inv=json.loads(invpath.read_text('utf8'))
def original(n):
 v=np.array(Image.open(invpath.parent/f'base_{n:03d}.png'))
 box=inv['base_frames'][n]['bounds'];out=np.zeros((384,384),np.uint8)
 ys,xs=np.nonzero(v);out[ys+box[1]+160,xs+box[0]+160]=v[ys,xs]%16
 return out
def historical_canvas(path,origin):
 v=np.array(Image.open(path));out=np.zeros((384,384),np.uint8)
 out[160-origin[1]:160-origin[1]+v.shape[0],160-origin[0]:160-origin[0]+v.shape[1]]=v
 return out
source_files=[invpath,ROOT/'scripts/normalize_nana_hurt.py',ROOT/'scripts/prepare_nana_hurt_aura.py',ROOT/'scripts/prepare_nana_hurt_aura_reference.py']
launch=a.layer(110)[0];old=original(110)>0;new=launch>0;derived=[]
for n in(112,113,114):
 path=historical/f'frame_{n:03d}.png';source_files.append(path)
 v=original(n);v[binary_dilation(old,iterations=2)]=0
 if n==114:v[np.isin(v,[3,5])]=0
 residual=v.copy()
 if n==112:v[binary_dilation(new)]=6;v[new]=14
 elif n==113:v[binary_dilation(new)]=1
 else:
  v[binary_dilation(new)]=1;v[new]=3;v[np.isin(launch,[1,2,4,8,15])]=5;v[np.isin(launch,[6,9])]=1
 labels,_=label(v>0);sizes=np.bincount(labels.ravel());removed=(sizes[labels]<4)&(labels!=0);v[removed]=0
 target=a.layer(n)[0]%16
 assert np.array_equal(v,target),(n,'historical silhouette rule does not match current')
 assert np.array_equal(historical_canvas(path,(48,40)),target),(n,'historical image mismatch')
 rule={112:'외부 잔여 원효과 위 Manhattan1 외곽6, 새110알파 내부14',113:'외부 잔여 원효과 위 Manhattan1 팽창 전체1',114:'외부 잔여 원효과 위 외곽1/내부3; 110색1·2·4·8·15→5, 6·9→1'}[n]
 derived.append({'ref':n,'historical_source':path.relative_to(ROOT).as_posix(),'historical_source_sha256':sha(path.read_bytes()),'current_exact':True,
  'body_ref':110,'base_clut':2,'rule':rule,'original_x_silhouette_removed':'원작110알파 Manhattan2 팽창 영역을 제거;114는남은색3/5도제거',
  'residual_effect_sha256':sha(residual.tobytes()),'residual_effect_pixels':int(np.count_nonzero(residual)),'historical_small_components_removed_pixels':int(np.count_nonzero(removed)),
  'small_component_rule':'합성 뒤 4연결 성분이4px미만이면 제거(과거구현). 새원화의세부를자동삭제하는규칙으로확대하지말것.'})
 a.rgba(np.where(residual,residual+32,0).astype(np.uint8)).save(O/f'{n}_residual_original_effect.png')
aura=ROOT/'work/ver_rin_nana/nana_fourth_armor/hurt_aura_packed_v1';aura_relations=[]
for n in(235,236):
 body=a.layer(234)[0];target=a.layer(n)[0];assert np.array_equal(target[body>0],body[body>0])
 effect=np.where(body==0,target,0).astype(np.uint8);path=aura/f'effect_{n}.png';source_files.append(path)
 assert np.array_equal(effect,historical_canvas(path,(80,80))),(n,'historical generated aura mismatch')
 layers=[]
 for pb in PBS[1:]:
  assert np.array_equal(a.layer(n,pb)[0],a.layer(234,pb)[0]),(n,pb,'body armor mismatch')
  layers.append(pb)
 tested=0
 for mask in range(16):
  for arm in(1,2):
   b=np.array(a.composite(234,mask,arm)[0]);q=np.array(a.composite(n,mask,arm)[0]);opaque=b[:,:,3]>0
   assert np.array_equal(b[opaque],q[opaque]),(n,mask,arm)
   tested+=1
 aura_relations.append({'ref':n,'body_reference':234,'body_base_and_armor_exact':True,'base_and_full_source_independent':True,
  'body_pixels':int(np.count_nonzero(body)),'effect_pixels':int(np.count_nonzero(effect)),'body_partial_rgba_conditions':tested,
  'effect_source':path.relative_to(ROOT).as_posix(),'effect_source_sha256':sha(path.read_bytes()),'effect_historical_exact':True,
  'effect_generation_source':'work/ver_rin_nana/nana_fourth_armor/hurt_aura_v1/generated.png',
  'effect_origin':'2026-10-30 사용자가 X외곽 잔존을 지적하여 나나 전신/부분아머 union에맞춰 별도생성한 오라. 원작X효과 그대로가아님.',
  'reuse_limit':'새234의알파/부분의상과 오라의겹침·간격을 재검토. 과거좌표를그대로보존하는것만으로새몸정합완료라고하지않는다.'})
 a.rgba(effect).save(O/f'{n}_accepted_aura_only.png')
# Every panel uses the same world window, including tall electrical FX.
images=[];box=(130,124,192,202);scale=5;cw,ch=330,420
for page in range((len(panels)+5)//6):
 subset=panels[page*6:page*6+6];sheet=Image.new('RGB',(cw*3,ch*2),'#263345');dr=ImageDraw.Draw(sheet)
 for k,(label,pic)in enumerate(subset):
  x,y=k%3*cw,k//3*ch;dr.text((x+5,y+5),label,fill='white');q=pic.crop(box).resize(((box[2]-box[0])*scale,(box[3]-box[1])*scale),Image.Resampling.NEAREST);sheet.paste(q,(x+10,y+25),q)
 q=O/f'body_effect_{page:02}.png';sheet.save(q);images.append({'path':q.relative_to(ROOT).as_posix(),'sha256':sha(q.read_bytes())})
report={'scope':'현재 나나 PL00 피격 원화 준비용 몸체/효과/공유 분리 읽기 조사. 새그림 패킹이나 게임 변경 없음.',
 'source':p.relative_to(ROOT).as_posix(),'source_sha256':sha(blob),'references':result,'body_plus_effect_relations':relations,
 'flash109':{'body_ref':106,'body_index':13,'outline_index':9,'outline':'Manhattan 1px dilation','parent_reconstructed_exact':True},
 'animation_sequences':seqs,'sequence_source':'work/sprite_consistency_20261105/coverage/ver_rin_nana/x_animations.json',
 'sheets':images,'actual_sheet_views':True,'viewed_sheets':[r['path']for r in images],
 'derived_clut2_silhouettes':derived,'body234_with_accepted_aura':aura_relations,
 'historical_evidence_files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}for p in source_files],
 'recommendations':[
  '106/107/108은동일19타일raw.107/108의몸체·부분의상기록은106과같고효과기록만추가되므로새106전체층을공유하고원효과타일/기록을보호한다.',
  '110/111은동일27타일raw.111은base층에CLUT2효과12records를추가하며그타일6..17전체를보존한다.새110전신을111에공유할때effect를16색몸체로양자화하지않는다.',
  '112..114는base parts전부CLUT2이며부분의상은빈타일이다.110의알파·일부내부색을쓰는과거파생규칙을현재표시와완전히재현했다.새110기준으로실루엣을동기화하되외부원효과를보호한다.자동전신생성대상으로넣지않는다.',
  '109는현106알파의색13몸체+색9한픽셀테두리와정확히일치하므로새106알파에도같은규칙으로동기화가능하다.',
  '235/236은현재독립raw지만234의기본/아머그림과완전히같은몸이다.나나용기수용오라85/172px가추가되므로새몸234를공유하고오라접점을새그림과다시검토한다.효과원화없이각몸을새로생성할필요는없다.'
 ],'limits':['현재원화/조립관계이며새원화수용·재삽입·MIPS·실기를수행했다는뜻아님.','애니메이션은기존원본바이트동일coverage표를참조했으며이번새게임코드실행은없음.','부분아머층의effect는원렌더러가고정CLUT를사용하므로원래물리타일과각층의추가조립을함께보호한다.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'report_sha256':sha((O/'report.json').read_bytes()),'relations':len(relations),'animation_ids':[s['id']for s in seqs],'sheets':len(images)}))
