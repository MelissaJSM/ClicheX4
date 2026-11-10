"""고정 호버10 원화사격6셀/의미영역/총열→50층/원효과 독립 읽기."""
from pathlib import Path
import collections,hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import binary_dilation,label
R=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent;H=W/'shibuki_audit';P=H/'prepared_hover_ultimate01';T=H/'hover_ultimate_targets01';O=D/'shibuki_ultimate_hover10_independent01';assert not O.exists()
sys.path[:0]=[str(R),str(D)]
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from scripts.prepare_riko_ui import entry
from src.psx_player import bank_offsets,composition_frame
from src.psx_static_effect import compose_static
from src.psx_ui_atlas import local_composition,tile_pixels
from verify_shibuki_ultimate_hurt13_independent import raw,parts,sig,tile,color
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(R).as_posix();tracked={};counts=collections.Counter();PBS=(0,5,6,7,8);REFS=set(range(221,231));CUTS={221:5,223:6,225:5,227:7,229:5};RESERVED={105,*range(175,183)}
def blob(p):
 v=p.read_bytes();tracked[rel(p)]=sha(v);return v
def js(p):return json.loads(blob(p))
def png(p):blob(p);return np.array(Image.open(p))
def same(z,p):assert np.array_equal(z,png(p)),str(p)
def shift(z,dx,dy):return np.roll(np.roll(z,dy,axis=0),dx,axis=1)
def composite(ls,mask,arm=1):
 out=color(a,ls[0])
 for bit,pb in((8,8),(1,5),(4,7),(2,6)):
  if mask&bit:z=color(a,ls[pb],32 if pb==7 and arm==2 else 16);m=z[:,:,3]>0;out[m]=z[m]
 return out
oldp=H/'prepared_nova_strike_ultimate01/PL02_U.ARC';newp=P/'PL02_U.ARC';old,new=blob(oldp),blob(newp);a,b=Archive(old),Archive(new)
assert sha(old)=='01997c949968d5a1a12d89e09c5eb46448bbcf245009feb9953e3d9e9356efd7'
assert sha(new)=='3f16886331dd693e841450cbaebc8c2c3ad226681cfb26478463481ce05048ba'
lock=js(P/'INPUT_LOCK.json');assert sha(blob(P/'INPUT_LOCK.json'))=='7c5c999016b1ed7ac7e15bafd56a33305c653269ba4840f3d9552857ee1e093c'and len(lock['files'])==355
assert lock['candidate_sha256']==sha(new)and lock['parent_sha256']==sha(old)
for p,h in lock['files'].items():assert sha(blob(R/p))==h,p
meta=js(T/'manifest.json');assert sha(blob(T/'manifest.json'))==lock['target_manifest_sha256']and meta['parent_sha256']==sha(old)
for p,h in meta['source_files'].items():assert sha(blob(R/p))==h,p
ver=js(P/'verification.json');proposal=js(P/'proposal.json');assert ver['candidate_sha256']==sha(new)and proposal['sequential_parent']['sha256']==sha(old)
Y,X=np.indices((384,384));Y-=160;X-=160
# 본체5의 고정 등록값→0/5분할은 별도 동료 source reader로 직접 재양자화하고 최종 결속한다.
bodies={}
for n in CUTS:
 source=H/('hover_ultimate_native02'if n==229 else'hover_ultimate_body_layers01')
 bodies[n]={pb:png(source/f'{n:03}_bank{pb}_indices.png')for pb in PBS}
 assert all(z.shape==(384,384)and z.dtype==np.uint8 and z.max()<16 for z in bodies[n].values())
 assert not any(bodies[n][pb].any()for pb in(6,7,8))
 assert not bodies[n][0][160+CUTS[n]:].any()and not bodies[n][5][:160+CUTS[n]].any()
registered={};source_cells=[];pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[:16]],np.int32)
def quant(cell):
 z=(1+np.square(cell[:,:,:3].astype(np.int32)[:,:,None]-pal[None,None,1:]).sum(3).argmin(2)).astype(np.uint8);z[cell[:,:,3]<128]=0;return z
