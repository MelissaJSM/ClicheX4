"""호버10 등록 몸/팔→정본총→층→ARC 및 원 추진/탄환 효과 독립 읽기."""
from pathlib import Path
import collections,hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;N=D.parent/'nana_audit'
sys.path[:0]=[str(ROOT),str(D)]
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from scripts.prepare_riko_ui import entry
from src.psx_player import bank_offsets,composition_frame
from src.psx_static_effect import compose_static
from src.psx_ui_atlas import local_composition,tile_pixels
from verify_shibuki_ultimate_hurt13_independent import raw,parts,sig,tile,color,polygons
U=N/'ultimate_hover_repaint';P=U/'packed_hover_candidate_v1';T=U/'targets_preview_v3';O=D/'nana_ultimate_hover10_independent01'
assert not O.exists()
PBS=(0,5,6,7,8);REFS=tuple(range(221,231));KEYS=(221,223,225,227,229);RESERVED={105,*range(175,183)}
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();tracked={};counts=collections.Counter()
def blob(p):
 z=p.read_bytes();tracked[rel(p)]=sha(z);return z
def js(p):return json.loads(blob(p))
def png(p):blob(p);return np.array(Image.open(p))
def npy(p):blob(p);return np.load(p)
Y,X=np.indices((384,384));Y-=160;X-=160
def box(q):return(X>=q[0])&(Y>=q[1])&(X<q[2])&(Y<q[3])
oldp=N/'ultimate_vehicle_repaint/packed_vehicle_candidate_v1/PL02_U.ARC';newp=P/'PL02_U.ARC'
old,new=blob(oldp),blob(newp);a,b=Archive(old),Archive(new)
assert sha(old)=='94326933d0dd62ccd7a5904019cae9fd36fc068a6acde8941d6bf8ff363666ca'
assert sha(new)=='e630d04286c1dbcbb65a5a301dd984f23cdecf13a1759dbaaf52ad8ae103efff'
lock=js(P/'INPUT_FROZEN.json');assert lock['candidate_sha256']==sha(new)and lock['parent_sha256']==sha(old)and len(lock['files'])==332
for q in lock['files']:assert sha(blob(ROOT/q['path']))==q['sha256'],q['path']
meta=js(T/'manifest.json');assert sha(blob(T/'manifest.json'))==lock['target_manifest_sha256']and meta['refs']==list(REFS)and meta['parent_arc_sha256']==sha(old)
jpath=D/'nana_ultimate_hover_relations01/conclusions.json';jetmeta=js(jpath);assert sha(blob(jpath))=='b518a054494823a9cb7de81947992b87470e4d880dd6951ba1cdafba54e2bf6c'
mpath=D/'nana_ultimate_hover_muzzle01/report.json';muzzle=js(mpath);assert sha(blob(mpath))=='dfaa75f60115ad090b787305a17bb5bc5df9626e92041ed7cc0f6cf86a30e679'
assert meta['source_relations']=={'path':rel(jpath),'sha256':sha(blob(jpath))}
origins={q['ref']:q['direction0_xy']for q in muzzle['origins']}
cm=js(U/'canonical_cases_probe_v4/manifest.json');jm=js(U/'muzzle_joint_probe_v1/manifest.json')
# 정본85의 피부/소매를 포함하지 않는 20개 색인을 부모에서 직접 얻는다.
ref85=a.layer(85,0)[0];gm=box([-22,-11,-14,-5])&np.isin(ref85,range(1,10))
coords=[[int(x-160),int(y-160),int(ref85[y,x])]for y,x in np.argwhere(gm)]
assert len(coords)==20 and coords==cm['canonical_source_texels']
def canonical(dx,dy):
 z=np.zeros((384,384),np.uint8)
 for x,y,v in coords:z[y+dy+160,x+dx+160]=v
 return z
