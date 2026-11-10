"""새 첫3 사다리의 실제 손/검정커프만 양의상에 공유한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
BOX={143:(-15,-28,-8,-22),144:(-11,-31,-5,-25),146:(-11,-32,-4,-26)}
def main():
 a=Archive((N/'ultimate_return_repaint/packed_return_candidate_v1/PL02_U.ARC').read_bytes());src=D/'a_common_probe_v1';out=D/'a_grip_probe_v1';out.mkdir(exist_ok=False);rows=[];records=[]
 for n,box in BOX.items():
  before=np.array(Image.open(src/f'before_{n}_indices.png'));initial=np.array(Image.open(src/f'after_{n}_indices.png'));after=initial.copy();x0,y0,x1,y1=box;view=(slice(y0+160,y1+160),slice(x0+160,x1+160));source=before[view].copy();need(not np.isin(source,(5,6,7,8,9,15)).any(),'손창에분홍소매/머리/별색포함');after[view]=source
  for form,z in(('before',before),('after',after)):Image.fromarray(z).save(out/f'{form}_{n:03}_indices.png')
  rows.append((str(n),[('old jacket',a.composite(n,15)[0]),('new jacket',a.rgba(before,16)),('new bare previous',a.rgba(initial)),('new shared grip',a.rgba(after))]));records.append({'ref':n,'source_box_world':box,'source':'new before actual hand and black cuff only','before_source_sha256':digest(src/f'before_{n}_indices.png'),'after_source_sha256':digest(src/f'after_{n}_indices.png'),'changed_pixels':[{'world':[int(x-160),int(y-160)],'from':int(initial[y,x]),'source_index':int(before[y,x])}for y,x in np.argwhere(after!=initial)],'hand_box_exact':True,'components8':int(label(after>0,np.ones((3,3)))[1]),'old_body_copied':False})
 helper.grid(rows,out/'comparison.png',6);write(out/'manifest.json',{'parent_sha256':sha(a.data),'frames':records,'scope':'새 손/검정커프 두의상 공유 진단. 기존 144 손 외곽의 고립된끝점과 새 손의 모양 차이는 남아 있어 단순 bbox를 맞추는 전체팔 이동을 하지 않는다. 원접점최종수용/패킹/실기 아님.','native_packed':False,'runtime_verified':False});print(json.dumps([{'ref':q['ref'],'changed':len(q['changed_pixels']),'components':q['components8']}for q in records]))
if __name__=='__main__':main()
