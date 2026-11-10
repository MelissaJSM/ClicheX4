"""등록 원화의 국소/의상→역사 효과규칙→노바40층·ARC 독립 읽기."""
from pathlib import Path
import collections,hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,binary_dilation,binary_fill_holes
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;N=D.parent/'nana_audit';U=N/'ultimate_nova_repaint'
sys.path[:0]=[str(ROOT),str(D)]
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from src.psx_player import bank_offsets,composition_frame
from verify_shibuki_ultimate_hurt13_independent import raw,parts,sig,tile,color
P=U/'packed_nova_candidate_v1';T=U/'targets_preview_v1';O=D/'nana_ultimate_nova8_independent01';assert not O.exists()
PBS=(0,5,6,7,8);REFS=set(range(213,221));RESERVED={105,*range(175,183)}
sha=lambda z:hashlib.sha256(z).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();tracked={};counts=collections.Counter()
def blob(p):
 z=p.read_bytes();tracked[rel(p)]=sha(z);return z
def js(p):return json.loads(blob(p))
def png(p):blob(p);return np.array(Image.open(p))
def rowmask(rows):
 m=np.zeros((384,384),bool)
 for y,(x0,x1)in rows.items():m[int(y)+160,x0+160:x1+161]=True
 return m
oldp=N/'ultimate_hover_repaint/packed_hover_candidate_v1/PL02_U.ARC';newp=P/'PL02_U.ARC';old,new=blob(oldp),blob(newp);a,b=Archive(old),Archive(new)
assert sha(old)=='e630d04286c1dbcbb65a5a301dd984f23cdecf13a1759dbaaf52ad8ae103efff'
assert sha(new)=='1ec00de5164827c5dd5322b93b7060e11a1afbddd26bacb23f5b585e63715195'
lock=js(P/'INPUT_FROZEN.json');assert lock['candidate_sha256']==sha(new)and lock['parent_sha256']==sha(old)and len(lock['files'])==167
for q in lock['files']:assert sha(blob(ROOT/q['path']))==q['sha256'],q['path']
meta=js(T/'manifest.json');assert meta['parent_arc_sha256']==sha(old)and set(meta['refs'])==REFS and sha(blob(T/'manifest.json'))==lock['target_manifest_sha256']
# Register-source pixel transitions are read directly; creation/area requantization is excluded.
sem=js(U/'semantic_samples_v1/manifest.json');semantic={}
for q in sem['frames']:
 n,form=q['ref'],q['form'];p=ROOT/q['source'];assert sha(blob(p))==q['source_sha256'];z=png(p);original=z.copy();assert sha(z.tobytes())==q['source_indexed_sha256']
 for e in q['iris_removed_upper_samples']:
  x,y=e['world'];assert z[y+160,x+160]==14;z[y+160,x+160]=e['nearest_noniris'];counts['registered_iris_samples']+=1
 for e in q['skin_rgb_samples']:
  x,y=e['world'];assert z[y+160,x+160]==e['old'];z[y+160,x+160]=e['nearest_skin_or_outline'];counts['registered_skin_samples']+=1
 for e in q['palette15_actual_samples']:
  x,y=e['world'];assert z[y+160,x+160]==15;z[y+160,x+160]=e['value'];counts['registered_palette15_samples']+=1
 assert np.array_equal(z>0,original>0)and sha(z.tobytes())==q['target_sha256']and np.array_equal(z,png(U/f'semantic_samples_v1/{form}_{n:03}_indices.png'));semantic[form,n]=z
arm=js(U/'raise215_local_probe_v2/manifest.json');raised={}
for q in arm['frames']:
 form=q['form'];master=semantic[form,215];donor=png(U/f'raise215_fixed_v1/{form}_215_indices.png');assert sha(donor.tobytes())==q['source_sha256']and sha(master.tobytes())==q['master_sha256']
 m=rowmask(q['local_rows']);z=master.copy();z[m]=donor[m]
 for e in q['palette15_source_samples']:
  x,y=e['world'];assert z[y+160,x+160]==15 and m[y+160,x+160];z[y+160,x+160]=e['source_value'];counts['registered_palette15_samples']+=1
 assert np.array_equal(z[~m],master[~m])and np.array_equal(z[165:],master[165:])and sha(z.tobytes())==q['target_sha256']and np.array_equal(z,png(U/f'raise215_local_probe_v2/{form}_215_indices.png'));raised[form]=z
