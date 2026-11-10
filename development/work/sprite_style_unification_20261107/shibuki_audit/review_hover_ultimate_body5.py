"""최신 두손221와229를 포함한 실제5몸/원15추진 위상을 같은 원점으로 비교."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_cdt,label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
from prepare_lowhp_final import compose
from prepare_hover_ultimate_inputs import P,PARENT,CUTS
def main():
    d=H/'hover_ultimate_body5_contacts01';need(not d.exists(),'새 비교');a=Archive(P.read_bytes());need(sha(a.data)==PARENT,'부모 변경');s=H/'hover_ultimate_contact_sources01';m=json.loads((s/'manifest.json').read_text('utf8'));d.mkdir();proof=[];pal=np.zeros((16,4),np.uint8)
    for i in range(1,16):pal[i]=[60+i*10,70+i*8,110+i*5,255]
    allims=[];files=[P,Path(__file__),s/'manifest.json']
    for n in(221,223,225,227,229):
        src=H/('hover_ultimate_native02'if n==229 else'hover_ultimate_body_layers01');paths={b:src/f'{n:03}_bank{b}_indices.png'for b in(0,5,6,7,8)};layers={b:np.array(Image.open(p))for b,p in paths.items()};new=compose(a,layers,15);need(label(np.array(new)[:,:,3]>0,np.ones((3,3)))[1]==1,'몸연결');old=a.composite(n,15)[0];lo=layers[5]>0;dist=distance_transform_cdt(~lo,metric='chessboard');row=next(q for q in m['frames']if q['ref']==n);cases=[];ims=[]
        for c in row['cases']:
            f=c['effect_frame'];jp=s/f'jet_{f:02}_indices.png';jet=np.array(Image.open(jp));need(sha(jet.tobytes())==c['indices_sha256'],'원효과변경');fx=Image.fromarray(pal[jet]);before=fx.copy();before.alpha_composite(old);after=fx.copy();after.alpha_composite(new);ims.extend([(f'{n} old jet{f}',before),(f'{n} new jet{f}',after)]);files.append(jp);cases.append({'effect_frame':f,'source_indexed_sha256':c['indices_sha256'],'old_overlap_lower':c['overlap_original_lower'],'new_overlap_lower':int(((jet>0)&lo).sum()),'old_min_chessboard':c['min_chessboard_to_any_lower_cell'],'new_min_chessboard':int(dist[jet>0].min()),'effect_world_shift':[0,0]})
        new.save(d/f'actual_{n}.png');page(ims,a.composite(0,0)[0],d/f'jet_{n}.png',cols=2,scale=5);proof.append({'ref':n,'source_layers':{str(b):{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}for b,p in paths.items()},'old_metrics':metrics(old),'new_metrics':metrics(new),'cases':cases});files.extend(paths.values());allims.extend([(f'{n} old actual15',old),(f'{n} new actual15',new)])
    for k in range(3):page(allims[k*4:k*4+4],a.composite(0,0)[0],d/f'body_comparison_{k:02}.png',cols=2,scale=5)
    write(d/'report.json',{'frames':proof,'actual_body_palettes':[0,16],'source_colors_diagnostic_only':True,'source_manifest_sha256':sha((s/'manifest.json').read_bytes()),'body_or_effect_changes_here':False,'runtime_verified':False,'art_acceptance_pending':True,'limits':['최소거리0은 하체와일부불꽃의겹침이며 양뒤꿈치정합 완전증명아님.','효과색은중립진단색이며 실제CLUT0x7802·블렌딩/실기별도.','221오른손높이1px차이는기록유지하고원외곽exact라고주장하지않음.'],'input_files':{p.relative_to(ROOT).as_posix():sha(p.read_bytes())for p in files}});print(json.dumps({r['ref']:[(c['new_overlap_lower'],c['new_min_chessboard'])for c in r['cases']]for r in proof}))
if __name__=='__main__':main()
