"""사격 원화 전체격자 표본만 등록한다. 신체에 채택하기 전 donor 검사."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
from prepare_hover_ultimate_inputs import P,PARENT
def main():
    pi=int(sys.argv[1]);default=sys.argv[2];s=H/f'hover_ultimate_shot_inputs01/page{pi:02}';d=H/f'hover_ultimate_shot_page{pi:02}_registered01';need(not d.exists(),'기존등록보호');m=json.loads((s/'input.json').read_text('utf8'));g=s/'generated_v1.png';a=Archive(P.read_bytes());need(sha(a.data)==PARENT,'부모변경')
    for name,h in m['files'].items():need(sha((s/name).read_bytes())==h,'입력변경')
    im=Image.open(g).convert('RGBA');need(im.width==im.height,'전체정사각격자');ls=m['layout'];cellsize=ls['cell'];origin=ls['origin'];whole=np.array(im.resize((ls['logical_canvas'],ls['logical_canvas']),Image.Resampling.NEAREST));rgb=np.array([[(int(w)>>k&31)*255//31 for k in(0,5,10)]for w in a.words[:16]],np.int32);d.mkdir();rows=[];ims=[]
    for i,n in enumerate(m['refs']):
        x=i%ls['columns']*cellsize;y=i//ls['columns']*cellsize;cell=whole[y:y+cellsize,x:x+cellsize];ind=(1+((cell[:,:,:3].astype(np.int32)[:,:,None]-rgb[None,None,1:])**2).sum(3).argmin(2)).astype(np.uint8);ind[cell[:,:,3]<128]=0;need(not(ind[0].any()or ind[-1].any()or ind[:,0].any()or ind[:,-1].any()),'셀경계');z=np.zeros((384,384),np.uint8);z[160-origin:160-origin+cellsize,160-origin:160-origin+cellsize]=ind;Image.fromarray(z).save(d/f'{n:03}_indices.png');Image.fromarray(cell).save(d/f'{n:03}_sample.png');a.rgba(z).save(d/f'{n:03}.png');lab,_=label(ind>0,np.ones((3,3)));sizes=sorted(np.bincount(lab.ravel())[1:].tolist(),reverse=True);rows.append({'ref':n,'cell':i,'metrics':metrics(a.rgba(z)),'components':sizes,'indices_sha256':sha(z.tobytes()),'known_visual_error':'222옛높은왼주먹잔류·팔3개라채택금지'if n==222 else None});ims.extend([(f'{n} original pose',a.composite(n,15)[0]),(f'{n} generated donor',a.rgba(z))])
    for i in range((len(ims)+3)//4):page(ims[i*4:i*4+4],a.composite(0,0)[0],d/f'comparison_{i:02}.png',cols=2,scale=6)
    write(s/'generation.json',{'tool':'builtin imagegen','default_saved_path':default,'workspace_path':g.relative_to(ROOT).as_posix(),'sha256':sha(g.read_bytes()),'actual_size':list(im.size),'prompt_sha256':sha((s/'prompt.txt').read_bytes()),'asset_saved':True,'accepted':False})
    write(d/'registration.json',{'source':g.relative_to(ROOT).as_posix(),'source_sha256':sha(g.read_bytes()),'whole_grid':ls,'alpha_cutoff':128,'sprite_specific_scaling':False,'native_palette_for_upper_arm':0,'whole_body_adoption':False,'frames':rows,'canonical_barrel_restore_pending':True,'files':{p.relative_to(ROOT).as_posix():sha(p.read_bytes())for p in[s/'input.json',s/'generation.json',g,Path(__file__),*d.glob('*.png')]}});print(json.dumps(rows))
if __name__=='__main__':main()