common=js(U/'common_probe_v5/manifest.json');masters={};zero=np.zeros((384,384),np.uint8)
for q in common['frames']:
 n=q['ref'];before=(semantic['before',n]if n==213 else raised['before']).copy();donor=semantic['after',n]if n==213 else raised['after'];assert sha(donor.tobytes())==q['donor_sha256']
 for e in q['source_boundary_links']:
  x,y=e['world'];assert before[y+160,x+160]==e['before_was']==0 and donor[y+160,x+160]==e['source_index']==2;before[y+160,x+160]=donor[y+160,x+160];counts['shared_new_boundary_sample']+=1
 m=rowmask(q['costume_rows']);after=before.copy();after[m]=donor[m]
 assert not np.any((after>0)&(before==0))and sha(before.tobytes())==q['before_sha256']and sha(after.tobytes())==q['after_sha256']
 for form,z in [('before',before),('after',after)]:assert np.array_equal(z,png(U/f'common_probe_v5/{form}_{n:03}_indices.png'))and label(z>0,np.ones((3,3)))[1]==1
 diff=np.any(color(a,before,16)!=color(a,after),axis=2);masters[n]={0:after,5:np.where(diff,before,0).astype(np.uint8),6:zero,7:zero,8:zero}
dash=js(U/'dash217_semantic_v1/manifest.json');body=png(U/'dash217_registered_v1/body_217_indices.png')
assert sha(body.tobytes())==dash['source_sha256'];x,y=dash['iris_actual_sample']['world'];assert body[y+160,x+160]==dash['iris_actual_sample']['old_index'];body[y+160,x+160]=dash['new_index'];assert sha(body.tobytes())==dash['target_sha256']and np.array_equal(body,png(U/'dash217_semantic_v1/body_217_indices.png'))
histp=ROOT/'work/ver_rin_nana/nana_ultimate_armor/nova_packed_v2/PL02_U.ARC';swapp=ROOT/'work/ultimate_costume_swap_20261105/core/prepared_complete_v1/ver_rin_nana/PL02_U.ARC';hist=Archive(blob(histp));swap=Archive(blob(swapp));fxmeta=js(U/'effects_probe_v1/manifest.json')
assert sha(hist.data)==fxmeta['historical_sha256']and sha(swap.data)==fxmeta['swap_seed_sha256'];oldbody=hist.layer(217,5)[0];seed=swap.layer(217,0)[0];effects={};fxproof=[]
for n,fill in [(218,14),(220,7)]:
 source=hist.layer(n,5)[0];remove=binary_dilation(oldbody>0,iterations=1);envelope=binary_fill_holes(source>0)
 def remake(z):
  fx=source.copy();fx[remove]=0;holes=remove&envelope&(fx==0)&(z==0);fx[holes]=fill;fx[z>0]=0;return fx,holes
 prior,_=remake(seed);assert np.array_equal(prior,a.layer(n,5)[0]);fx,holes=remake(body);protected=~remove&(body==0);assert np.array_equal(fx[protected],source[protected])and not np.any((fx>0)&(body>0))
 assert np.array_equal(fx,png(U/f'effects_probe_v1/effect_{n:03}_indices.png'))
 for name,z in [('original_body_dilation',remove),('original_envelope',envelope),('fill_mask',holes),('preserved_effect_mask',protected)]:assert np.array_equal(z,png(U/f'effects_probe_v1/{name}_{n}.png')>0)
 effects[n]=fx;fxproof.append({'ref':n,'parent_historical_rule_reproduced_exact':True,'old_effect_pixels':int((prior>0).sum()),'new_effect_pixels':int((fx>0).sum()),'new_fill_pixels':int(holes.sum()),'changed_effect_cells':int((fx!=prior).sum()),'old_body_dilate1_pixels':int(remove.sum()),'protected_source_world_exact':True,'new_body_occlusion':0,'whole_effect_byteexact_claim':False})
