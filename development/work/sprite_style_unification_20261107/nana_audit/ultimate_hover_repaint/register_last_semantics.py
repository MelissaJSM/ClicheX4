"""229 종아리의 실제 그늘 표본3셀을 피부/중성 팔레트로 등록한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
def main():
 out=D/'semantic_last_v1';out.mkdir(exist_ok=False);p=D/'last_registered_v1/body_229_indices.png';old=np.array(Image.open(p));z=old.copy();a=Archive((N/'ultimate_vehicle_repaint/packed_vehicle_candidate_v1/PL02_U.ARC').read_bytes());pal=np.array([[((int(w)>>k)&31)*255//31 for k in(0,5,10)]for w in a.words[:16]],np.float32);im=Image.open(D/'b_v1/generated.png').convert('RGBA');ar=np.array(im);alpha=ar[:,:,3].astype(np.float32)/255;rgb=ar[:,:,:3].astype(np.float32);resize=lambda v:np.array(Image.fromarray(v.astype(np.float32),'F').resize((96,96),Image.Resampling.BOX));mass=resize(alpha);means=np.stack([resize(rgb[:,:,k]*alpha)/np.maximum(mass,.001)for k in range(3)],2);links=[]
 for x,y in [(7,12),(5,16),(8,18)]:
  need(z[y+160,x+160]==5,'소스 붉은 그늘');mean=means[y+48,x+48];allowed=np.array([1,2,3,4,10,11,12,13]);value=int(allowed[((pal[allowed]-mean)**2).sum(1).argmin()]);links.append({'world':[x,y],'old':5,'new':value,'source_alpha_weighted_rgb':mean.tolist(),'meaning':'새 긴 종아리의 바깥 그늘. 머리/허리띠가 아니며 실제 생성RGB 의미양자화.'});z[y+160,x+160]=value
 need(np.array_equal(old>0,z>0),'원화 알파불변');Image.fromarray(z).save(out/'body_229_indices.png');helper.grid([('229',[('old fixed source',a.rgba(old)),('actual shadow samples',a.rgba(z)),('idle skin',a.composite(0)[0])])],out/'comparison.png',7);write(out/'manifest.json',{'source':p.relative_to(ROOT).as_posix(),'source_sha256':digest(p),'source_art':(D/'b_v1/generated.png').relative_to(ROOT).as_posix(),'source_art_sha256':digest(D/'b_v1/generated.png'),'links':links,'target_sha256':sha(z.tobytes()),'alpha_exact':True,'scope':'229 실제 원화 표본3셀의 피부/중성그늘 등록. 형상/기존그림복사 없음.'});print(json.dumps(links))
if __name__=='__main__':main()
