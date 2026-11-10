"""새 전후 의상의 의미영역 비교. 바깥팔을 기계적으로 자르지 않는 진단 후보."""
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
100:[(-11,-13),(-7,-13),(-6,-10),(-2,-10),(3,-11),(7,-8),(10,-4),(10,-1),(6,1),(0,2),(-5,0),(-6,-4),(-9,-5),(-11,-9)],
101:[(-11,-31),(-5,-31),(-5,-27),(-6,-19),(-4,-14),(2,-15),(7,-11),(11,-7),(11,-1),(8,0),(7,-2),(5,2),(-6,1),(-6,-7),(-7,-12),(-10,-17)],
102:[(-11,-26),(-5,-26),(-5,-20),(-6,-13),(-4,-7),(2,-7),(6,-4),(10,-1),(10,3),(6,5),(-4,5),(-6,1),(-7,-5),(-10,-12)],
103:[(-5,-8),(1,-8),(3,-10),(6,-16),(6,-20),(12,-20),(12,-14),(9,-8),(7,-3),(8,2),(6,4),(-4,4),(-6,0),(-9,0),(-9,-3),(-5,-3)],
104:[(-5,-11),(0,-11),(2,-13),(5,-22),(5,-28),(11,-28),(11,-22),(9,-13),(6,-9),(7,-2),(6,1),(-3,1),(-5,-2),(-9,-3),(-10,-6),(-5,-6)],
231:[(-11,-23),(-5,-23),(-5,-17),(-6,-12),(-4,-6),(1,-7),(5,-5),(9,-2),(10,3),(6,4),(5,6),(-6,6),(-6,0),(-7,-3),(-10,-9)]}
FAR={100:(7,-5,11,-1),101:(7,-4,11,1),102:(5,-3,10,2),103:(-9,-4,-4,1),104:(-10,-7,-5,-2),231:(5,-1,10,4)}
POLYS2={
100:POLYS[100],
101:[(-13,-31),(-5,-31),(-5,-27),(-6,-19),(-4,-14),(2,-15),(7,-11),(11,-7),(11,1),(9,3),(-8,3),(-9,-3),(-7,-12),(-12,-17)],
102:[(-13,-26),(-5,-26),(-5,-20),(-6,-13),(-4,-7),(2,-7),(6,-4),(11,-1),(11,4),(9,7),(-10,7),(-10,0),(-7,-5),(-12,-12)],
103:[(-5,-8),(1,-8),(3,-10),(6,-16),(6,-20),(12,-20),(12,-14),(9,-8),(7,-3),(10,3),(8,6),(-8,6),(-10,1),(-10,-4),(-5,-4)],
104:[(-5,-11),(0,-11),(2,-13),(5,-22),(5,-28),(11,-28),(11,-22),(9,-13),(6,-9),(9,-1),(8,4),(-8,4),(-10,-3),(-10,-7),(-5,-7)],
231:[(-13,-23),(-5,-23),(-5,-17),(-6,-12),(-4,-6),(1,-7),(5,-5),(10,-2),(11,4),(9,8),(-10,8),(-10,0),(-7,-3),(-12,-9)]}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--version',default='v1');args=ap.parse_args()
    need(args.version in('v1','v2','v3','v4','v5','v6'),'버전')
    out=D/f'ultimate_costume_pair_probe_{args.version}';out.mkdir(exist_ok=False)
    src=N/'ultimate_run_repaint/packed_run_candidate_v1/PL02_U.ARC';u=Archive(src.read_bytes())
    need(digest(src)=='49da59790a3ad45c6b5a99f78e4786c135d8d017baa67ff55c07373a26f7fbe9','부모')
    pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in u.words])
    mapping=int(np.argmin(((pal[1:16].astype(float)-pal[31])**2).sum(1))+1);need(mapping==13,'회색색상 의미')
    rows=[];records=[]
    for n,poly in (POLYS2 if args.version!='v1' else POLYS).items():
        bp=D/f'ultimate_weapon_probe_v1/before_{n:03}_indices.png';ap=D/f'ultimate_weapon_probe_v1/after_{n:03}_indices.png'
        b=np.array(Image.open(bp));donor=np.array(Image.open(ap));mi=Image.new('L',(384,384))
        ImageDraw.Draw(mi).polygon([(x+160,y+160)for x,y in poly],fill=255);mask=np.array(mi)>0
        boundary=[]
        semantic_edge=[]
        if args.version in('v3','v4','v5','v6'):
            edge=json.loads((D/('ultimate_boundary_audit_v2'if args.version in('v4','v5','v6')else'ultimate_boundary_audit_v1')/'report.json').read_text('utf8'))
            for q in edge['source_cells']:
                if q['ref']!=n:continue
                x,y=q['world'];v=q['source_palette_winner']
                need(b[y+160,x+160]==0,'경계 입력');need(digest(ROOT/q['source_art'])==q['source_art_sha256'],'경계 출처')
                b[y+160,x+160]=v;boundary.append(q)
            if n==101:mask|=(X>=-10)&(X<=-5)&(Y>=-13)&(Y<=3)
        if args.version in('v5','v6')and n==100:
            for x,y,bv,av in[(5,-10,9,12),(6,-10,9,12),(7,-9,9,12),(8,-8,9,12),(9,-7,9,5)]:
                need(int(b[y+160,x+160])==bv and int(donor[y+160,x+160])==av,'반대팔 소매 의미 출처')
                mask[y+160,x+160]=True;semantic_edge.append([x,y,bv,av])
        if args.version=='v6'and n==100:
            # 원화에서 목 앞 양쪽 재킷 옷깃과 어깨 시작으로 확인한 영역.
            # y=-14의 얼굴/옆머리 및 x>=4,y=-13의 뒤머리는 보호한다.
            # 새 맨팔 원화의 검은 상의끈·목·어깨와 팔 사이 투명틈을 함께 복원.
            for y,x0,x1 in[(-13,0,4),(-12,-5,5),(-11,-5,6)]:
                for x in range(x0,x1):
                    if not mask[y+160,x+160]:
                        semantic_edge.append([x,y,int(b[y+160,x+160]),int(donor[y+160,x+160])])
                    mask[y+160,x+160]=True
        case=np.array(Image.open(D/f'ultimate_weapon_probe_v1/before_{n:03}_case.png'))
        hand=np.array(Image.open(D/f'ultimate_weapon_probe_v1/before_{n:03}_hand_mask.png'))>0
        x0,y0,x1,y1=FAR[n];far=(X>=x0)&(X<x1)&(Y>=y0)&(Y<y1)&np.isin(b,[10,11,12,13])
        protected=(case>0)|hand|far
        expected=b.copy();expected[b==15]=mapping
        target=expected.copy();target[mask]=donor[mask];target[protected]=expected[protected]
        outside=(target>0)&(b==0)
        need(np.array_equal(target[~mask],expected[~mask]),'의상외 새 공통부분')
        need(np.array_equal(target[protected],expected[protected]),'새 손/총 보호')
        for name,z in [('before',b),('after',target),('mask',mask.astype(np.uint8)*255),('protected',protected.astype(np.uint8)*255),('outside',outside.astype(np.uint8)*255)]:
            Image.fromarray(z).save(out/f'{name}_{n:03}.png')
        records.append({'ref':n,'before_path':bp.relative_to(ROOT).as_posix(),'before_sha256':digest(bp),'after_donor_path':ap.relative_to(ROOT).as_posix(),'after_donor_sha256':digest(ap),
            'new_before_source_boundary_cells':boundary,'additional_clothing_region':[-10,-13,-5,3]if args.version in('v3','v4','v5','v6')and n==101 else None,
            'authored_after_shoulder_edge_cells':semantic_edge,
            'polygon':poly,'far_hand_box':FAR[n],'palette15_gray_mapping':mapping,'outside_new_before_alpha':[(int(x-160),int(y-160),int(target[y,x]))for y,x in np.argwhere(outside)],
            'components_8':int(label(target>0,np.ones((3,3)))[1]),'head_legs_outside_costume_exact':True,'body_alpha_clipped':False,'new_sha256':sha(target.tobytes())})
        rows.append((f'Ultimate costume {n}',[('accepted after idle',u.composite(0,0)[0]),('new jacket',u.rgba(b,16)),('new after donor',u.rgba(donor)),('semantic common body',u.rgba(target))]))
    for i in range(0,len(rows),2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',7)
    write(out/'registration.json',{'parent_sha256':digest(src),'frames':records,'method':'새 재킷 원화의 머리/다리/손과 정본 권총을 보호하고 새 후폼 원화의 의상·팔 의미영역만 선택. 원화 알파를 기계적으로 교집합 클립하지 않고 새 재킷 바깥 픽셀을 별도 기록한다.',
        'semantic_masks_under_review':True,'native_packed':False,'runtime_verified':False})
    print(json.dumps([{'ref':r['ref'],'outside':len(r['outside_new_before_alpha']),'components':r['components_8']}for r in records]))

if __name__=='__main__':main()