priorflash=np.zeros_like(body);priorflash[binary_dilation(seed>0,iterations=2)]=7;priorflash[seed>0]=6;assert np.array_equal(priorflash,a.layer(219,5)[0])
flash=np.zeros_like(body);flash[binary_dilation(body>0,iterations=2)]=7;flash[body>0]=6;assert np.array_equal(flash,png(U/'effects_probe_v1/effect_219_indices.png'));effects[219]=flash
target={}
for q in meta['frames']:
 n=q['ref'];ls=masters[n if n%2 else n-1]if n<217 else {0:zero if n==219 else body,5:effects.get(n,zero),6:zero,7:zero,8:zero}
 for pb,z in ls.items():assert np.array_equal(z,png(T/f'layer{pb}_{n:03}.png'))and sha(z.tobytes())==q['layer_hashes'][str(pb)];target[n,pb]=z
assert len(old)==len(new)and a.p==b.p;ae,be=psx_arc(old),psx_arc(new);assert [(e['type'],e['offset'],e['size'])for e in ae]==[(e['type'],e['offset'],e['size'])for e in be];allow=np.zeros(len(old),bool)
for e in ae:
 if int(e['type'],16)in (2,3):allow[e['offset']:e['offset']+e['size']]=True
assert not np.any((np.frombuffer(old,np.uint8)!=np.frombuffer(new,np.uint8))&~allow)
assert bank_offsets(a.g,allow_aliases=True)==bank_offsets(b.g,allow_aliases=True)and bank_offsets(a.c)==bank_offsets(b.c)
for gb,(ab,bb)in enumerate(zip(a.banks,b.banks)):
 assert(ab['base'],ab['end'],len(ab['frames']))==(bb['base'],bb['end'],len(bb['frames']))
 if gb:assert a.g[ab['base']:ab['end']]==b.g[bb['base']:bb['end']]
 for af,bf in zip(ab['frames'],bb['frames']):
  n=af['index'];assert n==bf['index']and af['tile_count']==bf['tile_count'];counts['raw_checked']+=1
  if not(gb==0 and n in REFS):assert raw(a,gb,n)==raw(b,gb,n);counts['non_target_raw_exact']+=1
reserved=[]
for n in range(237):
 for pb in PBS:
  if n in RESERVED:
   try:b.layer(n,pb)
   except(ValueError,IndexError)as ex:
    try:a.layer(n,pb)
    except(ValueError,IndexError)as ex2:assert type(ex)==type(ex2)and str(ex)==str(ex2)
    else:raise AssertionError('new invalid layer')
    reserved.append([n,pb,'same_exception']);continue
   assert np.array_equal(b.layer(n,pb)[0],a.layer(n,pb)[0]);reserved.append([n,pb,'exact']);continue
  assert np.array_equal(b.layer(n,pb)[0],target[n,pb]if n in REFS else a.layer(n,pb)[0]),(n,pb)
  counts['target_layers_exact'if n in REFS else'non_target_layers_exact']+=1
for pb in range(len(bank_offsets(a.c))):
 for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
  op,bp=parts(a,pb,n),parts(b,pb,n)
  if pb in PBS and n in REFS:
   for q in bp:
    t=q['tile']+q['page']*256;assert 0<=t<b.banks[0]['frames'][n]['tile_count']and q['unknown_flags']==0;z=tile(b,n,t)
    assert not(t%16==0 and z[:,0].any())and not(q['flip_y']and t//16==0 and z[0].any());counts['GPU_parts']+=1
  else:assert [sig(q)for q in op]==[sig(q)for q in bp];counts['non_target_compositions_exact']+=1
groups=[]
for n in sorted(REFS):
 owners=[q['index']for q in b.banks[0]['frames']if q['offset']==b.banks[0]['frames'][n]['offset']];oo=[q['index']for q in a.banks[0]['frames']if q['offset']==a.banks[0]['frames'][n]['offset']];assert owners==oo and set(owners)<=REFS
 groups.append({'ref':n,'owners':owners,'tile_count':b.banks[0]['frames'][n]['tile_count']})
for n in sorted(REFS):
 for mask in range(16):
  for arm in (1,2):
   exp=color(b,target[n,0])
   for bit,pb in((8,8),(1,5),(4,7),(2,6)):
    if mask&bit:v=color(b,target[n,pb],32 if pb==7 and arm==2 else 16);m=v[:,:,3]>0;exp[m]=v[m]
   assert np.array_equal(exp,np.array(b.composite(n,mask,arm)[0]));counts['partial_RGBA_exact']+=1
assert counts['raw_checked']==512 and counts['non_target_raw_exact']==504 and counts['target_layers_exact']==40 and counts['non_target_layers_exact']==1100 and counts['non_target_compositions_exact']==1751 and counts['GPU_parts']==107
relationp=D/'nana_ultimate_nova_relations01/report.json';relations=js(relationp);assert sha(blob(relationp))=='f61cdbe3df69a329b939e2468dcc2cfb1a5b0754fb303e2e82db9b08e5cc240e'
O.mkdir(exist_ok=False);sheets=[]
def sheet(name,rows,scale=4):
 boxes=[im.getbbox()for row in rows for _,im in row if im.getbbox()];crop=(min(z[0]for z in boxes)-3,min(z[1]for z in boxes)-3,max(z[2]for z in boxes)+3,max(z[3]for z in boxes)+3);w,h=crop[2]-crop[0],crop[3]-crop[1];cw,ch=w*scale+10,h*scale+25;out=Image.new('RGB',(cw*len(rows[0]),ch*len(rows)),'#263345');dr=ImageDraw.Draw(out)
 for y,row in enumerate(rows):
  for x,(caption,im)in enumerate(row):
   dr.text((x*cw+3,y*ch+3),caption,fill='white');v=im.crop(crop).resize((w*scale,h*scale),Image.Resampling.NEAREST);out.paste(v,(x*cw+5,y*ch+22),v)
 p=O/name;out.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes()),'crop':crop,'integer_scale':scale})