for page in(1,2):
 sd=H/f'hover_ultimate_shot_inputs01/page{page:02}';rd=H/f'hover_ultimate_shot_page{page:02}_registered01';m=js(sd/'input.json');rm=js(rd/'registration.json');art=sd/'generated_v1.png';assert sha(blob(art))==rm['source_sha256'];im=Image.open(art).convert('RGBA');ls=m['layout'];whole=np.array(im.resize((ls['logical_canvas'],ls['logical_canvas']),Image.Resampling.NEAREST))
 for i,n in enumerate(m['refs']):
  cx=i%ls['columns']*ls['cell'];cy=i//ls['columns']*ls['cell'];cell=whole[cy:cy+ls['cell'],cx:cx+ls['cell']];z=np.zeros((384,384),np.uint8);origin=160-ls['origin'];z[origin:origin+ls['cell'],origin:origin+ls['cell']]=quant(cell);same(z,rd/f'{n:03}_indices.png');registered[n]=z
  source_cells.append({'ref':n,'source':rel(art),'source_sha256':sha(art.read_bytes()),'whole_logical_grid':ls['logical_canvas'],'fixed_cell':ls['cell'],'indices_sha256':sha(z.tobytes()),'stage':'사격원화등록.222 초기여분팔은후속국소로교체되어최종그대로채택하지않음.'})
sd=H/'hover222_cleanup_inputs01';rd=H/'hover222_cleanup_native01';cm=js(sd/'input.json');cr=js(rd/'registration.json');art=sd/'generated_v1.png';assert sha(blob(art))==cr['source_sha256'];cell=np.array(Image.open(art).convert('RGBA').resize((128,128),Image.Resampling.NEAREST));donor=np.zeros((384,384),np.uint8);donor[96:224,96:224]=quant(cell);same(donor,rd/'donor_indices.png')
z=registered[222].copy();local=(X>=-17)&(X<=-8)&(Y>=-27)&(Y<=-11);same(local.astype(np.uint8)*255,rd/'semantic_mask.png');z[local]=donor[local];same(z,rd/'222_indices.png');registered[222]=z
source_cells.append({'ref':222,'source':rel(art),'source_sha256':sha(art.read_bytes()),'whole_logical_grid':128,'fixed_cell':128,'indices_sha256':sha(donor.tobytes()),'stage':'여분팔국소 동일좌표 직사각형 적용.나머지 사격donor exact.'})
# 현재 수용34 actual mask0의 색을 실제 팔레트0로 직접 역변환한다.
gm=png(H/'air_barrel_guard02/master_034_mask.png')>0;rgba=np.array(a.composite(34,0)[0]);master=np.zeros((384,384),np.uint8)
for y,x in np.argwhere(gm):
 if rgba[y,x,3]==0:continue
 matches=np.flatnonzero(np.all(pal[1:]==rgba[y,x,:3],axis=1))+1;assert len(matches);master[y,x]=matches[0]
assert int(gm.sum())==71 and int((master>0).sum())==60 and set(np.unique(master))=={0,2,5,8,14,15}
assert np.array_equal(color(a,master),color(a,master,16));same(master,H/'hover_ultimate_shot_inputs01/master_indices.png');same(gm.astype(np.uint8)*255,H/'hover_ultimate_shot_inputs01/master_mask.png')
relproof=js(D/'shibuki_base_hover_ownership01/report.json');assert sha(blob(D/'shibuki_base_hover_ownership01/report.json'))=='4a09339f0f6e270c89d75963c9676b38fdc896abe51abd4ecb8bb302fe5191af';origins={q['ref']:q['direction0']for q in relproof['muzzles']};guns={};guards={};targets={n:ll for n,ll in bodies.items()};shotproof=[]
for n in(222,224,226,228,230):
 body=bodies[n-1];base=body[0];donor=registered[n];mx,my=origins[n];gun=shift(master,mx+24,my+10);guard=shift(gm,mx+24,my+10);guns[n]=gun;guards[n]=guard
 same(gun,H/f'hover_ultimate_shot_inputs01/{n:03}_barrel_indices.png');same(guard.astype(np.uint8)*255,H/f'hover_ultimate_shot_inputs01/{n:03}_barrel_mask.png')
 high=(X>=-18)&(X<=-9)&(Y>=(-28 if n in(222,230)else-21))&(Y<=(-7 if n<=224 or n==230 else 3));rem=binary_dilation(high&np.isin(base,[10,11,12,13]),np.ones((3,3)))&high
 armroi=(X>=-31)&(X<=-7)&(Y>=-14)&(Y<=3);arm=binary_dilation(armroi&np.isin(donor,[10,11,12,13]),np.ones((3,3)))&armroi;shoulder=(X>=-8)&(X<=-4)&(Y>=-4)&(Y<=0)
 if n in(222,230):rem|=(X>=-17)&(X<=-8)&(Y>=-27)&(Y<=-11)
 mask=rem|arm|shoulder;z=base.copy();z[mask]=donor[mask];z[guard]=gun[guard];mask|=guard;same(mask.astype(np.uint8)*255,H/f'hover_ultimate_shot_composed03/{n:03}_semantic_mask.png')
 ll={**body,0:z};assert np.array_equal(z[~mask],base[~mask]);targets[n]=ll
 for pb,v in ll.items():same(v,H/f'hover_ultimate_shot_composed03/{n:03}_bank{pb}_indices.png')
 touch=binary_dilation(gun>0,np.array([[0,1,0],[1,1,1],[0,1,0]]))&(z>0)&~guard;assert touch.any()
 shotproof.append({'ref':n,'muzzle_origin':origins[n],'translation':[mx+24,my+10],'canonical_opaque':60,'transparent_guard':11,'arm_semantic_cells':int(mask.sum()),'changed_upper_cells':int((z!=base).sum()),'outside_semantic_exact':True,'lower5_pair_exact':True,'touching_non_guard_cells':int(touch.sum()),'generated_gun_adopted':False})
