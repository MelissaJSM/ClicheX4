"""확정된 다리 재질만 바꾸고 원래 조립·외곽·팔레트를 보존한다."""
from pathlib import Path
from collections import defaultdict
import hashlib,json,sys
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(H))
import numpy as np
from PIL import Image
from leg_material_expanded import SRC,SHA,REFS,targets,material_masks
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page
from scripts.prepare_riko_ui import entry
from scripts.restore_shibuki_special_detail import entry_replace
from src.psx_player import bank_offsets,graphics_bank,decode_stream,composition_frame,compose_indices,indexed_atlas
from src.psx_ui_atlas import local_composition
from src.psx_compress import encode_stream
from src.psx_bank_repack import repack_graphics_bank
from src.psx_disc import file_hash

BASE='884aeb493f23579a525000954031242e53fb13ebbdc28e0e09213bb599837f99'
SOURCE_ART='b6a4f2a5a321e8c37575e6593c3b86f396151c16a16690e16054c86e75f3fd59'
PARTS=(0,5,6,7,8)
def sha(b):return hashlib.sha256(b).hexdigest()
def need(ok,why):
 if not ok:raise ValueError(why)
def write(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n','utf8')
def raw_at(g,b,n):
 f=graphics_bank(g,b,allow_bank_aliases=True)['frames'][n]
 d=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128)
 return d.data,f,bytes(g[f['offset']:d.end])

