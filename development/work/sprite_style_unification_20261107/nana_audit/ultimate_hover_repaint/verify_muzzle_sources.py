"""생성10고정셀부터 실제표본·권총·발사팔·상하체50층을 자체 재구성한다."""
from pathlib import Path
import sys,json,importlib.util
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need

def module(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
reg=module('hover_requantize',N/'base_run_repaint/register_page.py')
sem=module('hover_vote',N/'ultimate_standing_repaint/prepare_common.py')
Y,X=np.indices((384,384));Y-=160;X-=160
def box(b):return(X>=b[0])&(Y>=b[1])&(X<b[2])&(Y<b[3])
def poly(points):
 im=Image.new('1',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in points],fill=1);return np.array(im,dtype=bool)
def read(p):return json.loads(p.read_text('utf8'))
def same(z,p):need(np.array_equal(z,np.array(Image.open(p))),'출처재구성 '+str(p.relative_to(D)))
def means(cell):
 ar=np.array(cell);rgb=ar[:,:,:3].astype(np.float32);alpha=ar[:,:,3].astype(np.float32)/255
 resize=lambda v:np.array(Image.fromarray(v.astype(np.float32),'F').resize((96,96),Image.Resampling.BOX))
 mass=resize(alpha);return np.stack([resize(rgb[:,:,k]*alpha)/np.maximum(mass,.001)for k in range(3)],2)
