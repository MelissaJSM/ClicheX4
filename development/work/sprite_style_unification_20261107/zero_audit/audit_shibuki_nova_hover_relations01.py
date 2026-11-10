"""시부키 준비/Nova/호버의 원US·현재·역사 소유 읽기. 제작 함수 미호출."""
from pathlib import Path
import hashlib,json,struct,sys
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import binary_dilation,binary_fill_holes,label
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent;H=W/'shibuki_audit'
O=D/'shibuki_nova_hover_relations01';assert not O.exists()
sys.path[:0]=[str(ROOT),str(D)]
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,animation_map
from scripts.prepare_riko_ui import entry
from src.psx_player import composition_frame,bank_offsets
from src.psx_static_effect import compose_static
from src.psx_ui_atlas import local_composition,tile_pixels
from verify_shibuki_ultimate_hurt13_independent import raw,parts,sig,tile
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();off=lambda a:a-0x80010000+2048
inputs={};PBS=(0,5,6,7,8);REFS=tuple(range(213,231))
def blob(p):
 b=p.read_bytes();inputs[rel(p)]=sha(b);return b
def js(p):return json.loads(blob(p))
def box(z):
 y,x=np.nonzero(z);return None if not len(x)else[int(x.min()-160),int(y.min()-160),int(x.max()+1-160),int(y.max()+1-160)]
def shift(z,dx,dy):
 out=np.zeros_like(z);y,x=np.nonzero(z);assert not len(x)or(min(x+dx)>=0 and max(x+dx)<384 and min(y+dy)>=0 and max(y+dy)<384);out[y+dy,x+dx]=z[y,x];return out
def static(ar,bank,n):
 c=composition_frame(ar.c,bank,n);b,s,bb,_=compose_static(entry(ar.data,0x10206),local_composition(c));z=np.zeros((384,384),np.uint8);z[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]=np.frombuffer(b,np.uint8).reshape(s[1],s[0]);return z,c
bp=H/'prepared_chaser_base01/PL00_U.ARC';up=H/'prepared_chaser_ultimate01/PL02_U.ARC'
base=Archive(blob(bp));ult=Archive(blob(up));assert sha(base.data)=='3e11b7e6f6c58e6e175ba8a53278a8329440c160096bf89abdb9df334c3ef52d';assert sha(ult.data)=='2b8faa71d3a94bc6d52ac0e389c6121d530d6455e664ad852061c43c77789b5c'
prior=Archive(blob(H/'prepared_standing_fire_ultimate01/PL02_U.ARC'))
orig,_=read_disc(ROOT/'MegaMan X4.bin',('PL00_U.ARC','PL02_U.ARC','SLUS_005.61'))
us0,us2=Archive(orig['PL00_U.ARC']),Archive(orig['PL02_U.ARC'])
disc=ROOT/'out/ver_buki_riko/sprite_style_unification_20261107_v26/shibuki_riko.bin'
now,_=read_disc(disc,('PL00_U.ARC','PL02_U.ARC','SLUS_005.61'));assert now['PL00_U.ARC']==base.data and now['PL02_U.ARC']==prior.data
for n in REFS:
 assert raw(ult,0,n)==raw(prior,0,n)
 for pb in PBS:assert np.array_equal(ult.layer(n,pb)[0],prior.layer(n,pb)[0])and [sig(q)for q in parts(ult,pb,n)]==[sig(q)for q in parts(prior,pb,n)]
core=ROOT/'work/ultimate_costume_swap_20261105/core'
proposal=js(core/'prepared_special_v1/ver_buki_riko/proposal.json')
histdata,_=read_disc(ROOT/proposal['baseline'],('PL02_U.ARC',));hist=Archive(histdata['PL02_U.ARC']);assert sha(hist.data)==proposal['source_arc_sha256']
swap=Archive(blob(core/'prepared_complete_v1/ver_buki_riko/PL02_U.ARC'))
for p in [ROOT/'scripts/ultimate_costume_swap.py',ROOT/'scripts/ultimate_costume_renderer.py',ROOT/'scripts/register_shibuki_ultimate_production.py',ROOT/'work/research/decomp/src/main/player_special.c',ROOT/'work/research/decomp/src/main/player_weapon.c',ROOT/'work/research/decomp/config/symbols.us.txt']:blob(p)
archives={'US_PL00':us0,'US_PL02':us2,'current_PL00':base,'current_PL02':ult}
pairs=[]
for tag,ar in archives.items():
 for n,m in ((213,214),(215,216)):
  ls=[]
  for pb in PBS:
   a,b=ar.layer(n,pb)[0],ar.layer(m,pb)[0];ls.append({'bank':pb,'different_cells':int((a!=b).sum()),'alpha_difference':int(((a>0)!=(b>0)).sum()),'difference_bounds':box(a!=b),'same_records':[sig(q)for q in parts(ar,pb,n)]==[sig(q)for q in parts(ar,pb,m)]})
  pairs.append({'archive':tag,'pair':[n,m],'all5layers_exact':all(q['different_cells']==0 for q in ls),'raw_stream_shared':ar.banks[0]['frames'][n]['offset']==ar.banks[0]['frames'][m]['offset'],'layers':ls})
