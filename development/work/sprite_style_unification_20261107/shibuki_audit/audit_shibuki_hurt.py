"""최신 시부키 두 ARC의 피격 몸체/효과 관계를 읽기만 조사한다."""
from pathlib import Path
from collections import Counter
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
from src.psx_player import composition_frame,decode_stream,compose_indices
from src.psx_ui_atlas import local_composition
PARTS=(0,5,6,7,8);REFS=tuple(range(106,115))+tuple(range(233,237))
SOURCES={'PL00_U.ARC':('prepared_base_run01','381d83fa2623d58a3302914196ffdd73bd8c972e27aa584380af05d819e688ce'),'PL02_U.ARC':('prepared_ultimate_ladder01','03a675626035b93ad2e2feef8dd643365ed8a3e1a61a1eb02a476063e2c55e8a')}
def sig(p):return p['flags'],p['tile'],p['x'],p['y']
def render(a,n,b,parts):
    z=np.zeros((384,384),np.uint8)
    if not parts:return z
    f=a.banks[0]['frames'][n];raw=decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128).data;comp={'parts':parts}
    if b:comp=local_composition(comp)
    pix,sz,bb,_=compose_indices(raw,f['tile_count'],comp,allowed_cluts={0,1,2,3});v=np.frombuffer(pix,np.uint8).reshape(sz[1],sz[0]);y,x=np.nonzero(v);z[y+bb[1]+160,x+bb[0]+160]=v[y,x];return z
def main():
    o=H/'hurt_relations01';need(not o.exists(),'Fresh audit');o.mkdir();out=[]
    for name,(folder,expected)in SOURCES.items():
        path=H/folder/name;need(sha(path.read_bytes())==expected,'Source changed');a=Archive(path.read_bytes());od=o/name[:4];od.mkdir();refs=[];relations=[]
        for n in REFS:
            f=a.banks[0]['frames'][n];row={'ref':n,'tile_count':f['tile_count'],'raw_owners':[v['index']for v in a.banks[0]['frames']if v['offset']==f['offset']],'layers':{}}
            for b in PARTS:
                v,m=a.layer(n,b);row['layers'][str(b)]={'indexed_sha256':sha(v.tobytes()),'opaque':int((v>0).sum()),'index_counts':{str(int(k)):int(c)for k,c in zip(*np.unique(v[v>0],return_counts=True))},'parts':m['parts']};Image.fromarray(v).save(od/f'{n:03}_bank{b}.png')
            refs.append(row)
            core=106 if n in(107,108)else 110 if n==111 else 234 if n in(235,236)else None
            if core is None:continue
            relation={'ref':n,'body_ref':core,'layers':{}}
            for b in PARTS:
                body=composition_frame(a.c,b,core)['parts'];curr=composition_frame(a.c,b,n)['parts'];rem=Counter(sig(p)for p in body);same=[];extra=[]
                for p in curr:
                    if rem[sig(p)]:same.append(p);rem[sig(p)]-=1
                    else:extra.append(p)
                bodypix=a.layer(core,b)[0];newpix=a.layer(n,b)[0];opaque=bodypix>0;rec={'all_body_record_signatures_present':not any(rem.values()),'body_record_render_exact':np.array_equal(render(a,n,b,same),bodypix),'body_occupied_pixels_exact':np.array_equal(bodypix[opaque],newpix[opaque]),'new_opaque_outside_body':int(((newpix>0)&~opaque).sum()),'extra_records':extra}
                if rec['all_body_record_signatures_present']and rec['body_record_render_exact']:
                    fx=render(a,n,b,extra);Image.fromarray(fx).save(od/f'effect_{n:03}_bank{b}.png');rec.update(extra_effect_pixels=int((fx>0).sum()),effect_sha256=sha(fx.tobytes()),effect_over_body=int(((fx>0)&opaque).sum()))
                relation['layers'][str(b)]=rec
            relations.append(relation)
        mask=a.layer(106)[0]>0;v=a.layer(109)[0];flash={'body13_exact':np.array_equal(v==13,mask),'outline9_manhattan1_exact':np.array_equal(v==9,binary_dilation(mask)&~mask)}
        forms=[('base',0),('fourth',15)]if name.startswith('PL00')else[('ultimate_before',15),('ultimate_after',0)]
        for form,mask in forms:
            page([(f'{n} current {form}',a.composite(n,mask)[0])for n in(106,110,233,234)],a.composite(0,mask)[0],od/f'{form}_bodies.png',cols=2,scale=5)
            for i,selected in enumerate([list(range(106,110)),list(range(110,115)),list(range(233,237))]):page([(f'{n} {form}',a.composite(n,mask)[0])for n in selected],a.composite(0,mask)[0],od/f'{form}_effects_{i:02}.png',cols=2,scale=4)
        out.append({'archive':name,'source':path.relative_to(ROOT).as_posix(),'source_sha256':expected,'references':refs,'body_effect_relations':relations,'flash109':flash,'source_read_only':True})
    write(o/'report.json',{'scope':'새 원화 준비를 위한 실제 시부키 부모별13참조×5층 읽기. 나나 효과/부모관계를 시부키라고 가정하지 않음.','archives':out,'suggested_unique_body_keys':[106,110,233,234],'visual_review_pending':True,'source_art_generated':False,'arc_modified':False,'native_code_run':False,'runtime_verified':False,'silhouette112_114_history_pending':True,'effect235_236_provenance_pending':True});print(json.dumps({'archives':len(out),'refs_per_archive':len(REFS),'report_sha256':sha((o/'report.json').read_bytes())}))
if __name__=='__main__':main()
