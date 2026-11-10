"""Independent source/readback proof. Do not call any art or packing producer."""
from pathlib import Path
import sys,json,hashlib,struct,collections
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.overhaul_sprites_audit import render,rgba
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas
R=ROOT/'work/sprite_style_unification_20261107/riko';O=Path(__file__).parent/'riko_ground_boots_independent';O.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:str(p.relative_to(ROOT))
P=R/'prepared_spin_clothes_v1';Q=R/'prepared_ground_boots_v1';old=(P/'PL01_U.ARC').read_bytes();new=(Q/'PL01_U.ARC').read_bytes()
assert sha(old)=='c68ef84d524a16062937359c52f9d640213b250ea2b679a673046f977d997e42'
assert sha(new)=='55950f7066b5fab6ff8c1c3285b64b530f9cca407d0f0f9027866b31e09bb689'
g,c=entry(old,2),entry(old,3);ng,nc=entry(new,2),entry(new,3)
assert c==nc and replace_entry(new,2,g)==old
assert bank_offsets(g,allow_aliases=True)==bank_offsets(ng,allow_aliases=True)
A=R/'ground_boots19';gen=A/'generated.png';assert sha(gen.read_bytes())=='8800cbd1aa15c78bdaba4b6d147d49598ade38941eec88a53d708d04b0acba75'
pal=struct.unpack_from('<16H',entry(old,9));colors=np.array([[(v>>s&31)*255//31 for s in(0,5,10)]for v in pal],np.int32)
v=np.array(Image.open(gen).convert('RGBA').resize((192,288),Image.Resampling.NEAREST));ix=(1+((v[:,:,None,:3].astype(np.int32)-colors[None,None,1:,:])**2).sum(3).argmin(2)).astype(np.uint8);ix[v[:,:,3]<128]=0
regions={91:[(135,173,159,184),(165,174,178,184)],71:[(137,177,155,184),(160,174,181,184)],61:[(143,172,160,183),(169,173,181,184)]};masters={};master_rows=[]
for n,cell in [(91,0),(71,2),(61,3)]:
 before=render(old,0,0,n)[0];authored=np.zeros_like(before);authored[112:208,112:208]=ix[cell//2*96:(cell//2+1)*96,cell%2*96:(cell%2+1)*96]
 assert np.array_equal(authored,np.array(Image.open(A/f'registered01/b0_{n:03}_authored.png')))
 region=np.zeros_like(before,bool)
 for x0,y0,x1,y1 in regions[n]:region[y0:y1,x0:x1]=True
 mask=region&np.isin(before,[1,3,7,12,15])&np.isin(authored,[1,3,7,12,15]);want=before.copy();want[mask]=authored[mask]
 if n==91:want[174,175]=before[174,175]
 masters[n]=want;master_rows.append({'ref':n,'changed_pixels':int((want!=before).sum()),'source_cell':cell,'regions':regions[n],'source_sha256':sha(gen.read_bytes()),'native_source_reconstructed':True})
mapping={61:(61,0),71:(71,0),75:(71,0),91:(91,0),93:(91,1),95:(91,1),97:(91,0),99:(91,0),101:(91,0)}
targets={};rows=[]
for n,(m,dx)in mapping.items():
 before=render(old,0,0,n)[0];mb=render(old,0,0,m)[0];y,x=np.where(mb!=masters[m]);assert np.array_equal(before[y,x+dx],mb[y,x]);want=before.copy();want[y,x+dx]=masters[m][y,x]
 p=A/f'targets02/b0_{n:03}_indices.png';assert np.array_equal(want,np.array(Image.open(p)));assert np.array_equal(want>0,before>0) and np.array_equal(want[:172],before[:172]);targets[n]=want
 rows.append({'ref':n,'master':m,'dx':dx,'changed_pixels':len(x),'authored_sha256':sha(p.read_bytes()),'source_material_pixels_before_exact':True,'upper_body_alpha_skin_contacts_exact':True})
support={62,63,64,72,73,74,76,92,94,96,98,100,102,103,104};counts=collections.Counter();consumed=[];gpu=0;raw_changes=[];display_changes=[]
for b in(0,1):
 ob,nb=graphics_bank(g,b),graphics_bank(ng,b);assert len(ob['frames'])==len(nb['frames'])
 if b==1:assert g[ob['base']:ob['end']]==ng[nb['base']:nb['end']]
 for f,nf in zip(ob['frames'],nb['frames']):
  n=f['index'];selected=b==0 and n in targets;shared=b==0 and n in support
  assert f['tile_count']==nf['tile_count']<=32
  raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;nr=decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data;counts['raw']+=1
  if raw==nr:counts['raw_exact']+=1
  else:assert selected or shared;raw_changes.append([b,n])
  cp=composition_frame(c,b*5,n)
  if shared or selected:
   aa=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256);zz=np.frombuffer(indexed_atlas(nr,nf['tile_count'])[0],np.uint8).reshape(-1,256)
   if shared:
    ts=sorted({p['tile']for p in cp['parts']})
    for t in ts:
     yy,xx=t//16*16,t%16*16;assert np.array_equal(aa[yy:yy+16,xx:xx+16],zz[yy:yy+16,xx:xx+16]),(n,t)
    consumed.append({'ref':n,'entire_consumed_tiles_exact':ts,'including_hidden_part_pixels':True})
   for p in cp['parts']:
    t=p['tile'];yy,xx=t//16*16,t%16*16
    if t%16==0:assert not np.any((aa[yy:yy+16,xx]==0)&(zz[yy:yy+16,xx]!=0))
    if p['flip_y']and t//16%16==0:assert not np.any((aa[yy,xx:xx+16]==0)&(zz[yy,xx:xx+16]!=0))
    gpu+=1
  if b==1 and 42<=n<=49:assert raw==nr;counts['partial8_exact']+=1;continue
  before=render(old,b,b*5,n)[0];after=render(new,b,b*5,n)[0];counts['display']+=1
  if selected:
   assert np.array_equal(after,targets[n]);counts['authored_exact']+=1;assert np.array_equal(after>0,before>0);display_changes.append([b,n])
  else:assert np.array_equal(after,before);counts['non_target_display_exact']+=1
assert counts=={'raw':444,'raw_exact':420,'display':436,'authored_exact':9,'non_target_display_exact':427,'partial8_exact':8},counts
assert len(consumed)==15 and sum(q['changed_pixels']for q in rows)==582
static=0
for b in(1,2,3,4,6):static+=composition_frame(c,b,0)['bank_frame_count']
assert static==404 and entry(old,0x10206)==entry(new,0x10206)
for name in('static_effects.json','effect_23.png','effect_24.png'):
 assert(P/name).read_bytes()==(Q/name).read_bytes()
# A separate crop makes the last body on producer sheet01 unambiguous to review.
for label,row in [('normal',0),('black',13)]:
 words=struct.unpack_from('<16H',entry(old,9),row*32);sheet=Image.new('RGB',(1152,384),'#64717b')
 for i,(a,name)in enumerate([(render(old,0,0,147)[0],'idle'),(render(old,0,0,99)[0],'old'),(render(new,0,0,99)[0],'new')]):
  im=rgba(a,words).crop((112,112,208,208)).resize((384,384),Image.Resampling.NEAREST);sheet.paste(im,(i*384,0),im)
 sheet.save(O/f'{label}_ref099.png')
result={'passed':True,'parent_sha256':sha(old),'candidate_sha256':sha(new),'producer_functions_called':False,'counts':dict(counts),'source_masters':master_rows,'registered_rows':rows,'changed_display_pixels':582,'raw_changed_references':raw_changes,'actual_display_changed_references':display_changes,'shared_support_consumed_tiles':consumed,'consumed_tiles_checked':sum(len(q['entire_consumed_tiles_exact'])for q in consumed),'gpu_parts_checked':gpu,'new_gpu_boundary_alpha':0,'all_composition_bytes_exact':True,'bank_boundaries_tilecounts_exact':True,'bank1_graphics_exact':True,'static_texture_recipe_404refs_exact':True,'palette_audio_other_entries_exact':True,'partial8_raw_exact':True,'visual_review_pending':False,'visual_review':[f'{form}_readback_{i:02}.png'for form in('normal','black')for i in range(3)]+['normal_ref099.png','black_ref099.png'],'visual_findings':['일반·무채색 6시트와99별도 확대2장을 직접 열람했다.','발등·발목 회색 명암이 추가되어 흰 부츠 큰 면이 분리되며 기존 세밀한 머리·의상과 더 가깝다.','71/75 낮은 자세와91~101 벌어진 자세의 발끝·굽·정강이 외곽은 원형이며 새 단절이나 잘림은 보이지 않았다.','이는 부츠 내부 재질9참조의 개선이다. 다른 옷·손·동작 전체의 미술 통일 완료나 실제 게임 수용을 뜻하지 않는다.'],'runtime_verified':False,'full_art_unification_complete':False}
(O/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'counts':dict(counts),'consumed_tiles':result['consumed_tiles_checked'],'gpu_parts':gpu}))
