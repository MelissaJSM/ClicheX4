"""새 귀환 전후 의상: 최초 전신의 머리/다리, 후폼 원화의 팔, 국소 새 하의."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(D)]
from preview_restore import Archive,digest,sha,write,need,helper
import register_body as rb
WAIST=[(-6,1),(-3,0),(1,0),(3,1),(6,1),(8,3),(8,6),(6,8),(2,8),(-2,7),(-6,6),(-7,4)]
COSTUME=[(-7,-10),(-4,-10),(0,-11),(3,-9),(5,-7),(5,-5),(6,-3),(6,-1),(6,1),(8,3),(8,6),(6,8),(2,8),(-2,7),(-6,6),(-7,4),(-6,1),(-8,-1),(-10,-3),(-11,-6),(-9,-8)]

def poly(points):
 im=Image.new('L',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in points],fill=1);return np.array(im)>0

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--version',choices=['v1','v2'],default='v2');args=ap.parse_args()
 out=D/f'costume_pair_probe_{args.version}';out.mkdir(exist_ok=False)
 p=N/'ultimate_victory_repaint/packed_victory_candidate_v1/PL02_U.ARC';a=Archive(p.read_bytes())
 bp=D/'body_registered_v1/before_156_indices.png';ap=D/'body_registered_v1/after_156_indices.png';b=np.array(Image.open(bp));initial=np.array(Image.open(ap))
 art=D/'costume_edit_v1/generated.png';need(digest(art)=='de834c6b7b77993e8f76080fac2cbc7fb5ba9dd252857e3662ca4a6baa66963f','국소 원화')
 im=Image.open(art).convert('RGBA');pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[:16]],np.float32)
 fixed=np.zeros((384,384),np.uint8);fixed[96:224,112:208]=rb.reg.register(im.crop((768,0,1536,1024)),(96,128),pal,'area_vote')
 donor=np.zeros_like(fixed);donor[:,4:]=fixed[:,:-4]
 wp=WAIST if args.version=='v1' else [(x,min(y,7))for x,y in WAIST]
 cp=COSTUME if args.version=='v1' else [(x,min(y,7))for x,y in COSTUME]
 boundary=[]
 if args.version=='v2':
  original=np.array(Image.open(D/'body_v1/generated.png').convert('RGBA'));x,y=5,5
  cell=original[(y+64)*8:(y+65)*8,(x+48)*8:(x+49)*8];opaque=cell[:,:,3]>=128;need(int(opaque.sum())==30,'최초 원화 경계30/64')
  rgb=np.median(cell[:,:,:3][opaque],axis=0);idx=int(np.argmin(np.sum((pal[1:]-rgb)**2,axis=1)))+1;need(idx==1 and b[165,165]==0,'실제 어두운 반바지 경계')
  b[165,165]=idx;boundary=[{'world':[5,5],'source_native_sample_rect':[424,552,432,560],'opaque_samples':30,'total_samples':64,'sample_median_rgb':rgb.tolist(),'index':idx,'reason':'면적투표에서 절반 미만으로 빠진 최초 재킷 원화의 실제 어두운 반바지 끝을1셀 복원. 새 donor 하의 윤곽과 같은 위치이며 다른외곽 확장 없음.'}]
 wm=poly(wp);cm=poly(cp);after_source=initial.copy();after_source[wm]=donor[wm]
 after=b.copy();after[b==15]=13;after[cm]=after_source[cm]
 need(np.array_equal(after[~cm],np.where(b==15,13,b)[~cm]),'새 공통 머리/다리 보존')
 outside=(after>0)&(b==0)
 for tag,z in [('before',b),('after',after),('after_source',after_source),('waist_donor',donor),('waist_mask',wm.astype(np.uint8)*255),('costume_mask',cm.astype(np.uint8)*255)]:Image.fromarray(z).save(out/f'{tag}_156.png')
 helper.grid([('before156',[('idle',a.composite(0,15)[0]),('previous',a.composite(156,15)[0]),('new body',a.rgba(b,16)),('new body',a.rgba(b,16))]),('after156',[('idle',a.composite(0,0)[0]),('initial wrong shorts',a.rgba(initial)),('local costume donor',a.rgba(after_source)),('shared new candidate',a.rgba(after))])],out/'comparison.png',7)
 result={'parent_arc_sha256':digest(p),'before_source':bp.relative_to(ROOT).as_posix(),'before_source_sha256':digest(bp),'after_body_source':ap.relative_to(ROOT).as_posix(),'after_body_source_sha256':digest(ap),'local_art':art.relative_to(ROOT).as_posix(),'local_art_sha256':digest(art),'local_fixed_source_crop':[768,0,1536,1024],'local_native_size':[96,128],'donor_translation':[4,0],'donor_translation_reason':'생성된 오른쪽 전신의 수평4px 이탈을 허리 의상 donor에만 강체 정합. 몸 전체·새 머리·다리는 교체하지 않음.','waist_polygon':wp,'costume_polygon':cp,'original_source_boundary':boundary,'donor_leg_excluded_from_costume':[[3,8]]if args.version=='v2'else[],'replaced_waist_pixels':int(np.count_nonzero(after_source!=initial)),'outside_before':[[int(x-160),int(y-160),int(after[y,x])]for y,x in np.argwhere(outside)],'before_components8':int(label(b>0,np.ones((3,3)))[1]),'after_components8':int(label(after>0,np.ones((3,3)))[1]),'before_sha256':sha(b.tobytes()),'after_sha256':sha(after.tobytes()),'floor_before_after':[rb.vreg.bbox(b)[3],rb.vreg.bbox(after)[3]],'eyes_before_after':[rb.vreg.eye(b),rb.vreg.eye(after)],'alpha_clipped':False,'old_body_copied':False,'native_packed':False,'runtime_verified':False}
 write(out/'manifest.json',result);print(json.dumps({k:result[k]for k in('replaced_waist_pixels','outside_before','before_components8','after_components8','floor_before_after','eyes_before_after')}))
if __name__=='__main__':main()
