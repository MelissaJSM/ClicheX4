"""새 기본/포스 작은머리의 고정셀과 장식 소유만 독립 읽기로 대조한다."""
from pathlib import Path
import hashlib,io,json,sys
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
O=Path(__file__).resolve().parent;H=ROOT/'work/sprite_style_unification_20261107/shibuki_audit';D=H/'vehicle_head_base_native02'
assert not (O/'report.json').exists()
sha=lambda b:hashlib.sha256(b).hexdigest();inputs={}
def read(p):
 b=p.read_bytes();inputs[p.relative_to(ROOT).as_posix()]=sha(b);return b
def arr(p):return np.array(Image.open(io.BytesIO(read(p))))
def xy(m):
 ys,xs=np.nonzero(m);return[[int(x)-160,int(y)-160]for y,x in zip(ys,xs)]
src=H/'vehicle_head_base_inputs01/generated_v1.png';data=read(src)
assert sha(data)=='93fb00c7cf81d5768e2d26ee68fe4a2fe0a22f50d78265c3dc8a6fc935223fd4'
parent=H/'prepared_nova_strike_base01/PL00_U.ARC';pdata=read(parent)
assert sha(pdata)=='36d4d0293abc77052c476e0495f4f4542ca75471c7a149f200e4bdb8f4e1bd4e'
a=Archive(pdata);oldalpha=a.layer(184,0)[0]>0;oldhead=a.layer(184,5)[0]>0
im=Image.open(io.BytesIO(data)).convert('RGBA');assert im.size==(1254,1254)
whole=np.array(im.resize((96,96),Image.Resampling.NEAREST));assert np.array_equal(whole,arr(D/'whole96_rgba.png'))
source={};rawrgba={};outside={}
for form,x0,start in(('base',8,0),('fourth',56,16)):
 cell=whole[32:59,x0:x0+25];pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.int32)
 distances=np.stack([((cell[:,:,:3].astype(np.int32)-pal[k])**2).sum(2)for k in range(1,16)],axis=2)
 idx=(distances.argmin(2)+1).astype(np.uint8);idx[cell[:,:,3]<128]=0
 z=np.zeros((384,384),np.uint8);z[117:144,144:169]=idx
 assert np.array_equal(z,arr(D/f'{form}_source_indices.png'))
 assert not (oldalpha&~(z>0)).any()
 outside[form]=xy((z>0)&~oldalpha);source[form]=z
 rgba=np.zeros((384,384,4),np.uint8);rgba[117:144,144:169]=cell;rawrgba[form]=rgba
assert len(outside['base'])==3 and len(outside['fourth'])==5
base=np.where(oldalpha,source['base'],0).astype(np.uint8)
side=np.zeros(oldalpha.shape,bool);side[127:135,160:163]=True
owner=(oldhead|side)&oldalpha
head=np.where(owner,source['fourth'],0).astype(np.uint8);gold=[]
for y,x in zip(*np.nonzero(owner)):
 r,g,b=rawrgba['fourth'][y,x,:3].astype(float)/255
 hi=max(r,g,b);lo=min(r,g,b);delta=hi-lo;s=delta/hi if hi else 0
 hue=0 if not delta else (60*((g-b)/delta)%360 if hi==r else 60*((b-r)/delta+2) if hi==g else 60*((r-g)/delta+4))
 if 28<=hue<=55 and s>.4 and hi>.55:
  gold.append({'world':[int(x)-160,int(y)-160],'nearest':int(head[y,x]),'gold':10});head[y,x]=10
assert owner.sum()==39 and (head>0).sum()==39
assert np.array_equal(owner,arr(D/'fourth_owner.png')>0)
assert np.array_equal(base,arr(D/'184_bank0_indices.png'))
assert np.array_equal(head,arr(D/'184_bank5_indices.png'))
assert base[135,156]==7 and head[135,156]==0
basic=a.rgba(base);fourth=basic.copy();fourth.alpha_composite(a.rgba(head,16))
assert np.array_equal(np.array(basic),arr(D/'base184.png'))
assert np.array_equal(np.array(fourth),arr(D/'fourth184.png'))
assert np.array_equal(np.array(basic)[:,:,3]>0,oldalpha)
assert np.array_equal(np.array(fourth)[:,:,3]>0,oldalpha)
for n in('register_vehicle_head_base.py','register_vehicle_head_base_semantic.py'):read(H/n)
read(D/'registration.json');read(D/'comparison.png');read(Path(__file__))
assert 'register_vehicle_head_base' not in sys.modules and 'register_vehicle_head_base_semantic' not in sys.modules
v={'scope':'패킹 전 기본/포스 작은머리2셀의 직접 양자화와 공통머리/포스39셀 소유 독립 대조. 전체19별칭/후보ARC 검사는 아님.',
 'passed':True,'source_sha256':sha(data),'source_parent_sha256':sha(pdata),'grid':[96,96],
 'reconstruction':'전체96 NEAREST→두 고정25×27 창→실제CLUT0/16 불투명15색 최근접/alpha128. 기본새머리를 기존alpha에 제한, 포스새장식은39셀만head5로 배정.',
 'old_alpha_pixels':int(oldalpha.sum()),'source_missing_inside_old_alpha':[0,0],'excluded_source_exterior':outside,
 'old_head5_count':int(oldhead.sum()),'new_head5_owner':39,'owner_added_from_old':xy(owner&~oldhead),
 'gold_samples':gold,'gold_changes_from_nearest':sum(g['nearest']!=10 for g in gold),
 'eye_world':[-4,-25],'common_eye_index':7,'head5_at_eye':0,'final_base_and_fourth_RGBA_exact_to_registration':True,
 'old_RGB_used_to_fill':False,
 'actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}for p in(src,D/'comparison.png')],
 'visual_observations':['기본의 중앙 밝은 단색면에 어두운 세로 가닥과 밝은 면의 경계가 생겨 기존보다 머릿결이 읽힌다.13×15의 귀/눈/얼굴 비율이 새로 커지거나 꺾인 확정 문제는 못 찾았다.','포스의 오른쪽 검보라 장식과 작은 금색 세로점이 대기의 장식 방향과 이어진다.공통 홍채는 유지되고장식이앞눈을덮거나별도고립조각처럼보이지않는다.','포스머리전체를다른팔레트로바꾼후보가아닌기본공통머리+포스옆장식이라는최종의미분리를확인했다.'],
 'limits':['새후보ARC/공유/19별칭/부분GPU/실기미검사','생성원화와비교판2파일정적열람','부모는36d4이며최종root호버부모합류는이후별도','producer미호출/입력·원화·ARC미변경'],
 'inputs':inputs}
(O/'report.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
for p,h in inputs.items():assert sha((ROOT/p).read_bytes())==h
lock={'inputs':inputs,'report_sha256':sha((O/'report.json').read_bytes())}
(O/'READER_LOCK.json').write_text(json.dumps(lock,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'report':sha((O/'report.json').read_bytes()),'lock':sha((O/'READER_LOCK.json').read_bytes()),'gold':gold,'old_head5':int(oldhead.sum()),'new_head5':39},ensure_ascii=False))
