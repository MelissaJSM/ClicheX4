"""Nova217 새 부츠의 강체 정합과 공통 머리/손·네 부분 의상 첫 검사."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
from prepare_lowhp_final import compose
from compose_nova_fourth_costume import poly
HEAD=[(-30,-18),(-10,-18),(-9,-9),(-12,-5),(-12,1),(-15,4),(-23,4),(-29,0)]
FLOW=[(-12,-10),(2,-9),(10,-5),(10,0),(5,1),(-2,-3),(-12,-2)]
BRAID=[(8,-1),(18,-1),(21,2),(19,5),(10,4)]
DECO=[(-16,-14),(-8,-14),(-7,-6),(-10,-3),(-15,-4)]
HANDS=[[(-28,3),(-22,3),(-21,8),(-28,8)],[(-6,2),(1,2),(1,7),(-6,7)]]
ARM=[(-29,3),(-20,2),(-14,6),(-15,12),(-21,15),(-27,12)]

def main():
    d=H/'nova_strike_layers_probe01';need(not d.exists(),'새 후보');d.mkdir();a=Archive((H/'prepared_nova_base01/PL00_U.ARC').read_bytes())
    base=np.array(Image.open(H/'nova_strike_base_native01/base_217_indices.png'));fourth=np.array(Image.open(H/'nova_strike_base_native01/fourth_217_indices.png'));donor=np.array(Image.open(H/'nova_strike_boot_native01/fourth_217_indices.png'));y,x=np.indices(base.shape);x=x-160;y=y-160
    # donor 부츠 끝1px 안쪽 차이는 새 부츠 전체의 강체 X+1 등록으로만 보정한다.
    boot=(x>=16)&(x<=27)&(y>=6)&(y<=14);translated=np.zeros_like(donor);translated[:,1:]=donor[:,:-1];costume=fourth.copy();costume[boot]=translated[boot]
    need(np.array_equal(costume[~boot],fourth[~boot]),'부츠 밖 보호')
    deco=poly(DECO);hair=(poly(HEAD)|poly(FLOW)|poly(BRAID))&~deco;hands=np.logical_or.reduce([poly(p)for p in HANDS])&np.isin(base,[10,12,13]);common=hair|hands
    rgb=np.array([[(int(w)>>k&31)*255//31 for k in(0,5,10)]for w in a.words[:32]],np.int32);lut=1+((rgb[:16,None]-rgb[None,17:32])**2).sum(2).argmin(1)
    over=costume.copy();over[common]=0;missing=(base>0)&(over==0)&~common;outline=missing&np.isin(base,[2,15]);over[outline]=lut[base[outline]];unresolved=missing&~outline
    owner=np.full(base.shape,6,np.uint8);owner[(x>=7)&(y>=6)]=8;owner[hair|deco]=5;owner[poly(ARM)]=7
    layers={0:base,**{pb:np.where(owner==pb,over,0).astype(np.uint8)for pb in(5,6,7,8)}}
    for pb,z in layers.items():Image.fromarray(z).save(d/f'217_bank{pb}_indices.png')
    for n,z in [('boot',boot),('common',common),('head',hair),('hands',hands),('deco',deco),('outline',outline),('unresolved',unresolved)]:Image.fromarray(z.astype(np.uint8)*255).save(d/f'217_{n}_mask.png')
    Image.fromarray(owner).save(d/'217_owner.png');Image.fromarray(costume).save(d/'fourth_boot_composed_indices.png');a.rgba(costume,16).save(d/'fourth_boot_composed.png')
    components=[]
    for mask in range(16):
        im=compose(a,layers,mask);labs,_=label(np.array(im)[:,:,3]>0,np.ones((3,3)));components.append({'mask':mask,'sizes':sorted(np.bincount(labs.ravel())[1:].tolist(),reverse=True)})
    for form,mask in(('base',0),('fourth',15)):
        im=compose(a,layers,mask);im.save(d/f'{form}_217.png');page([('현재217 몸/기존효과',a.composite(217,mask)[0]),('새217 몸/효과 별도',im)],a.composite(0,mask)[0],d/f'{form}_comparison.png',cols=2,scale=6)
    page([(f'217 mask{m:X}',compose(a,layers,m))for m in range(16)],a.composite(0,15)[0],d/'partial_217.png',cols=4,scale=4)
    write(d/'report.json',{'arc_written':False,'body_scaled':False,'boot_registration':[1,0],'boot_changed_cells':int((costume!=fourth).sum()),'boot_outside_preserved':True,'whole_donor_used':False,'common_base_head_and_hands':True,'costume_metrics':metrics(a.rgba(costume,16)),'unresolved':[[int(px-160),int(py-160),int(base[py,px])]for py,px in zip(*np.nonzero(unresolved))],'outline_native_palette_mapping_samples':[[int(px-160),int(py-160),int(base[py,px]),int(over[py,px])]for py,px in zip(*np.nonzero(outline))],'partial_components':components,'source_files':{p.relative_to(ROOT).as_posix():sha(p.read_bytes())for p in[H/'nova_strike_base_native01/base_217_indices.png',H/'nova_strike_base_native01/fourth_217_indices.png',H/'nova_strike_boot_native01/fourth_217_indices.png',Path(__file__)]}});print(json.dumps({'unresolved':[[int(px-160),int(py-160),int(base[py,px])]for py,px in zip(*np.nonzero(unresolved))],'outline':int(outline.sum()),'components':components,'boot_changed':int((costume!=fourth).sum())}))
if __name__=='__main__':main()
