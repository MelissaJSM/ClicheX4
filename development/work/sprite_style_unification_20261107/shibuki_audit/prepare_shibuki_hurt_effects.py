"""시부키 새 피격4몸체에 해당 부모의 원효과/실루엣 규칙을 합성하는 진단."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
from src.psx_player import decode_stream,compose_indices
from src.psx_ui_atlas import local_composition
from prepare_lowhp_final import compose
PBS=(0,5,6,7,8);BODIES=(106,110,233,234);REFS=tuple(range(106,115))+tuple(range(233,237))
PARENT='381d83fa2623d58a3302914196ffdd73bd8c972e27aa584380af05d819e688ce'
A=ROOT/'work/sprite_style_unification_20261107/zero_audit/shibuki_hurt_sources01'

def render(a,n,b,ps):
    out=np.zeros((384,384),np.uint8)
    if not ps:return out
    f=a.banks[0]['frames'][n];raw=decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128).data;c={'parts':ps}
    if b:c=local_composition(c)
    px,sz,bb,_=compose_indices(raw,f['tile_count'],c,allowed_cluts={0,1,2,3});z=np.frombuffer(px,np.uint8).reshape(sz[1],sz[0]);y,x=np.nonzero(z);out[y+bb[1]+160,x+bb[0]+160]=z[y,x];return out

def silhouette(n,residual,body):
    z=residual.copy();m=body>0
    if n==112:z[binary_dilation(m)]=6;z[m]=14
    elif n==113:z[binary_dilation(m)]=1
    else:
        z[binary_dilation(m)]=1;z[m]=3;z[np.isin(body,[1,2,4,8,15])&m]=5;z[np.isin(body,[6,9])&m]=1
    return np.where(z,z+32,0).astype(np.uint8)

def main():
    out=H/'hurt_effect_probe01';need(not out.exists(),'Fresh effect output');out.mkdir();a=Archive((H/'prepared_base_run01/PL00_U.ARC').read_bytes());need(sha(a.data)==PARENT,'Parent changed')
    adata=(A/'report.json').read_bytes();need(sha(adata)=='202898054ae9061a626b1a9088bfde79bf3ef15339963acfc3f4d3d0c49b348c','Independent source report changed');ar=json.loads(adata)['archives'][0]
    bodydir=H/'hurt_common_probe02';bm=json.loads((bodydir/'report.json').read_text('utf8'));need(all(not r['boundary_unresolved']for r in bm['rows']),'Body unresolved edges')
    bodies={n:{b:np.array(Image.open(bodydir/f'{n:03}_bank{b}_indices.png'))for b in PBS}for n in BODIES};targets={n:{b:v.copy()for b,v in ll.items()}for n,ll in bodies.items()};records=[];protected={};files={}
    def loadfx(path):
        p=Path(path);p=p if p.is_absolute()else ROOT/p;files[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes());return np.load(p)
    for e in ar['effects']:
        n,core=e['ref'],e['core'];targets[n]={};protected[n]={};rr=[]
        for b in PBS:
            if b==0:ps=e['original_effect_parts']if n in(107,108)else e['actual_CLUT2_records']
            elif n in(107,108):
                eb=e['original_armor_effect17_18'][str(b)];need(eb['current_records_equal_original']and eb['current_fixed_clut_effect_comparison']['different_pixels']==0,'Original armor effect mismatch');ps=eb['current_same_number_records']
            else:ps=[]
            fx=render(a,n,b,ps);protected[n][b]=ps;target=np.where(fx>0,fx,bodies[core][b]).astype(np.uint8);targets[n][b]=target
            Image.fromarray(fx).save(out/f'{n:03}_effect_bank{b}_indices.png')
            rr.append({'bank':b,'original_records':ps,'effect_opaque':int((fx>0).sum()),'effect_sha256':sha(fx.tobytes()),'body_overlap':int(((fx>0)&(bodies[core][b]>0)).sum())})
        records.append({'ref':n,'body':core,'policy':'각 부모에서 확인한 원효과 타일/레코드를 새몸 뒤가 아니라 원래 추가파트 순서대로 위에 그린다. 옛 의상 extra는 복사하지 않는다.','layers':rr})
    m=bodies[106][0]>0;v=np.zeros((384,384),np.uint8);v[binary_dilation(m)]=9;v[m]=14
    targets[109]={0:v,**{b:np.zeros_like(v)for b in PBS[1:]}}
    records.append({'ref':109,'body':106,'policy':'원PL00과 같은 기본몸 기준 내부14/Manhattan1 외곽9, 빈 아머층 유지','inside':14,'outline':9})
    for q in ar['silhouettes112_114']:
        n=q['ref'];res=loadfx(q['residual_path']).copy();removed=[]
        for r in q['small_components_deleted_coordinates']:
            y,x=r['y']+160,r['x']+160
            if res[y,x]:removed.append({'world':[r['x'],r['y']],'value':int(res[y,x])});res[y,x]=0
        v=silhouette(n,res,bodies[110][0]);targets[n]={0:v,**{b:np.zeros_like(v)for b in PBS[1:]}}
        Image.fromarray(res).save(out/f'{n:03}_external_residual.png')
        records.append({'ref':n,'body':110,'policy':'원US 출처의 외부효과에 새110 색상실루엣, 기존 외부효과 삭제좌표만 재현. 새머리/옷의 작은 성분은 삭제하지 않음.','legacy_external_removed':removed,'external_pixels':int((res>0).sum()),'external_sha256':sha(res.tobytes()),'new_body_component_deletion':False})
    for q in ar['aura235_236']:
        n=q['ref'];fx=loadfx(q['historical_effect_path']);ls={b:v.copy()for b,v in bodies[234].items()};ls[0]=np.where(ls[0]>0,ls[0],fx).astype(np.uint8);targets[n]=ls;Image.fromarray(fx).save(out/f'{n:03}_historical_effect.png');records.append({'ref':n,'body':234,'policy':'원래 시부키 제작식의 실제 오라256/464를 뒤에 두고 새234가 가림. 포스 옛 의상조각/오라 재색상은 복사하지 않음. 미술 검토 전 후보.','whole_effect_pixels':int((fx>0).sum()),'whole_effect_sha256':sha(fx.tobytes()),'old_fourth_external_color_changes':46 if n==235 else 77,'base_visible_external_pixels':int(((fx>0)&(bodies[234][0]==0)).sum()),'mask0_old_body_exact_rule':True,'fourth_aura_colour_normalization_pending_art_review':True})
    need(set(targets)==set(REFS),'Target refs');hashes={}
    for n,ll in targets.items():
        hashes[str(n)]={}
        for b,v in ll.items():Image.fromarray(v).save(out/f'{n:03}_bank{b}_indices.png');hashes[str(n)][str(b)]=sha(v.tobytes())
    for form,mask in(('base',0),('fourth',15)):
        for i,refs in enumerate(((106,107,108,109),(110,111,112,113,114),(233,234,235,236))):
            pics=[]
            for n in refs:pics.extend([(f'{n} current {form}',a.composite(n,mask)[0]),(f'{n} new {form}',compose(a,targets[n],mask))])
            page(pics,a.composite(0,mask)[0],out/f'{form}_effects_{i:02}.png',cols=2,scale=4)
    write(out/'manifest.json',{'parent_sha256':PARENT,'body_source':'hurt_common_probe02','body_report_sha256':sha((bodydir/'report.json').read_bytes()),'independent_source_report_sha256':sha(adata),'source_arrays':files,'refs':list(REFS),'targets':hashes,'records':records,'protected_effect_records':protected,'scope':'새 몸체/부분층과 부모별 원효과 규칙을 합성한 정적 미술 검토 후보. 원화 재생성/ARC/코드/타이밍 변경없음.','effect_aura_review_pending':True,'arc_written':False,'runtime_verified':False})
    print(json.dumps({'refs':len(targets),'layers':sum(map(len,targets.values())),'manifest_sha256':sha((out/'manifest.json').read_bytes())}))
if __name__=='__main__':main()
