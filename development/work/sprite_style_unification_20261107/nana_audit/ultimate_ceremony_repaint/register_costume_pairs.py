"""등장 원화의 의상 의미영역 초기 등록. 알파 교집합으로 자르지 않는다."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(D)]
from preview_restore import Archive,digest,sha,write,need,helper
from make_semantic_grids import path
POLYS={
133:[(-7,1),(-3,1),(-1,2),(3,1),(5,1),(9,4),(11,7),(12,11),(12,14),(9,15),(2,15),(1,12),(-1,11),(-2,9),(-4,8),(-7,6),(-9,7),(-10,10),(-14,13),(-17,13),(-17,10),(-13,6),(-9,3)],
135:[(-8,-9),(-4,-9),(-2,-8),(0,-9),(3,-9),(5,-6),(6,-2),(6,3),(5,6),(3,6),(3,4),(-1,4),(-3,5),(-6,4),(-8,5),(-11,5),(-11,0),(-10,-4),(-11,-5),(-12,-7),(-11,-9)],
136:[(-11,-9),(-9,-9),(-8,-6),(-6,-6),(-6,-8),(-4,-8),(-3,-7),(0,-8),(3,-8),(5,-4),(6,-2),(8,0),(8,5),(6,6),(4,5),(2,3),(-1,4),(-4,4),(-6,4),(-7,2),(-9,1),(-10,-3),(-12,-5),(-12,-8)],
137:[(-14,-16),(-12,-16),(-11,-13),(-10,-11),(-8,-10),(-5,-9),(-2,-10),(1,-10),(3,-10),(5,-7),(6,-5),(8,-3),(9,-1),(12,0),(14,2),(13,4),(9,5),(7,3),(4,4),(1,4),(-1,3),(-5,2),(-7,1),(-7,-4),(-10,-5),(-12,-8),(-14,-11)]}
def main():
    cli=argparse.ArgumentParser();cli.add_argument('--version',choices=['v1','v2','v3'],default='v3');args=cli.parse_args()
    p=N/'ultimate_hurt_repaint/packed_hurt_candidate_v1/PL02_U.ARC';need(digest(p)=='c9e68442829a7f149ae86317c88172e27dbce545e454687b98310fad28ef83a5','부모');a=Archive(p.read_bytes())
    out=D/f'costume_pair_probe_{args.version}';out.mkdir(exist_ok=False);records=[];rows=[]
    for n,points in POLYS.items():
        bp,ap=path('before',n),path('after',n);b=np.array(Image.open(bp));donor=np.array(Image.open(ap));boundary=[]
        if args.version in('v2','v3') and n in(133,135):
            reg=json.loads((D/'first_registered_v2/registration.json').read_text('utf8'));q=next(q for q in reg['frames']if q['ref']==n and q['form']=='before');art=ROOT/reg['source_art_path'];need(digest(art)==reg['source_art_sha256'],'원화 출처')
            ar=np.array(Image.open(art).convert('RGBA').crop(q['source_crop']));alpha=ar[:,:,3].astype(np.float32)/255;rgb=ar[:,:,:3].astype(np.float32);pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[16:32]],np.float32);labs=np.empty(alpha.shape,np.uint8)
            for yy in range(len(labs)):labs[yy]=1+((rgb[yy,:,None,:]-pal[None,1:,:])**2).sum(2).argmin(1)
            votes=np.stack([np.array(Image.fromarray(np.where(labs==i,alpha,0).astype(np.float32),'F').resize((96,96),Image.Resampling.BOX))for i in range(1,16)]);coverage=np.array(Image.fromarray(alpha,'F').resize((96,96),Image.Resampling.BOX))
            cells=[(-9,3),(-14,8),(-15,9)]if n==133 else[(-9,-6),(-8,-5),(-8,-4)]
            for x,y in cells:
                sx,sy=x+48,y+48;cv=float(coverage[sy,sx]);vv=votes[:,sy,sx];value=int(vv.argmax()+1);need(.1<cv<.5 and value==1 and b[y+160,x+160]==0,'실제 새 소매 그늘 경계')
                b[y+160,x+160]=value;boundary.append({'world':[x,y],'source_art':art.relative_to(ROOT).as_posix(),'source_art_sha256':digest(art),'source_crop':q['source_crop'],'source_native_cell':[sx,sy],'alpha_coverage':cv,'palette_votes':[float(v)for v in vv],'winner':value,'manual_paint':False,'status':'정합 후보: 원화의 얇은 경계 표본 등록, 최종 미술검토 전'})
        common=b.copy();common[b==15]=13
        im=Image.new('L',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in points],fill=1);m=np.array(im)>0
        if args.version in('v2','v3') and n==135:
            # 새 원화의 재킷 밑단/커프는 다리 공통부가 아니다. 이 부분은
            # 후폼 원화의 투명 영역까지 그대로 등록하여 소매 잔류를 없앤다.
            m[160:168,147:152]=True
            if args.version=='v3':
                # 재킷 앞단이 허벅지 위를 덮는 마지막 세 표본도 같은
                # 후폼 원화로 등록한다. 검정 밑단을 맨다리로 보존하지 않는다.
                for x,y in[(-7,5),(-7,6),(-8,7)]:m[y+160,x+160]=True
        after=common.copy();after[m]=donor[m]
        outside=(after>0)&(b==0);need(np.array_equal(after[~m],common[~m]),'새 공통 머리/다리')
        for tag,z in [('before',b),('after',after),('donor',donor),('costume_mask',m.astype(np.uint8)*255),('outside_mask',outside.astype(np.uint8)*255)]:Image.fromarray(z).save(out/f'{tag}_{n:03}.png')
        records.append({'ref':n,'before_source':bp.relative_to(ROOT).as_posix(),'before_source_sha256':digest(bp),'after_source':ap.relative_to(ROOT).as_posix(),'after_source_sha256':digest(ap),'costume_polygon':points,'source_boundary_cells':boundary,'costume_extra_box_world':[-13,0,-8,8]if args.version in('v2','v3') and n==135 else None,'costume_extra_points_world':[[-7,5],[-7,6],[-8,7]]if args.version=='v3' and n==135 else [],'common_gray15_to_after13_count':int((b==15).sum()),'before_sha256':sha(b.tobytes()),'after_sha256':sha(after.tobytes()),'new_outside_before':[[int(x-160),int(y-160),int(after[y,x])]for y,x in np.argwhere(outside)],'components_before':int(label(b>0,np.ones((3,3)))[1]),'components_after':int(label(after>0,np.ones((3,3)))[1]),'alpha_clipped':False,'old_pixels_copied':0})
        rows.append((f'costume {n}',[('after idle',a.composite(0)[0]),('new jacket body',a.rgba(b,16)),('new after donor',a.rgba(donor)),('semantic candidate',a.rgba(after))]))
    for i in range(0,4,2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',6)
    write(out/'manifest.json',{'parent_arc_sha256':digest(p),'frames':records,'scope':'새 before의 머리/다리와 새 after의 의상/팔만 의미영역 등록한 진단안. 바깥 픽셀을 지우지 않고 미해결로 기록. 효과 재합성·기술 패킹 전.','native_packed':False,'runtime_verified':False})
    print(json.dumps([{'ref':q['ref'],'outside':q['new_outside_before'],'components':[q['components_before'],q['components_after']]}for q in records]))
if __name__=='__main__':main()