bodies={};arms={};guns={};skins={};sourceproof=[]
for q in cm['frames']:
 n=q['ref'];v=png(ROOT/q['body_source']);assert sha(blob(ROOT/q['body_source']))==q['body_source_sha256']
 remove=np.zeros_like(v,bool)
 for rect in q['removal_boxes']:remove|=box(rect)
 assert q['removed_source_cells']==[[int(x-160),int(y-160),int(v[y,x])]for y,x in np.argwhere(remove&(v>0))]
 hx,hy=q['hand_anchor'];assert q['translation']==[hx+16,hy+9]
 case=canonical(*q['translation']);hand=box([hx-1,hy,hx+3,hy+5])&np.isin(v,[10,11,12,13])&~remove
 assert q['hand_source_cells']==[[int(x-160),int(y-160),int(v[y,x])]for y,x in np.argwhere(hand)]
 z=v.copy();z[remove]=0;use=(case>0)&~hand;z[use]=case[use]
 assert int(use.sum())==q['visible_case_texels']and int(((case>0)&hand).sum())==q['skin_occluded_case_texels']
 for tag,value in(('body',z),('case',case),('removal',remove.astype(np.uint8)*255),('hand',hand.astype(np.uint8)*255)):
  name=f'{tag}_{n:03}'+('_indices.png'if tag in('body','case')else'.png');assert np.array_equal(value,png(U/'canonical_cases_probe_v4'/name))
 assert sha(z.tobytes())==q['target_sha256']and label(z>0,np.ones((3,3)))[1]==1;bodies[n]=z
 sourceproof.append({'ref':n,'registered_body_and_canonical20_reconstructed':True,'translation':q['translation'],'old_firing_window_used':False})
for q in jm['frames']:
 n=q['ref'];donor=png(ROOT/q['source']);base=bodies[n-1];assert sha(blob(ROOT/q['source']))==q['source_sha256']and sha(blob(ROOT/q['body_source']))==q['body_source_sha256']
 assert np.array_equal(base,png(ROOT/q['body_source']))
 ox,oy=origins[n];assert q['engine_projectile_origin']==[ox,oy]and q['canonical_translation']==[ox+23,oy+9]
 mask=polygons([q['source_polygon']]);piece=np.where(mask,donor,0).astype(np.uint8)
 for x,y,v in q['source_generated_grip_removed_cells']:assert piece[y+160,x+160]==v and v in(5,6,7,8,9);piece[y+160,x+160]=0
 dx,dy=q['source_translation'];assert [dx,dy]==({224:[0,1],228:[3,0]}.get(n,[0,0]));placed=np.roll(np.roll(piece,dy,0),dx,1)
 z=base.copy();z[box(q['removed_held_window'])]=0;protected=((X>=-8)&(Y<=-10))|((X>=1)&(Y<=-7));use=(placed>0)&~protected;z[use]=placed[use]
 gun=canonical(*q['canonical_translation']);skin=box([ox+4,oy,ox+11,oy+6])&np.isin(placed,[10,11,12,13]);use=(gun>0)&~skin;z[use]=gun[use]
 assert int(use.sum())==q['canonical_visible']and int(((gun>0)&skin).sum())==q['canonical_skin_occluded']
 for tag,value in(('body',z),('source_arm',piece),('placed_arm',placed),('canonical',gun)):assert np.array_equal(value,png(U/'muzzle_joint_probe_v1'/f'{tag}_{n:03}_indices.png'))
 assert np.array_equal(z[Y>=3],base[Y>=3])and np.array_equal(z[(X>=-8)&(Y<=-10)],base[(X>=-8)&(Y<=-10)])
 assert sha(z.tobytes())==q['target_sha256']and label(z>0,np.ones((3,3)))[1]==1
 assert all(gun[160+yy,161+ox]>0 for yy in(oy-1,oy));assert np.array_equal(z[gun>0],np.where(skin,placed,gun)[gun>0])
 bodies[n]=z;arms[n]=placed;guns[n]=gun;skins[n]=skin
 sourceproof.append({'ref':n,'registered_arm_polygon_and_new_body_reconstructed':True,'new_arm_translation':[dx,dy],'engine_origin':[ox,oy],'canonical_front_x':ox+1,'barrel_rows':[oy-1,oy],'visible':q['canonical_visible'],'skin_occluded':q['canonical_skin_occluded'],'head_and_lower_body_exact':True,'old_firing_window_used':False})
