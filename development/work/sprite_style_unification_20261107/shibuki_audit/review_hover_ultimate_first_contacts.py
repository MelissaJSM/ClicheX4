"""새 호버 첫4와 원추진15 중12위상의 동일원점 정적비교."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_cdt
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
from prepare_hover_ultimate_inputs import P,PARENT,CUTS
def main():
    d=H/'hover_ultimate_contact_probe01';need(not d.exists(),'새 비교');a=Archive(P.read_bytes());need(sha(a.data)==PARENT,'부모 변경');s=H/'hover_ultimate_contact_sources01';m=json.loads((s/'manifest.json').read_text('utf8'));d.mkdir();proof=[];pal=np.zeros((16,4),np.uint8)
    for i in range(1,16):pal[i]=[60+i*10,70+i*8,110+i*5,255]
    for n in(221,223,225,227):
        old=a.composite(n,15)[0];p=H/f'hover_ultimate_native01/{n:03}_indices.png';z=np.array(Image.open(p));new=a.rgba(z);lo=z>0;lo[:160+CUTS[n]]=False;dist=distance_transform_cdt(~lo,metric='chessboard');row=next(q for q in m['frames']if q['ref']==n);cases=[];ims=[]
        for c in row['cases']:
            f=c['effect_frame'];jet=np.array(Image.open(s/f'jet_{f:02}_indices.png'));need(sha(jet.tobytes())==c['indices_sha256'],'원효과변경');fx=Image.fromarray(pal[jet]);before=fx.copy();before.alpha_composite(old);after=fx.copy();after.alpha_composite(new);ims.extend([(f'{n} old jet{f}',before),(f'{n} new jet{f}',after)]);cases.append({'effect_frame':f,'source_indexed_sha256':c['indices_sha256'],'old_overlap_lower':c['overlap_original_lower'],'new_overlap_lower':int(((jet>0)&lo).sum()),'old_min_chessboard':c['min_chessboard_to_any_lower_cell'],'new_min_chessboard':int(dist[jet>0].min()),'effect_world_shift':[0,0]})
        page(ims,a.composite(0,0)[0],d/f'comparison_{n}.png',cols=2,scale=5);proof.append({'ref':n,'source':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes()),'cases':cases})
    write(d/'report.json',{'frames':proof,'source_manifest_sha256':sha((s/'manifest.json').read_bytes()),'source_colors_diagnostic_only':True,'body_or_effect_changes':False,'runtime_verified':False,'art_acceptance_pending':True,'known_error':'221 오른쪽팔이 허리로 내려가 있어 국소교정 대기.접점판이 해당포즈 수용의미가 아님.','limits':['최소거리0은 하체와일부불꽃이겹친다는수치이며 양뒤꿈치정합 완전증명이 아니다.','별도효과를 중립색으로 표시한 원점진단이며0x7802실제색·실시간블렌딩·전체게임미검증.']});print(json.dumps(proof))
if __name__=='__main__':main()
