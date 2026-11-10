"""Ultimate의 실제 효과 출처를 새 피격 몸체에 연결하는 진단. 기본형 규칙 혼용 금지."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation,distance_transform_cdt,label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint'),str(D)]
from preview_restore import Archive,sha,digest,need,write,helper
from pack_cycle import raw
from src.psx_player import compose_indices
from prepare_body_layers import composite,PBS
AUDIT=ROOT/'work/sprite_style_unification_20261107/zero_audit/nana_ultimate_hurt_relations01'
PARENT=N/'rising_repaint/packed_ultimate_candidate_v1/PL02_U.ARC'

def full(a,n):
    z=a.layer(n)[0].copy()
    for pb in (8,5,7,6):
        v=a.layer(n,pb)[0];z[v>0]=v[v>0]
    return z
def render(a,n,ps):
    ps=[{**p,'page':p['flags']&3,'unknown_flags':p['flags']&0x30,'flip_x':bool(p['flags']&64),'flip_y':bool(p['flags']&128),'index':i}for i,p in enumerate(ps)]
    p,size,box,_=compose_indices(raw(a,0,n),a.banks[0]['frames'][n]['tile_count'],{'parts':ps},allowed_cluts={0,1,2,3})
    v=np.frombuffer(p,np.uint8).reshape(size[1],size[0]);z=np.zeros((384,384),np.uint8);y,x=np.nonzero(v);z[y+box[1]+160,x+box[0]+160]=v[y,x];return z
def silhouette(n,residual,body):
    v=residual.copy();m=body>0
    if n==112:v[binary_dilation(m)]=6;v[m]=14
    elif n==113:v[binary_dilation(m)]=1
    else:
        v[binary_dilation(m)]=1;v[m]=3;v[np.isin(body%16,(1,2,4,8,15))&m]=5;v[np.isin(body%16,(6,9))&m]=1
    return np.where(v,v+32,0).astype(np.uint8)

def main():
    out=D/'effect_probe_v1';out.mkdir(exist_ok=False);a=Archive(PARENT.read_bytes())
    need(digest(AUDIT/'report.json')=='6a848905f6170e4872cda020ae345a8e5b971718fdfe911906a069d5e7c33059','독립 효과 출처')
    report=json.loads((AUDIT/'report.json').read_text('utf8'));src=D/'body_layers_probe_v1';targets={};records=[];panels=[]
    for n in (106,110,233,234):targets[n]={pb:np.array(Image.open(src/f'layer{pb}_{n:03}.png'))for pb in PBS}
    for q in report['semantic_effect_comparisons']:
        n,core=q['ref'],q['body_ref'];fx=render(a,n,q['effect_records']);need(np.array_equal(fx,np.load(AUDIT/f'{n}_separate_effect.npy')),'독립 실제효과 대조')
        ls={pb:z.copy()for pb,z in targets[core].items()};ls[0]=np.where(fx,fx,ls[0]).astype(np.uint8)
        if n in(107,108):ls[5]=np.where(fx,fx,ls[5]).astype(np.uint8)
        targets[n]=ls;Image.fromarray(fx).save(out/f'effect_{n:03}.png')
        records.append({'ref':n,'body':core,'mode':'현재 재킷층의 분리된 원효과 전체타일/파트를 양폼에 보존'if n in(107,108)else'현재 CLUT2 10파트를 기존 표시순서로 보존','effect_source':q,'effect_sha256':sha(fx.tobytes()),'body_overlaps':int(((fx>0)&(targets[core][0]>0)).sum()),'old_after_body_difference_not_preserved':q['base_core_plus_fx_comparison']['pixels']})
    after=targets[106][0];before=np.array(Image.open(D/'costume_pair_probe_v4/before_106.png'))
    f=[]
    for b in(after,before):
        v=np.zeros_like(b);v[binary_dilation(b>0)]=9;v[b>0]=13;f.append(v)
    need(not np.any((f[0]>0)&(f[1]==0)),'전후 플래시알파')
    targets[109]={0:f[0],5:np.where(f[0]!=f[1],f[1],0).astype(np.uint8),**{pb:np.zeros_like(after)for pb in(6,7,8)}}
    records.append({'ref':109,'mode':'양폼 각각 새106 알파의13내부/Manhattan1px9외곽','before_pixels':int(np.count_nonzero(f[1])),'after_pixels':int(np.count_nonzero(f[0]))})
    history=ROOT/'work/overhaul_20261105/sprites/ver_rin_nana/baseline/PL02_U.ARC';h=Archive(history.read_bytes());oldmask=h.layer(110)[0]>0;oldlaunch=full(h,110)
    newlaunch=np.array(Image.open(D/'costume_pair_probe_v4/before_110.png'))
    for n in(112,113,114):
        res=h.layer(n)[0]%16;res=res.copy();res[binary_dilation(oldmask,iterations=2)]=0
        if n==114:res[np.isin(res,(3,5))]=0
        need(np.array_equal(res,np.load(AUDIT/f'{n}_external_residual.npy')),'역사 외부효과 독립대조')
        need(np.array_equal(silhouette(n,res,oldlaunch),a.layer(n)[0]),'현재 역사실루엣 exact')
        v=silhouette(n,res,newlaunch);targets[n]={0:v,**{pb:np.zeros_like(v)for pb in PBS[1:]}}
        Image.fromarray(res).save(out/f'residual_{n:03}.png')
        records.append({'ref':n,'body':110,'mode':'현재와 같은 재킷110의 공통CLUT2 실루엣/별도아머없음','source_history':history.relative_to(ROOT).as_posix(),'history_sha256':digest(history),'residual_sha256':sha(res.tobytes()),'residual_pixels':int(np.count_nonzero(res)),'new_small_component_deletion':False})
    oldbody=full(a,234);newbody=np.array(Image.open(D/'costume_pair_probe_v4/before_234.png'))
    for n in(235,236):
        current=full(a,n);need(np.array_equal(current[oldbody>0],oldbody[oldbody>0]),'재킷 234몸체 일치')
        fx=np.where(oldbody==0,current,0).astype(np.uint8);need(np.array_equal(fx,np.load(AUDIT/f'{n}_before_external_current.npy')),'확실한 외부오라 대조')
        ls={pb:z.copy()for pb,z in targets[234].items()};ls[0]=np.where(fx,fx,ls[0]).astype(np.uint8);ls[5]=np.where(fx,fx,ls[5]).astype(np.uint8);targets[n]=ls
        Image.fromarray(fx).save(out/f'effect_{n:03}.png');dist=distance_transform_cdt(newbody==0,metric='taxicab');over=(fx>0)&(newbody>0)
        labs,k=label(fx>0,np.ones((3,3)));components=[]
        for i in range(1,k+1):
            yy,xx=np.where(labs==i);components.append({'id':i,'pixels':len(xx),'bbox':[int(xx.min()-160),int(yy.min()-160),int(xx.max()-159),int(yy.max()-159)],'new_overlap':int(over[labs==i].sum())})
        records.append({'ref':n,'body':234,'mode':'현재 재킷234 바깥 확실한 오라만 분리;새몸겹침 미수용 진단','effect_pixels':int(np.count_nonzero(fx)),'effect_sha256':sha(fx.tobytes()),'new_before_overlap':int(over.sum()),'overlap_world':[[int(x-160),int(y-160)]for y,x in np.argwhere(over)],'max_distance':int(dist[fx>0].max()),'components':components,'old_after_body_costume_fragments_not_effects':True})
    for n,ls in sorted(targets.items()):
        for pb,z in ls.items():Image.fromarray(z).save(out/f'layer{pb}_{n:03}.png')
        if n not in(106,110,233,234):panels.append((f'Ultimate effect {n}',[('current before',a.composite(n,15)[0]),('new before diagnostic',composite(a,ls,15)),('current after',a.composite(n)[0]),('new after diagnostic',composite(a,ls))]))
    for i in range(0,len(panels),3):helper.grid(panels[i:i+3],out/f'comparison_{i//3+1}.png',5)
    write(out/'manifest.json',{'parent_sha256':digest(PARENT),'body_manifest_sha256':digest(src/'manifest.json'),'relation_report_sha256':digest(AUDIT/'report.json'),'frames':records,'targets':{str(n):{str(pb):sha(z.tobytes())for pb,z in ls.items()}for n,ls in targets.items()},'scope':'Ultimate 고유 효과 출처/새 몸체 동기화 진단. 새 ARC 없음. 235/236 새몸 오라겹침은 후속 정합 전.','native_packed':False,'runtime_verified':False})
    print(json.dumps([r for r in records if r['ref']in(235,236)]))
if __name__=='__main__':main()
