"""새 권총과 실제 쥔 손을 양 의상에 공통으로 등록한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
POLYS={133:[(-18,10),(-14,10),(-14,13),(-16,14),(-19,13)],135:[(-13,-6),(-8,-6),(-8,-3),(-12,-3)],136:[(-16,-12),(-10,-12),(-10,-9),(-9,-8),(-9,-6),(-15,-6)],137:[(-15,-19),(-10,-19),(-10,-16),(-15,-16)],138:[(-14,-27),(-10,-27),(-10,-24),(-14,-24)]}
def main():
 src=D/'canonical_cases_probe_v2';out=D/'common_hands_probe_v1';out.mkdir(exist_ok=False);a=Archive((N/'ultimate_hurt_repaint/packed_hurt_candidate_v1/PL02_U.ARC').read_bytes());records=[];rows=[]
 for n,poly in POLYS.items():
  b=np.array(Image.open(src/f'before_{n:03}_indices.png'));old=np.array(Image.open(src/f'after_{n:03}_indices.png'));case=np.array(Image.open(src/f'before_{n:03}_case.png'));mi=Image.new('L',(384,384));ImageDraw.Draw(mi).polygon([(x+160,y+160)for x,y in poly],fill=1);m=(np.array(mi)>0)|(case>0);common=b.copy();common[b==15]=13;after=old.copy();after[m]=common[m];need(np.array_equal(after[~m],old[~m]),'의상/몸 보호');outside=(after>0)&(b==0);need(not outside.any(),'공통손/몸 알파 포함');need(int(label(after>0,np.ones((3,3)))[1])==1,'손 연결')
  for form,z in(('before',b),('after',after),('hand_mask',m.astype(np.uint8)*255)):Image.fromarray(z).save(out/f'{form}_{n:03}.png')
  records.append({'ref':n,'source_manifest_sha256':digest(src/'manifest.json'),'before_path':(src/f'before_{n:03}_indices.png').relative_to(ROOT).as_posix(),'before_source_sha256':digest(src/f'before_{n:03}_indices.png'),'after_path':(src/f'after_{n:03}_indices.png').relative_to(ROOT).as_posix(),'after_source_sha256':digest(src/f'after_{n:03}_indices.png'),'common_hand_polygon':poly,'canonical_mask_also_common':True,'changes':[[int(x-160),int(y-160),int(old[y,x]),int(after[y,x])]for y,x in np.argwhere(after!=old)],'after_outside_before':0,'before_sha256':sha(b.tobytes()),'after_sha256':sha(after.tobytes()),'components8':[1,1]});rows.append((f'common hand {n}',[('before',a.rgba(b,16)),('after before sharing',a.rgba(old)),('common new hand',a.rgba(after)),('after idle',a.composite(0)[0])]))
 for i in range(0,len(rows),2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',7)
 write(out/'manifest.json',{'frames':records,'scope':'기존새원화/정본모듈에서같은쥔손의정확색인공유.새의상/팔/얼굴/다리는의미영역밖exact.외곽을임의절삭하거나새색칠하지않음.','native_packed':False,'runtime_verified':False});print(json.dumps([{'ref':q['ref'],'changes':q['changes']}for q in records]))
if __name__=='__main__':main()
