"""새 몸체와 기존 독립 효과/색상 실루엣을 분리해 비교한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation,label,distance_transform_cdt
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint')]
from preview_restore import Archive,sha,digest,write,need,helper
from pack_cycle import raw
from src.psx_player import compose_indices,composition_frame
PBS=(0,5,6,7,8)
def composite(a,layers,mask):
    im=a.rgba(layers[0])
    for bit,pb in((8,8),(1,5),(4,7),(2,6)):
        if mask&bit:im.alpha_composite(a.rgba(layers[pb],32 if pb==7 else 16))
    return im
def render(a,n,parts):
    z=np.zeros((384,384),np.uint8)
    if not parts:return z
    cnt=a.banks[0]['frames'][n]['tile_count']
    px,sz,bb,_=compose_indices(raw(a,0,n),cnt,{'parts':parts},allowed_cluts={0,1,2,3})
    ar=np.frombuffer(px,np.uint8).reshape(sz[1],sz[0]);y,x=np.nonzero(ar);z[y+bb[1]+160,x+bb[0]+160]=ar[y,x]
    return z
def main():
    a=Archive((N/'rising_repaint/packed_base_candidate_v1/PL00_U.ARC').read_bytes());src=D/'joint_layers_probe_v1'
    bodies={n:{pb:np.array(Image.open(src/f'layer{pb}_{n:03}.png'))for pb in PBS}for n in(106,110,233,234)}
    report=json.loads((ROOT/'work/sprite_style_unification_20261107/zero_audit/nana_hurt_relations01/report.json').read_text('utf8'))
    out=D/'effect_probe_v1';out.mkdir(exist_ok=False);targets={};records=[];panels=[]
    for n in(106,110,233,234):targets[n]={pb:z.copy()for pb,z in bodies[n].items()}
    for q in report['body_plus_effect_relations']:
        n,core=q['ref'],q['body_reference'];ls={};rr=[]
        for pb in PBS:
            ps=q['layers'][str(pb)]['extra_effect_records'];ps=[{**p,'page':p['flags']&3,'unknown_flags':p['flags']&0x30,'flip_x':bool(p['flags']&64),'flip_y':bool(p['flags']&128),'index':i}for i,p in enumerate(ps)]
            fx=render(a,n,ps);body=bodies[core][pb]
            ls[pb]=np.where(fx,fx,body).astype(np.uint8)
            Image.fromarray(fx).save(out/f'effect_{n:03}_bank{pb}.png')
            rr.append({'bank':pb,'effect_opaque':int(np.count_nonzero(fx)),'effect_sha256':sha(fx.tobytes()),'new_body_overlap':int(((fx>0)&(body>0)).sum()),'effect_parts':q['layers'][str(pb)]['extra_effect_records']})
        targets[n]=ls;records.append({'ref':n,'mode':'원추가파트/전체효과타일 보존','body':core,'layers':rr})
    mask=bodies[106][0]>0;flash=np.zeros((384,384),np.uint8);flash[binary_dilation(mask)]=9;flash[mask]=13
    targets[109]={0:flash,**{pb:np.zeros_like(flash)for pb in PBS[1:]}}
    old_launch=a.layer(110)[0];new_launch=bodies[110][0]
    invp=ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/inventory.json';inv=json.loads(invp.read_text('utf8'))
    def original(n):
        v=np.array(Image.open(invp.parent/f'base_{n:03d}.png'));bb=inv['base_frames'][n]['bounds'];z=np.zeros((384,384),np.uint8);y,x=np.nonzero(v);z[y+bb[1]+160,x+bb[0]+160]=v[y,x]%16;return z
    def silhouette(n,residual,launch):
        v=residual.copy();m=launch>0
        if n==112:v[binary_dilation(m)]=6;v[m]=14
        elif n==113:v[binary_dilation(m)]=1
        else:
            v[binary_dilation(m)]=1;v[m]=3;v[np.isin(launch,(1,2,4,8,15))]=5;v[np.isin(launch,(6,9))]=1
        return v
    original_body=original(110)>0
    for n in(112,113,114):
        residual=original(n);residual[binary_dilation(original_body,iterations=2)]=0
        if n==114:residual[np.isin(residual,(3,5))]=0
        historical=silhouette(n,residual,old_launch);labs,_=label(historical>0);sz=np.bincount(labs.flat);removed=(labs!=0)&(sz[labs]<4)
        old=historical.copy();old[removed]=0;need(np.array_equal(old,a.layer(n)[0]%16),'과거 부모 실루엣 재구성')
        # 과거 제거된 외부효과만 캐시한다. 새머리의 작은 성분을 일괄제거하지 않는다.
        residual[removed]=0
        new=silhouette(n,residual,new_launch)
        targets[n]={0:np.where(new,new+32,0).astype(np.uint8),**{pb:np.zeros_like(new)for pb in PBS[1:]}}
        Image.fromarray(residual).save(out/f'residual_{n:03}_local_indices.png')
        records.append({'ref':n,'mode':'원CLUT2 효과 + 새110 색상실루엣','body':110,'legacy_removal_coordinates_preserved':int(removed.sum()),
                        'new_body_small_component_deletion':False,'residual_sha256':sha(residual.tobytes()),'residual_pixels':int(np.count_nonzero(residual)),
                        'effect_under_new_silhouette':int(((residual>0)&binary_dilation(new_launch>0)).sum())})
    for n in(235,236):
        old_body=a.layer(234)[0];current=a.layer(n)[0];fx=np.where(old_body,0,current).astype(np.uint8)
        # 진단에서는 오라가 새몸에 겹치면 오라를 앞에 유지한다. 해당 셀을 공개한다.
        target={pb:z.copy()for pb,z in bodies[234].items()};target[0]=np.where(fx,fx,target[0]).astype(np.uint8)
        targets[n]=target
        union=np.logical_or.reduce([z>0 for z in bodies[234].values()]);dist=distance_transform_cdt(~union,metric='taxicab')
        overlap=(fx>0)&union
        records.append({'ref':n,'mode':'수용이력 나나오라 유지 진단, 신규몸 가림 미수용','body':234,'effect_pixels':int(np.count_nonzero(fx)),
                        'effect_sha256':sha(fx.tobytes()),'new_any_part_overlap':int(overlap.sum()),'overlap_world':[[int(x-160),int(y-160)]for y,x in np.argwhere(overlap)],
                        'max_effect_distance':int(dist[fx>0].max())})
        Image.fromarray(fx).save(out/f'effect_{n:03}_bank0.png')
    for n in sorted(targets):
        for pb,z in targets[n].items():Image.fromarray(z).save(out/f'layer{pb}_{n:03}.png')
        if n not in(106,110,233,234):panels.append((f'effect {n}',[('current base',a.composite(n)[0]),('new base and effect',composite(a,targets[n],0)),('current Fourth',a.composite(n,15)[0]),('new Fourth and effect',composite(a,targets[n],15))]))
    for k in range(0,len(panels),3):helper.grid(panels[k:k+3],out/f'comparison_{k//3+1}.png',5)
    write(out/'manifest.json',{'parent_sha256':sha(a.data),'body_manifest_sha256':digest(src/'manifest.json'),'frames':records,
                             'targets':{str(n):{str(pb):sha(z.tobytes())for pb,z in ls.items()}for n,ls in targets.items()},
                             'scope':'독립효과와 새실루엣 파생 진단.235/236 새몸 가림 여부는 미술 검토 전. ARC 출력 없음.', 'native_packed':False,'runtime_verified':False})
    print(json.dumps(records))
if __name__=='__main__':main()
