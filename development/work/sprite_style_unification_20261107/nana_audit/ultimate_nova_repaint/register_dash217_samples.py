"""217 새 원화에서 사라진 실제 녹색 홍채 한 표본을 등록한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,helper,need
def main():
 out=D/'dash217_semantic_v1';out.mkdir(exist_ok=False);meta=json.loads((D/'dash217_inputs_v1/manifest.json').read_text('utf8'));a=Archive((ROOT/meta['parent_arc']).read_bytes());audit=json.loads((D/'dash217_samples_v1/report.json').read_text('utf8'));src=np.array(Image.open(D/'dash217_registered_v1/body_217_indices.png'));z=src.copy();q=max(audit['iris_candidates'],key=lambda r:r['green_fraction']);need(q['world']==[-14,1] and q['green_fraction']>.28,'실제 가장강한 홍채');x,y=q['world'];need(z[y+160,x+160]==13,'원 실제표본');z[y+160,x+160]=14;need(np.array_equal(z>0,src>0),'알파 불변');need(label(z>0,np.ones((3,3)))[1]==1,'몸체 연결');Image.fromarray(z).save(out/'body_217_indices.png');helper.grid([('217',[('current217',a.composite(217,15)[0]),('new fixed',a.rgba(src)),('actual green source',a.rgba(z)),('new215',a.rgba(np.array(Image.open(D/'common_probe_v5/after_215_indices.png'))))])],out/'comparison.png',7);write(out/'manifest.json',{'source_sha256':sha(src.tobytes()),'source_art_sha256':audit['source_sha256'],'iris_actual_sample':q,'new_index':14,'original_green_positions':[[-15,0],[-15,1]],'new_green_position':[-14,1],'head_translation':[0,0],'body_alpha_exact':True,'target_sha256':sha(z.tobytes()),'scope':'새 원화의 녹색 홍채 한 표본만 의미 등록. 옛 눈의 x좌표보다1px 오른쪽이며 옛좌표에 녹색을 임의로 그리지 않았다. 허리 근처 분홍2셀은의상/피부 소유미확정이므로 이번등록에서변경없음. 원손발/효과/최종패킹 별도.','native_packed':False});print(sha(z.tobytes()))
if __name__=='__main__':main()
