"""실제 생성원화 등록과 공통층 출처를 재구성하고 패킹 재현/입력거부를 확인한다."""
from pathlib import Path
import sys,json,copy
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint'),str(D)]
from preview_restore import Archive,sha,digest,write,need
from register_page import register
from pack_native import build,PARENT,BEFORE,PBS,REFS
Y,X=np.indices((384,384));Y-=160;X-=160
def spans(mask):
    x=np.flatnonzero(mask)
    return []if not len(x)else np.split(x,np.flatnonzero(np.diff(x)>1)+1)
def main():
    out=D/'packed_hurt_candidate_v1';lock=json.loads((out/'INPUT_FROZEN.json').read_text('utf8'))
    for q in lock['files']:need(digest(ROOT/q['path'])==q['sha256'],q['path'])
    a=Archive(PARENT.read_bytes());registered={};source_checks=[]
    for page in ('first','extra'):
        m=json.loads((D/f'{page}_registered_v1/registration.json').read_text('utf8'));im=Image.open(ROOT/m['source_art_path']).convert('RGBA')
        need(digest(ROOT/m['source_art_path'])==m['source_art_sha256'],'생성 원화 해시')
        for q in m['frames']:
            start=16 if q['mask']else 0
            pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32)
            z=np.zeros((384,384),np.uint8);z[112:208,112:208]=register(im.crop(q['source_crop']),(96,96),pal,'area_vote')
            dx,dy=q['translation'];z=np.roll(z,(dy,dx),(0,1));need(sha(z.tobytes())==q['native_sha256'],'전체 고정셀 재등록')
            need(np.array_equal(z,np.array(Image.open(D/f'{page}_registered_v1'/f'{q["form"]}_{q["ref"]:03}_registered_indices.png'))),'저장 원화 등록')
            registered[q['ref'],q['form']]=z;source_checks.append({'ref':q['ref'],'form':q['form'],'sha256':sha(z.tobytes()),'source':m['source_art_path'],'translation':q['translation']})
    common={}
    for n,start,xmax,foot in((106,10,2,20),(110,7,1,17),(233,5,5,12),(234,5,2,15)):
        b,f=registered[n,'base'],registered[n,'fourth'];nb,nf=b.copy(),f.copy();region=(Y>=start)&(X<=xmax)
        for y in range(start+160,190):
            bs,fs=spans((b[y]>0)&region[y]),spans((f[y]>0)&region[y])
            if len(bs)!=len(fs):continue
            for sb,sf in zip(bs,fs):
                if np.array_equal(sb,sf)or abs(float(sb.mean()-sf.mean()))>1.5 or min(len(sb),len(sf))/max(len(sb),len(sf))<.5:continue
                dst=sb if y>=160+foot else sf
                for old,new,s in((b,nb,sb),(f,nf,sf)):
                    if np.array_equal(s,dst):continue
                    ix=s[np.rint(np.linspace(0,len(s)-1,len(dst))).astype(int)];new[y,s]=0;new[y,dst]=old[y,ix]
        for form,z in(('base',nb),('fourth',nf)):
            need(np.array_equal(z,np.array(Image.open(D/'common_legs_probe_v1'/f'{form}_{n:03}_indices.png'))),'같은 원화 행 표본 재구성')
            common[n,form]=z
    jm=json.loads((D/'joint_layers_probe_v1/manifest.json').read_text('utf8'));layer_checks=[]
    for q in jm['frames']:
        n=q['ref'];spec=q['owner_geometry'];b,f=common[n,'base'],common[n,'fourth'];full=np.where(f,f,b).astype(np.uint8)
        ex,ey=spec['eye'];owner=np.full(b.shape,6,np.uint8);owner[(Y>=spec['lower'])|((X>=ex+13)&(Y>=ey+5))]=8
        owner[(Y<ey+6)&((X>=ex-3)|(Y<ey-2))]=5
        p=Image.new('L',(384,384));ImageDraw.Draw(p).polygon([(x+160,y+160)for x,y in spec['arm']],fill=1);owner[np.array(p)>0]=7
        x0,y0,x1,y1=spec['right_hand'];owner[np.isin(full,(10,11,12,13))&(X>=x0)&(X<x1)&(Y>=y0)&(Y<y1)]=7
        pd=np.array([a.words[i]!=a.words[16+i]for i in range(16)])[full];change=((full!=b)|((f>0)&pd))&(full>0)
        ls={0:b,**{k:np.where(change&(owner==k),full,0).astype(np.uint8)for k in PBS[1:]}}
        for pb,z in ls.items():
            need(sha(z.tobytes())==q['layer_hashes'][str(pb)],'의미층 재구성')
            need(np.array_equal(z,np.array(Image.open(D/'final_targets_v1'/f'layer{pb}_{n:03}.png'))),'최종 몸체 층 보존')
            layer_checks.append([n,pb,sha(z.tobytes())])
    am=json.loads((D/'aura_contact_probe_v2/manifest.json').read_text('utf8'));aura_checks=[]
    for q in am['frames']:
        n=q['ref'];original=np.array(Image.open(D/'effect_probe_v1'/f'effect_{n:03}_bank0.png'));fx=np.zeros_like(original);sources=set()
        for link in q['source_links']:
            x,y=link['world'];sx,sy=link['source_world'];need((sx,sy)not in sources,'원 오라 중복 소비');sources.add((sx,sy))
            need(original[sy+160,sx+160]==link['index'],'원오라 색');need(fx[y+160,x+160]==0,'오라 목적 중복');fx[y+160,x+160]=link['index']
        need(len(sources)==np.count_nonzero(original),'모든 원 오라 소비');need(np.array_equal(fx,np.array(Image.open(D/'aura_contact_probe_v2'/f'effect_{n:03}_indices.png'))),'최종 오라')
        body=np.array(Image.open(D/'final_targets_v1/layer0_234.png'));need(np.array_equal(np.where(fx,fx,body),np.array(Image.open(D/'final_targets_v1'/f'layer0_{n:03}.png'))),'몸/오라 결합')
        aura_checks.append({'ref':n,'source_pixels':len(sources),'no_duplicate_sources':True,'effect_sha256':sha(fx.tobytes())})
    write(out/'source_reconstruction.json',{'passed':True,'asset_sha256':digest(out/'PL00_U.ARC'),'input_files_exact':len(lock['files']),'fixed_cell_registrations':source_checks,'common_body_registrations':8,'semantic_layers':layer_checks,'aura':aura_checks,'scope':'생성2장→고정셀8개→같은 원화 행 공통정합→20몸체층 및 기존 오라 일대일 출처 재구성. 효과 파생은 별도 독립 reader와 패킹/원타일 검사에 연결. 새 그림 생성·실기 없음.'})
    meta=json.loads((D/'final_targets_v1/manifest.json').read_text('utf8'));targets={(n,pb):np.array(Image.open(D/'final_targets_v1'/f'layer{pb}_{n:03}.png'))for n in REFS for pb in PBS}
    parent=PARENT.read_bytes();result,report=build(parent,targets,meta);need(result==(out/'PL00_U.ARC').read_bytes(),'동일 부모→최종 ARC 재현')
    failures=[]
    def reject(name,p,t,m):
        try:build(p,t,m)
        except (ValueError,KeyError,AssertionError) as e:failures.append({'case':name,'rejected':True,'reason':str(e)})
        else:raise ValueError('거부 실패 '+name)
    reject('부모 해시 변경',bytes([parent[0]^1])+parent[1:],targets,meta)
    bad=dict(targets);del bad[106,0];reject('필수 목표 누락',parent,bad,meta)
    bad=dict(targets);bad[0,0]=targets[106,0];reject('비대상 참조 추가',parent,bad,meta)
    bad=dict(targets);bad[106,0]=bad[106,0][:-1];reject('캔버스 크기',parent,bad,meta)
    bad=dict(targets);bad[106,0]=bad[106,0].astype(np.int16);reject('색인 자료형',parent,bad,meta)
    bad=dict(targets);bad[106,0]=bad[106,0].copy();bad[106,0][0,0]=48;reject('색인 범위',parent,bad,meta)
    bad=dict(targets);bad[106,0]=bad[106,0].copy();bad[106,0][0,0]=1;reject('목표 해시 변경',parent,bad,meta)
    bm=copy.deepcopy(meta);bm['targets']['106']['0']='0'*64;reject('매니페스트 해시 변경',parent,targets,bm)
    write(out/'reproduction.json',{'passed':True,'asset_sha256':sha(result),'parent_asset_sha256':BEFORE,'reproduction_exact':True,'rejected_inputs':failures,'runtime_verified':False})
    print(json.dumps({'source_layers':len(layer_checks),'input_files':len(lock['files']),'reproduced':sha(result),'rejected':len(failures)}))
if __name__=='__main__':main()
