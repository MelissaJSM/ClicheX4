"""노바213..220 원US/역사 제작/현재 몸·에너지 소유를 읽기만 비교."""
from pathlib import Path
import hashlib,json,sys,struct
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import binary_dilation,binary_fill_holes,label
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent;N=W/'nana_audit';O=D/'nana_ultimate_nova_relations01';assert not O.exists()
sys.path[:0]=[str(ROOT),str(D)]
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,animation_map
from src.psx_player import composition_frame,bank_offsets
from verify_shibuki_ultimate_hurt13_independent import raw,parts,sig,tile
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();tracked={};PBS=(0,5,6,7,8);REFS=tuple(range(213,221))
def blob(p):
 z=p.read_bytes();tracked[rel(p)]=sha(z);return z
def js(p):return json.loads(blob(p))
def shift(z,dx,dy):
 out=np.zeros_like(z);yy,xx=np.nonzero(z);assert not len(xx)or(min(xx+dx)>=0 and max(xx+dx)<384 and min(yy+dy)>=0 and max(yy+dy)<384);out[yy+dy,xx+dx]=z[yy,xx];return out
def bounds(z):
 y,x=np.nonzero(z);return None if not len(x)else[int(x.min()-160),int(y.min()-160),int(x.max()+1-160),int(y.max()+1-160)]
curp=N/'ultimate_hover_repaint/packed_hover_candidate_v1/PL02_U.ARC';cur=Archive(blob(curp));assert sha(cur.data)=='e630d04286c1dbcbb65a5a301dd984f23cdecf13a1759dbaaf52ad8ae103efff'
original,_=read_disc(ROOT/'MegaMan X4.bin',('PL02_U.ARC','SLUS_005.61'));us=Archive(original['PL02_U.ARC'])
hp=ROOT/'work/ver_rin_nana/nana_ultimate_armor/nova_packed_v2/PL02_U.ARC';hist=Archive(blob(hp))
core=ROOT/'work/ultimate_costume_swap_20261105/core';swap=Archive(blob(core/'prepared_complete_v1/ver_rin_nana/PL02_U.ARC'))
source,_=read_disc(ROOT/'out/ver_rin_nana/black_red_rin_20261105_v1/rin_nana.bin',('PL02_U.ARC',));src=Archive(source['PL02_U.ARC']);assert sha(src.data)=='95f0734990ebe2bcec99b61f13ebe009d96ddcb74e745f4acd9954a0cadb7cbc'
previous=Archive(blob(N/'ultimate_vehicle_repaint/packed_vehicle_candidate_v1/PL02_U.ARC'))
for n in REFS:
 assert raw(previous,0,n)==raw(cur,0,n)
 for pb in PBS:assert np.array_equal(previous.layer(n,pb)[0],cur.layer(n,pb)[0])and [sig(q)for q in parts(previous,pb,n)]==[sig(q)for q in parts(cur,pb,n)]
pairs=[]
for tag,ar in(('original_US',us),('historic_nova_v2',hist),('costume_swap_complete',swap),('current',cur)):
 for n,m in((213,214),(215,216)):
  layers=[]
  for pb in PBS:
   a,b=ar.layer(n,pb)[0],ar.layer(m,pb)[0];diff=a!=b
   layers.append({'bank':pb,'different_cells':int(diff.sum()),'alpha_difference':int(((a>0)!=(b>0)).sum()),'difference_bounds':bounds(diff),'same_records': [sig(q)for q in parts(ar,pb,n)]==[sig(q)for q in parts(ar,pb,m)]})
  pairs.append({'archive':tag,'pair':[n,m],'raw_stream_shared':ar.banks[0]['frames'][n]['offset']==ar.banks[0]['frames'][m]['offset'],'all5layers_exact':all(q['different_cells']==0 for q in layers),'layers':layers})
