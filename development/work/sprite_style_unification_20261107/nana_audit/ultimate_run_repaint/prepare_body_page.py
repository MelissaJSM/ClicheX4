"""남은 이동 몸체4개씩 원점보존 입력을 만든다. 새 원화 호출은 별도."""
from pathlib import Path
import sys,json,argparse,shutil
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,write,need,helper
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--refs',nargs=4,type=int,required=True);args=p.parse_args();out=D/args.out;need(D.resolve()in out.resolve().parents and not out.exists(),'Fresh scope');need(all(n in range(1,33,2)for n in args.refs)and len(set(args.refs))==4,'Odd run keys');src=N/'ultimate_wall_repaint/packed_wall_candidate_v1/PL02_U.ARC';need(digest(src)=='e151044c37b5a59016f10d8c4d9637ffd4e192563f03c6a76df528383cfb4031','Parent');a=Archive(src.read_bytes());out.mkdir();sheet=Image.new('RGBA',(1536,1536));window=(112,112,208,208)
 for i,n in enumerate(args.refs):
  im=a.composite(n,15)[0];outside=np.array(im)[:,:,3].copy();outside[112:208,112:208]=0;need(not outside.any(),'Crop');sheet.alpha_composite(im.crop(window).resize((768,768),Image.Resampling.NEAREST),(i%2*768,i//2*768))
  shutil.copy2(D/f'inputs_first_v1/before_{n:03}_indices.png',out/f'before_{n:03}_indices.png')
 sheet.save(out/'old_before_targets.png');shutil.copy2(D/'inputs_first_v1/before_accepted_style.png',out/'accepted_style.png');shutil.copy2(D/'before_first_v1/generated.png',out/'new_run_detail_reference.png');meta=json.loads((D/'inputs_first_v1/manifest.json').read_text('utf8'));meta.update(first_keys=args.refs,input_images={p.name:digest(p)for p in out.glob('*.png')},new_art_generated=False);write(out/'manifest.json',meta);helper.grid([(f'next {n}',[('idle',a.composite(0,15)[0]),('target pose',a.composite(n,15)[0])])for n in args.refs],out/'pose_review.png',5);print(out)
if __name__=='__main__':main()