for n,ll in targets.items():
 for pb,z in ll.items():assert sha(z.tobytes())==meta['targets'][str(n)][str(pb)];same(z,T/f'{n:03}_bank{pb}_indices.png')
 assert np.array_equal(composite(ll,15),png(T/f'actual_{n:03}.png'))
assert len(old)==len(new)and a.p==b.p
oe,ne=psx_arc(old),psx_arc(new);assert[(e['type'],e['offset'],e['size'])for e in oe]==[(e['type'],e['offset'],e['size'])for e in ne];allow=np.zeros(len(old),bool)
for e in oe:
 if int(e['type'],16)in(2,3):allow[e['offset']:e['offset']+e['size']]=True
assert not np.any((np.frombuffer(old,np.uint8)!=np.frombuffer(new,np.uint8))&~allow)
assert bank_offsets(a.g,allow_aliases=True)==bank_offsets(b.g,allow_aliases=True)and bank_offsets(a.c)==bank_offsets(b.c)
groups=[]
for gb,(ab,bb)in enumerate(zip(a.banks,b.banks)):
 assert(ab['base'],ab['end'],len(ab['frames']))==(bb['base'],bb['end'],len(bb['frames']))
 if gb:assert a.g[ab['base']:ab['end']]==b.g[bb['base']:bb['end']]
 for af,bf in zip(ab['frames'],bb['frames']):
  n=af['index'];assert n==bf['index'];counts['raw_checked']+=1
  if gb==0 and n in REFS:assert 0<bf['tile_count']<=32
  else:assert raw(a,gb,n)==raw(b,gb,n)and af['tile_count']==bf['tile_count'];counts['non_target_raw_exact']+=1
  og=[q['index']for q in ab['frames']if q['offset']==af['offset']];ng=[q['index']for q in bb['frames']if q['offset']==bf['offset']];assert og==ng
  if gb==0 and n in REFS:groups.append({'ref':n,'owners':ng,'tiles':bf['tile_count'],'raw_sha256':sha(raw(b,0,n))})
assert len({tuple(q['owners'])for q in groups})==5 and all(len(q['owners'])==2 and set(q['owners'])<=REFS for q in groups)
reserved=[]
for n in range(237):
 for pb in PBS:
  if n in RESERVED:
   try:b.layer(n,pb)
   except(ValueError,IndexError)as e:
    try:a.layer(n,pb)
    except(ValueError,IndexError)as e2:assert(type(e),str(e))==(type(e2),str(e2))
    else:raise AssertionError('new invalid layer')
    reserved.append([n,pb,'same_exception']);continue
   assert np.array_equal(b.layer(n,pb)[0],a.layer(n,pb)[0]);reserved.append([n,pb,'exact']);continue
  assert np.array_equal(b.layer(n,pb)[0],targets[n][pb]if n in REFS else a.layer(n,pb)[0]),(n,pb);counts['target_layers_exact'if n in REFS else'non_target_layers_exact']+=1
