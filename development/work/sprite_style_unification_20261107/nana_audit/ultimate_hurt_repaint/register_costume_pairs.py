"""새 Ultimate 피격의 같은 머리·다리와 별도 의상 의미영역을 결합한다."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
Y,X=np.indices((384,384));Y-=160;X-=160
POLYS={
106:[(-5,-8),(-3,-8),(-3,-7),(4,-7),(6,-4),(8,5),(6,9),(1,10),(0,7),(-7,5),(-14,8),(-15,4),(-12,1),(-9,-5),(-6,-7)],
110:[(-3,-8),(2,-8),(4,-7),(8,-2),(11,5),(12,9),(8,12),(5,10),(3,4),(-1,3),(-5,5),(-13,3),(-14,-1),(-10,-5),(-7,-7),(-3,-7)],
233:[(-4,-11),(2,-12),(4,-10),(6,-7),(9,-4),(12,-1),(11,2),(6,1),(4,-1),(-4,-1),(-5,-3),(-11,-4),(-13,-7),(-13,-11),(-8,-11),(-6,-9),(-4,-9)],
234:[(-7,-17),(-4,-15),(-4,-12),(-1,-9),(3,-9),(5,-10),(9,-8),(12,-5),(13,-1),(11,2),(7,1),(5,0),(0,2),(-4,1),(-4,-3),(-3,-6),(-7,-7),(-10,-10),(-10,-13)]}

def foot234(s):
    # 원 눈/머리/몸 원점은 유지. 새 발목 아래 신발 두 개만 -1y.
    # y12는 새 원화의 발목 접속행이며 y13..18의 신발을12..17로 이동한다.
    t=s.copy();region=(X>=-12)&(X<=-2)&(Y>=12)&(Y<=18);t[region]=0;links=[]
    for y in range(13,19):
        for x in range(-12,-1):
            t[y+159,x+160]=s[y+160,x+160];links.append([x,y,x,y-1,int(s[y+160,x+160])])
    need(np.array_equal(t[~region],s[~region]),'발 이외 보존')
    return t,links

def main():
    cli=argparse.ArgumentParser();cli.add_argument('--version',choices=['v1','v2','v3','v4'],default='v4');args=cli.parse_args()
    out=D/f'costume_pair_probe_{args.version}';out.mkdir(exist_ok=False)
    parent=N/'rising_repaint/packed_ultimate_candidate_v1/PL02_U.ARC';a=Archive(parent.read_bytes());rows=[];records=[]
    need(digest(parent)=='4132738ac872750507538cd8d150e13a510422df81cea99b502e7371b6753cd9','부모 보호')
    for n,initial in POLYS.items():
        points=list(initial)
        if args.version in('v2','v3','v4'):
            if n==106:points=[(-5,-8),(-3,-8),(-3,-7),(4,-7),(6,-4),(8,5),(6,9),(1,10),(0,7),(-7,5),(-14,8),(-15,4),(-12,1),(-9,-6),(-6,-7)]
            if n==234:points=[(-7,-17),(-4,-15),(-4,-12),(-1,-9),(3,-9),(5,-10),(9,-8),(12,-5),(13,-1),(11,2),(7,1),(5,0),(0,2),(-5,1),(-6,-2),(-5,-4),(-3,-6),(-7,-7),(-10,-10),(-10,-13)]
        page='first'if n<200 else'extra';base=D/f'{page}_registered_v1'
        bp=base/f'before_{n:03}_registered_indices.png';ap=base/f'after_{n:03}_registered_indices.png'
        b=np.array(Image.open(bp));donor=np.array(Image.open(ap));links=[];arm_links=[];boundary=[]
        if n==234:b,links=foot234(b)
        if (args.version=='v2' and n in (110,234)) or (args.version in('v3','v4') and n==110):
            # 새 맨팔의 아래 전완/손만 원래 새 재킷 손목에 1px 좌상 정합.
            # 상완 시작/목·머리는 고정한다. 자르기·색채움 없이 같은 원화 이동.
            x0,y0,x1,y1=(6,2,14,13) if n==110 else (5,-4,14,4)
            src=donor.copy();take=(X>=x0)&(X<x1)&(Y>=y0)&(Y<y1)
            if args.version in('v3','v4'):
                take[:]=False
                for sy,l,r in [(2,7,10),(3,7,10),(4,7,10),(5,7,11),(6,7,12),(7,7,12),(8,7,12),(9,7,12),(10,9,12),(11,10,10)]:take[sy+160,l+160:r+161]=True
            donor[take]=0
            for y,x in np.argwhere(take):
                donor[y-1,x-1]=src[y,x]
                arm_links.append([int(x-160),int(y-160),int(x-161),int(y-161),int(src[y,x])])
        im=Image.new('L',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in points],fill=1);m=np.array(im)>0
        if args.version in('v3','v4') and n==234:
            # 후폼 원화의 뒷머리 끝 두 셀을 의상으로 오분류했던 영역.
            # 새 재킷 원화의 동일 머리 가닥을 유지하며 팔/피부는 건드리지 않는다.
            m[(X>=11)&(Y>=1)]=False
        if args.version in('v3','v4') and n==110:
            reg=json.loads((base/'registration.json').read_text('utf8'));q=next(q for q in reg['frames']if q['ref']==n and q['form']=='before')
            art=ROOT/reg['source_art_path'];need(digest(art)==reg['source_art_sha256'],'원화 해시')
            cell=Image.open(art).convert('RGBA').crop(q['source_crop']);ar=np.array(cell);alpha=ar[:,:,3].astype(np.float32)/255;rgb=ar[:,:,:3].astype(np.float32)
            pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[16:32]],np.float32)
            labs=np.empty(alpha.shape,np.uint8)
            for yy in range(len(labs)):labs[yy]=1+((rgb[yy,:,None,:]-pal[None,1:,:])**2).sum(2).argmin(1)
            votes=np.stack([np.array(Image.fromarray(np.where(labs==i,alpha,0).astype(np.float32),'F').resize((96,96),Image.Resampling.BOX))for i in range(1,16)])
            coverage=np.array(Image.fromarray(alpha,'F').resize((96,96),Image.Resampling.BOX))
            for x,y in [(-11,1),(8,9)]:
                sx,sy=x+48,y+48;cv=float(coverage[sy,sx]);vv=votes[:,sy,sx];v=int(vv.argmax()+1)
                need(.35<=cv<.5 and b[y+160,x+160]==0,'실제 원화 경계 확인')
                b[y+160,x+160]=v
                boundary.append({'world':[x,y],'source_art':art.relative_to(ROOT).as_posix(),'source_art_sha256':digest(art),'source_crop':q['source_crop'],'source_native_cell':[sx,sy],'alpha_coverage':cv,'palette_votes':[float(v)for v in vv],'winner':v,'manual_paint':False})
            if args.version=='v4':
                # 위팔 아래 음영과 연결된 후폼의 분홍 뒷머리 끝. 팔/의상이
                # 아닌 머리 소유이므로 새 before의 같은 머리 가닥을 유지한다.
                need(donor[166,165]==5 and b[166,165]==0,'뒤머리 끝 의미 출처')
                m[166,165]=False
        common=b.copy();common[b==15]=13
        after=common.copy();after[m]=donor[m]
        # 이마를 감싸는 새 손은 의상 색과 무관한 공통 부위로 유지한다.
        hand=np.zeros_like(m)
        if n==234:hand=(X>=-5)&(X<=0)&(Y>=-19)&(Y<=-15)&np.isin(b,(10,11,12,13))
        after[hand]=common[hand]
        outside=(after>0)&(b==0)
        need(np.array_equal(after[~m],common[~m]),'머리/다리 공통부')
        for name,z in [('before',b),('after',after),('donor',donor),('costume_mask',m.astype(np.uint8)*255),('common_hand_mask',hand.astype(np.uint8)*255),('outside_mask',outside.astype(np.uint8)*255)]:Image.fromarray(z).save(out/f'{name}_{n:03}.png')
        records.append({'ref':n,'before_source':bp.relative_to(ROOT).as_posix(),'before_source_sha256':digest(bp),'after_source':ap.relative_to(ROOT).as_posix(),'after_source_sha256':digest(ap),
            'costume_polygon':points,'source_foot_links':links,'source_forearm_links':arm_links,'source_boundary_cells':boundary,'common_gray15_to_after13_count':int((b==15).sum()),'new_outside_before':[[int(x-160),int(y-160),int(after[y,x])]for y,x in np.argwhere(outside)],
            'components_before':int(label(b>0,np.ones((3,3)))[1]),'components_after':int(label(after>0,np.ones((3,3)))[1]),'old_pixels_copied':0,'alpha_clipped':False,
            'before_sha256':sha(b.tobytes()),'after_sha256':sha(after.tobytes())})
        rows.append((f'costume {n}',[('after idle',a.composite(0)[0]),('new jacket body',a.rgba(b,16)),('new after source',a.rgba(donor)),('new common body',a.rgba(after))]))
    for i in range(0,4,2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',7)
    write(out/'manifest.json',{'parent_sha256':digest(parent),'frames':records,'scope':'신규 원화 의상 의미경계 초기안. 새 몸체만 사용하고 의상외 머리/다리 공유. 알파 교집합 자르기·단색 채움 없음. 바깥 픽셀은 그대로 기록하여 후속 등록 검토한다.','native_packed':False,'runtime_verified':False})
    print(json.dumps([{'ref':r['ref'],'outside':r['new_outside_before'],'components':[r['components_before'],r['components_after']]}for r in records]))
if __name__=='__main__':main()
