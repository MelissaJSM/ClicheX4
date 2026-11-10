"""현재 Ultimate 외부 오라의 연결성분을 새 몸체 바깥으로 최소 평행 정합한다."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
from scipy.ndimage import label,distance_transform_cdt
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(D)]
from preview_restore import Archive,sha,digest,need,write,helper
from prepare_body_layers import composite,PBS
SHIFTS={235:{2:(0,-1),4:(2,0),5:(-1,0),6:(1,1)},236:{1:(-2,-4),2:(1,0),3:(-1,0),4:(0,-2),6:(-1,0),7:(2,0),8:(0,2),10:(-1,1)}}
def main():
    cli=argparse.ArgumentParser();cli.add_argument('--version',choices=['v1','v2'],default='v2');args=cli.parse_args()
    out=D/f'aura_contact_probe_{args.version}';out.mkdir(exist_ok=False);p=N/'rising_repaint/packed_ultimate_candidate_v1/PL02_U.ARC';a=Archive(p.read_bytes());src=D/'effect_probe_v1';body=D/'body_layers_probe_v1'
    b=np.array(Image.open(D/'costume_pair_probe_v4/before_234.png'));union=b>0;distance=distance_transform_cdt(~union,metric='taxicab');rows=[];frames=[]
    for n,shifts in SHIFTS.items():
        shifts=dict(shifts)
        if args.version=='v2' and n==236:shifts[1]=(4,-2)
        fx=np.array(Image.open(src/f'effect_{n:03}.png'));ls={pb:np.array(Image.open(body/f'layer{pb}_234.png'))for pb in PBS}
        labs,count=label(fx>0,np.ones((3,3)));result=np.zeros_like(fx);components=[];links=[]
        for k in range(1,count+1):
            yy,xx=np.where(labs==k);dx,dy=shifts.get(k,(0,0));y2,x2=yy+dy,xx+dx
            need(not np.any(result[y2,x2]),'오라성분 겹침');need(not np.any(union[y2,x2]),'새몸가림')
            result[y2,x2]=fx[yy,xx]
            components.append({'id':k,'pixels':len(xx),'translation':[dx,dy],'source_bbox':[int(xx.min()-160),int(yy.min()-160),int(xx.max()-159),int(yy.max()-159)],'max_body_distance':int(distance[y2,x2].max()),'source_shape_and_colors_preserved':True})
            links.extend([[int(x-160),int(y-160),int(x+dx-160),int(y+dy-160),int(fx[y,x])]for y,x in zip(yy,xx)])
        need(int(np.count_nonzero(result))==int(np.count_nonzero(fx)),'오라픽셀 보존')
        Image.fromarray(result).save(out/f'effect_{n:03}.png')
        for pb in(0,5):ls[pb]=np.where(result,result,ls[pb]).astype(np.uint8)
        for pb,z in ls.items():Image.fromarray(z).save(out/f'layer{pb}_{n:03}.png')
        oldls={pb:np.array(Image.open(src/f'layer{pb}_{n:03}.png'))for pb in PBS}
        rows.append((f'Ultimate aura {n}',[('current before',a.composite(n,15)[0]),('new source/old aura',composite(a,oldls,15)),('registered before',composite(a,ls,15)),('registered after',composite(a,ls))]))
        frames.append({'ref':n,'source_path':(src/f'effect_{n:03}.png').relative_to(ROOT).as_posix(),'source_sha256':digest(src/f'effect_{n:03}.png'),'pixels':len(links),'source_components':count,'components':components,'source_links':links,'before_overlap':int(((fx>0)&union).sum()),'new_overlap':0,'old_max_distance':int(distance[fx>0].max()),'new_max_distance':int(distance[result>0].max()),'new_effect_sha256':sha(result.tobytes()),'hidden_original_effect_restoration_claimed':False})
    helper.grid(rows,out/'comparison.png',7)
    write(out/'registration.json',{'parent_sha256':digest(p),'source_manifest_sha256':digest(src/'manifest.json'),'frames':frames,'scope':'현재 재킷234바깥 확실한오라66/135셀을 원형/색/성분별 보존한 평행정합 후보. 새몸·표정·다리는 그대로이며 오라만 이동. 실제시간표/게임미검증.','native_packed':False,'runtime_verified':False})
    print(json.dumps([{k:r[k]for k in('ref','pixels','source_components','before_overlap','new_overlap','old_max_distance','new_max_distance')}for r in frames]))
if __name__=='__main__':main()