target={}
for q in meta['frames']:
 n=q['ref'];z=bodies[n];assert np.array_equal(z,png(ROOT/q['source']))and sha(blob(ROOT/q['source']))==q['source_sha256']and 15 not in z
 cut=q['cut_world_y'];assert cut=={221:5,223:6,225:5,227:7,229:5}[n if n%2 else n-1]
 expected={0:np.where(Y<cut,z,0),5:np.where(Y>=cut,z,0),6:np.zeros_like(z),7:np.zeros_like(z),8:np.zeros_like(z)}
 for pb,v in expected.items():
  assert np.array_equal(v,png(T/f'layer{pb}_{n:03}.png'))and sha(v.tobytes())==q['layer_hashes'][str(pb)]==meta['targets'][str(n)][str(pb)];target[n,pb]=v
for n in KEYS:assert np.array_equal(target[n,5],target[n+1,5])
# 외부/그래픽/조립 경계, 비대상 raw 및 레코드 전수.
assert len(old)==len(new)and a.p==b.p
ae,be=psx_arc(old),psx_arc(new);assert [(q['type'],q['offset'],q['size'])for q in ae]==[(q['type'],q['offset'],q['size'])for q in be]
allowed=np.zeros(len(old),bool)
for e in ae:
 if int(e['type'],16)in(2,3):allowed[e['offset']:e['offset']+e['size']]=True
assert not np.any((np.frombuffer(old,np.uint8)!=np.frombuffer(new,np.uint8))&~allowed)
assert bank_offsets(a.g,allow_aliases=True)==bank_offsets(b.g,allow_aliases=True)and bank_offsets(a.c)==bank_offsets(b.c)
for gb,(ab,bb)in enumerate(zip(a.banks,b.banks)):
 assert(ab['base'],ab['end'],len(ab['frames']))==(bb['base'],bb['end'],len(bb['frames']))
 if gb:assert a.g[ab['base']:ab['end']]==b.g[bb['base']:bb['end']]
 for af,bf in zip(ab['frames'],bb['frames']):
  n=af['index'];assert n==bf['index']and af['tile_count']==bf['tile_count'];counts['raw_checked']+=1
  if gb or n not in REFS:assert raw(a,gb,n)==raw(b,gb,n);counts['non_target_raw_exact']+=1
groups=[]
for n in KEYS:
 for ar in(a,b):
  fs=ar.banks[0]['frames'];assert [f['index']for f in fs if f['offset']==fs[n]['offset']]==[n,n+1]and fs[n]['tile_count']==fs[n+1]['tile_count']==32
 groups.append({'refs':[n,n+1],'tiles':32,'parent_offset':a.banks[0]['frames'][n]['offset'],'candidate_offset':b.banks[0]['frames'][n]['offset']})
for n in range(237):
 for pb in PBS:
  if n in RESERVED:
   vals=[]
   for ar in(a,b):
    try:vals.append(('renderable',ar.layer(n,pb)[0]))
    except Exception as ex:vals.append((type(ex).__name__,str(ex)))
   assert vals[0][0]==vals[1][0]
   if vals[0][0]=='renderable':assert np.array_equal(vals[0][1],vals[1][1])
   else:assert vals[0][1]==vals[1][1]
   counts['reserved_same_state']+=1;continue
  assert np.array_equal(b.layer(n,pb)[0],target[n,pb]if n in REFS else a.layer(n,pb)[0]),(n,pb)
  counts['target_layers_exact'if n in REFS else'non_target_layers_exact']+=1
