"""Independent read-only source rules for Shibuki four-form hurt frames."""
from pathlib import Path
import collections, hashlib, json, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_dilation, label
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
from scripts.c01_audio_build import read_disc
from src.psx_player import composition_frame, decode_stream, compose_indices, indexed_atlas
from src.psx_ui_atlas import local_composition
D=Path(__file__).parent;H=D.parent/'shibuki_audit';O=D/'shibuki_hurt_sources01';O.mkdir(exist_ok=True)
PBS=(0,5,6,7,8);REFS=[*range(106,115),*range(233,237)]
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
sig=lambda p:(p['flags'],p['tile'],p['x'],p['y'])
sources={'PL00_U.ARC':(H/'prepared_base_run01/PL00_U.ARC','381d83fa2623d58a3302914196ffdd73bd8c972e27aa584380af05d819e688ce'),
         'PL02_U.ARC':(H/'prepared_ultimate_ladder01/PL02_U.ARC','03a675626035b93ad2e2feef8dd643365ed8a3e1a61a1eb02a476063e2c55e8a')}
original,_=read_disc(ROOT/'MegaMan X4.bin',('PL00_U.ARC','PL02_U.ARC'))
tracked={}
def read(p):
 v=p.read_bytes();tracked[rel(p)]=sha(v);return v
def raw(a,n):
 f=a.banks[0]['frames'][n];return decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128).data
def parts(a,n,pb):return composition_frame(a.c,pb,n)['parts']
def render(a,n,pb,ps):
 out=np.zeros((384,384),np.uint8)
 if not ps:return out
 f=a.banks[0]['frames'][n];cp={'parts':ps}
 if pb:cp=local_composition(cp)
 px,sz,bb,_=compose_indices(raw(a,n),f['tile_count'],cp,allowed_cluts={0,1,2,3})
 v=np.frombuffer(px,np.uint8).reshape(sz[1],sz[0]);y,x=np.nonzero(v);out[y+bb[1]+160,x+bb[0]+160]=v[y,x];return out
def full(a,n):
 v=a.layer(n,0)[0].copy()
 for pb in(8,5,7,6):
  z=a.layer(n,pb)[0];v[z>0]=z[z>0]
 return v
def box(m):
 y,x=np.nonzero(m);return[int(x.min()-160),int(y.min()-160),int(x.max()-159),int(y.max()-159)]if len(x)else None
def diff(v,w):
 m=np.any(v!=w,axis=2)if v.ndim==3 else v!=w
 return {'different_pixels':int(m.sum()),'bbox_world':box(m)}
def paste(v,fx):
 z=v.copy();z[fx>0]=fx[fx>0];return z
def minus(body,allparts):
 rem=collections.Counter(sig(p)for p in body);extra=[];matched=[]
 for p in allparts:
  if rem[sig(p)]:rem[sig(p)]-=1;matched.append(p)
  else:extra.append(p)
 return rem,matched,extra