# 역사 표시교환은 대시73의 최대 연결성분과 +3,-6 이동을 사용했다.
z=src.layer(73,0)[0];labs,_=label(z>0,np.ones((3,3)));sizes=np.bincount(labs.flat);sizes[0]=0;oldbody=np.where(labs==sizes.argmax(),z,0).astype(np.uint8);body=shift(oldbody,3,-6)
assert np.count_nonzero(oldbody)==683 and np.array_equal(body,swap.layer(217,0)[0])
flash=np.zeros_like(body);flash[binary_dilation(body>0,iterations=2)]=7;flash[body>0]=6
assert np.array_equal(flash,swap.layer(219,5)[0])and np.array_equal(flash,cur.layer(219,5)[0])and not cur.layer(219,0)[0].any()
effects=[]
for n in(218,220):
 oldfx=src.layer(n,5)[0];oldcore=src.layer(217,5)[0];options=[]
 for dy in range(-8,9):
  for dx in range(-16,17):
   moved=shift(oldcore,dx,dy);options.append((int(((moved>0)&(moved==oldfx)).sum()),-abs(dx)-abs(dy),dx,dy))
 score,_,dx,dy=max(options);remove=binary_dilation(shift(oldcore>0,dx,dy));out=oldfx.copy();out[remove]=0;placed=shift(body,dx,dy);envelope=binary_fill_holes(oldfx>0);vals,cnt=np.unique(out[out>0],return_counts=True);fill=int(vals[cnt.argmax()]);holes=remove&envelope&(out==0)&(placed==0);out[holes]=fill;out[placed>0]=0
 assert np.array_equal(out,swap.layer(n,5)[0])and np.array_equal(out,cur.layer(n,5)[0])and np.array_equal(placed,swap.layer(n,0)[0])
 newbody=cur.layer(n,0)[0];keep=sorted({q['tile']+q['page']*256 for pb in PBS[1:]for q in parts(cur,pb,n)})
 effects.append({'ref':n,'body_translation_from217':[dx,dy],'source_matching_score':score,'historical_source_layer5_opaque':int((oldfx>0).sum()),'old_body_dilate1_removed_region':int(remove.sum()),'historical_fill_existing_index':fill,'historical_envelope_fill_cells':int(holes.sum()),'current_effect_opaque':int((out>0).sum()),'indexed_sha256':sha(out.tobytes()),'historical_rule_reconstructed_exact':True,'current_overlay_unchanged_since_swap':True,'whole_reserved_tiles':[{'tile':t,'sha256':sha(tile(cur,n,t).tobytes())}for t in keep],'current_effect_covers_new_body_pixels':int(((out>0)&(newbody>0)).sum()),'current_body_extends_beyond_original_envelope':int(((newbody>0)&~envelope).sum())})
head=N/'ultimate_dash_repaint/nova_head_registered_v1';hr=js(head/'registration.json')
for n in(217,218,220):
 p=head/f'target_{n:03}.png';blob(p);assert np.array_equal(cur.layer(n,0)[0],np.array(Image.open(p)))
assert np.array_equal(cur.layer(217,0)[0],cur.layer(218,0)[0])and np.array_equal(cur.layer(217,0)[0],cur.layer(220,0)[0])
newbody=cur.layer(217,0)[0];newflash=np.zeros_like(body);newflash[binary_dilation(newbody>0,iterations=2)]=7;newflash[newbody>0]=6
frames=[]
for n in REFS:
 f=cur.banks[0]['frames'][n];layers=[];addresses=set()
 for pb in PBS:
  z=cur.layer(n,pb)[0];ps=parts(cur,pb,n);addresses.update(q['record_offset']for q in ps);layers.append({'bank':pb,'opaque':int((z>0).sum()),'bounds':bounds(z),'index_counts':{str(int(i)):int(c)for i,c in zip(*np.unique(z[z>0],return_counts=True))},'parts':ps,'indexed_sha256':sha(z.tobytes()),'whole_consumed_tiles':[{'tile':t,'sha256':sha(tile(cur,n,t).tobytes())}for t in sorted({q['tile']+q['page']*256 for q in ps})]})
 owners=[]
 for pb in range(len(bank_offsets(cur.c))):
  for nn in range(composition_frame(cur.c,pb,0)['bank_frame_count']):
   if pb in PBS and nn in REFS:continue
   common=addresses&{q['record_offset']for q in parts(cur,pb,nn)}
   if common:owners.append({'bank':pb,'ref':nn,'shared_record_offsets':sorted(common)})
 frames.append({'ref':n,'tile_count':f['tile_count'],'raw_offset':f['offset'],'raw_owners':[q['index']for q in cur.banks[0]['frames']if q['offset']==f['offset']],'layers':layers,'non_target_record_owners':owners})