def patch(data,source):
 need(sha(data)==BASE,'Unsupported current PL02 source')
 need(sha(source)==SOURCE_ART,'Unsupported PL00 material reference')
 arc=Archive(data);src=Archive(source);desired,recipe=targets(arc,src)
 g,c,p=arc.g,arc.c,arc.p
 aliases=defaultdict(list)
 for f in arc.banks[0]['frames']:aliases[f['offset']].append(f['index'])
 encoded={};expected={};proof=[]
 for n in REFS:
  raw,f,_=raw_at(g,0,n);writes={};layer_proof=[]
  need(set(aliases[f['offset']]).issubset(REFS),'Selected stream has an unselected reference')
  for pb in PARTS:
   cp=composition_frame(c,pb,n);cp=local_composition(cp) if pb else cp
   if not cp['parts']:
    need(not desired[n][pb].any(),'Expected empty layer');continue
   pixels,size,box,owners=compose_indices(raw,f['tile_count'],cp,allowed_cluts={0,1,2,3})
   target=desired[n][pb][160+box[1]:160+box[3],160+box[0]:160+box[2]].tobytes()
   need(len(pixels)==len(target),'Canvas mismatch')
   changes=0
   for k,(a,b) in enumerate(zip(pixels,target)):
    need(bool(a)==bool(b),'Alpha change rejected')
    if a==b:continue
    owner=owners[k];need(owner is not None and 0<b<16,'Invalid visible texel')
    key=(owner['byte'],owner['shift']);need(key not in writes or writes[key]==b,'Conflicting shared texel')
    writes[key]=b;changes+=1
   layer_proof.append({'bank':pb,'changed_visible_pixels':changes})
  new=bytearray(raw)
  for (offset,shift),v in writes.items():new[offset]=new[offset]&~(15<<shift)|v<<shift
  new=bytes(new)
  aa=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256)
  bb=np.frombuffer(indexed_atlas(new,f['tile_count'])[0],np.uint8).reshape(-1,256)
  need(np.array_equal(aa>0,bb>0),'Raw alpha changed')
  need(np.array_equal(aa[:,0],bb[:,0]),'GPU U boundary column changed')
  edgechecks=[]
  for pb in PARTS:
   for pp in composition_frame(c,pb,n)['parts']:
    if pp['flip_y']:
     tx=pp['tile']%16*16;ty=pp['tile']//16*16
     need(np.array_equal(aa[ty,tx:tx+16],bb[ty,tx:tx+16]),'GPU flipped V boundary changed')
     edgechecks.append([pb,pp['index'],pp['tile']])
  expected[n]=new;encoded[n]=encode_stream(new)
  proof.append({'ref':n,'tile_count':f['tile_count'],'changed_raw_texels':len(writes),'before_raw':sha(raw),'after_raw':sha(new),'layers':layer_proof,'alpha_exact':True,'gpu_u_boundary_exact':True,'gpu_v_boundaries_exact':edgechecks})
 shared_rules=[]
 for shared in aliases.values():
  selected=[n for n in shared if n in encoded]
  if not selected:continue
  canonical=min(selected);original,_,_=raw_at(g,0,canonical);merged=bytearray(original);used={}
  for n in selected:
   for i,(old,new) in enumerate(zip(original,expected[n])):
    for shift in (0,4):
     av=(old>>shift)&15;bv=(new>>shift)&15
     if av==bv:continue
     key=(i,shift);need(key not in used or used[key]==bv,f'Shared target conflict {selected}/{key}')
     used[key]=bv;merged[i]=merged[i]&~(15<<shift)|bv<<shift
  merged=bytes(merged)
  for n in selected:encoded[n]=encode_stream(merged);expected[n]=merged
  shared_rules.append({'refs':selected,'merged_changed_texels':len(used),'policy':'동일 압축 스트림 내 각 사격/입자 변형이 실제로 사용하는 하체 texel 변경의 합집합. 값 충돌 거부 및 모든 변형 목표 이미지 완전 일치 검사.'})
 ng,packing=repack_graphics_bank(g,0,encoded);result=entry_replace(data,2,ng)
 need(entry_replace(result,2,g)==data,'Unrelated ARC entries changed')
 out=Archive(result);raw_checks=0;changed=[]
 for gb in range(len(arc.banks)):
  for f in arc.banks[gb]['frames']:
   n=f['index'];a,af,ac=raw_at(g,gb,n);b,bf,bc=raw_at(ng,gb,n)
   need(af['tile_count']==bf['tile_count'],'Tile count changed')
   need(b==(expected[n] if gb==0 and n in expected else a),f'Unexpected decoded reference {gb}/{n}')
   if a==b:need(ac==bc,'Unselected encoded stream changed')
   else:changed.append([gb,n])
   raw_checks+=1
 need(changed==[[0,n] for n in REFS],'Changed reference set differs')
 layer_checks=0;mask_checks=0;main_checks=0;exceptions=[];visible_changes=[]
 for n in range(237):
  if n in [105,*range(175,183)]:exceptions.append(n);continue
  for pb in PARTS:
   a=arc.layer(n,pb)[0];b=out.layer(n,pb)[0];want=desired[n][pb] if n in desired else a
   need(np.array_equal(b,want),f'Layer target mismatch {n}/{pb}: {int((b!=want).sum())}')
   need(np.array_equal(a>0,b>0),'Layer silhouette changed')
   if n in desired:
    skin,shoe,_=material_masks(n,arc.layer(n)[0],arc)
    need(not np.any((a!=b)&~(skin|shoe)),'Outside material region changed')
   layer_checks+=1
  for mask in (0,15):
   for arm in (1,2):
    aa=np.asarray(arc.composite(n,mask,arm)[0]);bb=np.asarray(out.composite(n,mask,arm)[0])
    need(np.array_equal(aa[:,:,3],bb[:,:,3]),'Composite alpha changed')
    if n not in desired:need(np.array_equal(aa,bb),'Nonselected main pose changed')
    else:
     count=int(np.any(aa!=bb,axis=2).sum());need(count>0,f'Selected pose did not actually change {n}/{mask}/{arm}')
     visible_changes.append({'ref':n,'mask':mask,'arm':arm,'changed_rgba_pixels':count})
    main_checks+=1
  if n in desired:
   for mask in range(16):
    for arm in (1,2):
     want=arc.rgba(desired[n][0])
     for bit,pb in ((8,8),(1,5),(4,7),(2,6)):
      if mask&bit:want.alpha_composite(arc.rgba(desired[n][pb],32 if pb==7 and arm==2 else 16))
     need(want.tobytes()==out.composite(n,mask,arm)[0].tobytes(),'Mask composite differs')
     mask_checks+=1
 for row in proof:
  n=row['ref'];old,_,_=raw_at(g,0,n);new=expected[n]
  row['after_raw']=sha(new);row['changed_raw_texels']=sum(((a&15)!=(b&15))+((a>>4)!=(b>>4)) for a,b in zip(old,new))
  row['layers']=[{'bank':pb,'changed_visible_pixels':int((arc.layer(n,pb)[0]!=out.layer(n,pb)[0]).sum())} for pb in PARTS]
 return result,{'passed':True,'before':sha(data),'after':sha(result),'source_material':sha(source),'frames':proof,'recipe':recipe,'shared_stream_rules':shared_rules,'packing':packing,'changed_raw_refs':changed,'all_raw_refs':raw_checks,'layer_checks':layer_checks,'main_form_checks':main_checks,'selected_all_mask_checks':mask_checks,'selected_visible_changes':visible_changes,'all_selected_layer_targets_exact':True,'unrendered_reserved_refs':exceptions,'all_composition_palette_audio_entries_exact':True,'silhouette_all_exact':True,'coordinates_exact':True,'no_new_gpu_boundary_texels':True,'runtime_verified':False}

