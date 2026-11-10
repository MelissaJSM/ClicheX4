"""229/230 굽힌 발·고정 jet12~14와 새 국소원화 독립 읽기. ARC 쓰기 없음."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent;R=W/'root_nana_hover';sys.path[:0]=[str(ROOT),str(D)]
from scripts.export_x_consistency import Archive
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from src.psx_player import composition_frame
from src.psx_static_effect import compose_static
from src.psx_ui_atlas import local_composition,tile_pixels
O=D/'nana_base_hover229_rearfoot_read01';assert not O.exists()
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();inputs={}
def read(p):
 b=p.read_bytes();inputs[rel(p)]=sha(b);return b
def js(p):return json.loads(read(p))
def png(p):read(p);return np.array(Image.open(p))
def bbox(z):
 y,x=np.nonzero(z);return [int(x.min())-160,int(y.min())-160,int(x.max())-159,int(y.max())-159]if len(x)else None
def coords(z):
 y,x=np.nonzero(z);return [[int(xx)-160,int(yy)-160]for yy,xx in zip(y,x)]
def jet(ar,n,part=None):
 c=composition_frame(ar.c,12,n)
 if part is not None:c={**c,'parts':[c['parts'][part]]}
 z,size,box,_=compose_static(entry(ar.data,0x10206),local_composition(c));out=np.zeros((384,384),np.uint8);out[160+box[1]:160+box[3],160+box[0]:160+box[2]]=np.frombuffer(z,np.uint8).reshape(size[1],size[0]);return out,c
par=W/'root_nana_shot87/packed_settle01/PL00_U.ARC';a=Archive(read(par));assert sha(a.data)=='8951948879773266cae0bebd408b411f4806b5652257bba3c50df0212b3c6e10'
usdata=read_disc(ROOT/'MegaMan X4.bin',('PL00_U.ARC',))[0]['PL00_U.ARC'];u=Archive(usdata);assert sha(usdata)=='92b2a3209ad6603cf519616dc580400434271f87e8e7129495430c04d0d1c35a'
prior=js(D/'nana_base_hover_relations01/report.json');assert prior['parent_sha256']==sha(a.data)
jm=js(D/'nana_ultimate_hover_relations01/conclusions.json');jets={};jrows=[]
for n in(12,13,14):
 z,c=jet(a,n);uz,uc=jet(u,n);assert np.array_equal(z,uz);sg=lambda c:[(p['flags'],p['tile'],p['x'],p['y'])for p in c['parts']];assert sg(c)==sg(uc)
 for q in c['parts']:
  t=q['tile']+q['page']*256;assert tile_pixels(entry(a.data,0x10206),t)==tile_pixels(entry(u.data,0x10206),t)
 oldq=next(q for q in jm['effect_frames']if q['effect_frame']==n);dp=ROOT/oldq['source_dump'];read(dp);assert np.array_equal(z,np.load(dp))and sha(z.tobytes())==oldq['indexed_sha256']
 left,_=jet(a,n,0);right,_=jet(a,n,1);jets[n]=(z,left,right);jrows.append({'phase':n,'whole_indices_US_parent_prior_dump_exact':True,'parts':c['parts'],'left_bbox':bbox(left>0),'right_bbox':bbox(right>0),'tile256nibble_US_exact':True})
Y,X=np.indices((384,384));Y-=160;X-=160;roi=(X>=-8)&(X<=6)&(Y>=12)&(Y<=18)
manifest=js(R/'rearfoot_registered01/manifest.json');source=R/'rearfoot_edit01/generated.png';assert sha(read(source))==manifest['source_sha256'];im=Image.open(source).convert('RGBA');assert im.size==(1774,887)
donors={}
for i in(0,1):
 arr=np.array(im.crop((i*887,0,(i+1)*887,887)));rgb=arr[:,:,:3].astype(np.float32);alpha=arr[:,:,3].astype(np.float32)/255;pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[i*16:i*16+16]],np.float32)
 nearest=(1+np.square(rgb[:,:,None]-pal[None,None,1:]).sum(3).argmin(2)).astype(np.uint8);green=(rgb[:,:,1]>rgb[:,:,0]+15)&(rgb[:,:,1]>rgb[:,:,2]+15)&(arr[:,:,3]>=128);green[887//2:]=False;nearest[green]=14
 votes=np.stack([np.array(Image.fromarray(np.where(nearest==v,alpha,0).astype(np.float32),'F').resize((96,96),Image.Resampling.BOX))for v in range(1,16)]);coverage=np.array(Image.fromarray(alpha,'F').resize((96,96),Image.Resampling.BOX));z=1+votes.argmax(0).astype(np.uint8);z[coverage<.5]=0;eyes=votes[13].copy();eyes[coverage<.5]=0;eyes[48:]=0
 if eyes.max()>.015:z[np.unravel_index(eyes.argmax(),eyes.shape)]=14
 out=np.zeros((384,384),np.uint8);out[112:208,112:208]=z;assert np.array_equal(out,png(R/f'rearfoot_registered01/donor_{i}.png'));donors[i]=out
def compose(ls,mask):
 im=a.rgba(ls[0])
 for bit,pb in((8,8),(1,5),(4,7),(2,6)):
  if mask&bit:im.alpha_composite(a.rgba(ls[pb],32 if pb==7 else 16))
 return im
def measure(body,left):
 al=np.array(body)[:,:,3]>0;zone=(Y>=14)&(Y<=18)&(X>=-8)&(X<=1);foot=al&zone
 p=np.argwhere(foot);q=np.argwhere(left>0);dist=int(np.abs(p[:,None]-q[None]).max(2).min())if len(p)else None
 return {'lower_folded_region_definition':[-8,14,2,19],'opaque':int(foot.sum()),'bbox':bbox(foot),'coords':coords(foot),'left_jet_overlap_in_ROI':int((foot&(left>0)).sum()),'minimum_Chebyshev_ROI_pixel_distance':dist,'metric_is_ROI_not_semantic_shoe_segmentation':True,'whole_body_left_jet_overlap':int((al&(left>0)).sum()),'whole_lowest_y':bbox(al)[3]-1}
figures={};rows=[];delta=[];partial=[]
for n in(229,230):
 fd=R/('body_layers_probe01'if n==229 else'shoot_layers_probe02');js(fd/'manifest.json');ls={pb:png(fd/f'layer{pb}_{n}.png')for pb in(0,5,6,7,8)};newleg=png(R/f'rearfoot_registered01/layer8_{n}.png');expected=ls[8].copy();expected[roi]=donors[0][roi]
 assert np.array_equal(newleg,expected)and np.count_nonzero(newleg!=ls[8])==20;fixed={**ls,8:newleg};delta.append({'ref':n,'layer8_changed_cells':20,'coords':coords(newleg!=ls[8]),'outside_roi_exact':True,'new_source_donor0_indices_exact':True,'other_layers_unmodified':True})
 for mask in range(8,16):
  v=compose(fixed,mask);assert label(np.array(v)[:,:,3]>0,np.ones((3,3)))[1]==1;assert compose(ls,mask).getbbox()[3]==v.getbbox()[3];partial.append({'ref':n,'mask':mask,'single_component':True,'lowest_y_exact':True})
 for form,mask in(('base_legs',8),('fourth',15)):
  bodies={'original_US':u.composite(n,mask)[0],'parent_Nana':a.composite(n,mask)[0],'first_new_body':compose(ls,mask),'local_rearfoot':compose(fixed,mask)}
  for state,body in bodies.items():
   figures[n,form,state]=body
   rows.append({'ref':n,'form':form,'state':state,'contacts':{str(p):measure(body,jets[p][1])for p in(12,13,14)}})
assert np.array_equal(png(R/'rearfoot_registered01/layer8_229.png'),png(R/'rearfoot_registered01/layer8_230.png'))
O.mkdir(exist_ok=False);sheets=[]
def board(name,n,form,crop,scale,phases):
 states=['original_US','parent_Nana','first_new_body','local_rearfoot'];cw=(crop[2]-crop[0])*scale+8;ch=(crop[3]-crop[1])*scale+28;out=Image.new('RGB',(cw*4,ch*len(phases)),'#253044');dr=ImageDraw.Draw(out)
 for row,ph in enumerate(phases):
  for col,state in enumerate(states):
   body=figures[n,form,state];jj=jets[ph][0];v=np.zeros((384,384,4),np.uint8);v[jj>0]=[75,170,180,255];pic=Image.fromarray(v);pic.alpha_composite(body);pic=pic.crop(crop).resize(((crop[2]-crop[0])*scale,(crop[3]-crop[1])*scale),Image.Resampling.NEAREST);x=col*cw;y=row*ch;dr.text((x+2,y+2),f'{state} jet{ph}',fill='white');out.paste(pic,(x+4,y+24),pic)
 p=O/name;out.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes()),'neutral_color_static_overlay':True})
for n in(229,230):
 for form in('base_legs','fourth'):board(f'{form}_{n}_jet12.png',n,form,(125,124,195,196),4,[12])
board('folded_region_three_phases.png',229,'base_legs',(146,168,177,196),8,[12,13,14])
for p,h in inputs.items():assert sha((ROOT/p).read_bytes())==h,p
report={'passed':True,'scope':'기본/포스229230의 굽힌발·원추진12~14 정적 독립읽기. 최종ARC/실기 검사 아님.','parent_sha256':sha(a.data),'original_US_sha256':sha(usdata),'source_local_sha256':sha(source.read_bytes()),'source_local2_cells_independently_requantized':True,'original_effects':jrows,'body_delta':delta,'partial16':partial,'contacts':rows,'own_sheets':sheets,'effect_origin_unchanged':[0,0],'ordinary_player_mask_requirement':'PL00 player+A7 유지. 실제 hover에는 legs bit8 필요: 여기 mask8/15 및8..15만 검사.','limitations':['발의 의미별 마스크를 자동 추정하지 않았다. ROI 및 전체알파의 교차는 피부 무릎과도 겹치므로 신발 접점 만족의 대리 지표가 아니다.','추진색은 중립색 정적합성이다. 원 CLUT/반투명/원실제게임 드로우순서와 모든60Hz 접점 검증은 미실행.','신규96ac 패킹기술후보와 최종호버ARC는 이 감사대상 아님. 몸/원화/ARC/EXE/저장자료 미변경.'],'source_or_resource_modified':False,'producer_functions_called':False,'new_MIPS_execution':False,'runtime_verified':False,'inputs':inputs}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'report':sha((O/'report.json').read_bytes()),'contacts229':[{k:v for k,v in q.items()if k!='contacts'}|{'phase12':q['contacts']['12']}for q in rows if q['ref']==229 and q['form']=='base_legs'],'delta':delta}))
