"""新規8姿勢の原点・接点・部位寸法を記録。合格を自動推定しない。"""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy.ndimage import label
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent;N=D.parent
sys.path[:0]=[str(ROOT),str(D),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
from check_first_geometry import info,full
def source(n):return D/('skin_edge_registered_v3'if n in(33,39,47,51)else'before_second_registered_v1')/f'before_{n:03}.png'
def anchors(v):
    Y,X=np.indices(v.shape);green=(v==14)&(Y<160);gy,gx=np.nonzero(green);eye=[int(np.median(gx))-160,int(np.median(gy))-160]
    bottom=int(np.nonzero(v)[0].max());floor=(np.flatnonzero(v[bottom])-160).tolist()
    shoes=[]
    for y,x in np.argwhere((v==14)&(Y>=160)):
        shoes.append([int(x-160),int(y-160)])
    return {'eye_world':eye,'bottom_world':bottom-160,'bottom_x':floor,'shoe_lime_texels':shoes,'alpha_components_8':label(v>0,np.ones((3,3)))[1],'geometry':info(v,eye)}
def main():
    a=Archive((N/'native_restore/nova_sync_v1/PL02_U.ARC').read_bytes());out=D/'body_anchor_audit_v1';out.mkdir(exist_ok=False);rows=[];metrics=[]
    for n in(33,35,37,39,41,43,47,51):
        old=full(a,n);new=np.array(Image.open(source(n)));ob=anchors(old);nb=anchors(new);need(ob['eye_world']==nb['eye_world'],'Eye moved');need(ob['bottom_world']==nb['bottom_world'],'Sole height moved')
        metrics.append({'ref':n,'file':source(n).relative_to(ROOT).as_posix(),'file_sha256':digest(source(n)),'old':ob,'new':nb,'hands_shoes_x_pending':True})
        rows.append((f'body {n}',[('original',a.rgba(old,16)),('new source native',a.rgba(new,16))]))
    for start in(0,4):helper.grid(rows[start:start+4],out/f'comparison_{start//4+1}.png',6)
    write(out/'metrics.json',{'frames':metrics,'parent_arc_sha256':sha(a.data),'scope':'8 body candidates only; quantized source images, not ARC readback. Eye/crown and global sole height unchanged. Individual hand/shoe contact and art continuity remain to review.','native_packed':False,'runtime_verified':False})
    write(out/'skin_v2_erratum.json',{'previous':'skin_edge_registered_v2/registration.json','incorrect_field':'head_jacket_gun_shoes_preserved','explanation':'33번 y15..17에 발목/신발 경계 검정5픽셀도 원화의 회색으로 등록되었으므로 신발 전체색인 exact가 아니었다. v3에서 이5픽셀 원상보호. v2는 중간안으로 보존하나 최종입력에서 제외.','v3_total_changed_pixels':32,'alpha_preserved':True,'source_color_provenance':'Same full-body local correction, not invented color replacement.'})
    print(json.dumps({q['ref']:{'old_sole':q['old']['bottom_x'],'new_sole':q['new']['bottom_x'],'components':q['new']['alpha_components_8']}for q in metrics}))
if __name__=='__main__':main()