rows={};ownership={}
for tag,ar in [('current_PL00',base),('current_PL02',ult)]:
 record_users={}
 for pb in range(len(bank_offsets(ar.c))):
  for n in range(composition_frame(ar.c,pb,0)['bank_frame_count']):
   for q in parts(ar,pb,n):record_users.setdefault(q['record_offset'],set()).add((pb,n))
 rows[tag]=[]
 for n in REFS:
  f=ar.banks[0]['frames'][n];ls=[];outside={}
  for pb in PBS:
   z=ar.layer(n,pb)[0];ps=parts(ar,pb,n);ts=sorted({q['page']*256+q['tile']for q in ps})
   for q in ps:
    oo=sorted([list(v)for v in record_users[q['record_offset']]if not(v[0]in PBS and v[1]in REFS)])
    if oo:outside[str(q['record_offset'])]=oo
   ls.append({'bank':pb,'opaque':int((z>0).sum()),'bbox_world':box(z>0),'indexed_sha256':sha(z.tobytes()),'indices':{str(int(v)):int(c)for v,c in zip(*np.unique(z[z>0],return_counts=True))},'parts':ps,'whole_consumed_tiles':[{'tile':t,'sha256':sha(tile(ar,n,t).tobytes())}for t in ts]})
  rows[tag].append({'ref':n,'tile_count':f['tile_count'],'raw_owners':[q['index']for q in ar.banks[0]['frames']if q['offset']==f['offset']],'layers':ls,'outside_record_owners':outside,'mask0_vs15_RGBA_differences':int(np.any(np.array(ar.composite(n,0)[0])!=np.array(ar.composite(n,15)[0]),axis=2).sum())})
# 11/05 실제 시부키 source의73 몸체를 같은 분리·이동 규칙으로 독립 재구성한다.
z=hist.layer(73,0)[0];labs,_=label(z>0,np.ones((3,3)));counts=np.bincount(labs.flat);counts[0]=0;body=shift(np.where(labs==counts.argmax(),z,0).astype(np.uint8),-3,-7)
assert int((body>0).sum())==840 and np.array_equal(body,swap.layer(217,0)[0])
histproof={'body_source_ref':73,'largest_component':840,'excluded_dust':int((z>0).sum())-840,'translation':[-3,-7],'swap_body_exact':True,'current_body_exact':bool(np.array_equal(body,ult.layer(217,0)[0])),'current_body_difference':int((body!=ult.layer(217,0)[0]).sum()),'effects':[]}
for n in (218,220):
 oldfx=hist.layer(n,5)[0];oldbody=hist.layer(217,5)[0];candidates=[]
 for dy in range(-8,9):
  for dx in range(-16,17):
   q=shift(oldbody,dx,dy);candidates.append((int(((q>0)&(q==oldfx)).sum()),-abs(dx)-abs(dy),dx,dy))
 _,_,dx,dy=max(candidates);placed=shift(body,dx,dy);remove=binary_dilation(shift(oldbody>0,dx,dy),iterations=1);fx=oldfx.copy();fx[remove]=0;envelope=binary_fill_holes(oldfx>0);vals,ct=np.unique(fx[fx>0],return_counts=True);holes=np.zeros_like(remove);fill=None
 if len(vals)and np.count_nonzero(fx)>100:fill=int(vals[ct.argmax()]);holes=remove&envelope&(fx==0)&(placed==0);fx[holes]=fill
 fx[placed>0]=0;protected=~remove&(placed==0)
 assert np.array_equal(fx,swap.layer(n,5)[0])and np.array_equal(placed,swap.layer(n,0)[0])and np.array_equal(fx[protected],oldfx[protected])
 histproof['effects'].append({'ref':n,'translation':[dx,dy],'original_source_effect_pixels':int((oldfx>0).sum()),'removed_region':int(remove.sum()),'fill_index':fill,'fill_cells':int(holes.sum()),'reproduced_effect_pixels':int((fx>0).sum()),'swap_exact':True,'current_layer0_exact':bool(np.array_equal(placed,ult.layer(n,0)[0])),'current_layer5_exact':bool(np.array_equal(fx,ult.layer(n,5)[0])),'current_body_overlap':int(((ult.layer(n,0)[0]>0)&(ult.layer(n,5)[0]>0)).sum()),'external_source_world_exact':True})
