"""세 원화를 다시 정규화해 최종19 목표를 확인하고 입력 거부를 점검한다."""
from pathlib import Path
import sys,hashlib,json,struct,importlib.util
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_run import quantize
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render
D=Path(__file__).parent/'rin_extension';A=D/'ride_head_registered_v3';O=D/'prepared_ride_heads02';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sources=[(D/'ride_head01/generated.png','2283d7060f40e64730007807c86a166c0e40e5e072d6269ecffbf4945c2890b2',1/16),(D/'ride_head_rear_fix01/generated.png','df5cf4752b9f80509b977a8014a1843b175592cc5c6a8ff5175bf23103497c6e',32/887),(D/'ride_head75_crown_fix02/generated.png','251194b9e4ab9f58983d41a1e81b3a1bd44978cff585e475c782c7e1764bfc7a',32/1254)]
src=D/'prepared_bank1_recovery128/PL01_U.ARC';arc=src.read_bytes();assert sha(src)=='07ec6077969f17d08c51ffd8e4326b476e1c6ab5635bea8420faee9528b39a89';pal=struct.unpack_from('<16H',entry(arc,9));colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in pal[1:]],np.int32)
aa=[]
for p,h,scale in sources:
 assert sha(p)==h;aa.append(quantize(Image.open(p).convert('RGBA'),colors,scale))
assert aa[0].shape==(96,64)and aa[1].shape==(32,64)and aa[2].shape==(32,32)
info=json.loads((D/'ride_head01/inputs.json').read_text('utf8'));expected={};records=[]
for m in info['masters']:
 n=m['ref'];cx,cy=m['cell'];v=aa[0][cy*32:(cy+1)*32,cx*32:(cx+1)*32].copy()
 if n==66:
  im=np.array(Image.open(sources[0][0]).convert('RGBA'));q=im[304:320,208:224];nearest=np.argmin(((q[:,:,:3].astype(np.int32)[:,:,None]-colors[None,None])**2).sum(-1),axis=2)+1;coverage=float(np.where(nearest==15,q[:,:,3],0).sum()/256);assert 54<=coverage<=58;v[19,13]=15
 assert not v[-1].any();v=np.roll(v,1,axis=0)[8:24,8:24]
 if n in(75,77):
  col=(75,77).index(n);v=aa[1][8:24,col*32+8:col*32+24].copy()
 if n==75:v[2:7,1:15]=aa[2][10:15,9:23]
 assert np.array_equal(v,np.array(Image.open(A/f'head_{n}_indices16.png')))
 for ref in m['aliases']:
  x,y,r,b=info['frames'][str(ref)]['world_bounds'];z=np.zeros((384,384),np.uint8);z[y:b,x:r]=v;expected[ref]=z;assert np.array_equal(z,np.array(Image.open(A/f'b1_{ref:03}_indices.png')))
 records.append({'master':n,'source_reconstruction_exact':True,'alias_count':len(m['aliases'])})
candidate=(O/'PL01_U.ARC').read_bytes();assert sha(O/'PL01_U.ARC')=='c82e6230bcc687e2cc851a88735b695b04636b9fce3baddcf4c771abf81e265b'
for n,z in expected.items():assert np.array_equal(render(candidate,1,5,n)[0],z)
spec=importlib.util.spec_from_file_location('headpacker',Path(__file__).parent/'pack_rin_ride_heads02.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);again,proof=mod.build(arc);assert again==candidate
reject=[]
def must_fail(name,source,targets=None):
 try:mod.build(source,targets)
 except (AssertionError,ValueError,IndexError):reject.append(name)
 else:raise AssertionError('Invalid input accepted:'+name)
bad=bytearray(arc);bad[-1]^=1;must_fail('wrong_source_hash',bytes(bad))
t={n:z.copy()for n,z in expected.items()};t.pop(75);must_fail('missing_head_reference',arc,t)
t={n:z.copy()for n,z in expected.items()};t[66][0,0]=1;must_fail('opaque_outside_part',arc,t)
t={n:z.copy()for n,z in expected.items()};t[66][info['frames']['66']['world_bounds'][1],info['frames']['66']['world_bounds'][0]]=16;must_fail('palette_index16',arc,t)
t={n:z.copy()for n,z in expected.items()};t[66]=t[66].astype(np.int16);must_fail('wrong_index_dtype',arc,t)
t={n:z.copy()for n,z in expected.items()};x,y,_,_=info['frames']['66']['world_bounds'];t[66][y+5,x]=1;must_fail('GPU_U0_firstcolumn',arc,t)
j=json.loads((O/'proposal.json').read_text('utf8'));j['scope']='라이드 아머19참조의5각도 머리만 새 원화로 교체합니다.75/77 보닛 높이를 추가 보완했고75 상단17셀은 별도 국소 원화입니다. 원래조립전체/비대상/부분VRAM8/팔레트/음향/정적효과 보존. 조종석 미술 수용과 실기는 구분합니다.';j['source_proof']='rin259_v2_source_proof.json';j['generated_sources']=[{'path':str(p.relative_to(ROOT)),'sha256':h,'scale':scale}for p,h,scale in sources];(O/'proposal.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
result={'passed':True,'candidate_sha256':sha(O/'PL01_U.ARC'),'source_sha256':sha(src),'source_reconstruction':records,'19_target_png_and_candidate_exact':True,'reproducible_separate_process':True,'meaningful_rejections':reject,'parts_entry_exact':entry(candidate,3)==entry(arc,3),'scope':'원화3개 고정 캔버스 정규화 및 허용된66 눈표본/75 상단 의미영역 등록을 독립적으로 다시 계산했습니다. 게임 실행이 아닙니다.'}
(D/'rin259_v2_source_proof.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
c=json.loads((D/'rin259_components.json').read_text('utf8'));c['resources']['PL01_U.ARC']['path']=str((O/'PL01_U.ARC').relative_to(ROOT));c['resources']['PL01_U.ARC']['after']=sha(O/'PL01_U.ARC');(D/'rin259_v2_components.json').write_text(json.dumps(c,indent=2)+'\n','utf8');print(json.dumps(result))