for pb in range(len(bank_offsets(a.c))):
 for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
  ps,qs=parts(a,pb,n),parts(b,pb,n)
  if pb in PBS and n in REFS:
   for q in qs:
    t=q['tile']+q['page']*256;assert 0<=t<32 and not q['unknown_flags'];v=tile(b,n,t)
    assert not(t%16==0 and v[:,0].any())and not(q['flip_y']and t//16==0 and v[0].any());counts['GPU_parts_checked']+=1
  else:assert [sig(q)for q in ps]==[sig(q)for q in qs];counts['non_target_compositions_exact']+=1
for n in REFS:
 for mask in range(16):
  for arm in(1,2):
   z=bodies[n]if mask&1 else target[n,0];expect=color(b,z);actual=np.asarray(b.composite(n,mask,arm)[0]);assert np.array_equal(actual,expect);counts['partial_RGBA_exact']+=1
   if mask&1:assert label(actual[:,:,3]>0,np.ones((3,3)))[1]==1
   if n in guns:assert np.array_equal(actual[guns[n]>0],color(b,bodies[n])[guns[n]>0]);counts['muzzle_hand_conditions']+=1
# 별도 추진기15위상 및 첫 탄환7프레임은 원래 독립 조사와 전체 타일 대조.
static=entry(new,0x10206);assert static==entry(old,0x10206)
def static_canvas(pb,n):
 cp=composition_frame(b.c,pb,n);px,sz,bb,_=compose_static(static,local_composition(cp));z=np.zeros((384,384),np.uint8);z[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]=np.frombuffer(px,np.uint8).reshape(sz[1],sz[0]);return z,cp
jets={}
for q in jetmeta['effect_frames']:
 f=q['effect_frame'];z,cp=static_canvas(12,f);assert [sig(p)for p in cp['parts']]==[sig(p)for p in q['parts']]and sha(z.tobytes())==q['indexed_sha256']and np.array_equal(z,npy(ROOT/q['source_dump']));jets[f]=z;counts['original_jet_phases_exact']+=1
for q in jetmeta['whole_tiles']:assert sha(tile_pixels(static,q['tile']))==q['sha256'];counts['original_jet_whole_tiles_exact']+=1
for q in muzzle['first7_effect_frames']:
 z,cp=static_canvas(1,q['frame']);assert [sig(p)for p in cp['parts']]==[sig(p)for p in q['parts']]and sha(z.tobytes())==q['indexed_sha256'];counts['original_lemon_phases_exact']+=1
first=static_canvas(1,0)[0];assert np.count_nonzero(first)==188
native=js(U/'native_components_v1_native_checks.json');res=native['resources']['PL02_U.ARC'];assert native['passed']and res['candidate_sha256']==sha(new)
for q in res['banks'][0]['native_decoder_checks']:assert sha(raw(b,0,q['frame']))==q['decoded_sha256']and q['buffer_outside_and_unused_tail_preserved'];counts['producer_native_decoded_hash_bound']+=1
assert dict((k,counts[k])for k in('raw_checked','non_target_raw_exact','target_layers_exact','non_target_layers_exact','non_target_compositions_exact','GPU_parts_checked','partial_RGBA_exact','muzzle_hand_conditions'))=={'raw_checked':512,'non_target_raw_exact':502,'target_layers_exact':50,'non_target_layers_exact':1090,'non_target_compositions_exact':1741,'GPU_parts_checked':116,'partial_RGBA_exact':320,'muzzle_hand_conditions':160}
O.mkdir(exist_ok=False);sheets=[]
def board(items,name,columns,scale=5):
 boxes=[im.getbbox()for _,im in items if im.getbbox()];bb=(min(q[0]for q in boxes)-3,min(q[1]for q in boxes)-3,max(q[2]for q in boxes)+3,max(q[3]for q in boxes)+3);w,h=bb[2]-bb[0],bb[3]-bb[1];cw,ch=w*scale+10,h*scale+25;im=Image.new('RGB',(cw*columns,ch*((len(items)+columns-1)//columns)),'#263345');dr=ImageDraw.Draw(im)
 for i,(title,pic)in enumerate(items):
  x,y=i%columns*cw,i//columns*ch;v=pic.crop(bb).resize((w*scale,h*scale),Image.Resampling.NEAREST);im.paste(v,(x+5,y+22),v);dr.text((x+5,y+3),title,fill='white')
 p=O/name;im.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes()),'same_origin':True,'no_opaque_clipping':True})
for n in KEYS:
 board([(f'{r} {title}',ar.composite(r,15)[0])for r in(n,n+1)for ar,title in((a,'old mask15'),(b,'new mask15'))],f'pair_{n}.png',2,6)
items=[]
for n in(222,224,226,228,230):
 ox,oy=origins[n];world=np.roll(np.roll(first,oy,0),ox,1);fi=np.zeros((384,384,4),np.uint8);fi[world>0]=(173,154,40,255);im=Image.fromarray(fi);im.alpha_composite(b.composite(n,15)[0]);ImageDraw.Draw(im).point((ox+160,oy+160),fill='#00ffee');items.append((f'{n} neutral first188 ({ox},{oy})',im))
board(items,'first_effect_occupancy.png',5,5)
for n in KEYS:
 items=[]
 for q in jetmeta['effect_frames']:
  if n not in q['player_refs']:continue
  f=q['effect_frame'];fi=np.zeros((384,384,4),np.uint8);fi[jets[f]>0]=(70,150,210,255)
  for r in(n,n+1):im=Image.fromarray(fi);im.alpha_composite(b.composite(r,15)[0]);items.append((f'{r} neutral jet{f}',im))
 board(items,f'jets_{n}.png',2,4)
for p,h in tracked.items():assert sha((ROOT/p).read_bytes())==h,p
report={'passed':True,'scope':'Nana Ultimate 호버10 등록소스/정본20/실제발사점/상하체50층/비대상/원추진기 독립 읽기','candidate':rel(newp),'candidate_sha256':sha(new),'parent_sha256':sha(old),'locked_inputs':332,'input_frozen_sha256':sha((P/'INPUT_FROZEN.json').read_bytes()),'counts':dict(counts),'source_reconstruction':sourceproof,'shared_raw_groups':groups,'mask_policy':'217..230 실제 engine mask15 고정. layer0=상체,layer5=하체,6/7/8=빈층. mask0은 기술부분표시이지 후폼 전신이 아니다.','original_muzzle_evidence':{'path':rel(mpath),'sha256':sha(blob(mpath))},'original_jet_evidence':{'path':rel(jpath),'sha256':sha(blob(jpath))},'code_or_timing_modified':False,'entries_palette_audio_external_and_all_bank_boundaries_preserved':True,'readback_sheets':sheets,'readback_actually_viewed':False,'inputs':tracked,'producer_functions_called':False,'new_MIPS_executed':False,'runtime_verified':False,'limits':['생성10셀 재양자화는 제작자 증거이고 여기서는 고정 등록 몸/팔의 국소 재구성→정본총→50층→ARC를 직접 대조했다.','독립 부분은320RGBA/160총손 조건이며 제작자 전체7296RGBA 재검사와 구분한다.','15추진위상과 최초탄환7프레임/188픽셀은 원색인·원파트 보존이다. 진단 합성은 중립색 점유이며 실제 효과 CLUT/블렌딩/발사시점의 실기 검증이 아니다.','원 발사점 표에 맞춘 것은 정적 좌표 검사이다. 이미 수행된 제작자 MIPS decoded hash만 결속했고 여기서 새 원MIPS나 게임 실행을 하지 않았다.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'report_sha256':sha((O/'report.json').read_bytes()),'counts':dict(counts),'sheets':len(sheets)}))
