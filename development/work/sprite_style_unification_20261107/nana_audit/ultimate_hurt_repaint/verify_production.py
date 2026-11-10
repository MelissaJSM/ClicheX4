"""고정 생성원화8 등록·의상/손발/경계 표본·효과65층 및 패킹 재현 검사."""
from pathlib import Path
import sys,json,copy
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import binary_dilation
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint'),str(D)]
from preview_restore import Archive,sha,digest,write,need
from register_page import register
from pack_native import build,PARENT,BEFORE,PBS,REFS
from src.psx_player import compose_indices
from pack_cycle import raw
Y,X=np.indices((384,384));Y-=160;X-=160
def load(folder,name):return np.array(Image.open(D/folder/name))
def full(a,n):
    z=a.layer(n)[0].copy()
    for pb in(8,5,7,6):
        p=a.layer(n,pb)[0];z[p>0]=p[p>0]
    return z
def main():
    out=D/'packed_hurt_candidate_v1';lock=json.loads((out/'INPUT_FROZEN.json').read_text('utf8'))
    for q in lock['files']:need(digest(ROOT/q['path'])==q['sha256'],q['path'])
    a=Archive(PARENT.read_bytes());registered={};sources=[]
    for page in('first','extra'):
        m=json.loads((D/f'{page}_registered_v1/registration.json').read_text('utf8'));im=Image.open(ROOT/m['source_art_path']).convert('RGBA')
        for q in m['frames']:
            start=16 if q['mask']else 0;pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32)
            z=np.zeros((384,384),np.uint8);z[112:208,112:208]=register(im.crop(q['source_crop']),(96,96),pal,'area_vote')
            dx,dy=q['translation'];z=np.roll(z,(dy,dx),(0,1));need(sha(z.tobytes())==q['native_sha256'],'전체 고정셀 등록')
            need(np.array_equal(z,load(f'{page}_registered_v1',f'{q["form"]}_{q["ref"]:03}_registered_indices.png')),'저장 등록')
            registered[q['ref'],q['form']]=z;sources.append({'ref':q['ref'],'form':q['form'],'source_art_sha256':m['source_art_sha256'],'native_sha256':sha(z.tobytes()),'translation':q['translation']})
    cm=json.loads((D/'costume_pair_probe_v4/manifest.json').read_text('utf8'));bodies={};common=[];boundaries=[]
    for q in cm['frames']:
        n=q['ref'];b=registered[n,'before'].copy();donor=registered[n,'after'].copy()
        if q['source_foot_links']:
            before=b.copy();region=(X>=-12)&(X<=-2)&(Y>=12)&(Y<=18);b[region]=0
            for sx,sy,x,y,v in q['source_foot_links']:need(before[sy+160,sx+160]==v,'신발 출처');b[y+160,x+160]=v
            need(np.array_equal(b[~region],before[~region]),'신발 외 보존')
        if q['source_forearm_links']:
            before=donor.copy()
            for sx,sy,x,y,v in q['source_forearm_links']:need(before[sy+160,sx+160]==v,'전완 출처');donor[sy+160,sx+160]=0
            for sx,sy,x,y,v in q['source_forearm_links']:donor[y+160,x+160]=v
        for cell in q['source_boundary_cells']:
            art=Image.open(ROOT/cell['source_art']).convert('RGBA').crop(cell['source_crop']);ar=np.array(art);alpha=ar[:,:,3].astype(np.float32)/255;rgb=ar[:,:,:3].astype(np.float32)
            pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[16:32]],np.float32)
            labels=np.empty(alpha.shape,np.uint8)
            for yy in range(len(labels)):labels[yy]=1+((rgb[yy,:,None,:]-pal[None,1:,:])**2).sum(2).argmin(1)
            votes=np.stack([np.array(Image.fromarray(np.where(labels==i,alpha,0).astype(np.float32),'F').resize((96,96),Image.Resampling.BOX))for i in range(1,16)])
            coverage=np.array(Image.fromarray(alpha,'F').resize((96,96),Image.Resampling.BOX));sx,sy=cell['source_native_cell'];v=int(votes[:,sy,sx].argmax()+1)
            need(v==cell['winner'] and np.allclose(votes[:,sy,sx],cell['palette_votes'],atol=0,rtol=0),'원화 실제색 투표')
            need(float(coverage[sy,sx])==cell['alpha_coverage'],'경계 실제알파');x,y=cell['world'];b[y+160,x+160]=v;boundaries.append(cell)
        mask=Image.new('L',(384,384));ImageDraw.Draw(mask).polygon([(x+160,y+160)for x,y in q['costume_polygon']],fill=1);mask=np.array(mask)>0
        if n==234:mask[(X>=11)&(Y>=1)]=False
        if n==110:mask[166,165]=False
        shared=b.copy();shared[b==15]=13;after=np.where(mask,donor,shared).astype(np.uint8)
        hand=(X>=-5)&(X<=0)&(Y>=-19)&(Y<=-15)&np.isin(b,(10,11,12,13))if n==234 else np.zeros(b.shape,bool)
        after[hand]=shared[hand]
        for name,z in [('before',b),('after',after),('donor',donor),('costume_mask',mask.astype(np.uint8)*255),('common_hand_mask',hand.astype(np.uint8)*255)]:need(np.array_equal(z,load('costume_pair_probe_v4',f'{name}_{n:03}.png')),'의상/의미 경계 '+name)
        need(not np.any((after>0)&(b==0)),'후폼 경계 밖 픽셀')
        bodies[n]={0:after,5:np.where((b!=after)|(b==15),b,0).astype(np.uint8),**{pb:np.zeros_like(b)for pb in(6,7,8)}}
        for pb,z in bodies[n].items():need(np.array_equal(z,load('body_layers_probe_v1',f'layer{pb}_{n:03}.png')),'몸체층 재구성')
        common.append({'ref':n,'foot_source_links':len(q['source_foot_links']),'forearm_source_links':len(q['source_forearm_links']),'before':sha(b.tobytes()),'after':sha(after.tobytes())})
    targets={n:{pb:z.copy()for pb,z in ls.items()}for n,ls in bodies.items()}
    relation=json.loads((N.parent/'zero_audit/nana_ultimate_hurt_relations01/report.json').read_text('utf8'));fxproof=[]
    for q in relation['semantic_effect_comparisons']:
        n,core=q['ref'],q['body_ref'];parts=[{**p,'page':p['flags']&3,'unknown_flags':p['flags']&48,'flip_x':bool(p['flags']&64),'flip_y':bool(p['flags']&128),'index':i}for i,p in enumerate(q['effect_records'])]
        buf,size,box,_=compose_indices(raw(a,0,n),a.banks[0]['frames'][n]['tile_count'],{'parts':parts},allowed_cluts={0,1,2,3});v=np.frombuffer(buf,np.uint8).reshape(size[1],size[0]);fx=np.zeros((384,384),np.uint8);y,x=np.nonzero(v);fx[y+box[1]+160,x+box[0]+160]=v[y,x]
        need(np.array_equal(fx,load('effect_probe_v1',f'effect_{n:03}.png')),'실제 효과 레코드 재구성');ls={pb:z.copy()for pb,z in bodies[core].items()}
        for pb in ((0,5)if n in(107,108)else(0,)):ls[pb]=np.where(fx,fx,ls[pb]).astype(np.uint8)
        targets[n]=ls;fxproof.append({'ref':n,'pixels':int(np.count_nonzero(fx)),'source_records':len(parts),'same_proven_effect_both_forms_new_policy':n in(107,108)})
    flashes=[]
    for b in [bodies[106][0],load('costume_pair_probe_v4','before_106.png')]:
        z=np.zeros_like(b);z[binary_dilation(b>0)]=9;z[b>0]=13;flashes.append(z)
    targets[109]={0:flashes[0],5:np.where(flashes[0]!=flashes[1],flashes[1],0).astype(np.uint8),**{pb:np.zeros_like(z)for pb in(6,7,8)}}
    history=Archive((ROOT/'work/overhaul_20261105/sprites/ver_rin_nana/baseline/PL02_U.ARC').read_bytes());oldmask=history.layer(110)[0]>0;newbody=load('costume_pair_probe_v4','before_110.png')
    for n in(112,113,114):
        res=history.layer(n)[0]%16;res=res.copy();res[binary_dilation(oldmask,iterations=2)]=0
        if n==114:res[np.isin(res,(3,5))]=0
        need(np.array_equal(res,load('effect_probe_v1',f'residual_{n:03}.png')),'과거 외부효과')
        computed=[]
        for body in(full(history,110),newbody):
            z=res.copy();m=body>0
            if n==112:z[binary_dilation(m)]=6;z[m]=14
            elif n==113:z[binary_dilation(m)]=1
            else:z[binary_dilation(m)]=1;z[m]=3;z[np.isin(body%16,(1,2,4,8,15))&m]=5;z[np.isin(body%16,(6,9))&m]=1
            computed.append(np.where(z,z+32,0).astype(np.uint8))
        need(np.array_equal(computed[0],a.layer(n)[0]),'기존 역사 규칙 exact')
        targets[n]={0:computed[1],**{pb:np.zeros_like(z)for pb in PBS[1:]}}
    am=json.loads((D/'aura_contact_probe_v2/registration.json').read_text('utf8'));auraproof=[]
    for q in am['frames']:
        n=q['ref'];body=full(a,234);source=np.where(body==0,full(a,n),0).astype(np.uint8);fx=np.zeros_like(source);seen=set()
        need(np.array_equal(source,load('effect_probe_v1',f'effect_{n:03}.png')),'현재 확실한 오라 출처')
        for sx,sy,x,y,v in q['source_links']:
            need((sx,sy)not in seen and source[sy+160,sx+160]==v,'오라 출처/중복');seen.add((sx,sy));need(fx[y+160,x+160]==0,'오라 목적중복');fx[y+160,x+160]=v
        need(len(seen)==np.count_nonzero(source),'원오라 전체소비');need(np.array_equal(fx,load('aura_contact_probe_v2',f'effect_{n:03}.png')),'오라 정합 exact')
        ls={pb:z.copy()for pb,z in bodies[234].items()}
        for pb in(0,5):ls[pb]=np.where(fx,fx,ls[pb]).astype(np.uint8)
        targets[n]=ls;auraproof.append({'ref':n,'pixels':len(seen),'source_links_exact':True})
    flat={};meta=json.loads((D/'final_targets_v1/manifest.json').read_text('utf8'))
    for n,ls in targets.items():
        for pb,z in ls.items():need(np.array_equal(z,load('final_targets_v1',f'layer{pb}_{n:03}.png')),'최종65층 재구성');flat[n,pb]=z
    write(out/'source_reconstruction.json',{'passed':True,'candidate_sha256':digest(out/'PL02_U.ARC'),'input_files_verified':len(lock['files']),'fixed_cell_registrations':sources,'common_body_reconstruction':common,'actual_source_boundary_cells':boundaries,'effect_records':fxproof,'aura':auraproof,'target_layers_reconstructed':len(flat),'scope':'제작자 원화2장 고정셀8 등록부터 의미경계·새손/신발 출처 정합·효과 역사규칙·오라 일대일 이동 및65층 재구성. 별도 독립검사·원MIPS·실기와 구분.','runtime_verified':False})
    parent=PARENT.read_bytes();rejected=[]
    def reject(name,p,t,m):
        try:build(p,t,m)
        except (ValueError,KeyError,AssertionError)as e:rejected.append({'case':name,'rejected':True,'reason':str(e)})
        else:raise ValueError('거부 실패 '+name)
    reject('부모해시',bytes([parent[0]^1])+parent[1:],flat,meta)
    bad=dict(flat);del bad[106,0];reject('목표누락',parent,bad,meta)
    bad=dict(flat);bad[0,0]=flat[106,0];reject('비대상추가',parent,bad,meta)
    bad=dict(flat);bad[106,0]=bad[106,0][:-1];reject('크기',parent,bad,meta)
    bad=dict(flat);bad[106,0]=bad[106,0].astype(np.int16);reject('자료형',parent,bad,meta)
    bad=dict(flat);bad[106,0]=bad[106,0].copy();bad[106,0][0,0]=48;reject('색인범위',parent,bad,meta)
    bad=dict(flat);bad[106,0]=bad[106,0].copy();bad[106,0][0,0]=1;reject('목표해시',parent,bad,meta)
    bm=copy.deepcopy(meta);bm['targets']['106']['0']='0'*64;reject('매니페스트해시',parent,flat,bm)
    result,report=build(parent,flat,meta);need(result==(out/'PL02_U.ARC').read_bytes(),'부모부터 ARC 재현')
    write(out/'reproduction.json',{'passed':True,'candidate_sha256':sha(result),'parent_sha256':BEFORE,'reproduction_exact':True,'same_process_rebuild':True,'rejected_inputs':rejected,'full_rgba_rechecked':report['rgba_combinations'],'runtime_verified':False})
    print(json.dumps({'source_layers':len(flat),'input_files':len(lock['files']),'reproduced':sha(result),'rejected':len(rejected)}))
if __name__=='__main__':main()
