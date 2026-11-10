"""새 공통 접점/치마 끝의 투명 경계를 양폼에 명시적으로 맞춘다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
from prepare_ultimate_wall_page02_shared import LUT

B=H/'ultimate_wall_raised_native01';A=H/'ultimate_wall_page02_shared01';O=H/'ultimate_wall_page02_contacts01'
STRAY={61:[(16,-8),(-8,-3)],63:[(14,-27),(13,-25),(12,-24),(12,-23),(12,-22),(-7,-3)],65:[(11,-26)]}
HEM={61:[(-5,5),(-4,5)],63:[(-4,2),(-2,3),(-3,4),(-2,4),(-4,5),(-3,5),(-4,6)],65:[(-4,2),(-2,3),(-3,4),(-2,4),(-4,5),(-3,5),(-4,6)]}

def main():
    need(not O.exists(),'Fresh contact output required');O.mkdir();(O/'before').mkdir();(O/'after').mkdir()
    a=Archive((H/'prepared_ultimate_lowhp01/PL02_U.ARC').read_bytes());rows=[];poses={}
    for n in (61,63,65):
        before=np.array(Image.open(B/f'{n:03}_indices.png'));after=np.array(Image.open(A/f'{n:03}_indices.png'));oldb=before.copy();olda=after.copy()
        outside={(int(x-160),int(y-160))for y,x in zip(*np.nonzero((after>0)&(before==0)))}
        need(outside==set(STRAY[n]+HEM[n]),'Unexamined alpha change')
        for x,y in STRAY[n]:
            # These are old locations of the NEW source's palm/hair/front-hand
            # outline; the newly registered common modules define the contact.
            need(before[y+160,x+160]==0 and after[y+160,x+160]in(2,15),'Unexpected skin or clothing removal')
            after[y+160,x+160]=0
        hem=[]
        for x,y in HEM[n]:
            v=int(after[y+160,x+160]);need(v in(2,8,14,15),'Unexpected hem material')
            need(a.words[v]==a.words[16+v],'Hem color differs across costumes')
            before[y+160,x+160]=v;hem.append([x,y,v])
        need(not np.any((after>0)&(before==0)),'After silhouette leaks')
        need(np.array_equal(after[167:],LUT[before][167:]),'New common legs changed')
        for name,q,start in [('before',before,16),('after',after,0)]:
            Image.fromarray(q).save(O/name/f'{n:03}_indices.png');a.rgba(q,start).save(O/name/f'{n:03}.png')
        Image.fromarray(((before!=oldb)|(after!=olda)).astype(np.uint8)*255).save(O/f'{n:03}_contact_changes.png');poses[n]=(before,after)
        rows.append({'ref':n,'new_before_hem_pixels_added':hem,'new_after_duplicate_outline_pixels_removed':STRAY[n],'source_skin_pixels_removed':0,'before_changed_pixels':int(np.count_nonzero(before!=oldb)),'after_changed_pixels':int(np.count_nonzero(after!=olda)),'after_outside_before':0,'common_new_head_hand_legs_preserved':True,'old_art_reused':False})
    page([(f'{n} jacket with shared inner hem',a.rgba(v[0],16))for n,v in poses.items()]+[(f'{n} sleeveless, same contacts',a.rgba(v[1]))for n,v in poses.items()],a.composite(0,0)[0],O/'comparison.png',cols=3,scale=6)
    for name,start,mask in [('before',16,15),('after',0,0)]:
        items=[]
        for n in (55,57,59,61,63,65):
            p=(H/'ultimate_wall_contacts_probe01'if n<61 else O)/name/f'{n:03}.png';items.append((f'{n} {name}',Image.open(p)))
        page(items,a.composite(0,mask)[0],O/f'six_{name}.png',cols=3,scale=6)
    write(O/'registration.json',{'rows':rows,'source_art_sha256':'f3baf9b3e367e149cbe881151c0d8ff2a9e39c2ea88934b82745219b79852a59','candidate_only':True,'packed':False,'explanation':'새 공통 손/머리 접점 밖에 겹친 짙은 외곽만 제거했다. 재킷 아래에서 보이는 새 민소매 치마 끝 2/7/7px는 동일 색상 그대로 재킷형에도 등록했다. 피부·전신 축소·옛 머리 복사는 없다.','full_shot_pairs_pending':True})
    # Correct the intermediate explanatory metadata without regenerating art.
    p=A/'registration.json';v=json.loads(p.read_text('utf8'));v['reason']='새 재킷의 머리·손·다리를 보존하고 의상과 팔만 새 민소매 원화에서 같은 기준점으로 등록한다.';write(p,v)
    print(rows)

if __name__=='__main__':main()
