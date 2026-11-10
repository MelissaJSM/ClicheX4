"""대시 사격 원화의 실제 크기 후보. 팔 확장이나 옛 몸체 복제 없음."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(D),str(D.parent/'native_restore')]
from refine_second_inputs import one,crop_count
from register_last_keys import horizontal_crop
from preview_restore import Archive,sha,digest,need,write,helper
PAGES={'a':('basic_firing_a_v1',(68,70,72,76),'c4b2bf0dcbd062660c8e68df4695557e4f306f56e25f78bc2b8a124255591ca2'),
       'b':('basic_firing_b_v1',(78,80,82,84),'105f9e53027c01cb9c969c828105b69b55e026c91269d2f394268ef2ec94ec97'),
       'lowreach':('low_arm_reach_v1',(72,76),'041d117dc7fbba7acdf565cbc2b7409908a93c51a898a620cef0c52788255f06'),
       'reach_a2':('arm_reach_a_v2',(68,70,72,76),'50dc0a6eb40510222b259774446f6e35c65783b231c647d3e41acaf373137d6e'),
       'reach_b2':('arm_reach_b_v2',(78,80,82,84),'8864f50778ebda0aefda0191c2cfd373a4030878c150eeb03b50d47d08bbc768')}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--page',choices=PAGES,default='a');args=ap.parse_args();folder,refs,expected=PAGES[args.page]
    plan=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/plan['parent_arc']).read_bytes());need(sha(a.data)==plan['parent_arc_sha256'],'Parent');src=D/folder/'generated.png';need(digest(src)==expected,'Source');im=Image.open(src).convert('RGBA');out=D/f'basic_firing_{args.page}_registered_v1';need(not out.exists(),'Fresh output');out.mkdir();pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[:16]],np.float32);frames=[];rows=[]
    for i,n in enumerate(refs):
        q=next(q for q in plan['frames']if q['ref']==n);crop,box=horizontal_crop(im,i)if len(refs)==2 else crop_count(im,i,len(refs));new,r=one(crop,q,pal);crop.save(out/f'source_{n:03}.png');Image.fromarray(new).save(out/f'base_{n:03}.png');a.rgba(new).save(out/f'base_{n:03}_rgba.png');yy,xx=np.nonzero(new);r.update(ref=n,source_crop=box,source_art_sha256=expected,indexed_sha256=sha(new.tobytes()),components_8=int(label(new>0,np.ones((3,3)))[1]),native_bbox=[int(xx.min()-160),int(yy.min()-160),int(xx.max()+1-160),int(yy.max()+1-160)],old_game_pixels_used=0);frames.append(r)
        rows.append((f'dash shot {n}',[('기존',a.composite(n)[0]),('새 원화 직접등록',a.rgba(new)),('승인 대기',a.composite(0)[0])]))
    helper.grid(rows,out/'comparison.png',7);write(out/'registration.json',{'source_arc_sha256':sha(a.data),'source_art_sha256':expected,'frames':frames,'scope':'사격팔 원화의 직접 등록 진단. 총구와 새 비사격 몸체 합성 전.','native_packed':False,'runtime_verified':False});print(json.dumps(frames))
if __name__=='__main__':main()