for pb in range(len(bank_offsets(a.c))):
 for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
  op,bp=parts(a,pb,n),parts(b,pb,n)
  if pb in PBS and n in REFS:
   for p in bp:
    t=p['tile']+p['page']*256;assert 0<=t<b.banks[0]['frames'][n]['tile_count']and p['unknown_flags']==0;z=tile(b,n,t);assert not(t%16==0 and z[:,0].any())and not(p['flip_y']and t//16==0 and z[0].any());counts['GPU_parts']+=1
  else:assert[sig(q)for q in op]==[sig(q)for q in bp];counts['non_target_compositions_exact']+=1
for n in sorted(REFS):
 for mask in range(16):
  for arm in(1,2):
   actual=np.array(b.composite(n,mask,arm)[0]);assert np.array_equal(actual,composite(targets[n],mask,arm));counts['target_partial_RGBA_exact']+=1
   if n%2==0:assert np.array_equal(actual[guards[n]],color(a,guns[n])[guards[n]]);counts['canonical_RGBA_conditions']+=1
def static(ar,pb,frame,ps=None):
 c=composition_frame(ar.c,pb,frame)if ps is None else{'parts':ps};px,size,bb,_=compose_static(entry(ar.data,0x10206),local_composition(c));z=np.zeros((384,384),np.uint8)
 if len(px):z[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]=np.frombuffer(px,np.uint8).reshape(size[1],size[0])
 return z,c
jets={};jetproof=[]
for q in relproof['jets']['frames']:
 jf=q['frame'];az,ac=static(a,12,jf);bz,bc=static(b,12,jf);expected=np.load(D/f'shibuki_base_hover_ownership01/jet_{jf:02}.npy');blob(D/f'shibuki_base_hover_ownership01/jet_{jf:02}.npy');assert np.array_equal(az,bz)and np.array_equal(bz,expected)and[sig(p)for p in ac['parts']]==[sig(p)for p in bc['parts']]
 for t in q['tiles']:assert tile_pixels(entry(a.data,0x10206),t)==tile_pixels(entry(b.data,0x10206),t)
 jets[jf]=bz;jetproof.append({'frame':jf,'refs':q['refs'],'indices_sha256':sha(bz.tobytes()),'whole_tiles':q['tiles'],'world_origin_unchanged':True})
lemons=[]
for q in relproof['lemon7']:
 n=q['step'][3];az,ac=static(a,1,n);bz,bc=static(b,1,n);assert np.array_equal(az,bz)and[sig(p)for p in ac['parts']]==[sig(p)for p in bc['parts']];lemons.append(bz)
 for t in q['tiles']:assert tile_pixels(entry(a.data,0x10206),t)==tile_pixels(entry(b.data,0x10206),t)
assert int((lemons[0]>0).sum())==188
native=js(H/'hover_ultimate_components_native_checks.json');nr=native['resources']['PL02_U.ARC'];assert native['passed']and nr['candidate_sha256']==sha(new)and nr['GPU_part_edge_checks']==97
for row in nr['banks'][0]['native_decoder_checks']:assert row['decoded_sha256']==sha(raw(b,0,row['frame']))
assert[ counts[k]for k in('raw_checked','non_target_raw_exact','target_layers_exact','non_target_layers_exact','non_target_compositions_exact','GPU_parts','target_partial_RGBA_exact','canonical_RGBA_conditions')]==[512,502,50,1090,1741,97,320,160],counts
O.mkdir(exist_ok=False);sheets=[]
def board(name,rows,scale=5,bg='#263345',crop=None):
 if crop is None:
  boxes=[im.getbbox()for row in rows for _,im in row if im.getbbox()];crop=(min(z[0]for z in boxes)-3,min(z[1]for z in boxes)-3,max(z[2]for z in boxes)+3,max(z[3]for z in boxes)+3)
 w,h=crop[2]-crop[0],crop[3]-crop[1];cw,ch=w*scale+10,h*scale+25;out=Image.new('RGB',(cw*len(rows[0]),ch*len(rows)),bg);dr=ImageDraw.Draw(out)
 for y,row in enumerate(rows):
  for x,(caption,im)in enumerate(row):
   dr.text((x*cw+3,y*ch+3),caption,fill='white'if bg=='#263345'else'black');pic=im.crop(crop).resize((w*scale,h*scale),Image.Resampling.NEAREST);out.paste(pic,(x*cw+5,y*ch+22),pic)
 p=O/name;out.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes()),'crop':list(crop),'integer_scale':scale,'background':bg})
