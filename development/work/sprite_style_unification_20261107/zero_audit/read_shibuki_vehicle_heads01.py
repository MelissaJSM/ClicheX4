"""작은 차량머리19+빈198의 원US/현재 소유·공유를 독립으로 읽는다."""
from pathlib import Path
import sys,json,hashlib,collections
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent;H=W/'shibuki_audit';O=D/'shibuki_vehicle_head_ownership01';assert not O.exists()
sys.path[:0]=[str(R),str(D)]
from scripts.export_x_consistency import Archive
from scripts.c01_audio_build import read_disc
from src.psx_player import composition_frame,bank_offsets
from verify_shibuki_ultimate_hurt13_independent import raw,sig,tile
PBS=(0,5,6,7,8);REFS=set(range(184,204));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();hb=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(R).as_posix();tracked={}
def blob(p):tracked[rel(p)]=sha(p);return p.read_bytes()
def bbox(m):y,x=np.nonzero(m);return[int(x.min()-160),int(y.min()-160),int(x.max()-159),int(y.max()-159)]if len(x)else None
original,_=read_disc(R/'MegaMan X4.bin',('PL00_U.ARC','PL02_U.ARC'))
arcs={'US00':Archive(original['PL00_U.ARC']),'US02':Archive(original['PL02_U.ARC']),'current00':Archive(blob(H/'prepared_nova_strike_base01/PL00_U.ARC')),'current02':Archive(blob(H/'prepared_nova_strike_ultimate01/PL02_U.ARC'))}
assert hb(arcs['current00'].data)=='36d4d0293abc77052c476e0495f4f4542ca75471c7a149f200e4bdb8f4e1bd4e'
assert hb(arcs['current02'].data)=='01997c949968d5a1a12d89e09c5eb46448bbcf245009feb9953e3d9e9356efd7'
other=Archive(blob(H/'prepared_hover_ultimate01/PL02_U.ARC'))
for n in REFS:
 assert raw(arcs['current02'],0,n)==raw(other,0,n)
 for p in PBS:assert np.array_equal(arcs['current02'].layer(n,p)[0],other.layer(n,p)[0])and[sig(x)for x in arcs['current02'].layer(n,p)[1]['parts']]==[sig(x)for x in other.layer(n,p)[1]['parts']]
ui=json.loads(blob(H/'vehicle_head_accessory_read01/report.json'));assert hb((H/'vehicle_head_accessory_read01/report.json').read_bytes())=='e8d966939bbce92eddecac550c58a63dbe94ea2aee7ef482c5ce80e94372891f'
blob(H/'vehicle_head_accessory_read01/conclusions.json');blob(H/'vehicle_head_accessory_read01/four_forms_existing_head.png')
details={};group_summary={};outside_nonempty=[]
for name,a in arcs.items():
 users=collections.defaultdict(set)
 for pb in range(len(bank_offsets(a.c))):
  for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
   for p in composition_frame(a.c,pb,n)['parts']:users[p['record_offset']].add((pb,n))
 rows=[];groups={}
 for n in sorted(REFS):
  f=a.banks[0]['frames'][n];owners=[x['index']for x in a.banks[0]['frames']if x['offset']==f['offset']];groups[f['offset']]={'offset':f['offset'],'tiles':f['tile_count'],'owners':owners,'raw_sha256':hb(raw(a,0,n))};ll=[]
  for pb in PBS:
   z,c=a.layer(n,pb);outside={};pts=[]
   for p in c['parts']:
    outside[str(p['record_offset'])]=[list(x)for x in sorted(users[p['record_offset']])if not(x[0]in PBS and x[1]in REFS)]
    ti=p['tile']+p['page']*256;v=tile(a,n,ti)
    pts.append({'record':p,'whole_tile_sha256':hb(v.tobytes()),'opaque_in_whole_tile':int((v>0).sum()),'U_first_column':int((v[:,0]>0).sum())if ti%16==0 else None})
   outside={k:v for k,v in outside.items()if v}
   if outside and z.any():outside_nonempty.append([name,n,pb,outside])
   ll.append({'part':pb,'bbox':bbox(z>0),'opaque':int((z>0).sum()),'indices_sha256':hb(z.tobytes()),'parts':pts,'outside_record_owners':outside})
  assert not any(a.layer(n,p)[0].any()for p in(6,7,8)),(name,n)
  # 전부분 조합은 오직 head 비트1의 유무에만 달라지는지 확인한다.
  for m in range(16):
   for arm in(1,2):assert np.array_equal(np.array(a.composite(n,m,arm)[0]),np.array(a.composite(n,m&1)[0]))
  rows.append({'ref':n,'stream_owners':owners,'layers':ll,'all32_combinations_only_head_bit':True})
 details[name]=rows;group_summary[name]=list(groups.values())
