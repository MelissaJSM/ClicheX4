"""호버 첫4 새몸의 원상체0/하체5 소유와 각 실제CLUT를 등록한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
from prepare_lowhp_final import compose
from prepare_hover_ultimate_inputs import P,PARENT,CUTS
def main():
    d=H/'hover_ultimate_body_layers01';need(not d.exists(),'기존목표보호');a=Archive(P.read_bytes());need(sha(a.data)==PARENT,'부모변경');d.mkdir();rows=[];ims=[];files=[P,Path(__file__),H/'prepare_hover_ultimate_inputs.py'];rgb=np.array([[(int(w)>>k&31)*255//31 for k in(0,5,10)]for w in a.words[16:32]],np.int32)
    for n in(221,223,225,227):
        src=H/('hover221_reach_native01/221_indices.png'if n==221 else f'hover_ultimate_native01/{n:03}_indices.png');z=np.array(Image.open(src));sp=H/f'hover_ultimate_native01/{n:03}_sample.png';cell=np.array(Image.open(sp).convert('RGBA'));q=(1+((cell[:,:,:3].astype(np.int32)[:,:,None]-rgb[None,None,1:])**2).sum(3).argmin(2)).astype(np.uint8);q[cell[:,:,3]<128]=0;lower=np.zeros_like(z);lower[112:208,112:208]=q;lower[:160+CUTS[n]]=0;up=z.copy();up[160+CUTS[n]:]=0;need(np.array_equal(lower[160+CUTS[n]:]>0,z[160+CUTS[n]:]>0),'고정새다리alpha변경');layers={0:up,5:lower,6:np.zeros_like(z),7:np.zeros_like(z),8:np.zeros_like(z)};actual=compose(a,layers,15);need(label(np.array(actual)[:,:,3]>0,np.ones((3,3)))[1]==1,'전체연결');actual.save(d/f'actual_{n}.png')
        for b,v in layers.items():Image.fromarray(v).save(d/f'{n:03}_bank{b}_indices.png')
        oldlow=z.copy();oldlow[:160+CUTS[n]]=0;diff=int(np.any(np.array(a.rgba(oldlow,0))!=np.array(a.rgba(lower,16)),axis=2).sum());rows.append({'ref':n,'body_source':{'path':src.relative_to(ROOT).as_posix(),'sha256':sha(src.read_bytes())},'lower_RGBA_sample':{'path':sp.relative_to(ROOT).as_posix(),'sha256':sha(sp.read_bytes())},'cut_world_y':CUTS[n],'lower_direct_quantization_palette':16,'lower_alpha_exact':True,'lower_RGB_cells_different_from_temporary_palette0':diff,'target_hashes':{str(b):sha(v.tobytes())for b,v in layers.items()},'metrics':metrics(actual),'native_hands_feet_registration_pending_final':True});files.extend([src,sp]);ims.extend([(f'{n} old actual15',a.composite(n,15)[0]),(f'{n} new actual15',actual)])
    for i in range(2):page(ims[i*4:i*4+4],a.composite(0,0)[0],d/f'comparison_{i:02}.png',cols=2,scale=5)
    write(d/'manifest.json',{'parent_sha256':PARENT,'refs':[221,223,225,227],'frames':rows,'source_files':{p.relative_to(ROOT).as_posix():sha(p.read_bytes())for p in files},'policy':'원상체0 CLUT0/하체5 CLUT16과빈678을유지.하체는생성원RGBA에서직접실제CLUT16으로양자화하며임시전체CLUT0와의색차이는별도기록.221새팔외에는위치/알파변경없다.실제엔진강제15만완성호버표시.사격짝/229미완료.','native_packed':False,'runtime_verified':False,'art_final':False});print(json.dumps({'refs':4,'layers':20,'lower_RGB_differences':{str(r['ref']):r['lower_RGB_cells_different_from_temporary_palette0']for r in rows},'manifest':sha((d/'manifest.json').read_bytes())}))
if __name__=='__main__':main()
