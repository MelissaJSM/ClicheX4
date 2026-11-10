"""생성원화12→권총→의상/5경계→접지→35층의 제작 출처 재구성."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint')]
from preview_restore import Archive,sha,digest,write,need
from register_page import register
Y,X=np.indices((384,384));Y-=160;X-=160
read=lambda p:json.loads(p.read_text('utf8'))
png=lambda p:np.array(Image.open(p))

def main():
    a=Archive((N/'ultimate_run_repaint/packed_run_candidate_v1/PL02_U.ARC').read_bytes());out=D/'packed_ultimate_candidate_v1';fixed={};proof=[]
    for folder in('ultimate_air_registered_v1','ultimate_charge_registered_v3','ultimate_recovery_registered_v1'):
        meta=read(D/folder/'registration.json');src=ROOT/meta['source_art_path'];need(digest(src)==meta['source_art_sha256'],'원화 해시');im=Image.open(src).convert('RGBA')
        for q in meta['frames']:
            n,form=q['ref'],q['form'];off=16 if form=='before'else 0
            pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[off:off+16]],np.float32)
            z=np.zeros((384,384),np.uint8);z[112:208,112:208]=register(im.crop(tuple(q['crop'])),(96,96),pal,'area_vote')
            dx,dy=q['whole_translation'];z=np.roll(z,(dy,dx),(0,1))
            need(np.array_equal(z,png(D/folder/f'{form}_{n:03}_registered_indices.png')),'전체 셀 원화 등록')
            fixed[n,form]=z;proof.append({'ref':n,'form':form,'source_art_sha256':digest(src),'fixed_registration_exact':True})
    wm=read(D/'ultimate_weapon_probe_v1/manifest.json');canonical=read(D/'canonical_weapon_probe_v2/manifest.json');weapons={}
    for q in wm['frames']:
        n,form=q['ref'],q['form'];z=fixed[n,form].copy();case=np.zeros_like(z);gx,top=q['case_bbox']
        for sx,sy,v in canonical['canonical_source_texels']:
            need(int(a.layer(85)[0][sy+160,sx+160])==v,'85색인');case[sx+top+22+160,-sy+gx-9+160]=v
        hand=(X>=gx-4)&(X<=gx+3)&(Y>=top+4)&(Y<=top+11)&np.isin(z,[10,11,12,13])
        first=int(np.nonzero(hand)[0].min()-160);remove=(X>=gx-4)&(X<=gx+3)&(Y>=top-3)&(Y<=first)&(z>0)&~hand
        z[remove]=0;v=(case>0)&~hand;z[v]=case[v]
        need(np.array_equal(z,png(D/f'ultimate_weapon_probe_v1/{form}_{n:03}_indices.png')),'권총/손 등록')
        need(np.array_equal(case,png(D/f'ultimate_weapon_probe_v1/{form}_{n:03}_case.png')),'90도 정본');weapons[n,form]=z
    boundary=read(D/'ultimate_boundary_audit_v2/report.json')['source_cells']
    for q in boundary:
        im=Image.open(ROOT/q['source_art']).convert('RGBA').crop(tuple(q['source_crop']));arr=np.array(im);rgb=arr[:,:,:3].astype(np.float32);alpha=arr[:,:,3].astype(np.float32)/255
        pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[16:32]],np.float32)
        labels=np.empty(alpha.shape,np.uint8)
        for y in range(len(labels)):labels[y]=1+((rgb[y,:,None,:]-pal[None,1:,:])**2).sum(2).argmin(1)
        votes=np.stack([np.array(Image.fromarray(np.where(labels==i,alpha,0).astype(np.float32),'F').resize((96,96),Image.Resampling.BOX))for i in range(1,16)])
        sx,sy=q['source_native_cell'];need(int(votes[:,sy,sx].argmax()+1)==q['source_palette_winner'],'실제 경계 원화 투표')
        need(np.allclose(votes[:,sy,sx],q['source_palette_votes'],atol=1e-7),'경계 투표 값')
    costume=read(D/'ultimate_costume_pair_probe_v6/registration.json');bodies={}
    for q in costume['frames']:
        n=q['ref'];b=weapons[n,'before'].copy();donor=weapons[n,'after'];canvas=Image.new('L',(384,384));ImageDraw.Draw(canvas).polygon([(x+160,y+160)for x,y in q['polygon']],fill=255);mask=np.array(canvas)>0
        for row in q['new_before_source_boundary_cells']:
            x,y=row['world'];need(b[y+160,x+160]==0,'경계 투명');b[y+160,x+160]=row['source_palette_winner']
        if q['additional_clothing_region'] is not None:
            x0,y0,x1,y1=q['additional_clothing_region'];mask|=(X>=x0)&(X<=x1)&(Y>=y0)&(Y<=y1)
        for x,y,bv,av in q['authored_after_shoulder_edge_cells']:
            need(b[y+160,x+160]==bv and donor[y+160,x+160]==av,'100옷깃 실제 원화');mask[y+160,x+160]=True
        need(np.array_equal(mask,png(D/f'ultimate_costume_pair_probe_v6/mask_{n:03}.png')>0),'의미마스크')
        case=png(D/f'ultimate_weapon_probe_v1/before_{n:03}_case.png');hand=png(D/f'ultimate_weapon_probe_v1/before_{n:03}_hand_mask.png')>0
        x0,y0,x1,y1=q['far_hand_box'];far=(X>=x0)&(X<x1)&(Y>=y0)&(Y<y1)&np.isin(b,[10,11,12,13]);protected=(case>0)|hand|far
        expected=b.copy();expected[b==15]=q['palette15_gray_mapping'];after=expected.copy();after[mask]=donor[mask];after[protected]=expected[protected]
        for form,z in(('before',b),('after',after)):
            need(np.array_equal(z,png(D/f'ultimate_costume_pair_probe_v6/{form}_{n:03}.png')),'의상 재구성');bodies[n,form]=z
    feet=read(D/'ultimate_ground_feet_probe_v1/registration.json')
    for q in feet['frames']:
        form=q['form'];s=bodies[231,form];need(np.array_equal(s,png(ROOT/q['source'])),'231역사 donor 동일');z=s.copy()
        for x0,x1 in((-18,-9),(7,15)):z[(X>=x0)&(X<x1)&(Y>=20)&(Y<=23)]=0
        for sx,sy,tx,ty,v in q['source_to_target']:need(int(s[sy+160,sx+160])==v,'접지 원표본');z[ty+160,tx+160]=v
        for n in(231,232):need(np.array_equal(z,png(D/f'ultimate_ground_feet_probe_v1/{form}_{n:03}.png')),'접지 재구성');bodies[n,form]=z
    targets=read(D/'ultimate_layers_probe_v2/manifest.json');count=0
    for q in targets['frames']:
        n=q['ref'];b,after=bodies[n,'before'],bodies[n,'after'];overlay=np.where((b!=after)|(b==15),b,0).astype(np.uint8)
        for pb,z in((0,after),(5,overlay),(6,np.zeros_like(b)),(7,np.zeros_like(b)),(8,np.zeros_like(b))):need(np.array_equal(z,png(D/f'ultimate_layers_probe_v2/layer{pb}_{n:03}.png')),'35층 재구성');count+=1
    write(out/'source_reconstruction.json',{'passed':True,'candidate_sha256':digest(out/'PL02_U.ARC'),'generated_full_cell_registrations':proof,'authored_boundary_votes_checked':len(boundary),'canonical_weapons_reconstructed':len(weapons),'costume_bodies_reconstructed':12,'grounded_body_copies':4,'layers_reconstructed':count,'shared_registration_helper':(N/'base_run_repaint/register_page.py').relative_to(ROOT).as_posix(),'shared_registration_helper_sha256':digest(N/'base_run_repaint/register_page.py'),'scope':'제작자 재구성 검사. 원화12의 고정셀 양자화부터 중간 의미영역·실제표본5·권총·접지·최종35층을 다시 계산. 독립감사/미술·게임 검증과 구분.','runtime_verified':False})
    print(json.dumps({'passed':True,'source_full_bodies':len(fixed),'layers':count}))
if __name__=='__main__':main()
