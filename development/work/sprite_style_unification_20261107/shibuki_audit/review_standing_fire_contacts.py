"""원점 동일 새 조합과 부모의 발끝·발목 범위를 읽기 대조한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive
from prepare_lowhp_final import compose
PBS=(0,5,6,7,8)
def foot(v,side):
    alpha=np.array(v)[:,:,3]>0;yy,xx=np.indices(alpha.shape);m=alpha&(yy>=173)&((xx<160)if side=='left'else(xx>=160));y,x=np.nonzero(m)
    if not len(x):return None
    bottom=int(y.max());sole=x[y==bottom]
    return {'opaque':len(x),'bbox':[int(x.min())-160,int(y.min())-160,int(x.max())-159,int(y.max())-159],'sole_y':bottom-160,'sole_xs':(sole-160).tolist(),'ankle_rows':{str(k):[int(px)-160 for px in np.flatnonzero(m[k+160])]for k in range(13,19)}}
def main():
    d=H/'standing_fire_contacts_review01';need(not d.exists(),'새 폴더 필요');d.mkdir();a=Archive((H/'prepared_standing_special_base01/PL00_U.ARC').read_bytes());s=H/'standing_fire_targets_probe01';rows=[]
    for form,mask in(('base',0),('fourth',15)):
        sheet=Image.new('RGB',(1100,960),(24,29,40));dr=ImageDraw.Draw(sheet)
        for i,n in enumerate((85,90,91)):
            old=a.composite(n,mask)[0];ll={b:np.array(Image.open(s/f'{n:03}_bank{b}_indices.png'))for b in PBS};new=compose(a,ll,mask)
            for j,(name,pic)in enumerate((('parent',old),('new target',new))):
                x=20+j*540;y=20+i*315;dr.text((x,y),f'{n} {form} {name} - identical origin',fill='white')
                body=pic.crop((128,128,192,192)).resize((256,256),Image.Resampling.NEAREST);sheet.paste(body,(x,y+22),body)
                feet=pic.crop((128,171,192,185)).resize((256,56),Image.Resampling.NEAREST);sheet.paste(feet,(x+270,y+70),feet)
                dr.line((x,y+22+54*4,x+256,y+22+54*4),fill=(80,105,80));dr.text((x+270,y+140),'foot strip y11..24',fill=(190,210,220))
            row={'ref':n,'form':form,'body_transform':[0,0],'feet':{side:{'parent':foot(old,side),'target':foot(new,side)}for side in('left','right')}}
            rows.append(row)
        sheet.save(d/f'{form}_contacts.png')
    write(d/'report.json',{'parent_sha256':sha(a.data),'target_manifest_sha256':sha((s/'manifest.json').read_bytes()),'rows':rows,'scope':'정적 원점 동일 발끝/발목 비교. 발판/지면 실기와 신규정합은 수행하지 않음.','art_changed':False,'arc_written':False})
    print(json.dumps([{'ref':r['ref'],'form':r['form'],'soles':{side:[q['parent']['sole_y'],q['target']['sole_y']]for side,q in r['feet'].items()}}for r in rows]))
if __name__=='__main__':main()