flash=np.zeros_like(body);flash[binary_dilation(body>0,iterations=2)]=7;flash[body>0]=6;assert np.array_equal(flash,swap.layer(219,5)[0]);histproof['flash219']={'rule':'Manhattan2 / body6 / ring7','swap_exact':True,'current_exact':bool(np.array_equal(flash,ult.layer(219,5)[0])),'current_body_count':int((ult.layer(217,0)[0]>0).sum()),'current_flash_pixels':int((ult.layer(219,5)[0]>0).sum())}
# 호버의5층은 하체. 효과는 별도visual21/bank12이다.
hover=[]
for n,source,cut in [(221,39,5),(223,37,6),(225,45,5),(227,47,7),(229,41,5)]:
 ls=[]
 for f,s in ((n,source),(n+1,source+1)):
  a=hist.layer(s,0)[0].copy();a[160+cut:]=0;b=hist.layer(f,5)[0].copy();b[:160+cut]=0;low=hist.layer(f,0)[0].copy();low[:160+cut]=0;m=(low>0)&(b==0);a[m]=low[m]
  assert np.array_equal(a,swap.layer(f,0)[0])and np.array_equal(b,swap.layer(f,5)[0])
  ls.append({'ref':f,'upper_source':s,'cut_world_y':cut,'swap_layer0_exact':True,'swap_layer5_exact':True,'current_layer0_exact':bool(np.array_equal(a,ult.layer(f,0)[0])),'current_layer5_exact':bool(np.array_equal(b,ult.layer(f,5)[0])),'lower5_opaque':int((b>0).sum()),'lower5_bbox':box(b>0),'nonempty_678':{str(pb):int((ult.layer(f,pb)[0]>0).sum())for pb in(6,7,8)}})
 hover.append({'pair':[n,n+1],'historical':ls,'current_pair_layers':[{'bank':pb,'different_cells':int((ult.layer(n,pb)[0]!=ult.layer(n+1,pb)[0]).sum()),'difference_bbox':box(ult.layer(n,pb)[0]!=ult.layer(n+1,pb)[0])}for pb in PBS]})
oe,ce=orig['SLUS_005.61'],now['SLUS_005.61'];renderer=ce[off(0x800257bc):off(0x8002588c)];assert sha(renderer)=='46c1fe4c8c01be08e49c733c24e99fe7e4e2416b93a2dc50585a3503854038c5'
caller=struct.unpack_from('<I',ce,off(0x80023ea4))[0];assert caller>>26==3 and ((caller&0x3ffffff)<<2|0x80000000)==0x800257bc
codes=[]
for name,lo,hi in [('nova_check',0x800375b4,0x80037760),('nova_state',0x80038e90,0x80039120),('hover_check',0x8003751c,0x800375b0),('hover_start',0x80038970,0x800389dc),('hover_jet',0x800b2ad0,0x800b2c8c),('muzzle',0x80092e2c,0x80092f08)]:
 data=ce[off(lo):off(hi)];assert data==oe[off(lo):off(hi)];codes.append({'name':name,'start':lo,'end':hi,'sha256':sha(data),'US_exact':True,'bytes':data.hex()})
an,refs=animation_map(ce);uan,urefs=animation_map(oe);ids=sorted({i for n in REFS for i in refs[n]});seq=[an[i]for i in ids]
for q in seq:assert q==uan[q['id']]
jetrows=[];jettiles=set()
for n,aid in [(221,33),(223,34),(225,35),(227,36),(229,32)]:
 address=struct.unpack_from('<I',oe,off(0x8011bf40+aid*4))[0];assert oe[off(address):off(address+12)]==ce[off(address):off(address+12)];steps=[list(struct.unpack_from('<bbbB',oe,off(address+i*4)))for i in range(3)]
 for _,_,_,f in steps:
  z,c=static(us0,12,f);ts={p['page']*256+p['tile']for p in c['parts']};jettiles.update(ts)
  for ar in (us2,base,ult):
   zz,cc=static(ar,12,f);assert np.array_equal(z,zz)and [sig(p)for p in c['parts']]==[sig(p)for p in cc['parts']]
   for t in ts:assert tile_pixels(entry(ar.data,0x10206),t)==tile_pixels(entry(us0.data,0x10206),t)
  jetrows.append({'player_refs':[n,n+1],'animation_id':aid,'frame':f,'opaque':int((z>0).sum()),'bbox':box(z>0),'parts':c['parts'],'four_archives_exact':True})
muzzle=[]
for n in (222,224,226,228,230):
 at=off(0x8011b230+n*2);assert oe[at:at+2]==ce[at:at+2];x,y=struct.unpack_from('<bb',oe,at);muzzle.append({'ref':n,'direction0':[x,y],'direction1':[-x,y],'US_BR26_exact':True})
