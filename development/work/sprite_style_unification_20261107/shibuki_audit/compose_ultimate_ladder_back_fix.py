"""생성한 네 후면 안경 교정 구역만 인덱스에 등록하고 다른 새 몸체를 보존."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
RECT={144:(-7,-17,2,-11),146:(-10,-18,-2,-11)}

def main():
    out=H/'ultimate_ladder_native03';need(not out.exists(),'Fresh output');out.mkdir();ult=Archive((H/'prepared_ultimate_dash01/PL02_U.ARC').read_bytes());rows=[]
    for form,mask,pal in(('before',15,16),('after',0,0)):
        pics=[]
        for n in(143,144,146):
            first=np.array(Image.open(H/f'ultimate_ladder_native01/{form}_{n:03}_indices.png'));donor=np.array(Image.open(H/f'ultimate_ladder_back_native01/{form}_{n:03}_indices.png'));result=first.copy();allowed=np.zeros(first.shape,bool)
            if n in RECT:
                x0,y0,x1,y1=RECT[n];allowed[y0+160:y1+160,x0+160:x1+160]=True
                result[allowed]=donor[allowed]
            need(np.array_equal(result[~allowed],first[~allowed]),'Nonlocal new art changed')
            Image.fromarray(result).save(out/f'{form}_{n:03}_indices.png');Image.fromarray(allowed.astype(np.uint8)*255).save(out/f'{form}_{n:03}_edit_mask.png');im=ult.rgba(result,pal);im.save(out/f'{form}_{n:03}.png')
            pics.extend([(f'{n} old',ult.composite(n,mask)[0]),(f'{n} new rear correction',im)])
            rows.append({'form':form,'ref':n,'world_region':RECT.get(n),'changed_pixels':int(np.count_nonzero(result!=first)),'nonlocal_new_body_exact':True,'local_alpha_removed':int(np.count_nonzero((first>0)&(result==0))),'local_alpha_added':int(np.count_nonzero((first==0)&(result>0))),'silhouette_exact_outside_head_edit':True,'current':metrics(im)})
        page(pics,ult.composite(0,mask)[0],out/f'{form}_comparison.png',cols=2,scale=5)
    original=H/'ultimate_ladder_inputs01/page01';corrected=H/'ultimate_ladder_back_accessory01'
    for folder,filename,inputs in[(original,'exec-f1c1852b-f953-4704-9229-b4ed3485b7d4.png',[original/'new_pose_reference.png',original.parent/'accepted_ultimate_style.png',original/'current_ultimate_coordinates.png']),(corrected,'exec-ae85315c-fba8-40cc-b486-23f2efd27596.png',[corrected/'edit_target.png'])]:
        prompt=(folder/'prompt.txt').read_text('utf8').strip();(folder/'prompt_used.txt').write_text(prompt,encoding='utf8');write(folder/'generation_receipt.json',{'tool':'builtin imagegen','original_filename':filename,'source_sha256':sha((folder/'generated.png').read_bytes()),'prompt_sha256':sha(prompt.encode()),'inputs':{p.relative_to(H).as_posix():sha(p.read_bytes())for p in inputs},'source_alpha_retained':True})
    write(out/'report.json',{'scope':'뒤통수의 잘못된 앞면 안경만 생성 국소 원화로 교정. 옛머리/수작업 단색채움 사용 없음. 안경이 머리 외곽보다 돌출했던 국소픽셀의 알파 제거는 허용하며 몸체 외곽은 그대로.','original_generation_sha256':sha((original/'generated.png').read_bytes()),'correction_generation_sha256':sha((corrected/'generated.png').read_bytes()),'rows':rows,'first_native_nonlocal_exact':True,'native_scale':0.125,'palette_unchanged':True,'contacts_and_common_layers_pending':True,'packed':False,'actually_viewed':False})
    print(json.dumps(rows))
if __name__=='__main__':main()