forms=[];previews=[]
for form,name,mask in(('base','current00',0),('fourth','current00',15),('ultimate_before','current02',15),('ultimate_after','current02',0)):
 a=arcs[name];old=arcs['US00'if name=='current00'else'US02'];master=a.composite(184,mask)[0];bb=master.getbbox();normalized=np.array(master.crop(bb));aliases=[];orig_hashes=collections.defaultdict(list)
 for n in sorted(REFS):
  im=a.composite(n,mask)[0];b=im.getbbox();oldim=old.composite(n,mask)[0];ob=oldim.getbbox()
  if n==198:assert b is None and ob is None;continue
  assert np.array_equal(np.array(im.crop(b)),normalized)
  orig_hashes[hb(np.array(oldim.crop(ob)).tobytes())].append(n)
  aliases.append({'ref':n,'world_bbox':[x-160 for x in b],'delta184':[b[0]-bb[0],b[1]-bb[1]],'US_world_bbox':[x-160 for x in ob]})
 q=next(x for x in ui['forms']if x['form']==form);assert q['normalized_RGBA_sha256']==hb(normalized.tobytes());assert q['metrics']['opaque_pixels']==144 and q['metrics']['size']==[13,15]
 forms.append({'form':form,'selected_mask':mask,'current_pixels':144,'current_size':[13,15],'current19_aliases_exact':True,'aliases':aliases,'US_normalized_RGBA_groups':dict(orig_hashes),'selected_after_before_difference_pixels':int(np.any(np.array(a.composite(184,0)[0])!=np.array(a.composite(184,15)[0]),axis=2).sum())})
 previews.append((form,old.composite(184,mask)[0].crop(old.composite(184,mask)[0].getbbox()),master.crop(bb)))
O.mkdir(exist_ok=False);out=Image.new('RGB',(640,4*220),'#e8e4db');dr=ImageDraw.Draw(out)
for i,(name,old,cur)in enumerate(previews):
 dr.text((4,i*220+4),name+' / US head vs current head',fill='black')
 for j,im in enumerate((old,cur)):
  pic=im.resize((im.width*10,im.height*10),Image.Resampling.NEAREST);out.paste(pic,(j*300+15,i*220+25),pic);out.paste(im,(j*300+200,i*220+30),im)
out.save(O/'US_current_fourforms.png')
for p in(Path(__file__),R/'scripts/export_x_consistency.py',R/'src/psx_player.py',D/'verify_shibuki_ultimate_hurt13_independent.py'):blob(p)
for p,h in tracked.items():assert sha(R/p)==h,p
r={'passed':True,'scope':'Shibuki 작은차량머리184..203 원US/현재 독립소유·별칭·빈부분층읽기.198은의도된빈프레임.','arc_hashes':{k:hb(v.data)for k,v in arcs.items()},'latest_hover_parent_head_raw_layers_records_exact':True,'raw_groups':group_summary,'frames':details,'forms':forms,'outside_nonempty_record_owners':outside_nonempty,'all_four_archives_20refs_32_masks_checked':4*20*32,'no_opaque_678':True,'original_disc_input':'MegaMan X4.bin에서기존read_disc로PL00/PL02만읽음.추출파일작성없음.','inputs':tracked,'sheets':[{'path':rel(O/'US_current_fourforms.png'),'sha256':sha(O/'US_current_fourforms.png')}],'actually_viewed':False,'producer_functions_called':False,'source_or_ARC_modified':False,'new_MIPS_execution':False,'runtime_verified':False,'caller_proof':'동료의원코드읽기후최종결속.현재보고는오프라인32mask소유만직접입증한다.'}
(O/'report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'passed':True,'report_sha256':sha(O/'report.json'),'groups':group_summary,'nonempty_external':outside_nonempty,'US_shapes':[{k:q[k]for k in('form','US_normalized_RGBA_groups','selected_after_before_difference_pixels')}for q in forms]}))
