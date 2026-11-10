"""새 대시 원화의 접지와 샘플 경계의 실제 금색 눈동자만 정합한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
P=H/'prepared_rising_right_base01/PL00_U.ARC';PSHA='13a29023365419d32475cf5a6551adc4658116c8f03622d962d5b8071744e8b8'
PAGES={1:([67,69,71],'390a5ff9080abd924ce2c9ccb161da0b28442602bfabff51be3fe4a5b00639fe'),2:([75,77,79],'e7fa7a7e6a454309e7728a658a9ae840d7522a5cf7c60bf5c939eee8d9271f11')}
EYES={67:[(-8,-6),(-8,-5)],69:[(-11,-1),(-11,0)],71:[(-17,6),(-17,7)],75:[(-16,5),(-16,6)],77:[(-11,-4),(-11,-3)],79:[(-7,-7),(-7,-6)]}
def main():
    o=H/'dash_detail_contacts01';need(not o.exists(),'Fresh contact output required');need(sha(P.read_bytes())==PSHA,'Changed parent');a=Archive(P.read_bytes());o.mkdir();rows=[];pics={f:[]for f in('base','fourth')}
    for pg,(refs,digest)in PAGES.items():
        d=H/f'dash_detail_inputs{pg:02}';native=H/f'dash_detail_native{pg:02}';p=d/'generated.png';need(sha(p.read_bytes())==digest,'Changed new source');source=np.array(Image.open(p).convert('RGBA'));registration=json.loads((native/'registration.json').read_text('utf8'))
        for row,(form,pal,mask)in enumerate((('base',0,0),('fourth',16,15))):
            colors=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[pal:pal+16]],np.int32)
            for col,n in enumerate(refs):
                q=native/f'{form}_{n:03}_indices.png';rm=next(r for r in registration['rows']if r['form']==form and r['ref']==n);need(sha(q.read_bytes())==rm['sha256'],'Changed native');old=np.array(Image.open(q));new=old.copy();cell=source[row*512:(row+1)*512,col*512:(col+1)*512].astype(int)
                gold=(cell[:,:,0]>160)&(cell[:,:,1]>90)&(cell[:,:,2]<100)&(cell[:,:,1]-cell[:,:,2]>30)&(cell[:,:,0]-cell[:,:,1]>20)&(cell[:,:,0]-cell[:,:,1]<110)&(cell[:,:,3]>128);counts=gold.reshape(64,8,64,8).sum((1,3));iris=[]
                for x,y in EYES[n]:
                    coverage=int(counts[y+36,x+32]);need(coverage>=9 and old[y+160,x+160]>0,'Iris not supported by new source')
                    color=7 if form=='base'else 10;iris.append({'world':[x,y],'gold_source_pixels_in_8x8':coverage,'before_index':int(new[y+160,x+160]),'after_index':color});new[y+160,x+160]=color
                sole=[]
                if n==69 and form=='fourth':
                    # The source has a half-cell sole at y22, skipped by the
                    # regular center sample. Use that same new source row2.
                    for x in(-3,-2,-1,0):
                        px=(x+32)*8+4;py=(22+36)*8+2;sample=cell[py,px];need(sample[3]>=128 and new[182,x+160]==0,'Unexpected sole edge')
                        color=int(1+((colors[1:]-sample[:3])**2).sum(1).argmin());new[182,x+160]=color;sole.append({'world':[x,22],'source_cell_xy':[px,py],'source_rgba':sample.tolist(),'index':color})
                changed=new!=old;need(np.count_nonzero(changed)<=6,'Unexpected local material scope')
                # The second page sits one native pixel high as a whole. A
                # translation preserves every new joint and source pixel.
                dy=1 if pg==2 else 0
                if dy:
                    need(not np.any(new[-1]),'Translation clips art');new=np.roll(new,dy,axis=0);new[:dy]=0
                yy,xx=np.nonzero(new);need(int(yy.max()-160)==22,'Sole no longer on original ground')
                Image.fromarray(new).save(o/f'{form}_{n:03}_indices.png');rgba=a.rgba(new,pal);rgba.save(o/f'{form}_{n:03}.png');Image.fromarray(changed.astype(np.uint8)*255).save(o/f'{form}_{n:03}_local_source_sample_mask.png')
                rows.append({'form':form,'ref':n,'source_native_sha256':sha(q.read_bytes()),'generated_source_sha256':digest,'iris_samples':iris,'sole_samples':sole,'local_pixel_changes_before_translation':int(changed.sum()),'translation':[0,dy],'output_sha256':sha((o/f'{form}_{n:03}_indices.png').read_bytes()),'final_floor_world':22,'body_resize':False,'old_art_reused':False})
                pics[form].extend([(f'{n} current dash',a.composite(n,mask)[0]),(f'{n} new contact + source iris',rgba)])
    for form,mask in(('base',0),('fourth',15)):
        for i in range(0,len(pics[form]),6):page(pics[form][i:i+6],a.composite(0,mask)[0],o/f'{form}_comparison_{i//6:02}.png',cols=2,scale=5)
    write(o/'report.json',{'parent_sha256':PSHA,'rows':rows,'policy':'전체몸 재크기변환 없음. 2페이지는 전체+1y 평행등록, 포스69신발하단4점은 실제새원화8x8셀의반칸불투명발바닥표본을복구. 새원화금색홍채가피부/빨강으로양자화되거나센터샘플을피한6자세는 실제해당8x8셀의금색표본9점이상으로두눈동자픽셀을원팔레트금색에등록. 옛얼굴복사 없음.','not_final':'공통머리/포스장식·의상소유/부분아머·사격·속도선/패킹/실기는아직미완료.','visual_review_pending':True,'resource_written':False,'runtime_verified':False})
    print(json.dumps({'out':str(o),'rows':len(rows),'local_changes':sum(r['local_pixel_changes_before_translation']for r in rows)}))
if __name__=='__main__':main()
