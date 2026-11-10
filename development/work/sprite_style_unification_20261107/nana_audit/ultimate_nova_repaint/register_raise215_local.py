"""215의 새 굽힌 팔과 이전 낮춘 팔 제거 영역만 등록한다."""
from pathlib import Path
import sys,json,importlib.util,argparse
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,helper,need
s=importlib.util.spec_from_file_location('nova_raise_samples',N/'ultimate_standing_repaint/prepare_common.py');u=importlib.util.module_from_spec(s);s.loader.exec_module(u)
SPANS={-23:(9,15),-22:(8,16),-21:(8,17),-20:(8,18),-19:(8,19),-18:(8,19),-17:(8,19),-16:(8,19),-15:(8,19),-14:(7,19),-13:(6,19),-12:(5,19),-11:(4,18),-10:(3,17),-9:(2,16),-8:(2,15),-7:(1,14),-6:(0,15),-5:(0,15),-4:(0,16),-3:(0,17),-2:(0,17),-1:(0,17),0:(0,17),1:(0,17),2:(0,16),3:(2,15),4:(3,14)}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--version',default='v2');args=ap.parse_args()
 out=D/f'raise215_local_probe_{args.version}';out.mkdir(exist_ok=False);meta=json.loads((D/'a_inputs_v1/manifest.json').read_text('utf8'));a=Archive((ROOT/meta['parent_arc']).read_bytes());im=Image.open(D/'raise215_v1/generated.png').convert('RGBA');mask=np.zeros((384,384),bool)
 if args.version=='v2':
  for y in(-2,-1,0):SPANS[y]=(0,18)
 for y,(x0,x1)in SPANS.items():mask[y+160,x0+160:x1+161]=True
 rows=[];proof=[]
 for row,(form,start,engine_mask)in enumerate((('before',16,15),('after',0,0))):
  original=np.array(Image.open(D/f'semantic_samples_v1/{form}_215_indices.png'));source=np.array(Image.open(D/f'raise215_fixed_v1/{form}_215_indices.png'));z=original.copy();z[mask]=source[mask];cell=im.crop((627,row*627,1254,(row+1)*627));pal=np.array([[((int(w)>>k)&31)*255//31 for k in(0,5,10)]for w in a.words[start:start+16]],np.float32);p15=[]
  for yy,xx in np.argwhere(mask&(z==15)):
   x,y=int(xx-160),int(yy-160);value,votes=u.source_vote(cell,pal,(x,y),{15});z[yy,xx]=value;p15.append({'world':[x,y],'source_value':value,'votes':votes})
  need(np.array_equal(z[~mask],original[~mask]),'팔/몸 연결 의미영역 밖 보호');need(np.array_equal(z[165:],original[165:]),'무릎/종아리/신발 원화 그대로');Image.fromarray(z).save(out/f'{form}_215_indices.png');Image.fromarray(mask.astype(np.uint8)*255).save(out/'local_mask.png');proof.append({'form':form,'source_sha256':sha(source.tobytes()),'master_sha256':sha(original.tobytes()),'local_rows':SPANS,'palette15_source_samples':p15,'target_sha256':sha(z.tobytes()),'components':int(label(z>0,np.ones((3,3)))[1]),'old_pixels_copied':0,'full_source_body_used':False,'hand_native_translation':[0,0]});rows.append((form,[('old pose',a.composite(215,engine_mask)[0]),('first detail source',a.rgba(original,start)),('new raised source',a.rgba(source,start)),('arm local candidate',a.rgba(z,start))]))
 helper.grid(rows,out/'comparison.png',7);write(out/'manifest.json',{'generated_sha256':digest(D/'raise215_v1/generated.png'),'frames':proof,'scope':'직접 선행215의 높은 주먹/굽힌팔 방향을 새 원화로 복원한 국소 등록 후보. 첫 머리/눈/귀와 하체는 의미영역 밖에서 exact. 손 위치는 새 원화 그대로이며 기존 손좌표 exact를 주장하지 않음. 전후 공통층/최종 ARC는 미완료.','native_packed':False});print(json.dumps([{'form':q['form'],'components':q['components'],'p15':len(q['palette15_source_samples'])}for q in proof]))
if __name__=='__main__':main()