O.mkdir(exist_ok=False);sheets=[]
def board(name,items,cols,scale=4):
 boxes=[im.getbbox()for _,im in items if im.getbbox()];bb=(min(b[0]for b in boxes)-3,min(b[1]for b in boxes)-3,max(b[2]for b in boxes)+3,max(b[3]for b in boxes)+3);w,h=bb[2]-bb[0],bb[3]-bb[1];cw,ch=w*scale+10,h*scale+25;out=Image.new('RGB',(cw*cols,ch*((len(items)+cols-1)//cols)),'#263345');dr=ImageDraw.Draw(out)
 for i,(caption,im)in enumerate(items):
  x,y=(i%cols)*cw,(i//cols)*ch;dr.text((x+3,y+3),caption,fill='white');q=im.crop(bb).resize((w*scale,h*scale),Image.Resampling.NEAREST);out.paste(q,(x+5,y+22),q)
 p=O/name;out.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes()),'crop':bb,'integer_scale':scale})
board('preparation_current.png',[(f'{n} {tag}',ar.composite(n,mask)[0])for n in (213,215)for tag,ar,mask in [('base',base,0),('fourth',base,15),('U before',ult,15),('U after',ult,0)]],4)
board('preparation_US.png',[(f'{n} US {tag}',ar.composite(n,15)[0])for n in range(213,217)for tag,ar in [('PL00',us0),('PL02',us2)]],2)
for n in range(217,221):board(f'nova_{n}.png',[(f'{n} actual mask15',ult.composite(n,15)[0]),(f'{n} body0',ult.rgba(ult.layer(n,0)[0])),(f'{n} overlay5',ult.rgba(ult.layer(n,5)[0],16))],3,3 if n==220 else 4)
for n in (221,223,225,227,229):board(f'hover_{n}.png',[(f'{n} actual mask15',ult.composite(n,15)[0]),(f'{n+1} shot mask15',ult.composite(n+1,15)[0]),(f'{n} body0',ult.rgba(ult.layer(n,0)[0])),(f'{n} lower5',ult.rgba(ult.layer(n,5)[0],16))],4)
for p,h in inputs.items():assert sha((ROOT/p).read_bytes())==h
report={'scope':'Shibuki PL00/PL02 준비213..216 및 Nova/호버217..230 실제 소유·원코드·역사 읽기','sources':{'base':{'path':rel(bp),'sha256':sha(base.data)},'ultimate':{'path':rel(up),'sha256':sha(ult.data)},'US_PL00':sha(us0.data),'US_PL02':sha(us2.data),'historical_source_PL02':sha(hist.data),'historical_swap_PL02':sha(swap.data)},'BR26_disc':rel(disc),'BR26_exe_sha256':sha(ce),'BR26_PL02_to_new_chaser_all18_unchanged':True,'preparation_pairs':pairs,'current_frames':rows,'history_nova':histproof,'history_hover':hover,'renderer':{'address':'0x800257BC','bytes':208,'sha256':sha(renderer),'caller':'0x80023EA4','engine_ultimate_byte':'engine+0x37','ownership_byte':'engine+0x47','ordinary_parts_byte':'player+0xA7','rule':'Ultimate는 ownership0 또는 frame217..230이면15, 그외0. 일반PL00는playerA7 그대로.','layer_order':[8,5,7,6],'clut':{'5/6/8':16,'7_arm2':32},'code_hex':renderer.hex()},'US_equal_code_ranges':codes,'animation_ids':ids,'animations':seq,'jet':{'visual_id':'0x21','composition_bank':12,'static_entry':'0x10206','source_clut':'0x7802','object_origin':'player와같은x/y/facing','frames':jetrows,'whole_tiles':sorted(jettiles)},'original_muzzle_origins':muzzle,'readback_sheets':sheets,'inputs':inputs,'producer_functions_called':False,'new_MIPS_executed':False,'runtime_verified':False,'actually_viewed':False,'limits':['프레임별 마스크 합성은 정적 진단이며 사용 불가능한 Ultimate 부분 조합을 실제 의상으로 세지 않는다.','최신 원화/후보 수정이나 최초 생성 재양자화는 실행하지 않았다.','원코드 바이트 비교와 기존 함수 의미를 읽었으며 새 MIPS 실행/게임 실기는 수행하지 않았다.','213214/215216 current exact는 원US exact를 뜻하지 않는다. 217 옷 상태의 미술 정책은 현재 실제 재추출 뒤 별도 판단한다.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'report_sha256':sha((O/'report.json').read_bytes()),'history_nova':histproof,'pairs':[{k:p[k]for k in ('archive','pair','all5layers_exact')}for p in pairs],'hover':hover,'sheets':len(sheets)},ensure_ascii=False))
