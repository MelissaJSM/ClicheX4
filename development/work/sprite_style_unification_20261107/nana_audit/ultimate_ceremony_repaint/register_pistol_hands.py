"""권총/손 편집 원화를 실제 전체 셀 고정 축척으로 읽고 국소 후보를 만든다."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint')]
from preview_restore import Archive,sha,digest,write,need,helper
from register_page import register
POLY={
133:[(-27,7),(-14,7),(-11,8),(-11,10),(-12,13),(-13,17),(-16,22),(-27,24)],
135:[(-20,-20),(-12,-20),(-12,-16),(-10,-13),(-9,-10),(-7,-9),(-7,-4),(-10,-3),(-15,-5),(-20,-10)],
136:[(-23,-25),(-14,-25),(-14,-19),(-12,-15),(-10,-12),(-9,-10),(-9,-7),(-11,-5),(-14,-5),(-20,-10)],
137:[(-22,-36),(-10,-36),(-10,-27),(-11,-23),(-9,-20),(-9,-17),(-10,-14),(-15,-14),(-22,-22)]}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',default='pistol_hands_registered_v1');args=ap.parse_args();out=D/args.out;out.mkdir(exist_ok=False);a=Archive((N/'ultimate_hurt_repaint/packed_hurt_candidate_v1/PL02_U.ARC').read_bytes());records=[];rows=[]
 for group in('a','b'):
  meta=json.loads((D/f'pistol_hands_{group}_inputs_v1/manifest.json').read_text('utf8'));g=json.loads((D/f'pistol_hands_{group}_v1/generation.json').read_text('utf8'));art=ROOT/g['workspace_path'];need(digest(art)==g['workspace_sha256'],'원화');im=Image.open(art).convert('RGBA')
  for q in meta['frames']:
   i,n,form=q['cell'],q['ref'],q['form'];start=16 if form=='before'else 0;crop=tuple(round(v)for v in(i%2*im.width/2,i//2*im.height/2,(i%2+1)*im.width/2,(i//2+1)*im.height/2));cell=im.crop(crop);arr=np.array(cell);pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32);fixed=np.zeros((384,384),np.uint8);fixed[112:208,112:208]=register(cell,(96,96),pal,'area_vote');p=ROOT/q['source'];need(digest(p)==q['source_sha256'],'새몸');base=np.array(Image.open(p));mi=Image.new('L',(384,384));ImageDraw.Draw(mi).polygon([(x+160,y+160)for x,y in POLY[n]],fill=1);m=np.array(mi)>0;target=base.copy();target[m]=fixed[m];need(np.array_equal(target[~m],base[~m]),'보호된 새몸')
   for tag,z in(('fixed',fixed),('local',target),('mask',m.astype(np.uint8)*255)):Image.fromarray(z).save(out/f'{form}_{n:03}_{tag}.png')
   comps=int(label(target>0,np.ones((3,3)))[1]);records.append({'ref':n,'form':form,'source_art':art.relative_to(ROOT).as_posix(),'source_art_sha256':digest(art),'source_crop':list(crop),'fixed_cell_native':[96,96],'source_size':list(im.size),'base_path':p.relative_to(ROOT).as_posix(),'base_sha256':digest(p),'polygon':POLY[n],'changed_pixels':int((target!=base).sum()),'components8':comps,'outside_edit_changes':0,'target_sha256':sha(target.tobytes())});rows.append((f'{form} {n}',[('new body before pistol',a.rgba(base,start)),('generated fixed cell',a.rgba(fixed,start)),('local hand only',a.rgba(target,start))]))
   x0,y0,x1,y1=(-28,-38,1,26);s=14;w=(x1-x0)*s+45;board=Image.new('RGB',(w*2,(y1-y0)*s+55),'#b6c0c7');dr=ImageDraw.Draw(board)
   for j,(z,title)in enumerate(((base,'new body'),(fixed,'new gun/hand donor'))):
    ox=j*w+35;oy=50;pic=a.rgba(z,start).crop((160+x0,160+y0,160+x1,160+y1)).resize(((x1-x0)*s,(y1-y0)*s),Image.Resampling.NEAREST);board.paste(pic,(ox,oy),pic);dr.text((ox,3),f'{form} {n} {title}',fill='black')
    for x in range(x0,x1):dr.text((ox+(x-x0)*s,30),str(x),fill='black')
    for y in range(y0,y1):dr.text((ox-30,oy+(y-y0)*s),str(y),fill='black')
    for x in range(x0,x1+1):dr.line((ox+(x-x0)*s,oy,ox+(x-x0)*s,oy+(y1-y0)*s),fill='#879099')
    for y in range(y0,y1+1):dr.line((ox,oy+(y-y0)*s,ox+(x1-x0)*s,oy+(y-y0)*s),fill='#879099')
   board.save(out/f'{form}_{n:03}_grid.png')
 for i in range(0,len(rows),2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',7)
 write(out/'manifest.json',{'frames':records,'method':'전체 셀 고정96 축척, 실제 원화 면적투표16색 후 손/총 의미영역만 교체. 새 머리/몸/다리 보존, 정본8px 모듈·공통손 정합 전.','native_packed':False,'runtime_verified':False});print(json.dumps([{k:r[k]for k in('ref','form','changed_pixels','components8')}for r in records]))
if __name__=='__main__':main()
