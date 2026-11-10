"""新大시10몸체×두의상 접점/원화 금색홍채 표본을 통합한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
P=H/'prepared_rising_right_base01/PL00_U.ARC';PSHA='13a29023365419d32475cf5a6551adc4658116c8f03622d962d5b8071744e8b8'
EXTRA=((H/'dash_recovery_height01',H/'dash_recovery_height_native01',(81,83),'28f6376f4b942cc4e16e1ff2611c2014dd6428ccc85025c52b664e3eb20b79e8'),(H/'dash_detail_inputs04',H/'dash_detail_native04',(93,94),'39ef69d0a315c4615e9a611e2da81a231795d637c58577dd9d0551df135a3574'))
EYES={81:[(-8,-8),(-8,-7)],83:[(-8,-9),(-8,-8)],93:[(-7,-7),(-7,-6)],94:[(-10,-1),(-10,0)]}
def main():
    o=H/'dash_detail_contacts02';need(not o.exists(),'Fresh output only');need(sha(P.read_bytes())==PSHA,'Wrong parent');a=Archive(P.read_bytes());o.mkdir();rows=[]
    first=json.loads((H/'dash_detail_contacts01/report.json').read_text('utf8'))
    for r in first['rows']:
        form=r['form'];n=r['ref'];src=H/f'dash_detail_contacts01/{form}_{n:03}_indices.png';need(sha(src.read_bytes())==r['output_sha256'],'Changed previous contact')
        q=np.array(Image.open(src));Image.fromarray(q).save(o/src.name);a.rgba(q,0 if form=='base' else 16).save(o/f'{form}_{n:03}.png')
        row=dict(r);row['source_native_path']=src.relative_to(ROOT).as_posix();row['contact_parent_exact']=True;rows.append(row)
    for d,native,refs,digest in EXTRA:
        need(sha((d/'generated.png').read_bytes())==digest,'Changed artwork');source=np.array(Image.open(d/'generated.png').convert('RGBA')).astype(int)
        for row,(form,pal)in enumerate((('base',0),('fourth',16))):
            for col,n in enumerate(refs):
                src=native/f'{form}_{n:03}_indices.png';before=np.array(Image.open(src));q=before.copy();cell=source[row*512:(row+1)*512,col*512:(col+1)*512]
                gold=(cell[:,:,0]>160)&(cell[:,:,1]>90)&(cell[:,:,2]<100)&(cell[:,:,1]-cell[:,:,2]>30)&(cell[:,:,0]-cell[:,:,1]>20)&(cell[:,:,0]-cell[:,:,1]<110)&(cell[:,:,3]>128);counts=gold.reshape(64,8,64,8).sum((1,3));iris=[]
                for x,y in EYES[n]:
                    count=int(counts[y+36,x+32]);need(count>=9 and q[y+160,x+160]>0,'No gold sample support');v=7 if form=='base' else 10
                    iris.append({'world_before_translation':[x,y],'source_gold_count':count,'before_index':int(q[y+160,x+160]),'after_index':v});q[y+160,x+160]=v
                need(np.count_nonzero(before!=q)<=2,'Material scope escaped iris');dy=-1 if n==93 else 1 if n==94 else 0
                q=np.roll(q,dy,axis=0)
                if dy<0:q[dy:]=0
                elif dy>0:q[:dy]=0
                yy,xx=np.nonzero(q);floor=int(yy.max()-160);need(floor==(19 if n==93 else 24 if n==94 else 22),'Foot contact changed')
                Image.fromarray(q).save(o/src.name);a.rgba(q,pal).save(o/f'{form}_{n:03}.png')
                rows.append({'form':form,'ref':n,'source_native_path':src.relative_to(ROOT).as_posix(),'source_native_sha256':sha(src.read_bytes()),'generated_source_sha256':digest,'iris_samples':iris,'translation':[0,dy],'output_sha256':sha((o/src.name).read_bytes()),'final_floor_world':floor,'ear_top_world':int(yy.min()-160),'body_resize':False,'old_art_reused':False})
    for form,mask in(('base',0),('fourth',15)):
        items=[]
        for n in (67,69,71,75,77,79,81,83,93,94):items.extend([(f'{n} current body',a.composite(n,mask)[0]),(f'{n} new body, contacts aligned',Image.open(o/f'{form}_{n:03}.png').convert('RGBA'))])
        for i in range(0,len(items),6):page(items[i:i+6],a.composite(0,mask)[0],o/f'{form}_comparison_{i//6:02}.png',cols=2,scale=5)
    write(o/'report.json',{'parent_sha256':PSHA,'rows':rows,'scope':'10몸체·두의상. 73/74속도선·사격짝·부분파츠·패킹 후속','old_art_reused':False,'whole_body_resize':False,'game_modified':False,'visual_review_pending':True})
    print(json.dumps({'out':str(o),'rows':len(rows)}))
if __name__=='__main__':main()