for n in(213,215):sheet(f'preparation_{n}.png',[[(f'{n} old before',a.composite(n,15)[0]),(f'{n} new before',b.composite(n,15)[0]),(f'{n} old after',a.composite(n,0)[0]),(f'{n} new after',b.composite(n,0)[0])]],5)
for n in(217,218,219,220):sheet(f'effect_{n}.png',[[(f'{n} old mask15',a.composite(n,15)[0]),(f'{n} new mask15',b.composite(n,15)[0])]],3 if n==220 else 5)
sheet('preparation_sequence.png',[[(f'{n} before',b.composite(n,15)[0])for n in(213,215,216,214,217)],[(f'{n} after',b.composite(n,0)[0])for n in(213,215,216,214,217)]],4)
sheet('effect_cycle.png',[[(f'{n} mask15',b.composite(n,15)[0])for n in(217,218,219,220)]],3)
for path,h in tracked.items():assert sha((ROOT/path).read_bytes())==h,path
report={'passed':True,'scope':'Nana Ultimate 준비213..216/돌진효과217..220 등록출처·역사규칙·40층 독립읽기','candidate':rel(newp),'candidate_sha256':sha(new),'parent_sha256':sha(old),'input_lock_sha256':sha((P/'INPUT_FROZEN.json').read_bytes()),'locked_inputs':167,'counts':dict(counts),'registered_source_to_layers_reconstructed':True,'source_generation7_cells_requantized':False,'effects':fxproof,'silhouette219':{'old_Manhattan2_exact':True,'new_Manhattan2_exact':True,'new_body_count':int((body>0).sum()),'new_flash_count':int((flash>0).sum())},'stream_groups':groups,'reserved_layers':reserved,'all_arc_entries_bank_boundaries_palette_audio_unchanged':True,'parent_213214_215216_shared_policy_retained':True,'renderer_scope':'213..216은일반의상정책.217..220은engine획득과무관mask15.0몸/5효과이며219만0빈/5실루엣.','effect_220_rightmost_world_x':int(np.where(target[220,5]>0)[1].max()-160),'readback_sheets':sheets,'actually_viewed':False,'inputs':tracked,'producer_functions_called':False,'new_MIPS_execution':False,'runtime_verified':False,'overall_complete':False,'limits':['등록된7셀의최초생성재양자화는제작자증거이며이reader는직접수행하지않았다. 기록된홍채/피부/15표본의색인전후·국소215팔·의상행·허리1셀과대상40층을독립재구성했다.','218/220은역사규칙의부모exact재현후새몸을대입.원효과전체byteexact라고하지않고old몸팽창1영역과새몸밖색/좌표보존을검사했다.','GPU107파트정적경계검사만추가.원MIPS·실제게임·원표동적재생은다른증거다.','준비4와돌진효과4를고유원화8장이나전체완료율로계산하지않는다.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'report_sha256':sha((O/'report.json').read_bytes()),'counts':dict(counts),'effects':fxproof}))
