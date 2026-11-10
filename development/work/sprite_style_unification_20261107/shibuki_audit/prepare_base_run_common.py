"""15 새 보행의 공통 머리와 의상 외곽 등록. 조립은행 경계 변경 없음."""
from pathlib import Path
import sys,json,struct
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
from scripts.prepare_shibuki_ultimate_production import repack_parts
from probe_dash_common_head import poly
def main():
    o=H/'base_run_common01';need(not o.exists(),'Fresh output');o.mkdir();d=H/'base_run_contacts02';meta=json.loads((d/'report.json').read_text('utf8'));p=H/'prepared_dash_base01/PL00_U.ARC';a=Archive(p.read_bytes());rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[16:32]],np.int32);rgbbase=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[:16]],np.int32);mapping={i:int(np.argmin(((rgb[1:]-rgbbase[i])**2).sum(1)))+1 for i in range(1,16)};y,x=np.indices((384,384));x-=160;y-=160;rows=[];pics=[];heads={}
    for n in sorted(map(int,meta['new_eye_positions'])):
        ex,ey=meta['new_eye_positions'][str(n)];base=np.array(Image.open(d/f'base_{n:03}_indices.png'));raw=np.array(Image.open(d/f'fourth_{n:03}_indices.png'));m=next(r for r in meta['rows']if r['form']=='fourth'and r['ref']==n);sd=ROOT/m['source_directory'];sm=json.loads((sd/'manifest.json').read_text('utf8'));refs=sm.get('refs',sm.get('first_new_keys'));col=refs.index(n);src=np.array(Image.open(sd/'generated.png'));need(sha((sd/'generated.png').read_bytes())==m['source_sha256'],'Source changed')
        region=poly([(ex-12,ey-18),(ex+16,ey-18),(ex+16,ey-7),(ex+34,ey-2),(ex+34,ey+5),(ex+17,ey+8),(ex+5,ey+3),(ex-6,ey+3),(ex-12,ey-3)]);face=(x>=ex-4)&(x<=ex+4)&(y>=ey-3)&(y<=ey+3);common=region&(np.isin(base,[0,2,5,8,14,15])|(face&np.isin(base,[7,10,11,12,13])));dec=(x>=ex+5)&(x<ex+21)&(y>=ey-13)&(y<ey+3)&region;common|=dec
        if n==19:common|=(x>=13)&(y>=-3)&(y<=3)&np.isin(base,[0,2,5,8,14,15]);dec&=~((x>=13)&(y>=-3))
        over=raw.copy();over[common]=0;over[dec]=raw[dec];edge=(base>0)&(over==0)&(~common|dec);changes=[]
        for py,px in zip(*np.nonzero(edge)):
            wx,wy=int(px)-160,int(py)-160;b=src[512+(wy+36)*8:512+(wy+37)*8,col*512+(wx+32)*8:col*512+(wx+33)*8];bm=b[:,:,3]>=128;count=int(bm.sum());idxbase=int(base[py,px])
            if count>=8:
                q=1+((b[:,:,:3].astype(np.int32)[:,:,None,:]-rgb[None,None,1:,:])**2).sum(3).argmin(2);vv,cc=np.unique(q[bm],return_counts=True);idx=int(vv[cc.argmax()]);method='new_source_cell_opaque_mode';hist=dict(zip(map(str,vv),map(int,cc)))
            else:
                idx={1:2,4:11,10:10,11:11,12:9,13:9,15:1}.get(idxbase,mapping[idxbase]);method='new_base_local_material';hist={}
            over[py,px]=idx;changes.append({'world':[wx,wy],'base_index':idxbase,'fourth_index':idx,'source_opaque':count,'method':method,'source_histogram':hist})
        head=np.where(dec,over,0).astype(np.uint8);rest=np.where(~dec,over,0).astype(np.uint8);need(not np.any((base>0)&(over==0)&(~common|dec)),'Visible base costume leakage');full=a.rgba(base);full.alpha_composite(a.rgba(rest,16));full.alpha_composite(a.rgba(head,16));full.save(o/f'fourth_{n:03}.png');a.rgba(base).save(o/f'base_{n:03}.png')
        for name,v in(('base_indices',base),('raw_fourth_indices',raw),('head_indices',head),('rest_indices',rest)):Image.fromarray(v).save(o/f'{n:03}_{name}.png')
        for name,v in(('common',common),('decoration',dec)):Image.fromarray(v.astype(np.uint8)*255).save(o/f'{n:03}_{name}_mask.png')
        yy,xx=np.nonzero(head);bbox=[int(xx.min())-160,int(yy.min())-160,int(xx.max())-159,int(yy.max())-159];need(bbox[2]-bbox[0]<=16 and bbox[3]-bbox[1]<=16,'Decoration over single tile');heads[n]=struct.pack('<BBbb',0,10,bbox[0],bbox[1]);heads[n+1]=heads[n]
        rows.append({'ref':n,'new_eye':list(map(int,(ex,ey))),'head_bbox':bbox,'new_common_opaque':int(np.count_nonzero(base[common])),'head_record_hex':heads[n].hex(),'source_boundary_registration':changes,'source_sha256':m['source_sha256'],'base_exact_to_contact_registration':True,'old_head_or_body_copied':False});pics.extend([(f'{n} raw new Fourth',a.rgba(raw,16)),(f'{n} common new head / contour',full)])
    _,slack=repack_parts(a.c,5,heads)
    for k in range(0,len(pics),6):page(pics[k:k+6],a.composite(0,15)[0],o/f'comparison_{k//6:02}.png',cols=2,scale=4)
    write(o/'report.json',{'candidate_only':True,'rows':rows,'head_bank_dry_run_including_shot_aliases_slack':slack,'shot_head_aliases_only_for_capacity_probe':True,'source_contact_report_sha256':sha((d/'report.json').read_bytes()),'source_parent_sha256':sha(a.data),'part_ownership_pending':True,'shots_art_pending':True,'arc_written':False,'bank_boundaries_changed':False,'runtime_verified':False});print(json.dumps({'refs':len(rows),'boundary_cells':[len(r['source_boundary_registration'])for r in rows],'head_bank_slack':slack}))
if __name__=='__main__':main()
