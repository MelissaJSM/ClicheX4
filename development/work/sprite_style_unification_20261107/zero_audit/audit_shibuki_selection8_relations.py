"""ea216 선택1..8 원점·타일/조립공유 읽기. 후보 쓰기 없음."""
from pathlib import Path
import hashlib,json,struct,sys
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent
sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import Archive
from src.psx_ui_atlas import aliased_composition
O=D/'shibuki_selection8_relations01';sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();tracked={}
def blob(p):
 z=p.read_bytes();tracked[rel(p)]=sha(z);return z
def js(p):return json.loads(blob(p))
plan=js(W/'staging_br_v22.json');oldrow=plan['resources']['PL00_U.ARC'];uirow=plan['resources']['ST0E_U1.ARC']
old=blob(ROOT/oldrow['path']);ui=blob(ROOT/uirow['path']);newp=W/'shibuki_audit/prepared_standing_fire_base01/PL00_U.ARC';new=blob(newp)
assert sha(old)==oldrow['after']=='fdba798cc2586f53f576d9255a2b44ddfffda7b7dc850effc7ee4dace5dfc08e'
assert sha(ui)==uirow['after']=='ea2167e98f8ae045c4353cca18cc571614e34949160cd85cc14ac9a6cb8e1c54'
assert sha(new)=='4fe7173665d2bd2e5484a8c62eeb17d286ee61b781abf78e9525e03acb5f8175'
oldmap=js(W/'x_selection_audit13/shibuki/report.json');a,b=Archive(old),Archive(new)
assets,_=read_disc(ROOT/plan['source_bin'],('COL0E_U1.ARC',));col=assets['COL0E_U1.ARC'];assert sha(col)==oldmap['asset_sha256']['COL0E_U1.ARC']
pal=entry(col,5);assert pal[512:544]==a.p[:32]==b.p[:32]
g,p=entry(ui,0x10102),entry(ui,10);starts=struct.unpack('<3I',entry(ui,12));assert starts==(0,40960,90112)
def tile(tex,t):
 z=np.zeros((16,16),np.uint8)
 for y in range(16):
  for x in range(16):
   off=(t//16*16+y)*128+t%16*8+x//2;assert off<len(tex);z[y,x]=(tex[off]>>(4*(x%2)))&15
 return z
def render(bank,n):
 tex=g[starts[bank]:(starts[bank+1]if bank<2 else len(g))];c=aliased_composition(p,bank,n);idx=np.zeros((384,384),np.uint16);rgba=np.zeros((384,384,4),np.uint8)
 for q in c['parts']:
  assert not q['unknown_flags'];z=tile(tex,q['page']*256+q['tile'])
  if q['flip_x']:z=z[:,::-1]
  if q['flip_y']:z=z[::-1]
  x,y=q['x']+160,q['y']+160;assert 0<=x<=368 and 0<=y<=368;hit=z>0;idx[y:y+16,x:x+16][hit]=z[hit]+q['clut']*16
  if bank in(0,2):
   row=(16 if bank==2 else 0)+q['clut'];words=struct.unpack_from('<16H',pal,row*32);colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]+[255]for w in words],np.uint8);colors[0]=0;rgba[y:y+16,x:x+16][hit]=colors[z][hit]
 return idx,rgba,c
def orient(z,dy=0,mirror=False):
 out=np.zeros_like(z);ys,xs=np.nonzero(z[:,:,3]>0 if z.ndim==3 else z>0);xx=319-xs if mirror else xs;yy=ys+dy;assert not len(xs)or min(yy)>=0 and max(yy)<384;out[yy,xx]=z[ys,xs];return out
mapping={i:(84+i,{-1:-1}.get(i,0))for i in range(1,9)}
mapping={1:(85,-1),2:(86,0),3:(87,0),4:(88,0),5:(89,0),6:(90,-1),7:(91,-2),8:(92,0)}
frames={};total=0
for bank in range(3):
 for n in range(aliased_composition(p,bank,0)['bank_frame_count']):frames[bank,n]=render(bank,n);total+=1
targettiles={q['page']*256+q['tile']for n in mapping for q in frames[2,n][2]['parts']};othertiles={q['page']*256+q['tile']for(bank,n),(_,_,c)in frames.items()if bank==2 and n not in mapping for q in c['parts']}
tr={q['record_offset']for n in mapping for q in frames[2,n][2]['parts']};recordoverlap=[];tileoverlap=[]
for(bank,n),(_,_,c)in frames.items():
 if bank!=2 or n in mapping:continue
 rs=sorted(tr&{q['record_offset']for q in c['parts']});ts=sorted(targettiles&{q['page']*256+q['tile']for q in c['parts']})
 if rs:recordoverlap.append({'ref':n,'record_offsets':rs})
 if ts:tileoverlap.append({'ref':n,'tiles':ts})