for n in CUTS:board(f'readback_{n}.png',[[(f'{n} parent',a.composite(n,15)[0]),(f'{n} candidate',b.composite(n,15)[0])],[(f'{n+1} parent',a.composite(n+1,15)[0]),(f'{n+1} candidate',b.composite(n+1,15)[0])]])
def effect_image(z,c):
 arr=np.zeros((384,384,4),np.uint8);arr[z>0]=c;return Image.fromarray(arr)
for n in CUTS:
 seq=next(q for q in relproof['jets']['sequences']if q['refs'][0]==n);rows=[]
 for ref in(n,n+1):
  row=[]
  for step in seq['steps']:jf=step[3];im=effect_image(jets[jf],(32,208,232,180));im.alpha_composite(b.composite(ref,15)[0]);row.append((f'{ref} fixed jet{jf}',im))
  rows.append(row)
 board(f'jets_{n}.png',rows,5)
rows=[]
for n in(222,224,226,228,230):
 ox,oy=origins[n];im=effect_image(shift(lemons[0],ox,oy),(180,145,0,180));im.alpha_composite(b.composite(n,15)[0]);dr=ImageDraw.Draw(im);dr.line((ox+159,oy+160,ox+161,oy+160),fill='#00b8dd');dr.line((ox+160,oy+159,ox+160,oy+161),fill='#00b8dd');rows.append([(f'{n} new actual15',b.composite(n,15)[0]),(f'{n} original first bullet',im)])
board('muzzle_light.png',rows,5,'#e8e4db')
for p,h in tracked.items():assert sha((R/p).read_bytes())==h,p
report={'passed':True,'scope':'시부키 Ultimate 호버10의 사격생성5셀+222국소1셀 직접 재양자화/의미등록/정본총→50층/실제ARC·원효과 독립','candidate':rel(newp),'candidate_sha256':sha(new),'parent_sha256':sha(old),'counts':dict(counts),'generated_shot_fixed_cells_direct_requantized':source_cells,'body5_source_reconstruction':'동료 별도 reader 결과를 최종 마감에 결속. 여기서는 비사격25층 등록 PNG와 target/ARC exact 직접대조.','shot_reconstruction':shotproof,'actual_mask':15,'upper0_lower5_cuts':CUTS,'empty678_preserved':True,'body_shot_lower5_pair_exact':True,'canonical_source':'현재수용after34 actualmask0에서61이아닌60불투명+11투명guard 직접복원.원US개별총전체exact 주장은아님.','stream_groups':groups,'jet15':jetproof,'original_jet_6fulltiles_30parts_exact':True,'original_lemon7_fulltiles_records_exact':True,'muzzle_table_evidence':{'path':rel(D/'shibuki_base_hover_ownership01/report.json'),'sha256':sha((D/'shibuki_base_hover_ownership01/report.json').read_bytes())},'reserved_layers':reserved,'entry_bank_boundaries_palette_audio_exact':True,'native_producer10_raw_hashes_bound':True,'new_MIPS_execution':False,'readback_sheets':sheets,'actually_viewed':False,'inputs':tracked,'producer_functions_called':False,'resources_modified':False,'runtime_verified':False,'limits':['비사격5몸 생성 출처와221국소2회는 별도 독립 reader 결과를 최종 결속한다.','사격5의 초기222 여분팔은 국소수정 후 채택했고 생성총은 정본34로 대체했다. 의미 마스크 밖 새몸은 그대로다.','원15jet/7탄환의 현재후보와부모의바이트/의미조립은exact이다. 중립색정적합성은 실제팔레트/블렌딩/실기재현이아니다.','320부분은회귀진단이며실제Ultimate호버는mask15. 그림반쪽인mask0을새미술결함으로세지않는다.','원MIPS10 실행은제작자기존근거와raw해시결속이며새독립실행/실기주장이아니다.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({'passed':True,'report_sha256':sha((O/'report.json').read_bytes()),'counts':dict(counts),'source_cells':len(source_cells),'sheets':len(sheets)}))
