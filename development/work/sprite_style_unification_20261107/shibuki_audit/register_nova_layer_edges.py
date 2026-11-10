"""새 포스 원화의 인접 윤곽 표본으로 공통 실루엣의11셀을 정합한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
from prepare_lowhp_final import compose
MAP={213:[(0,20,1,20)],215:[(-13,-21,-14,-21),(10,-17,9,-17),(10,-16,9,-16),(11,-16,9,-16),(10,-15,9,-14),(11,-15,9,-14),(11,-10,10,-11),(-16,-9,-15,-9),(-9,-1,-8,-1),(-9,0,-8,0)]}
def main():
    s=H/'nova_layers_probe01';d=H/'nova_layers_final01';need(not d.exists(),'새 후보');d.mkdir();a=Archive((H/'prepared_chaser_base01/PL00_U.ARC').read_bytes());report=json.loads((s/'report.json').read_text('utf8'));rows=[]
    for n in(213,215):
        layers={b:np.array(Image.open(s/f'{n:03}_bank{b}_indices.png'))for b in(0,5,6,7,8)};owner=np.array(Image.open(s/f'{n:03}_owner.png'));donor=np.array(Image.open(H/f'nova_fourth_costume_composed01/fourth_{n:03}_indices.png'));common=np.array(Image.open(s/f'{n:03}_common_mask.png'))>0
        expected={(p[0],p[1])for r in report['rows']if r['ref']==n for p in r['unresolved']};need(expected=={(x,y)for x,y,_,_ in MAP[n]},'정확 미정합집합');records=[]
        for x,y,sx,sy in MAP[n]:
            b=int(owner[y+160,x+160]);v=int(donor[sy+160,sx+160]);need(v>0,'새 donor 투명');need(layers[b][y+160,x+160]==0,'기존 새그림 보호');layers[b][y+160,x+160]=v;records.append({'target':[x,y],'source':[sx,sy],'palette16_index':v,'owner':b,'manhattan_distance':abs(x-sx)+abs(y-sy),'source_sha256':sha(donor.tobytes())})
        overlay=np.zeros_like(layers[0])
        for b in(5,6,7,8):overlay[layers[b]>0]=layers[b][layers[b]>0]
        need(not((layers[0]>0)&~common&(overlay==0)).any(),'기본 의상 누출');need(np.array_equal(layers[0],np.array(Image.open(H/f'nova_base_native01/base_{n:03}_indices.png'))),'기본 원화 보존')
        partial=[]
        for m in range(16):
            im=compose(a,layers,m);labs,_=label(np.array(im)[:,:,3]>0,np.ones((3,3)));components=sorted(map(int,np.bincount(labs.flat)[1:]),reverse=True);need(len(components)==1,'부분 단절');partial.append({'mask':m,'rgba_sha256':sha(im.tobytes()),'components':components})
        for b,z in layers.items():Image.fromarray(z).save(d/f'{n:03}_bank{b}_indices.png')
        for form,m in(('base',0),('fourth',15)):compose(a,layers,m).save(d/f'{form}_{n:03}.png')
        page([(f'{n} mask{m:X}',compose(a,layers,m))for m in range(16)],a.composite(0,15)[0],d/f'partial_{n:03}.png',cols=4,scale=4)
        rows.append({'ref':n,'edge_source_registration':records,'base_exact':True,'unresolved':0,'partial':partial,'layer_hashes':{str(b):sha(z.tobytes())for b,z in layers.items()}})
    for form,m in(('base',0),('fourth',15)):
        page([(f'{n} 기존',a.composite(n,m)[0])if i==0 else(f'{n} 새 공통부',Image.open(d/f'{form}_{n:03}.png'))for n in(213,215)for i in(0,1)],a.composite(0,m)[0],d/f'{form}_comparison.png',cols=2,scale=5)
    write(d/'report.json',{'rows':rows,'source_probe_sha256':sha((s/'report.json').read_bytes()),'all32_partial_single_component':True,'policy':'새 기본형의 실제 실루엣과 새 포스 의상의 인접 윤곽11표본을 정합. 기존 옛몸/머리 덮기·일괄축소·저장을 위한 도트삭감 없음. 머리/손 공통부는 기본 새원화 그대로.','arc_written':False,'packed_or_runtime_verified':False});print(json.dumps({'keys':2,'layers':10,'partial':32,'edge_source_samples':11}))
if __name__=='__main__':main()