rows=[];pictures=[]
for n,(ref,dy)in mapping.items():
 idx,rgb,c=frames[2,n];oldi=a.layer(ref)[0];oldrgb=np.asarray(a.composite(ref,0)[0]);newrgb=np.asarray(b.composite(ref,0)[0]);assert np.array_equal(idx,orient(oldi,dy))and np.array_equal(rgb,orient(oldrgb,dy))
 matches=[{'mirror':flip,'dy':dd}for flip in(False,True)for dd in range(-3,4)if np.array_equal(rgb,orient(oldrgb,dd,flip))];assert matches==[{'mirror':False,'dy':dy}]
 hist=next(q for q in oldmap['rows']if q['ui_ref']==n);assert hist['body_ref']==ref and hist['exact_translation_if_same']==[0,dy]and not hist['mirrored_x']
 neworiented=orient(newrgb,dy);rows.append({'UI':n,'game':ref,'transform':{'mirror_x':False,'dx':0,'dy':dy},'existing_rgba_and_indices_exact':True,'only_measured_match':matches,'UI_parts':len(c['parts']),'game_new_parts':len(b.layer(ref)[1])if isinstance(b.layer(ref),tuple)and isinstance(b.layer(ref)[1],list)else None,'current_vs_new_changed_pixels':int(np.any(rgb!=neworiented,axis=2).sum()),'old_record_offsets':[q['record_offset']for q in c['parts']],'old_whole_tiles':sorted({q['page']*256+q['tile']for q in c['parts']})});pictures.append((n,ref,rgb,orient(oldrgb,dy),neworiented))
protected=[]
for n,ref,dy,flip in((18,207,-1,False),(19,156,1,True),(20,157,1,True),(21,158,0,False),(23,160,-1,False)):
 idx,rgb,c=frames[2,n];expected=orient(np.asarray(a.composite(ref,0)[0]),dy,flip);assert np.array_equal(rgb,expected);assert np.array_equal(a.layer(ref)[0],b.layer(ref)[0]);protected.append({'UI':n,'game':ref,'dy':dy,'mirror_x':flip,'existing_exact':True,'not_selected_for_sync':True})
O.mkdir(exist_ok=False);sheets=[]
for begin in(0,4):
 im=Image.new('RGB',(1008,4*350),'#263345');dr=ImageDraw.Draw(im)
 for row,(n,ref,oldim,oldgp,newgp)in enumerate(pictures[begin:begin+4]):
  for col,(caption,z)in enumerate((('current UI',oldim),('old game transformed',oldgp),('new game expected',newgp))):
   pic=Image.fromarray(z);box=(124,120,188,184);ys,xs=np.nonzero(z[:,:,3]);assert min(xs)>=box[0]and max(xs)<box[2]and min(ys)>=box[1]and max(ys)<box[3]
   small=pic.crop(box).resize((320,320),Image.Resampling.NEAREST);im.paste(small,(col*336+8,row*350+24),small);dr.text((col*336+8,row*350+4),f'UI {n} / game {ref} {caption}',fill='white')
 f=O/f'mapping_{begin//4}.png';im.save(f);sheets.append({'path':rel(f),'sha256':sha(f.read_bytes()),'actually_viewed':False})
for pp,h in tracked.items():assert sha((ROOT/pp).read_bytes())==h,pp
report={'passed':True,'scope':'시부키 ea216 선택1..8 원점과 저장 소유를 읽고 새4fe717 사본 준비조건을 기록. 후보 작성/동기화 검증은 아님.','UI_sha256':sha(ui),'parent_game_sha256':sha(old),'new_game_sha256':sha(new),'mapping':rows,'existing_protected_special_origins':protected,'UI_total_frames':total,'same_bank_nonselected_frames':len([n for bank,n in frames if bank==2 and n not in mapping]),'target_tiles':sorted(targettiles),'nonselected_consumed_tiles':sorted(othertiles),'exclusive_target_tiles':sorted(targettiles-othertiles),'shared_tiles_require_preservation':sorted(targettiles&othertiles),'nonselected_tile_users':tileoverlap,'nonselected_shared_record_users':recordoverlap,'texture_bank2_bytes':len(g)-90112,'other_texture_bank_bytes_to_preserve':90112,'recommendation':['1..8는85..92에 대응하며 X반전 없음. Y는−1/0/0/0/0/−1/−2/0을 각각 유지한다.','대상과 비대상이 공유하는 타일은 전체256색인과 비대상 조립의 형상/반전/팔레트를 보존한다. 공통record는 비대상seq를 유지하며 새대상만 분리 가능 여부를 검사한다.','19/20은BR의 mirror+1,18/23은Y−1,21은그대로이며 이번 변경대상이 아니다. RN의mirror Y0와혼동하지 않는다.','다른 모든 선택프레임,bank0/1,초상화/배경90112바이트,디렉터리/길이/19..21/23을 보호해야 한다.'],'readback_sheets':sheets,'inputs':tracked,'producer_functions_called':False,'resources_modified':False,'runtime_verified':False,'new_candidate_created':False}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'sha256':sha((O/'report.json').read_bytes()),'target_tiles':len(targettiles),'exclusive':len(targettiles-othertiles),'shared':len(targettiles&othertiles),'record_users':recordoverlap,'tile_users':tileoverlap}))
