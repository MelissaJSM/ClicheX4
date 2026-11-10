"""새 두 의상을 투명 포스층으로 합성할 때 남는 기본층을 숨기지 않고 진단."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,helper
Y,X=np.indices((384,384));Y-=160;X-=160
def main():
 a=Archive((N/'dash_repaint/packed_dash_candidate_v1/PL00_U.ARC').read_bytes());out=D/'common_coverage_audit_v1';out.mkdir(exist_ok=False);source=D/'body_contacts_probe_v1';rows=[];records=[]
 for n in(100,101,102,103,104,231):
  b=np.array(Image.open(source/f'base_{n:03}_indices.png'));f=np.array(Image.open(source/f'fourth_{n:03}_indices.png'));residual=(b>0)&(f==0);intended=a.rgba(f,16);actual=a.rgba(b);actual.alpha_composite(intended);diagnostic=actual.copy();rgba=np.array(diagnostic);rgba[residual]=[240,42,42,255];diagnostic=Image.fromarray(rgba)
  skin=np.isin(f,(10,11,12));counts={'upper_y_below_0':int(np.count_nonzero(residual&(Y<0))),'lower_y_at_least_0':int(np.count_nonzero(residual&(Y>=0)))}
  Image.fromarray(residual.astype(np.uint8)*255).save(out/f'base_residual_{n:03}.png');rows.append((f'Rising {n}',[('new base',a.rgba(b)),('intended Fourth source',intended),('transparent overlay result',actual),('uncovered base in red',diagnostic)]));records.append({'ref':n,'source_base_sha256':sha(b.tobytes()),'source_fourth_sha256':sha(f.tobytes()),'uncovered_base_pixels':int(residual.sum()),'regions':counts,'coordinates':[[int(x-160),int(y-160),int(b[y,x])]for y,x in np.argwhere(residual)],'actual_full_is_not_final':True})
 for i in range(0,len(rows),2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',6)
 write(out/'manifest.json',{'source_arc_sha256':sha(a.data),'source_contact_manifest_sha256':digest(source/'manifest.json'),'frames':records,'conclusion':'투명 파츠는 기본층을 지우지 않으므로 현재 전신 두 장을 그대로 덮어 완성하지 않는다. 빨강은 추가 그림이 아니라 잔류 기본층 진단색이다. 새 공통 몸체/머리·각 다리 접점을 별도로 등록해야 한다.','source_files_modified':False,'native_packed':False,'runtime_verified':False});print(json.dumps({r['ref']:r['uncovered_base_pixels']for r in records}))
if __name__=='__main__':main()