def main():
 td=D/'targets_preview_v3';tm=read(td/'manifest.json');p=ROOT/tm['parent_arc'];need(digest(p)==tm['parent_arc_sha256'],'차량 동결 부모')
 a=Archive(p.read_bytes());pal=np.array([[((int(w)>>k)&31)*255//31 for k in(0,5,10)]for w in a.words[:16]],np.float32)
 source={};cells={};rgbmeans={};proof=[]
 for folder in('first_registered_v1','last_registered_v1','muzzle_arm_a_registered_v1','muzzle_arm_b_registered_v1'):
  m=read(D/folder/'manifest.json');art=ROOT/m['source_art'];need(digest(art)==m['source_art_sha256'],'생성 원화 hash');im=Image.open(art).convert('RGBA');need(im.size==(1254,1254),'전체캔버스 크기')
  for q in m['frames']:
   n=q['ref'];cell=im.crop(q['crop']);z=np.zeros((384,384),np.uint8);z[112:208,112:208]=reg.register(cell,(96,96),pal,'area_vote');same(z,D/folder/f'body_{n:03}_indices.png');source[n]=z;cells[n]=cell;rgbmeans[n]=means(cell);proof.append({'ref':n,'source_art_sha256':digest(art),'crop':q['crop'],'registered_sha256':sha(z.tobytes())})
 body={};iris=skin=0;allowed=np.array([1,2,3,4,10,11,12,13])
 for q in read(D/'semantic_samples_v1/manifest.json')['frames']:
  n=q['ref'];z=source[n].copy();need(sha(z.tobytes())==q['source_sha256'],'의미표본 등록부모')
  for e in q['iris_source_registration']:
   x,y=e['world'];need(int(z[y+160,x+160])==e['old'],'눈 표본 전색')
   if e['new']==14:
    _,votes=sem.source_vote(cells[n],pal,(x,y),set());need(votes['14']>=.2 and abs(votes['14']-e['green_fraction'])<1e-7,'동일셀 실제 녹색분율')
   else:
    value,votes=sem.source_vote(cells[n],pal,(x,y),{14,15});need(value==e['new']and votes==e['votes'],'동일셀 비홍채 표본')
   z[y+160,x+160]=e['new'];iris+=1
  for e in q['skin_source_registration']:
   x,y=e['world'];mean=rgbmeans[n][y+48,x+48];value=int(allowed[((pal[allowed]-mean)**2).sum(1).argmin()]);need(int(z[y+160,x+160])==e['current_index']and value==e['nearest_nonpink_index'],'다리 실제RGB 의미색');need(np.allclose(mean,e['source_alpha_weighted_mean_rgb'],atol=1e-6),'다리 원RGB');z[y+160,x+160]=value;skin+=1
  need(np.array_equal(z>0,source[n]>0),'의미색 알파불변');same(z,D/f'semantic_samples_v1/body_{n:03}_indices.png');body[n]=z
 q=read(D/'semantic_last_v1/manifest.json');z=source[229].copy()
 for e in q['links']:
  x,y=e['world'];mean=rgbmeans[229][y+48,x+48];value=int(allowed[((pal[allowed]-mean)**2).sum(1).argmin()]);need(int(z[y+160,x+160])==e['old']and value==e['new']and np.allclose(mean,e['source_alpha_weighted_rgb'],atol=1e-6),'229 그림자 실제RGB');z[y+160,x+160]=value;skin+=1
 same(z,D/'semantic_last_v1/body_229_indices.png');body[229]=z
 cm=read(D/'canonical_cases_probe_v4/manifest.json');canonical=a.layer(85)[0];gm=box([-22,-11,-14,-5])&np.isin(canonical,range(1,10));coords=[[int(x-160),int(y-160),int(canonical[y,x])]for y,x in np.argwhere(gm)];need(coords==cm['canonical_source_texels']and len(coords)==20,'정본85 직접 재독출20')
 held={};canonical_visible=canonical_occluded=0
 for q in cm['frames']:
  n=q['ref'];v=body[n];z=v.copy();remove=np.zeros_like(z,dtype=bool)
  for b in q['removal_boxes']:remove|=box(b)
  removed=[[int(x-160),int(y-160),int(v[y,x])]for y,x in np.argwhere(remove&(v>0))];need(removed==q['removed_source_cells'],'새생성총 제거 의미영역');z[remove]=0;case=np.zeros_like(z);dx,dy=q['translation']
  for x,y,i in coords:case[y+dy+160,x+dx+160]=i
  hx,hy=q['hand_anchor'];hand=box([hx-1,hy,hx+3,hy+5])&np.isin(v,[10,11,12,13])&~remove;use=(case>0)&~hand;z[use]=case[use]
  need(int(use.sum())==q['visible_case_texels']and int(((case>0)&hand).sum())==q['skin_occluded_case_texels'],'정본/새피부손 가림');same(z,D/f'canonical_cases_probe_v4/body_{n:03}_indices.png');same(case,D/f'canonical_cases_probe_v4/case_{n:03}_indices.png');same(hand.astype(np.uint8)*255,D/f'canonical_cases_probe_v4/hand_{n:03}.png');held[n]=z;canonical_visible+=int(use.sum());canonical_occluded+=int(((case>0)&hand).sum())
 shot={};arm_pieces=grip_removed=0;origins={q['ref']:q['direction0_xy']for q in read(N.parent/'zero_audit/nana_ultimate_hover_muzzle01/report.json')['origins']}
 for q in read(D/'muzzle_joint_probe_v1/manifest.json')['frames']:
  n=q['ref'];base=held[n-1];donor=source[n].copy();mask=poly(q['source_polygon']);piece=np.where(mask,donor,0)
  for x,y,index in q['source_generated_grip_removed_cells']:need(int(piece[y+160,x+160])==index,'?? ?? ???');piece[y+160,x+160]=0;grip_removed+=1
  dx,dy=q['source_translation'];placed=np.roll(np.roll(piece,dy,0),dx,1);z=base.copy();remove=box(q['removed_held_window']);z[remove]=0;head=(X>=-8)&(Y<=-10);opposite=(X>=1)&(Y<=-7);use=(placed>0)&~(head|opposite);z[use]=placed[use];gun=np.zeros_like(z);tx,ty=q['canonical_translation'];ox,oy=origins[n];need(q['engine_projectile_origin']==origins[n]and(tx,ty)==(ox+23,oy+9),'???? ?? ??')
  for x,y,i in coords:gun[y+ty+160,x+tx+160]=i
  skinmask=box([ox+4,oy,ox+11,oy+6])&np.isin(placed,[10,11,12,13]);guse=(gun>0)&~skinmask;z[guse]=gun[guse];need(int(guse.sum())==q['canonical_visible']and int(((gun>0)&skinmask).sum())==q['canonical_skin_occluded'],'??? ??')
  same(z,D/f'muzzle_joint_probe_v1/body_{n:03}_indices.png');same(piece,D/f'muzzle_joint_probe_v1/source_arm_{n:03}_indices.png');same(placed,D/f'muzzle_joint_probe_v1/placed_arm_{n:03}_indices.png');same(gun,D/f'muzzle_joint_probe_v1/canonical_{n:03}_indices.png');need(np.array_equal(z[head],base[head])and np.array_equal(z[Y>=3],base[Y>=3]),'???/?? ??');need(sha(z.tobytes())==q['target_sha256'],'?? hash');shot[n]=z;arm_pieces+=1
 targets=[];metrics=[]
 for q in tm['frames']:
  n=q['ref'];z=(held if n%2 else shot)[n];cut=q['cut_world_y'];up=z.copy();up[160+cut:]=0;down=z.copy();down[:160+cut]=0;layers={0:up,5:down,6:np.zeros_like(z),7:np.zeros_like(z),8:np.zeros_like(z)};need(label(z>0,np.ones((3,3)))[1]==1,'전신 연결');need(not np.any(z==15),'팔레트15 혼동없음')
  for pb,v in layers.items():same(v,td/f'layer{pb}_{n:03}.png');need(sha(v.tobytes())==tm['targets'][str(n)][str(pb)],'50층hash');targets.append([n,pb,sha(v.tobytes())])
  yy,xx=np.nonzero(z);metrics.append({'ref':n,'bbox':[int(xx.min()-160),int(yy.min()-160),int(xx.max()-159),int(yy.max()-159)],'opaque':int((z>0).sum()),'components8':1})
 need(len(proof)==10 and iris==9 and skin==20 and arm_pieces==5 and len(targets)==50,'증거 범위')
 out=td/'source_reconstruction.json';need(not out.exists(),'고유 출처증거 경로');write(out,{'passed':True,'parent_sha256':digest(p),'target_manifest_sha256':digest(td/'manifest.json'),'generated_fixed_cells_requantized':proof,'iris_source_samples':iris,'lower_body_rgb_samples':skin,'new_muzzle_arm_pieces':arm_pieces,'generated_grip_source_cells_removed':grip_removed,'canonical_pistol_source_texels':20,'held_visible_canonical_texels':canonical_visible,'held_skin_occluded_texels':canonical_occluded,'old_firing_8column_preservation_policy_rejected':True,'native_muzzle_table_bound_to_independent_static_audit':True,'new_native_execution':False,'targets_exact':targets,'body_metrics':metrics,'scope':'생성10고정셀 재양자화부터 원화 의미색/새권총·팔/원8열 무기창/원상하체50층을 자체 재구성했다. 발사 좌표·탄환 오프셋 추가조사 전의 진단후보이며 독립·원MIPS·실기와 구분한다.'});print(json.dumps({'passed':True,'cells':10,'layers':50,'iris':iris,'lower_skin':skin,'muzzle_arm_pieces':arm_pieces,'sha256':digest(out)}))
if __name__=='__main__':main()