an,refs=animation_map(original['SLUS_005.61']);used=sorted({v for n in REFS for v in refs[n]});seq=[an[i]for i in used]
for p in(ROOT/'scripts/prepare_nana_ultimate_nova.py',ROOT/'scripts/ultimate_costume_swap.py',N/'native_restore/prepare_nova_hair_sync.py',N/'ultimate_dash_repaint/prepare_nova_head.py',N/'ultimate_dash_repaint/pack_nova_head.py',ROOT/'work/research/decomp/src/main/player_special.c'):blob(p)
provenance=js(core/'prepared_special_v1/ver_rin_nana/proposal.json');renderer=js(D/'nana_ultimate_hover_relations01/report.json')
O.mkdir(exist_ok=False);sheets=[]
def board(items,name,columns,scale=4):
 boxes=[im.getbbox()for _,im in items if im.getbbox()];bb=(min(q[0]for q in boxes)-3,min(q[1]for q in boxes)-3,max(q[2]for q in boxes)+3,max(q[3]for q in boxes)+3);w,h=bb[2]-bb[0],bb[3]-bb[1];cw,ch=w*scale+10,h*scale+25;im=Image.new('RGB',(cw*columns,ch*((len(items)+columns-1)//columns)),'#263345');dr=ImageDraw.Draw(im)
 for i,(title,pic)in enumerate(items):
  x,y=i%columns*cw,i//columns*ch;v=pic.crop(bb).resize((w*scale,h*scale),Image.Resampling.NEAREST);im.paste(v,(x+5,y+22),v);dr.text((x+5,y+3),title,fill='white')
 p=O/name;im.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes())})
board([(f'{n} {tag}',ar.composite(n,15)[0])for n in(213,214,215,216)for tag,ar in(('US',us),('historical',hist),('current',cur))],'preparation_pairs.png',3)
board([(f'{n} {tag}',im)for n in(217,218,219,220)for tag,im in(('current mask15',cur.composite(n,15)[0]),('body0',cur.rgba(cur.layer(n,0)[0])),('overlay5',cur.rgba(cur.layer(n,5)[0],16)))],'dash_layers.png',3)
board([('old seed683',swap.rgba(body)),('current body727',cur.rgba(newbody)),('current219 old rule',cur.rgba(flash,16)),('newbody rule diagnostic only',cur.rgba(newflash,16))],'flash_rule_diagnostic.png',4)
r={'scope':'Nana Ultimate 노바213..220 원US·역사규칙·현재 소유 읽기','current_path':rel(curp),'current_sha256':sha(cur.data),'source_US_sha256':sha(us.data),'historic_nova_sha256':sha(hist.data),'swap_complete_sha256':sha(swap.data),'pairs':pairs,'frames':frames,'historical_effect_reconstruction':effects,'flash219':{'historical_seed_ref73_main_component':683,'excluded_original73_other_pixels':int((src.layer(73,0)[0]>0).sum())-683,'seed_translation':[3,-6],'rule':'Manhattan거리2 팽창 index7, 원몸알파 index6','old_rule_current_exact':True,'current_flash_counts':{'6':int((flash==6).sum()),'7':int((flash==7).sum())},'latest_body_pixels':int((newbody>0).sum()),'new_body_rule_difference_cells':int((newflash!=flash).sum()),'diagnostic_only_no_asset_written':True},'latest_head_registration':{'path':rel(head/'registration.json'),'sha256':sha(blob(head/'registration.json')),'body3_targets_exact':True,'219_unchanged_by_head_edit':True},'original_animation_tables':seq,'current_renderer_evidence':{'path':rel(D/'nana_ultimate_hover_relations01/report.json'),'sha256':sha(blob(D/'nana_ultimate_hover_relations01/report.json')),'217_230_always15':True},'readback_sheets':sheets,'inputs':tracked,'conclusions':['213/214 및215/216의 현5층 exact는 역사 제작의 준비짝 공통정책이다. 원US 차이는 pairs에 따로 기록했으며 동일원작 복원으로 부르지 않는다.','213..216은일반의상정책이고217..220은ownership과무관한mask15다.217의base0몸/빈overlay,218/220의base0몸+효과overlay5,219의빈base0+효과overlay5를서로다른두의상으로오인하지않는다.','219는머리후속전683px실루엣의정확한Manhattan2파생이다.새217교체시새몸의같은규칙동기화는새제작정책이며기존219를그대로복사하면새머리알파와불일치한다.','218/220은원작타일전체복사정책이아니라역사oldbody팽창1제거/원envelope안기존색메움/새몸영역투명화로작성된효과다.현재효과층/소비전체타일을보호출처로쓰고새몸과겹침·구멍은별도검토해야한다.','지금판에는효과전체타일과조립·다른소비자목록을기록했다.미사용같아보이는타일을원효과라고임의합치거나누락하지말고실제소비union을보호할것.','원표106의event80/40/20은준비/충돌취소/돌진발동에연결된다.217..220 4프레임단순루프만검사하면213..216준비와외부상태전환이누락된다.'],'producer_functions_called':False,'new_MIPS_execution':False,'runtime_verified':False,'actually_viewed':False}
(O/'report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'report_sha256':sha((O/'report.json').read_bytes()),'pairs':[{'archive':p['archive'],'pair':p['pair'],'exact':p['all5layers_exact']}for p in pairs],'effects':effects,'flash':r['flash219'],'tables':used}))