def main():
 need(file_hash(SRC)==SHA,'Wrong source BIN')
 assets,records=read_disc(SRC,('PL00_U.ARC','PL02_U.ARC'))
 result,proof=patch(assets['PL02_U.ARC'],assets['PL00_U.ARC'])
 again,_=patch(assets['PL02_U.ARC'],assets['PL00_U.ARC']);need(again==result,'Nonreproducible result')
 rejects=[]
 for label,a,b in [('changed_current',bytes([assets['PL02_U.ARC'][0]^1])+assets['PL02_U.ARC'][1:],assets['PL00_U.ARC']),('changed_material',assets['PL02_U.ARC'],bytes([assets['PL00_U.ARC'][0]^1])+assets['PL00_U.ARC'][1:]),('already_patched',result,assets['PL00_U.ARC'])]:
  try:patch(a,b)
  except ValueError as e:rejects.append({'case':label,'error':str(e)})
  else:raise ValueError('Invalid input accepted')
 folder=H/'prepared_v4';folder.mkdir(exist_ok=True);path=folder/'PL02_U.ARC';path.write_bytes(result)
 proof.update({'reproduction_exact':True,'rejected_inputs':rejects});write(folder/'verification.json',proof)
 write(folder/'proposal.json',{'project':'ver_buki_riko','baseline':SRC.relative_to(ROOT).as_posix(),'baseline_sha256':SHA,'files':{'PL02_U.ARC':{'before':sha(assets['PL02_U.ARC']),'after':sha(result),'size':len(result),'path':path.relative_to(ROOT).as_posix(),'record':records['PL02_U.ARC']}},'scope':'Ultimate 11..16 및 33..84의 피부/샌들 재질 58참조. 좌표·외곽·팔레트·다른 프레임 보존.','runtime_verified':False})
 a=Archive(assets['PL02_U.ARC']);b=Archive(result);items=[]
 for n in REFS:
  for mask,label in ((0,'after'),(15,'before')):
   old=a.composite(n,mask)[0];new=b.composite(n,mask)[0];old.save(folder/f'{label}_{n:03}_before.png');new.save(folder/f'{label}_{n:03}_after.png')
   diff=np.any(np.array(old)!=np.array(new),axis=2);r=np.zeros((384,384,4),np.uint8);r[diff]=[255,50,60,255];Image.fromarray(r).save(folder/f'{label}_{n:03}_changes.png')
   items.extend([(f'{label} {n} old',old),(f'{label} {n} restored',new)])
 page(items,a.composite(0,0)[0],folder/'comparison.png',cols=4,scale=3)
 print(json.dumps({'path':str(path),'sha256':sha(result),'raw_refs':proof['all_raw_refs'],'layers':proof['layer_checks'],'forms':proof['main_form_checks'],'masks':proof['selected_all_mask_checks'],'repro':True,'rejections':len(rejects)}))
if __name__=='__main__':main()
