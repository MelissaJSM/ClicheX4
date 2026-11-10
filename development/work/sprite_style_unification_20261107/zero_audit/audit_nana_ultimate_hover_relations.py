"""호버10 몸체/효과/공유와 현재 renderer 예외 읽기. 제작 함수 실행 없음."""
from pathlib import Path
import hashlib,json,struct,sys
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent;N=W/'nana_audit'
sys.path[:0]=[str(ROOT),str(D)]
from scripts.export_x_consistency import Archive,animation_map
from scripts.c01_audio_build import read_disc
from src.psx_player import composition_frame
from verify_shibuki_ultimate_hurt13_independent import raw,parts,sig,tile,render
O=D/'nana_ultimate_hover_relations01';O.mkdir(exist_ok=True)
sha=lambda z:hashlib.sha256(z).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();tracked={}
def blob(p):
 z=p.read_bytes();tracked[rel(p)]=sha(z);return z
def js(p):return json.loads(blob(p))
def write(name,z):(O/name).write_text(json.dumps(z,ensure_ascii=False,indent=2)+'\n','utf8')
def box(z):
 y,x=np.nonzero(z);return None if not len(x)else[int(x.min()-160),int(y.min()-160),int(x.max()+1-160),int(y.max()+1-160)]
def board(items,name,cols=5):
 crop=(120,124,200,204);scale=4;cw,ch=336,356
 out=Image.new('RGB',(cols*cw,((len(items)+cols-1)//cols)*ch),'#263345');dr=ImageDraw.Draw(out)
 for i,(label,im)in enumerate(items):
  x,y=i%cols*cw,i//cols*ch;dr.text((x+4,y+4),label,fill='white');im=im.crop(crop).resize((320,320),Image.Resampling.NEAREST);out.paste(im,(x+8,y+28),im)
 out.save(O/name)
cp=N/'ultimate_vehicle_repaint/packed_vehicle_candidate_v1/PL02_U.ARC';pp=N/'ultimate_special_finish_repaint/packed_special_candidate_v1/PL02_U.ARC'
a=Archive(blob(cp));p=Archive(blob(pp));assert sha(a.data)=='94326933d0dd62ccd7a5904019cae9fd36fc068a6acde8941d6bf8ff363666ca'
assets,_=read_disc(ROOT/'MegaMan X4.bin',('PL02_U.ARC','SLUS_005.61'));us=Archive(assets['PL02_U.ARC'])
bp=ROOT/'out/ver_rin_nana/sprite_style_unification_20261107_v36/rin_nana.bin'
now,_=read_disc(bp,('PL02_U.ARC','SLUS_005.61'));assert now['PL02_U.ARC']==a.data
exe=now['SLUS_005.61'];off=lambda addr:addr-0x80010000+2048
code=exe[off(0x800257bc):off(0x8002588c)];assert sha(code)=='46c1fe4c8c01be08e49c733c24e99fe7e4e2416b93a2dc50585a3503854038c5'
caller=struct.unpack_from('<I',exe,off(0x80023ea4))[0];assert caller>>26==3 and ((caller&0x3ffffff)<<2|0x80000000)==0x800257bc
renderer=blob(ROOT/'scripts/ultimate_costume_renderer.py')
histroot=ROOT/'work/ver_rin_nana/nana_ultimate_armor'
hp=histroot/'hover_alignment_packed_v1/PL02_U.ARC';hist=Archive(blob(hp))
oldref=js(histroot/'hover_reference_v1/manifest.json') if(histroot/'hover_reference_v1/manifest.json').exists()else None
contacts=js(histroot/'hover_alignment_v1/contacts.json');registrations=js(histroot/'hover_alignment_packed_v1/registration.json')
for name in('prepare_nana_ultimate_hover_reference.py','prepare_nana_ultimate_hover.py','prepare_nana_ultimate_hover_alignment.py'):blob(ROOT/'scripts'/name)
PBS=(0,5,6,7,8);refs=list(range(221,231));cuts={221:5,223:6,225:5,227:7,229:5};reuse={221:39,223:37,225:45,227:47,229:41}
rows=[];items=[];pairrows=[]
for n in refs:
 assert raw(a,0,n)==raw(p,0,n)
 f=a.banks[0]['frames'][n];layers=[]
 for pb in PBS:
  z,m=a.layer(n,pb);old,_=us.layer(n,pb);hz,_=hist.layer(n,pb)
  assert np.array_equal(z,p.layer(n,pb)[0])and[sig(q)for q in parts(a,pb,n)]==[sig(q)for q in parts(p,pb,n)]
  ts=sorted({q['tile']for q in parts(a,pb,n)})
  save=O/f'layer{pb}_{n}.npy';np.save(save,z)
  layers.append({'bank':pb,'opaque':int((z>0).sum()),'bbox_world':box(z>0),'indices':np.unique(z[z>0]).tolist(),'parts':[dict(q)for q in parts(a,pb,n)],'tiles':ts,'whole_tiles':[{'tile':t,'sha256':sha(tile(a,n,t).tobytes()),'original_us_exact':t<us.banks[0]['frames'][n]['tile_count']and np.array_equal(tile(a,n,t),tile(us,n,t))}for t in ts],'original_us_layer_exact':np.array_equal(z,old),'original_us_part_exact':[sig(q)for q in parts(a,pb,n)]==[sig(q)for q in parts(us,pb,n)],'historical_aligned_layer_exact':np.array_equal(z,hz),'indexed_sha256':sha(z.tobytes()),'dump':rel(save)})
 owners=[q['index']for q in a.banks[0]['frames']if q['offset']==f['offset']]
 rows.append({'ref':n,'offset':f['offset'],'tile_count':f['tile_count'],'raw_owners':owners,'raw_sha256':sha(raw(a,0,n)),'layers':layers,'mask0_vs15_rgba_differences':int(np.any(np.array(a.composite(n,0)[0])!=np.array(a.composite(n,15)[0]),axis=2).sum())})
 if n%2:
  fx=Image.new('RGBA',(384,384))
  for pb in(8,5,7,6):fx.alpha_composite(a.rgba(a.layer(n,pb)[0],32 if pb==7 else 16))
  items.extend([(f'{n} current body0',a.composite(n,0)[0]),(f'{n+1} shot body0',a.composite(n+1,0)[0]),(f'{n} overlay layers',fx),(f'{n} actual mask15',a.composite(n,15)[0]),(f'{n+1} shot mask15',a.composite(n+1,15)[0])])
  common=[]
  for pb in PBS:
   z=a.layer(n,pb)[0];zz=a.layer(n+1,pb)[0];df=z!=zz
   common.append({'bank':pb,'difference_cells':int(df.sum()),'difference_bbox':box(df),'same_below_historical_cut':np.array_equal(z[160+cuts[n]:],zz[160+cuts[n]:]),'parts_exact':[sig(q)for q in parts(a,pb,n)]==[sig(q)for q in parts(a,pb,n+1)]})
  pairrows.append({'refs':[n,n+1],'shared_raw':owners==[n,n+1],'historical_air_refs':[reuse[n],reuse[n]+1],'historical_cut_world_y':cuts[n],'layers':common})
for k in range(0,len(items),10):board(items[k:k+10],f'current_layers_{k//10:02}.png')
# Static stage jet images are separate captured objects; do not relabel them as player atlas.
jetrows=[];jit=[]
for n in refs[::2]:
 jp=histroot/f'hover_alignment_v1/jets_{n}.png';blob(jp);jim=Image.open(jp).convert('RGBA');assert jim.size==(160,160)
 jarr=np.array(jim);jc=next(v for v in contacts if v['frame']==n)
 jet=Image.new('RGBA',(384,384));jet.alpha_composite(jim,(80,80));body=a.composite(n,15)[0];co=jet.copy();co.alpha_composite(body)
 jit.extend([(f'{n} historical jet only',jet),(f'{n} current + historical jet',co)])
 al=np.array(jet)[:,:,3]>0;ba=np.array(body)[:,:,3]>0
 jetrows.append({'ref':n,'historical_jet_image':rel(jp),'historical_contact_record':jc,'jet_alpha_bbox_world':box(al),'jet_opaque':int(al.sum()),'current_body_overlap':int((al&ba).sum()),'source_scope':'11/04 정적 합성/당시 캡처로 분리된 추진 효과 이미지. 현재 플레이어 raw 타일이나 새 실기 증거로 주장하지 않음.'})
board(jit,'historical_jets.png',cols=5)
anims,arefs=animation_map(exe);uanims,uarefs=animation_map(assets['SLUS_005.61'])
ids=sorted({v for n in refs for v in arefs[n]});aseq=[q for q in anims if q['id']in ids]
for q in aseq:assert q==uanims[q['id']]
report={'passed':True,'scope':'현재 Ultimate 호버10 읽기 관계; 새 원화/후보/실기 미검증','candidate_path':rel(cp),'candidate_sha256':sha(a.data),'comparison_parent':rel(pp),'comparison_parent_sha256':sha(p.data),'original_us_arc_sha256':sha(us.data),'current_disc':rel(bp),'disc_pl02_exact':True,'current_exe_sha256':sha(exe),'current_renderer_208B_sha256':sha(code),'caller_address':'0x80023EA4','caller_word':f'{caller:08x}','renderer_rule':'engine+0x37 Ultimate!=0이면 engine+0x47 ownership0 또는 ref217..230일 때 mask15, 그외0. hover는 ownership과 무관하게15. 플레이어+0xA7의 일시 mask0으로 바뀌지 않음.','renderer_layer_order':[8,5,7,6],'renderer_clut':{'5/6/8':'row16 /0x7843','7 arm2':'row32 /0x7844'},'current_56a3_to9432_all_raw_parts_layers_unchanged':True,'frames':rows,'pairs':pairrows,'historical_aligned_arc':rel(hp),'historical_aligned_arc_sha256':sha(hist.data),'historical_feet_registrations':registrations,'historical_jets':jetrows,'original_animation_ids':ids,'original_sequences_exact':aseq,'inputs':tracked,'limits':['제작 함수 호출 없음.','옛 jets PNG와 contacts.json의 캡처 출처를 읽었으나 해당 과거 캡처 영상과 다시 픽셀 매칭하지 않음.','새 이미지 생성/재양자화/원MIPS/실기 실행 없음.','독립 그림 실제 열람은 후속 visual.json에 구분.']}
write('report.json',report)
print(json.dumps({'report_sha256':sha((O/'report.json').read_bytes()),'layers':[[q['ref'],[(r['bank'],r['opaque'],r['original_us_layer_exact'],r['historical_aligned_layer_exact'])for r in q['layers']]]for q in rows],'animation_ids':ids},ensure_ascii=False))
