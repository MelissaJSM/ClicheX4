"""사다리 새 몸체 공통부와 원반전 관계를 후보로 묶는다. 사격은 별도."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
ALIASES={145:(144,-1),147:(146,0),148:(149,0),152:(151,0)}
def mirror(v,k):
    out=np.zeros_like(v);y,x=np.nonzero(v);tx=320+k-x;need(np.all((tx>=0)&(tx<v.shape[1])),'Mirror clipped');out[y,tx]=v[y,x];return out
def main():
    o=H/'ultimate_ladder_contacts01';need(not o.exists(),'Fresh target');o.mkdir();s=H/'ultimate_ladder_common_probe02';p=H/'prepared_ultimate_dash01/PL02_U.ARC';a=Archive(p.read_bytes());j=json.loads((s/'report.json').read_text('utf8'));rgb=np.array([[(int(w)>>v&31)for v in(0,5,10)]for w in a.words]);data={};rows=[]
    for r in j['rows']:
        n=r['ref'];before=np.array(Image.open(s/f'before_{n:03}_indices.png'));after=np.array(Image.open(s/f'after_{n:03}_indices.png'));points=[]
        for x,y,val in r['outside_jacket_pixels']:
            need(before[160+y,160+x]==0 and after[160+y,160+x]==val,'Outside point changed');need(val in(2,8,15)and np.array_equal(rgb[val],rgb[16+val]),'Only identical-source contour');before[160+y,160+x]=val;points.append([x,y,val])
        need(not np.any((after>0)&(before==0)),'Bare body escapes jacket');data[n]=(before,after);rows.append({'ref':n,'source':s.relative_to(ROOT).as_posix(),'source_outline_points_added_to_jacket':points,'whole_body_translation':[0,0],'source_scale_unchanged':True,'current_old_lowest_y':r['old_lowest_y'],'new_lowest_y':r['new_lowest_y'],'sole_exact_claimed':False,'source_joint_review_pending':r['new_lowest_y']!=r['old_lowest_y']})
    for n,(src,k)in ALIASES.items():
        data[n]=tuple(mirror(v,k)for v in data[src]);rows.append({'ref':n,'source_ref':src,'world_transform':f'x=-x+({k});y=y','current_old_raw_mirror_exact_claimed':False,'reference_basis':'원US base 층의 정확 반전.147/148 원overlay 하단1px 예외는 새후폼·공통몸체에 재도입하지 않음.','new_common_pose_mirror_exact':True})
    pics={'before':[],'after':[]}
    for n in sorted(data):
        for form,v,pal,mask in [('before',data[n][0],16,15),('after',data[n][1],0,0)]:
            Image.fromarray(v).save(o/f'{form}_{n:03}_indices.png');rgba=a.rgba(v,pal);rgba.save(o/f'{form}_{n:03}.png');pics[form].append((f'{n} new {form}',rgba))
    for form,mask in [('before',15),('after',0)]:
        for start in range(0,len(pics[form]),6):page(pics[form][start:start+6],a.composite(0,mask)[0],o/f'{form}_poses_{start//6:02}.png',cols=3,scale=5)
    alias=ROOT/'work/sprite_style_unification_20261107/zero_audit/ultimate_ladder_aliases01/report.json';need(sha(alias.read_bytes())=='eda0c968a5d38ee11122dbc9cd2f1a9e5c0b516022a528604c050deb475a9cbc','Alias evidence changed')
    write(o/'report.json',{'parent_sha256':sha(a.data),'source_common_report_sha256':sha((s/'report.json').read_bytes()),'source_alias_report_sha256':sha(alias.read_bytes()),'rows':rows,'added_source_outline_points':6,'target_refs':sorted(data),'after_alpha_subset_before':True,'old_art_reused':False,'native_draw_times_unchanged':True,'unmodified_sole_discrepancy_needs_visual_review':[r['ref']for r in rows if r.get('source_joint_review_pending')],'shooting_refs_not_present':[150,155],'arc_written':False,'runtime_verified':False});print(json.dumps({'refs':sorted(data),'outside':6,'pending_shooting':[150,155]}))
if __name__=='__main__':main()
