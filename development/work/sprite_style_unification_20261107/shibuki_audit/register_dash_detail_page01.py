"""대시 첫6 새 원화의 고정 1/8 등록. 구형 머리/몸체 덮기 없음."""
from pathlib import Path
import argparse,json,sys
import numpy as np
from PIL import Image
from scipy.ndimage import label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive,page
from native_pose_pack import need,sha,write
D=H/'dash_detail_inputs01';O=H/'dash_detail_native01'
SOURCE_SHA='390a5ff9080abd924ce2c9ccb161da0b28442602bfabff51be3fe4a5b00639fe'
def main():
    global D,O,SOURCE_SHA
    parser=argparse.ArgumentParser();parser.add_argument('--page',type=int,choices=(1,2,3,4),default=1);args=parser.parse_args();number=args.page
    D=H/f'dash_detail_inputs{number:02}';O=H/f'dash_detail_native{number:02}'
    SOURCE_SHA={1:'390a5ff9080abd924ce2c9ccb161da0b28442602bfabff51be3fe4a5b00639fe',2:'e7fa7a7e6a454309e7728a658a9ae840d7522a5cf7c60bf5c939eee8d9271f11',3:'042afb0fbe745f740cd0f9afcd9d52a4934fa2c828c76616be65279f75938153',4:'39ef69d0a315c4615e9a611e2da81a231795d637c58577dd9d0551df135a3574'}[number]
    need(not O.exists(),'Fresh native output required');info=json.loads((D/'manifest.json').read_text('utf8'))
    arc=(ROOT/info['parent']).read_bytes();need(sha(arc)==info['parent_sha256'],'Wrong native parent');a=Archive(arc)
    source=D/'generated.png';need(sha(source.read_bytes())==SOURCE_SHA,'Wrong generated input');im=Image.open(source).convert('RGBA');need(im.size==(1536,1024),'Wrong fixed sheet layout')
    sample=np.array(im.resize((192,128),Image.Resampling.NEAREST));O.mkdir();rows=[]
    for row,(form,mask,pal)in enumerate((('base',0,0),('fourth',15,16))):
        colors=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[pal:pal+16]],np.int32);items=[]
        for col,n in enumerate(info['first_page']):
            cell=sample[row*64:(row+1)*64,col*64:(col+1)*64]
            q=(1+((cell[:,:,:3].astype(np.int32)[:,:,None,:]-colors[None,None,1:,:])**2).sum(3).argmin(2)).astype(np.uint8);q[cell[:,:,3]<128]=0
            arr=np.zeros((384,384),np.uint8);arr[124:188,128:192]=q;name=f'{form}_{n:03}'
            Image.fromarray(arr).save(O/f'{name}_indices.png');rgba=a.rgba(arr,pal);rgba.save(O/f'{name}.png');old=a.composite(n,mask)[0]
            yy,xx=np.nonzero(arr);oy,ox=np.nonzero(np.array(old)[:,:,3]);labels,count=label(arr>0,np.ones((3,3),int));sizes=sorted([int((labels==i).sum())for i in range(1,count+1)],reverse=True)
            rows.append({'form':form,'ref':n,'native_png':(O/f'{name}_indices.png').relative_to(ROOT).as_posix(),'sha256':sha((O/f'{name}_indices.png').read_bytes()),'fixed_scale':0.125,'translation':[0,0],
                         'before_bbox_world':[int(ox.min()-160),int(oy.min()-160),int(ox.max()+1-160),int(oy.max()+1-160)],'after_bbox_world':[int(xx.min()-160),int(yy.min()-160),int(xx.max()+1-160),int(yy.max()+1-160)],
                         'original_foot_y':int(oy.max()-160),'new_foot_y':int(yy.max()-160),'connected_components_8way':sizes,'old_pixels_reused':0})
            items.extend([(f'{n} current dash',old),(f'{n} new fixed-scale artwork',rgba)])
        page(items,a.composite(0,mask)[0],O/f'{form}_comparison.png',cols=2,scale=6)
    write(O/'registration.json',{'parent_sha256':sha(arc),'source_sha256':SOURCE_SHA,'source_size':list(im.size),'source_scale':0.125,'alpha_threshold':128,'rows':rows,'source_palette_bytes_unchanged':True,'new_art_only':True,'contact_alignment_pending':True,'partial_layer_registration_pending':True,'no_resource_written':True,'gameplay_validation':False})
    print(json.dumps({'out':str(O),'rows':rows}))
if __name__=='__main__':main()
