"""새 Ultimate 대시 두 의상20참조를 원화 근거와 함께 고정한다."""
from pathlib import Path
import sys,json,shutil
import numpy as np
from PIL import Image
from scipy.ndimage import label,binary_dilation
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,same_rgba
from scripts.export_x_consistency import Archive,page
from register_dash_shot_page import palette
P=H/'prepared_ultimate_air01/PL02_U.ARC'
PARENT='3ae1d8d56c595b04e59abf735ac377ab381c73673c2eaade99679031f3fc65f7'
BODY=(67,69,71,75,77,79,81,83,93,94)
SHOTS=(68,70,72,76,78,80,82,84)
EDGES={78:[(-17,-10,33,2),(-17,-9,24,2)],80:[(-18,-2,39,15),(-10,-1,18,15)],82:[],84:[]}

def main():
    o=H/'ultimate_dash_complete_targets01';need(not o.exists(),'Fresh output required');need(sha(P.read_bytes())==PARENT,'Parent changed');a=Archive(P.read_bytes());o.mkdir();full={};base={};rows=[];sources={};colors=palette(a,16);gdir=H/'ultimate_dash_barrel_guard01'
    def read(folder,form,n):
        p=H/folder/f'{form}_{n:03}_indices.png';sources[p.relative_to(H).as_posix()]=sha(p.read_bytes());return np.array(Image.open(p))
    for n in BODY:full[n]=read('ultimate_dash_contacts05','before',n);base[n]=read('ultimate_dash_contacts05','after',n)
    for n in SHOTS:
        folder='ultimate_dash_shot_targets01'if n<78 else f'ultimate_dash_shot_native0{3 if n<82 else 4}'
        full[n]=read(folder,'before',n);base[n]=read(folder,'after',n);samples=[]
        if n>=78:
            pn=3 if n<82 else 4;col=int(n in(80,84));src=H/f'ultimate_dash_shot_inputs01/page{pn:02}/generated.png';raw=np.array(Image.open(src));sources[src.relative_to(H).as_posix()]=sha(src.read_bytes())
            outside=[(int(x-160),int(y-160))for y,x in zip(*np.nonzero((base[n]>0)&(full[n]==0)))];need(outside==[(x,y)for x,y,_,_ in EDGES[n]],'Unreviewed new contour')
            for wx,wy,coverage,expected in EDGES[n]:
                cell=raw[(wy+36)*8:(wy+37)*8,(wx+48)*8+col*768:(wx+49)*8+col*768];opaque=cell[:,:,3]>=128;need(int(opaque.sum())==coverage,'Source coverage changed');q=1+((cell[:,:,:3].astype(np.int32)[:,:,None,:]-colors[None,None,1:,:])**2).sum(3).argmin(2);v,c=np.unique(q[opaque],return_counts=True);idx=int(v[c.argmax()]);need(idx==expected,'Source color changed');full[n][wy+160,wx+160]=idx;samples.append({'world':[wx,wy],'source_opaque_samples':coverage,'source_mode_index':idx,'histogram':dict(zip(map(str,v),map(int,c)))})
        gun=np.array(Image.open(gdir/f'{n:03}_indices.png'));guard=np.array(Image.open(gdir/f'{n:03}_mask.png'))>0
        for form,v in(('before',full[n]),('after',base[n])):
            need(np.array_equal(v[guard],gun[guard]),'Barrel changed');need(label(v>0,np.ones((3,3),int))[1]==1,'Detached component');contact=binary_dilation(gun>0,structure=np.array([[0,1,0],[1,1,1],[0,1,0]]))&(v>0)&~guard;need(contact.any(),'Hand contact missing')
        rows.append({'ref':n,'source_folder':folder,'source_contour_samples':samples,'body_outside_arm_exact':True,'canonical_gun_exact':True,'fourway_contact':True,'whole_new_exposed_forearm_shared':n in(68,70),'after_alpha_clipped':False})
    streak=H/'ultimate_dash_streak_audit01'
    for n,bn in((73,71),(74,72)):
        ep=streak/f'{n:03}_original_indices.png';effect=np.array(Image.open(ep));need(np.count_nonzero(effect)==54,'Original effect pixels changed');sources[ep.relative_to(H).as_posix()]=sha(ep.read_bytes());full[n]=np.where(effect>0,effect,full[bn]);base[n]=np.where(effect>0,effect,base[bn]);rows.append({'ref':n,'body_ref':bn,'original_effect_pixels':54,'original_effect_record_count':9,'effect_order':'original body records followed by original effect records','effect_timing_changed':False})
    targetrows=[]
    for n in sorted(full):
        need(not np.any((base[n]>0)&(full[n]==0)),f'After alpha outside jacket {n}');targets={0:base[n],5:np.where(same_rgba(a,full[n],base[n]),0,full[n]).astype(np.uint8)}
        for b in(6,7,8):need(not a.layer(n,b)[0].any(),'Independent armor unexpectedly nonblank');targets[b]=np.zeros((384,384),np.uint8)
        for b,v in targets.items():Image.fromarray(v).save(o/f'{n:03}_bank{b}_indices.png')
        for name,im,pal in(('before',full[n],16),('after',base[n],0)):
            Image.fromarray(im).save(o/f'{name}_{n:03}_indices.png');a.rgba(im,pal).save(o/f'{name}_{n:03}.png')
        targetrows.append({'ref':n,'after_alpha_subset':True,'before_pixels':int(np.count_nonzero(full[n])),'after_pixels':int(np.count_nonzero(base[n])),'jacket_overlay_pixels':int(np.count_nonzero(targets[5]))})
    for name,mask,images,pal in(('before',15,full,16),('after',0,base,0)):
        pics=[(f'{n} new {name}',a.rgba(images[n],pal))for n in sorted(full)]
        for j in range(0,len(pics),6):page(pics[j:j+6],a.composite(0,mask)[0],o/f'{name}_comparison_{j//6:02}.png',cols=3,scale=4)
    prefixes=['ultimate_dash_inputs01','ultimate_dash_native01','ultimate_dash_native02','ultimate_dash_native03','ultimate_dash_native04','ultimate_dash93_barearm01','ultimate_dash93_barearm_native02','ultimate_dash_common_probe01','ultimate_dash_common_probe02','ultimate_dash_common_probe03','ultimate_dash_common_probe04','ultimate_dash_contacts02','ultimate_dash_contacts03','ultimate_dash_contacts04','ultimate_dash_contacts05','ultimate_dash_shot_inputs01','ultimate_dash_shot_native01','ultimate_dash_shot_native02b','ultimate_dash_shot_native03','ultimate_dash_shot_native04','ultimate_dash_shot_targets01','ultimate_dash_barrel_guard01','ultimate_dash_streak_audit01']
    for prefix in prefixes:
        for p in sorted((H/prefix).rglob('*')):
            if p.is_file()and p.suffix in('.png','.json','.txt'):sources[p.relative_to(H).as_posix()]=sha(p.read_bytes())
    for name in ['prepare_ultimate_dash_targets.py','register_ultimate_dash_shot_probe.py','finalize_ultimate_dash_first_shots.py','finalize_ultimate_dash_bodies.py','register_dash93_barearm.py']:sources[name]=sha((H/name).read_bytes())
    manifest={'parent_sha256':PARENT,'rows':targetrows,'shot_and_effect_evidence':rows,'sources':sources,'policy':'새 전신/원화 팔만 사용. 새 노출 전완의 실제 공유와 재킷 원화 경계 표본을 등록하며 맨팔 알파를 임의로 깎지 않음. 73/74는 원작9개 속도선·원 tile6만 재사용.','palette_changed':False,'runtime_verified':False,'candidate_only':True}
    write(o/'targets.json',manifest);write(o/'LOCK.json',{'target_manifest_sha256':sha((o/'targets.json').read_bytes()),'files':{p.name:sha(p.read_bytes())for p in sorted(o.glob('*.png'))},'sources':sources});print(json.dumps({'refs':len(full),'sources':len(sources),'lock':sha((o/'LOCK.json').read_bytes())}))
if __name__=='__main__':main()
