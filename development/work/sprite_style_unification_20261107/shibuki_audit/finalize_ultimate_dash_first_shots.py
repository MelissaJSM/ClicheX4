"""새 노출 손/아래팔 공통화와 실제 소매 외곽 표본으로 첫4사격 정합."""
from pathlib import Path
import sys,json,shutil
import numpy as np
from PIL import Image
from scipy.ndimage import label,binary_dilation
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
from register_dash_shot_page import palette
MAP={68:(1,'ultimate_dash_shot_native01',0),70:(1,'ultimate_dash_shot_native01',1),72:(2,'ultimate_dash_shot_native02b',0),76:(2,'ultimate_dash_shot_native02b',1)}
EDGES={68:[[-10,3,27]],70:[[-17,2,34]],72:[],76:[[-24,6,21],[-23,7,16],[-22,8,25]]}

def main():
    o=H/'ultimate_dash_shot_targets01';need(not o.exists(),'Fresh target candidate');o.mkdir();a=Archive((H/'prepared_ultimate_air01/PL02_U.ARC').read_bytes());gdir=H/'ultimate_dash_barrel_guard01';gm=json.loads((gdir/'report.json').read_text('utf8'));y,x=np.indices((384,384));rows=[];pics={'before':[],'after':[]}
    for n,(pn,dirname,col)in MAP.items():
        src=H/dirname;b=np.array(Image.open(src/f'before_{n:03}_indices.png'));a0=np.array(Image.open(src/f'after_{n:03}_indices.png'));aa=a0.copy();oldb=b.copy();m=next(r for r in gm['rows']if r['shot_ref']==n and r['form']=='before');mx,my=m['muzzle_world'];shared=np.zeros(b.shape,bool)
        if n in(68,70):
            shared=(x>=160+mx+8)&(x<=160+mx+13)&(y>=160+my-3)&(y<=160+my+11)
            vals=set(map(int,np.unique(b[shared])));need(vals<={0,2,5,8,12,13,14,15},'Shared region includes jacket cuff')
            for idx in vals:need(int(a.words[idx])==int(a.words[16+idx]),'Shared exposed forearm color differs')
            aa[shared]=b[shared]
        outside=[(int(px-160),int(py-160))for py,px in zip(*np.nonzero((aa>0)&(b==0)))];need(outside==[(e[0],e[1])for e in EDGES[n]],'Unreviewed contour')
        image_path=H/f'ultimate_dash_shot_inputs01/page{pn:02}/generated.png';raw=np.array(Image.open(image_path).convert('RGBA'));colors=palette(a,16);samples=[]
        for wx,wy,expected in EDGES[n]:
            cell=raw[(wy+36)*8:(wy+37)*8,(wx+48)*8+col*768:(wx+49)*8+col*768];v=cell[:,:,3]>=128;need(int(v.sum())==expected,'Source coverage changed');q=1+((cell[:,:,:3].astype(np.int32)[:,:,None,:]-colors[None,None,1:,:])**2).sum(3).argmin(2);vals,cnt=np.unique(q[v],return_counts=True);index=int(vals[cnt.argmax()]);need(index in(1,2,4,8,15),'Not a source sleeve contour');b[wy+160,wx+160]=index;samples.append({'world':[wx,wy],'opaque_source_samples':expected,'total_samples':64,'source_mode_index':index,'histogram':dict(zip(map(str,vals),map(int,cnt)))})
        need(not np.any((aa>0)&(b==0)),'After alpha escapes before');gun=np.array(Image.open(gdir/f'{n:03}_indices.png'));guard=np.array(Image.open(gdir/f'{n:03}_mask.png'))>0;need(np.array_equal(b[guard],gun[guard])and np.array_equal(aa[guard],gun[guard]),'Canonical barrel changed')
        for form,v,pal in(('before',b,16),('after',aa,0)):
            Image.fromarray(v).save(o/f'{form}_{n:03}_indices.png');im=a.rgba(v,pal);im.save(o/f'{form}_{n:03}.png');pics[form].append((f'{n} {form} new arm',im));contact=binary_dilation(gun>0,structure=np.array([[0,1,0],[1,1,1],[0,1,0]]))&(v>0)&~guard;need(contact.any(),'Hand does not touch canonical gun');lab,cnt=label(v>0,np.ones((3,3),int));need(cnt==1,'New part detached');allowed=np.array(Image.open(src/f'{form}_{n:03}_allowed_mask.png'))>0;baseline=np.array(Image.open(src/f'{form}_{n:03}_indices.png'));delta=v!=baseline;need(np.all(allowed[delta]),'Changed outside original arm patch')
        Image.fromarray(shared.astype(np.uint8)*255).save(o/f'{n:03}_shared_exposed_forearm_mask.png')
        rows.append({'ref':n,'source_folder':dirname,'source_report_sha256':sha((src/'report.json').read_bytes()),'source_image_sha256':sha(image_path.read_bytes()),'shared_exposed_forearm_source':'same new before arm, not old art'if shared.any()else None,'shared_forearm_opaque':int(np.count_nonzero(oldb[shared])),'after_shared_changes':int(np.count_nonzero(aa!=a0)),'source_sleeve_edge_samples':samples,'no_alpha_clipping':True,'after_alpha_subset':True,'barrel_exact':True,'fourway_hand_barrel_contact':True,'connected_components8':1,'body_outside_arm_exact':True})
    for form,mask in(('before',15),('after',0)):page(pics[form],a.composite(0,mask)[0],o/f'{form}_comparison.png',cols=2,scale=5)
    write(o/'report.json',{'passed':True,'candidate_only':True,'parent_sha256':sha(a.data),'refs':list(MAP),'rows':rows,'policy':'68/70 두 의상에 이미 드러난 새 손·아래팔 모듈만 공통 사용. 소매 영역은 복사하지 않음. 나머지5경계셀은 실제 새 재킷 원화의 최빈 외곽색을 등록. 맨팔 알파를 잘라 소매 안으로 숨기지 않음.','palette_changed':False,'packed':False,'gameplay_verified':False,'remaining_shots':[78,80,82,84]});print(json.dumps({'refs':list(MAP),'shared_changes':[r['after_shared_changes']for r in rows],'source_edges':sum(len(r['source_sleeve_edge_samples'])for r in rows)}))
if __name__=='__main__':main()