def tile(a,n,t):
 f=a.banks[0]['frames'][n];v=np.frombuffer(indexed_atlas(raw(a,n),f['tile_count'])[0],np.uint8).reshape(-1,256)
 return v[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
def clut2_shape(res,body,n,remove_small=False):
 z=res.copy();m=body>0
 if n==112:z[binary_dilation(m)]=6;z[m]=14
 elif n==113:z[binary_dilation(m)]=1
 else:
  z[binary_dilation(m)]=1;z[m]=3
  z[np.isin(body%16,[1,2,4,8,15])&m]=5;z[np.isin(body%16,[6,9])&m]=1
 deleted=[]
 if remove_small:
  labs,count=label(z>0);sizes=np.bincount(labs.ravel());sizes[0]=0;drop=(labs>0)&(sizes[labs]<4)
  deleted=[{'x':int(x-160),'y':int(y-160),'value':int(z[y,x])}for y,x in zip(*np.nonzero(drop))];z[drop]=0
 return np.where(z,z+32,0).astype(np.uint8),deleted
records=[];images=[]
for name,(path,expected)in sources.items():
 blob=read(path);assert sha(blob)==expected;a=Archive(blob);us=Archive(original[name]);od=O/name[:4];od.mkdir(exist_ok=True)
 histp=ROOT/'work/overhaul_20261105/sprites/ver_buki_riko/baseline'/name
 hist=Archive(read(histp));rows=[];effects=[];flashes=[];aura=[];derived=[]
 for n in REFS:
  f=a.banks[0]['frames'][n]
  rows.append({'ref':n,'stream':f['offset'],'tile_count':f['tile_count'],
   'stream_owners':[q['index']for q in a.banks[0]['frames']if q['offset']==f['offset']],
   'layers':{str(pb):{'parts':parts(a,n,pb),'indexed_sha256':sha(a.layer(n,pb)[0].tobytes()),'opaque':int(np.count_nonzero(a.layer(n,pb)[0]))}for pb in PBS}})
 for n,core in((107,106),(108,106),(111,110)):
  origrem,_,origextra=minus(parts(us,core,0),parts(us,n,0));assert not any(origrem.values())
  origfx=render(us,n,0,origextra);fxpath=od/f'original_effect_{n}.npy';np.save(fxpath,origfx)
  tiles=sorted({p['tile']+p['page']*256 for p in origextra})
  layerproof={}
  for pb in PBS:
   rem,matched,extra=minus(parts(a,core,pb),parts(a,n,pb));cm=render(a,n,pb,matched);ex=render(a,n,pb,extra)
   layerproof[str(pb)]={'all_core_records_found':not any(rem.values()),'matched_core_diff':diff(cm,a.layer(core,pb)[0]),
     'unmatched_records':extra,'unmatched_pixels':int(np.count_nonzero(ex)),
     'unmatched_proven_only_effect':not any(rem.values())and np.array_equal(cm,a.layer(core,pb)[0]),
     'core_plus_original_base_effect_diff':diff(paste(a.layer(core,pb)[0],origfx%16 if pb else origfx),a.layer(n,pb)[0])}
  forms={}
  for mask,labelname in((0,'base_or_after'),(15,'fourth_or_before')):
   coreidx=a.layer(core)[0]if mask==0 else full(a,core);target=a.layer(n)[0]if mask==0 else full(a,n)
   rgbcore=np.asarray(a.composite(core,mask,1)[0]);rgbtarget=np.asarray(a.composite(n,mask,1)[0]);rgbeffect=np.asarray(a.rgba(origfx));predrgb=rgbcore.copy();predrgb[origfx>0]=rgbeffect[origfx>0]
   forms[labelname]={'core_plus_original_effect_index_diff':diff(paste(coreidx,origfx),target),
     'core_plus_original_effect_RGBA_diff':diff(predrgb,rgbtarget),
     'RGBA_difference_outside_original_effect':int(np.count_nonzero(np.any(rgbcore!=rgbtarget,axis=2)&(origfx==0))),
     'body_inside_changed':int(np.count_nonzero((target!=coreidx)&(coreidx>0))),
     'outside_body_pixels':int(np.count_nonzero((target>0)&(coreidx==0)))}
  clut2=[p for p in parts(a,n,0)if p['clut']==2]
  native_fx=render(a,n,0,clut2)
  armorfx={}
  if n in(107,108):
   for pb in PBS[1:]:
    op=[p for p in parts(us,n,pb)if p['tile']in(17,18)]
    cur=[p for p in parts(a,n,pb)if p['tile']in(17,18)]
    armorfx[str(pb)]={'original_effect_records':op,
     'current_same_number_records':cur,
     'current_records_equal_original':[(p['flags'],p['tile'],p['x'],p['y'])for p in op]==[(p['flags'],p['tile'],p['x'],p['y'])for p in cur],
     'original_fixed_clut_effect_pixels':int(np.count_nonzero(render(us,n,pb,op))),
     'current_fixed_clut_effect_comparison':diff(render(us,n,pb,op),render(a,n,pb,cur))}
  effects.append({'ref':n,'core':core,'original_effect_pixels':int(np.count_nonzero(origfx)),
   'original_effect_parts':origextra,'original_effect_tiles':tiles,
   'whole_original_tiles_preserved':{str(t):bool(np.array_equal(tile(a,n,t),tile(us,n,t)))if t<a.banks[0]['frames'][n]['tile_count']else False for t in tiles},
   'original_tile_pattern_matches_any_current_tile':{str(t):[j for j in range(a.banks[0]['frames'][n]['tile_count'])if np.array_equal(tile(us,n,t),tile(a,n,j))]for t in tiles},
   'actual_CLUT2_records':clut2,'actual_CLUT2_pixels':int(np.count_nonzero(native_fx)),
   'actual_CLUT2_core_prediction':diff(paste(a.layer(core)[0],native_fx),a.layer(n)[0]),
   'original_armor_effect17_18':armorfx,
   'whole_original_armor_tiles_17_18_preserved':{str(t):bool(np.array_equal(tile(a,n,t),tile(us,n,t)))for t in(17,18)}if n in(107,108)else{},
   'layers':layerproof,'forms':forms,'effect_npy':rel(fxpath)})
 for mask,labelname in((0,'base_or_after'),(15,'fourth_or_before')):
  body=a.layer(106)[0]if mask==0 else full(a,106);actual=a.layer(109)[0]if mask==0 else full(a,109);m=body>0
  vals,cnt=np.unique(actual[actual>0],return_counts=True);tests=[]
  for inside in(13,14):
   z=np.where(binary_dilation(m),9,0).astype(np.uint8);z[m]=inside;tests.append({'inside':inside,**diff(z,actual)})
  flashes.append({'form':labelname,'index_counts':dict(zip(map(int,vals),map(int,cnt))),'rules':tests,
                  'body_pixels':int(m.sum()),'overlay_nonzero':{str(pb):int(np.count_nonzero(a.layer(109,pb)[0]))for pb in PBS[1:]}})
 # PL00 retains the early native-source external rays and small-component cleanup.
 # PL02 uses the later full-jacket CLUT2 policy recorded in state_layers.
 for n in(112,113,114):
  origin=us if name.startswith('PL00')else hist
  oldbody=origin.layer(110)[0];native=origin.layer(n)[0]%16
  residual=native.copy();residual[binary_dilation(oldbody>0,iterations=2)]=0
  if n==114:residual[np.isin(residual,[3,5])]=0
  refbody=a.layer(110)[0]if name.startswith('PL00')else full(hist,110)
  predicted,deleted=clut2_shape(residual,refbody,n,remove_small=name.startswith('PL00'))
  np.save(od/f'{n}_external_residual.npy',residual)
  derived.append({'ref':n,'body_source':'current_base110'if name.startswith('PL00')else'historical_full_jacket110',
   'historical_jacket110_vs_current':diff(full(hist,110),full(a,110)),
   'external_residual_pixels':int(np.count_nonzero(residual)),'residual_path':rel(od/f'{n}_external_residual.npy'),
   'old_rule_reconstruction':diff(predicted,a.layer(n)[0]),'small_components_deleted_coordinates':deleted,
   'empty_armor_layers':{str(pb):not np.any(a.layer(n,pb)[0])for pb in PBS[1:]}})
 for n in(235,236):
  native=us.layer(n)[0]%16;nativebody=us.layer(234)[0]>0
  sourcefx=np.where(native==(8 if n==235 else 5),9 if n==235 else 6,0).astype(np.uint8)
  sourcefx[binary_dilation(nativebody)]=0
  np.save(od/f'{n}_historical_original_effect.npy',sourcefx)
  forms={}
  for mask,labelname in((0,'base_or_after'),(15,'fourth_or_before')):
   body=a.layer(234)[0]if mask==0 else full(a,234);v=a.layer(n)[0]if mask==0 else full(a,n)
   external=np.where(body==0,v,0).astype(np.uint8);labs,cnt=label(external>0,np.ones((3,3)))
   np.save(od/f'{n}_{labelname}_external.npy',external)
   dif=(body>0)&(v!=body)
   histbody=hist.layer(234)[0]if mask==0 else full(hist,234);histv=hist.layer(n)[0]if mask==0 else full(hist,n)
   forms[labelname]={'inside234_difference':int(dif.sum()),'inside234_difference_bbox':box(dif),
    'inside234_changes':[{'x':int(x-160),'y':int(y-160),'body234':int(body[y,x]),'frame':int(v[y,x])}for y,x in zip(*np.nonzero(dif))],
    'external_pixels':int(np.count_nonzero(external)),'external_components8':cnt,'external_sha256':sha(external.tobytes()),
    'historical_body_vs_current':diff(histbody,body),'historical_frame_vs_current':diff(histv,v),
    'external_path':rel(od/f'{n}_{labelname}_external.npy'),
    'historical_original_effect_plus_current_body':diff(paste(sourcefx,body),v),
    'external_vs_historical_original_effect':diff(external,np.where(body==0,sourcefx,0).astype(np.uint8))}
  # Original current-base body separation does not imply its armor differences are FX.
  aura.append({'ref':n,'core':234,'historical_original_effect_pixels':int(np.count_nonzero(sourcefx)),
    'historical_effect_rule':'원US 색인235:8→9,236:5→6 중 원234 Manhattan1팽창 안을 제외한 뒤 새몸을 위에 합성',
    'historical_effect_path':rel(od/f'{n}_historical_original_effect.npy'),
    'layers':{str(pb):diff(a.layer(n,pb)[0],a.layer(234,pb)[0])for pb in PBS},'forms':forms})
 for number,ns in enumerate((list(range(106,110)),list(range(110,115)),list(range(233,237)))):
  cw,ch=270,360;board=Image.new('RGB',(cw*len(ns),ch*2),'#263345');draw=ImageDraw.Draw(board)
  for row,mask in enumerate((0,15)):
   for col,n in enumerate(ns):
    im=a.composite(n,mask,1)[0].crop((128,112,192,196)).resize((256,336),Image.Resampling.NEAREST)
    board.paste(im,(col*cw+7,row*ch+20),im);draw.text((col*cw+7,row*ch+4),f'{name[:4]} ref{n} mask{mask}',fill='white')
  p=od/f'current_{number:02}.png';board.save(p);images.append({'path':rel(p),'sha256':sha(p.read_bytes()),'refs':ns,'forms':[0,15]})
 records.append({'archive':name,'source':rel(path),'source_sha256':expected,'refs':rows,'effects':effects,
                 'flash109':flashes,'silhouettes112_114':derived,'aura235_236':aura})
codepaths=['work/ver_buki_riko/shibuki_art/hurt_v1/prepare_effects03.py','scripts/overhaul_sprites_state_layers.py','scripts/overhaul_sprites_costume.py',
           'work/ver_buki_riko/shibuki_art/remaining_v1/assemble04.py','work/ver_buki_riko/shibuki_art/fourth_armor_remaining_v1/register_remaining.py',
           'scripts/register_shibuki_ultimate_production.py']
for p in codepaths:read(ROOT/p)
report={'scope':'시부키 네폼 피격13의 현재바이트·원US 효과타일·과거 실루엣 규칙을 별도 읽었다. 미술 제작함수 호출/ARC 변경/새MIPS/실기 없음.',
 'archives':records,'original_asset_sha256':{n:sha(v)for n,v in original.items()},'input_files':tracked,
 'producer_code_read_only':codepaths,'sheets':images,'actual_sheet_views':True,
 'visual_review':'현재 네폼13참조52표시를 재추출6판에서 실제 열람했다.107/108의 지그재그는 효과로 구분되며109/112~114는 의상 일반색이 아니라 섬광이다.235/236은234와 신발·옷 일부가 달라지는 것이 실제 정지판에서도 보인다. 이 관찰은 새원화 수용이나 실제 게임 검증이 아니다.',
 'conclusions':[
  '현재 각ARC의106/107/108 및110/111은 각각raw를 공유한다.235/236은234와 별도stream이다. raw/조립을 같은것으로 간주하여 단순복사하지 않는다.',
  'PL00 기본107/108은106+원US99/76픽셀 효과와exact. 원효과tile6/7와 아머효과17/18을 별도 보호할 수 있다. 일부Fourth body레코드 subset이 실패해도 각폼RGBA의106과다른좌표는 모두 원99/76 효과마스크 안이다. unmatched전체를 효과로 분류하면몸체가 섞인다.',
  'PL02 107/108은 원효과tile6/7가 그대로남은구조가 아니라 재패킹한합성이다. 현재두폼의변화좌표는 원US효과마스크 안이지만 원99/76을그대로덮은결과와22/24(after),23/25(before)픽셀다르다. before layer5 extra112픽셀을 원효과99/76로 오인하지 않는다. 새몸체+원효과공통화는 기존그림exact보존과구분해검토할 사항이다.',
  '111 PL00은 원CLUT2 12타일202픽셀을110위에합성하면exact. PL02는 실제CLUT2 194픽셀로110위합성이exact이며 일부원타일패턴은없다. 나나의188픽셀이나새12타일을그대로가져오지않는다. 두ARC모두 아머그리기 뒤의가림은 따로검사한다.',
  '109 내부는14이고외곽은Manhattan1의9다. PL00은빈아머층+기본106공통실루엣이며포스106알파를써서현재exact라고하면18픽셀오류다. PL02는after106과before106각각실루엣으로정확재구성된다.',
  '112~114 PL00은원US110몸의Manhattan2를뺀130/123/319외부잔여와현재기본110으로exact재구성된다. 원small-component삭제9/9/11좌표를명시했다. 새몸 작은성분을다시삭제하지말고원효과삭제좌표와구분한다. PL02는과거baseline full110+잔여62/56/242의공통CLUT2로exact이며모든아머층이빈칸이다.',
  '235/236 과거제작은원US235색8→9,236색5→6 중원234 Manhattan1밖256/464픽셀을취하고새몸234를위에합성했다. 이독립규칙으로현재PL00기본을0픽셀오차재현했다. 현재가시외부는199/353으로나나85/172와다르다.',
  'PL00 Fourth235/236은234내부158/156픽셀과외부오라46/77색인픽셀이위기본규칙과다르며과거의상등록결과가그대로남아있다. PL02두폼역시234내부157/141(after),163/165(before)픽셀차이 및오라색차이가있다. 이몸/옷차이를효과로보존하여새234에붙이면구형옷조각이섞일수있다.',
  '새234를모든파생에공유하려면실제원오라256/464출처와현재가시외부199/353출처를구분하여선택하고새가림/색을직접검토해야한다. 이보고는무조건원US색으로되돌리거나현재가시색을자동재작화하는승인이아니다.'
 ],
 'limits':['부분아머 조합 전체와 프레임 간 실제 가림은 이 읽기조사에서 실행하지 않았다.',
 '모든 unmatched part를 효과로 간주하지 않는다. body subset 실패 및 내부 색 차이는 별도로 남겼다.',
 '현재 몸 바깥 픽셀은 확실히 분리할 수 있는 현재 외부상이며 숨은 원효과 전체 복원으로 부르지 않는다.']}
for p,h in tracked.items():assert sha((ROOT/p).read_bytes())==h,p
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'sha':sha((O/'report.json').read_bytes()),'archives':[{'archive':r['archive'],
 'fx':[{'ref':x['ref'],'pixels':x['original_effect_pixels'],'tiles':x['whole_original_tiles_preserved'],'forms':x['forms']}for x in r['effects']],
 'flash':r['flash109'],'derived':r['silhouettes112_114'],
 'aura':[{'ref':x['ref'],'forms':{k:{q:v[q]for q in('inside234_difference','external_pixels','external_components8')}for k,v in x['forms'].items()}}for x in r['aura235_236']]}for r in records]},ensure_ascii=False))
