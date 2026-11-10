"""현재 시부키 전완 버스터의 출처/조립/팔레트 읽기. 제작함수 호출 없음."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;H=D.parent/'shibuki_audit'
sys.path[:0]=[str(ROOT),str(D)]
from scripts.export_x_consistency import Archive
from verify_shibuki_ultimate_hurt13_independent import parts,render
O=D/'shibuki_standing_fire_modules01';O.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();tracked={}
def readb(p):
 b=p.read_bytes();tracked[rel(p)]=sha(b);return b
def box(m):
 y,x=np.nonzero(m);return [int(x.min()-160),int(y.min()-160),int(x.max()+1-160),int(y.max()+1-160)]if len(x)else None
def mask(rect):
 x0,y0,x1,y1=rect;m=np.zeros((384,384),bool);m[y0+160:y1+160,x0+160:x1+160]=True;return m
def histpng(p,origin):
 readb(p);im=np.array(Image.open(p));out=np.zeros((384,384),np.uint8);x,y=origin;out[160-y:160-y+im.shape[0],160-x:160-x+im.shape[1]]=im;return out
ap=H/'prepared_standing_special_base01/PL00_U.ARC';a=Archive(readb(ap))
assert sha(a.data)=='fdba798cc2586f53f576d9255a2b44ddfffda7b7dc850effc7ee4dace5dfc08e'
history=ROOT/'work/ver_buki_riko/shibuki_art';refs=[85,86,89,90,91]
sources={n:history/('standing_buster_v1/production03'if n<89 else'special_style_v2/production06')/(f'standing_{n:03}.png'if n<89 else f'frame_{n:03}.png')for n in refs}
for p in [history/'standing_buster_v1/prompt.txt',history/'standing_buster_v1/assemble.py',history/'standing_buster_v1/production03/art.json',history/'special_style_v2/prompt.txt',history/'special_style_v2/normalize.py',history/'special_style_v2/production06/art.json',history/'fourth_armor_remaining_v1/register_remaining.py']:readb(p)
font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',13)
rows=[];full=Image.new('RGB',(250*len(refs),540),'#263442');fd=ImageDraw.Draw(full)
grid=Image.new('RGB',(510*len(refs),920),'#263442');gd=ImageDraw.Draw(grid)
for col,n in enumerate(refs):
 z=a.layer(n)[0];hz=histpng(sources[n],(48,40)if n<89 else(80,80));region=mask((-28,-31,-3,2));slices=[]
 for pb in(0,5,6,7,8):
  ps=parts(a,pb,n)
  for i,p in enumerate(ps):
   pr=render(a,n,pb,[p]);touch=(pr>0)&region
   if touch.any():slices.append({'pb':pb,'part_index':i,'part':p,'region_opaque':int(touch.sum()),'region_bbox':box(touch),'values':sorted(map(int,np.unique(pr[touch])))})
 forms=[]
 for row,(form,m)in enumerate((('base',0),('fourth',15))):
  im=a.composite(n,m,2)[0];arr=np.array(im);crop=im.crop((132,123,182,185)).resize((200,248),Image.Resampling.NEAREST);full.paste(crop,(col*250+20,row*270+20),crop);fd.text((col*250+3,row*270+2),f'{n} {form}',fill='white')
  # Native coordinates and index labels in an expanded visual region.
  ox=col*510+32;oy=row*460+30;gd.text((col*510+5,row*460+2),f'{n} {form} RGBA/index0 grid',font=font,fill='white')
  for y in range(-28,0):
   gd.text((col*510,row*460+30+(y+28)*15),str(y),font=font,fill='#ffffff')
   for x in range(-27,1):
    v=arr[y+160,x+160];xx=ox+(x+27)*16;yy=oy+(y+28)*15
    gd.rectangle((xx,yy,xx+15,yy+14),fill=tuple(v[:3])if v[3]else'#1a2430',outline='#44515a')
    if v[3]:gd.text((xx+1,yy),format(int(z[y+160,x+160]),'X'),font=font,fill='black'if int(v[:3].sum())>450 else'white')
  for x in range(-27,1,2):gd.text((ox+(x+27)*16,oy+420),str(x),font=font,fill='white')
  forms.append({'form':form,'rgba_sha256':sha(arr.tobytes())})
 rows.append({'ref':n,'history':rel(sources[n]),'whole_history_diff':int(np.count_nonzero(z!=hz)),'history_diff_bbox':box(z!=hz),'region_history_diff':int(np.count_nonzero((z!=hz)&region)),'parts_in_inspection_region':slices,'forms':forms})
full.save(O/'full_poses.png');grid.save(O/'coordinate_grid.png')
relreport=json.loads(readb(D/'shibuki_standing85_92_relations01/report.json'))
result={'scope':'PL00 fdba 85/86/89/90/91 실제 파트/색과 역사 원화 읽기. 표시창이 곧 무기 의미마스크라는 가정 없음.','candidate_sha256':sha(a.data),'frames':rows,'historical_85_to86':'standing_buster_v1/assemble.py의 동일 새 원화 arm source85, 위치(7,-5)→(8,-5), 머리/하체 보호. 원US 전체그림 관계와 별개.','original_current_recoil_relation':[q for q in relreport['relations']if q['source']==85 and q['target']==86],'palette0':[[int(w),[(int(w)>>s&31)*255//31 for s in(0,5,10)]]for w in a.words[:16]],'palette16':[[int(w),[(int(w)>>s&31)*255//31 for s in(0,5,10)]]for w in a.words[16:32]],'palette32':[[int(w),[(int(w)>>s&31)*255//31 for s in(0,5,10)]]for w in a.words[32:48]],'source_files':tracked,'art_or_resource_modified':False,'producer_functions_called':False,'native_or_gameplay_performed':False}
(O/'probe.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
modules=[]
for n,rect in [(85,(-21,-11,-11,-5)),(89,(-17,-24,-7,-14)),(90,(-23,-22,-13,-12)),(91,(-28,-8,-17,0))]:
 m=mask(rect);z=a.layer(n)[0];base=np.array(a.composite(n,0,2)[0]);fourth=np.array(a.composite(n,15,2)[0]);used=sorted(map(int,np.unique(z[m&(z>0)])))
 touched=[]
 for i,p in enumerate(parts(a,0,n)):
  pr=render(a,n,0,[p]);q=(pr>0)&m
  if q.any():touched.append({'index':i,'record':p,'pixels_inside':int(q.sum()),'opaque_outside':int(np.count_nonzero((pr>0)&~m))})
 pm=np.zeros_like(base);pm[m]=base[m];Image.fromarray(pm).save(O/f'roi_{n}.png')
 modules.append({'ref':n,'rect_world_exclusive':list(rect),'meaning':'85/89는 UI 제안 창; 90/91은 이번 읽기용 창. 완성 총 전용 마스크로 수용된 값 아님.','opaque':int(np.count_nonzero(z[m])),'base_fourth_RGBA_diff':int(np.count_nonzero(np.any(base!=fourth,axis=2)&m)),'base_palette_indices':used,'palette0_colors_absent_in16':[v for v in used if not any((int(a.words[v])&32767)==(int(w)&32767)for w in a.words[17:32])],'actual_parts':touched,'pixels':[{'xy':[int(x-160),int(y-160)],'index':int(z[y,x]),'rgba':base[y,x].tolist()}for y,x in np.argwhere(m&(z>0))]})
ear=[(x,y)for y,xs in [(-23,[-9]),(-22,[-10,-9,-8]),(-21,[-10,-9,-8])]for x in xs]
result['inspection_windows']=modules
result['proven_historical_design_notes']=[
 'standing_buster_v1/prompt.txt는 보라/흰 전완 버스터 및 팔/소매 분리 지시다. special_style_v2/prompt.txt 89는 이마 위,90은 사선 위,91은 사격 방향으로 내리는 별도 자세다.',
 '현재 5개 기본 그림 전체가 해당 역사 등록 PNG와 exact이다. 이는 역사 그림 출처 확인이며 그림의 모든 픽셀을 총으로 분류하는 근거가 아니다.',
 '85의 UI 창은 총 중간 46셀이며 y−5 x−17..−12의 어두운 하부 윤곽 6셀을 제외한다. 오른쪽 총/피부/소매 접합부도 창 밖이므로 완성 모듈이라고 부르지 않는다.',
 '89의 UI 창은 귀 상단 7셀을 확실히 포함한다. 아래 y−20의 귀/버스터 맞닿는 경계는 추가 시각 분리가 필요하다. 이 창 전체 복사는 권고하지 않는다.',
 '현재 총과 머리/소매는 같은 16×16 기본 파트에 함께 저장된다. raw tile 전체를 총으로 복사하면 다른 신체 픽셀이 따라온다.',
 '85/89의 UI 창은 기본/포스 RGBA가 동일하다. 포스 아머 층이 이 영역을 덮지 않아 기본 CLUT0 색이 남은 결과다. 90/91의 이번 조사 창은 아래 소매 경계까지 포함하여 각각1/7셀 차이가 있으므로 완성 총 마스크로 쓰지 않는다.',
 '동일 RGBA 보존은 총을 기본층 CLUT0에 유지하고 아머층 의미마스크가 총을 덮지 않게 하는 기존 방식이 맞다. row16 색인으로 바꾸면 이 색들이 exact하지 않다.',
 '85→86은 역사 동일 팔/소매 원화의 X+1 등록이다. 전체몸체 평행이동은 아니며 현재 전체97셀 차이는 합성/가림 결과다. 원US PL00은391셀 차이로 이 신규 제작정책과 구별한다.']
result['ear_pixels_inside_ui_89_window']=[{'xy':[x,y],'index':int(a.layer(89)[0][y+160,x+160])}for x,y in ear]
result['missing_85_lower_outline']=[{'xy':[x,-5],'index':int(a.layer(85)[0][155,x+160])}for x in range(-17,-11)]
for p in [history/'standing_buster_v1/generated.png',history/'special_style_v2/generated_v1.png']:readb(p)
result['source_files']=tracked
result['visual_status']='역사 원화2장·좌표판·UI gun_modules 및 발끝 포함 전체 전후판을 실제 열람했다. 원화 의미 구분 의견이며 실기 검증은 수행하지 않았다.'
result['recommendation']='총 전용 canonical 판정을 수치만으로 확정하지 않는다. 원화에서 귀/소매를 분리한 행별 의미마스크를 제작자가 등록하고 새 손 접점과 함께 재검토한다. 여기 기록한 색/파트/좌표는 그 읽기 근거다.'
(O/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps([{k:r[k]for k in('ref','whole_history_diff','history_diff_bbox','region_history_diff')}for r in rows]))
