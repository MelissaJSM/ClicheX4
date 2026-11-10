"""새 이동15몸체의 실제 눈/발 원화 표본을 등록한다. 구형 그림 치환 없음."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
GROUPS=[(None,[3,11,19]),('page02',[5,7,9]),('page03',[13,15,17]),('page04',[21,23,25]),('page05',[27,29,31])]
def main():
    o=H/'base_run_contacts02';need(not o.exists(),'Fresh output');o.mkdir();a=Archive((H/'prepared_dash_base01/PL00_U.ARC').read_bytes());rows=[];allpics={'base':[],'fourth':[]};eyes={};sources=[]
    for pg,refs in GROUPS:
        d=H/'base_run_inputs01'/pg if pg else H/'base_run_followup02';native=H/f'base_run_{pg}_native01' if pg else H/'base_run_native01';src=np.array(Image.open(d/'generated.png'));meta=json.loads((native/'report.json').read_text('utf8'));need(sha((d/'generated.png').read_bytes())==meta['source_sha256'],'Source changed');sources.append({'path':d.relative_to(ROOT).as_posix(),'sha256':meta['source_sha256']})
        for row,(form,mask,pal)in enumerate((('base',0,0),('fourth',15,16))):
            rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[pal:pal+16]],np.int32)
            def cell(wx,wy,col):
                b=src[row*512+(wy+36)*8:row*512+(wy+37)*8,col*512+(wx+32)*8:col*512+(wx+33)*8];m=b[:,:,3]>=128;q=1+((b[:,:,:3].astype(np.int32)[:,:,None,:]-rgb[None,None,1:,:])**2).sum(3).argmin(2);return b,m,q
            for col,n in enumerate(refs):
                before=np.array(Image.open(native/f'{form}_{n:03}_indices.png'));v=before.copy();marks=[]
                if (form,n)==('fourth',3) or n==21:
                    target_y=22;xs=range(10,16)if n==3 else(-8,-7)
                    for wx in xs:
                        b,m,q=cell(wx,target_y,col);need(m.sum()>=8,'Insufficient actual sole source');vv,cc=np.unique(q[m],return_counts=True);idx=int(vv[cc.argmax()]);need(v[target_y+160,wx+160]==0,'Sole already opaque');v[target_y+160,wx+160]=idx;marks.append({'kind':'sole_coverage_sample','world':[wx,target_y],'source_opaque':int(m.sum()),'source_mode':idx,'histogram':dict(zip(map(str,vv),map(int,cc)))})
                if form=='base':
                    gold=v==7;gold[155:]=False
                    if not gold.any():
                        old=a.layer(n)[0];m=old==7;m[155:]=False;yy,xx=np.nonzero(m);need(1<=len(xx)<=2,'Ambiguous original eye anchor');ex,ey=int(xx[0])-160,int(yy[0])-160;options=[]
                        for wy in range(ey-1,ey+2):
                            for wx in range(ex-1,ex+2):
                                b,m,q=cell(wx,wy,col);count=int(((q==7)&m).sum());options.append((count,-abs(wx-ex)-abs(wy-ey),wx,wy))
                        count,_,wx,wy=max(options);need(count>=8,'Gold eye requires actual source');need(v[wy+160,wx+160]!=0,'Eye outside new face');prev=int(v[wy+160,wx+160]);v[wy+160,wx+160]=7;marks.append({'kind':'actual_gold_eye_subsample','world':[wx,wy],'source_gold_pixels':count,'old_nearest_index':prev,'new_index':7,'original_anchor':[ex,ey],'policy':'원화의 금색 눈 표본이 가장 많은 8x8셀 한 점. 원래 눈 위치±1 내 새 원화 기준이며 옛 눈 도트 복사 아님.'});gold=v==7;gold[155:]=False
                    yy,xx=np.nonzero(gold);need(len(xx)==1,'Ambiguous new eye');eyes[n]=[int(xx[0])-160,int(yy[0])-160]
                oldrgba=np.array(a.composite(n,mask)[0]);oy,ox=np.nonzero(oldrgba[:,:,3]);yy,xx=np.nonzero(v);need(int(yy.max())==int(oy.max()),'Foot height not preserved')
                Image.fromarray(v).save(o/f'{form}_{n:03}_indices.png');im=a.rgba(v,pal);im.save(o/f'{form}_{n:03}.png');rows.append({'form':form,'ref':n,'source_directory':d.relative_to(ROOT).as_posix(),'source_sha256':meta['source_sha256'],'registration':marks,'changed_from_fixed_nearest_pixels':int(np.count_nonzero(v!=before)),'sole_y':int(yy.max())-160,'output_indices_sha256':sha((o/f'{form}_{n:03}_indices.png').read_bytes())});allpics[form].append((n,im))
    for form,items in allpics.items():
        items=sorted(items)
        for k in range(0,len(items),5):page([(f'{form} {n} new',im)for n,im in items[k:k+5]],a.composite(0,0 if form=='base' else 15)[0],o/f'{form}_all_{k//5:02}.png',cols=3,scale=4)
    write(o/'report.json',{'candidate_only':True,'rows':rows,'new_eye_positions':eyes,'sources':sources,'original_sole_heights_all_exact':True,'old_master_copied':False,'global_body_scale_changed':False,'part_ownership_pending':True,'runtime_verified':False});print(json.dumps({'body_keys':15,'form_displays':30,'registered_cells':sum(r['changed_from_fixed_nearest_pixels']for r in rows),'eyes':eyes}))
if __name__=='__main__':main()
