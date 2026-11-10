"""Ultimate 고유 피격 출처와 새 전후 몸체를 연결하는 정적 후보."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,same_rgba
from scripts.export_x_consistency import Archive,page
from prepare_shibuki_hurt_effects import render,silhouette
from prepare_lowhp_final import compose
P=H/'prepared_ultimate_ladder01/PL02_U.ARC'
PARENT='03a675626035b93ad2e2feef8dd643365ed8a3e1a61a1eb02a476063e2c55e8a'
AUDIT=H.parent/'zero_audit/shibuki_hurt_sources01'
PBS=(0,5,6,7,8);BODIES=(106,110,233,234);REFS=tuple(range(106,115))+tuple(range(233,237))

def main():
 o=H/'ultimate_hurt_effect_probe02';need(not o.exists(),'Fresh effects');o.mkdir()
 need(sha(P.read_bytes())==PARENT,'Parent changed');a=Archive(P.read_bytes())
 ab=(AUDIT/'report.json').read_bytes();need(sha(ab)=='202898054ae9061a626b1a9088bfde79bf3ef15339963acfc3f4d3d0c49b348c','Source audit changed');ar=json.loads(ab)['archives'][1];need(ar['source_sha256']==PARENT,'Audit parent')
 src=H/'ultimate_hurt_common_probe02';targets={};bodies={};fulls={};rows=[];files={};fxrecords={}
 def load(p):
  files[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes());return np.load(p)if p.suffix=='.npy'else np.array(Image.open(p))
 for n in BODIES:
  before=load(src/f'before_{n:03}_indices.png');after=load(src/f'after_{n:03}_indices.png');need(not np.any((after>0)&(before==0)),'After outside jacket')
  ls={0:after,5:np.where(same_rgba(a,before,after),0,before).astype(np.uint8),**{b:np.zeros_like(after)for b in(6,7,8)}}
  for b in(6,7,8):need(not a.layer(n,b)[0].any(),'Previously independent armor nonempty')
  targets[n]=ls;bodies[n]=ls;fulls[n]=before;rows.append({'ref':n,'body':n,'policy':'새전후몸체의실제RGBA차이만layer5.머리/사지구형덮기없음.'})
 for q in ar['effects']:
  n,core=q['ref'],q['core'];ls={b:v.copy()for b,v in bodies[core].items()}
  if n in(107,108):
   fx=load(ROOT/q['effect_npy']);need(set(map(int,np.unique(fx)))=={0,8},'Original spark colors')
   policy='원US 출처99/76개의전기픽셀 전체를새106위에표시.구형합성에서몸체와섞여22~25px가가려졌던결과를그대로복사하지않음.정적미술검토후보.'
   record_source='원US PL02 original_effect_parts/6·7타일.현재PL02타일번호로직접읽지않음.'
  else:
   fx=render(a,n,0,q['actual_CLUT2_records']);need(np.count_nonzero(fx)==194,'Actual Ultimate111 count');fxrecords[n]={0:q['actual_CLUT2_records']}
   policy='현재PL02 실제CLUT2 효과194픽셀을원파트순서대로새110위에표시.기본형202/Nana188혼용없음.';record_source='현재PL02 actual_CLUT2_records'
  # The exact effect tiles can be shared by both costume records. 111 keeps
  # its original CLUT2 base records; its index3 is the same RGB555 in all
  # three relevant CLUT rows, so layer5 repeats the same visible colour.
  for idx in np.unique(fx[fx>0]):need(a.words[int(idx)]==a.words[16+int(idx)%16],'Effect CLUT differs')
  ls[0]=np.where(fx,fx,ls[0]).astype(np.uint8);ls[5]=np.where(fx,fx%16,ls[5]).astype(np.uint8);targets[n]=ls
  Image.fromarray(fx).save(o/f'{n:03}_effect_indices.png');rows.append({'ref':n,'body':core,'policy':policy,'effect_pixels':int((fx>0).sum()),'effect_sha256':sha(fx.tobytes()),'source':record_source,'old_core_plus_original_effect_differences':{f:v['core_plus_original_effect_index_diff']['different_pixels']for f,v in q['forms'].items()}if n in(107,108)else None,'after_body_overlap':int(((fx>0)&(bodies[core][0]>0)).sum()),'before_body_overlap':int(((fx>0)&(fulls[core]>0)).sum())})
 for n in(109,):
  ss=[]
  for body in(bodies[106][0],fulls[106]):
   v=np.zeros_like(body);m=body>0;v[binary_dilation(m)]=9;v[m]=14;ss.append(v)
  need(not np.any((ss[0]>0)&(ss[1]==0)),'Flash alpha subset')
  targets[n]={0:ss[0],5:np.where(ss[0]!=ss[1],ss[1],0).astype(np.uint8),**{b:np.zeros_like(ss[0])for b in(6,7,8)}}
  rows.append({'ref':n,'body':106,'policy':'현재PL02와동일하게각의상106자체알파 내부14/Manhattan1px외곽9.양의상실루엣독립.'})
 for q in ar['silhouettes112_114']:
  n=q['ref'];need(not q['small_components_deleted_coordinates'],'Unexpected legacy removal');res=load(ROOT/q['residual_path']);v=silhouette(n,res,fulls[110]);targets[n]={0:v,**{b:np.zeros_like(v)for b in PBS[1:]}}
  Image.fromarray(res).save(o/f'{n:03}_external_residual.png');rows.append({'ref':n,'body':110,'policy':'현재원칙그대로새재킷110의공통CLUT2실루엣+원외부효과.별도아머층없으며후폼도같은실루엣정책.','external_pixels':int((res>0).sum()),'new_body_component_deletion':False})
 for q in ar['aura235_236']:
  n=q['ref'];fx=load(ROOT/q['historical_effect_path']);ls={b:v.copy()for b,v in bodies[234].items()};ls[0]=np.where(ls[0],ls[0],fx).astype(np.uint8);targets[n]=ls
  Image.fromarray(fx).save(o/f'{n:03}_historical_effect.png');rows.append({'ref':n,'body':234,'policy':'기본새피격과동일하게시부키역사오라256/464를먼저그리고새234를위에표시.기존프레임의옛수영복/재킷조각을효과로복사하지않음.','whole_effect_pixels':int((fx>0).sum()),'whole_effect_sha256':sha(fx.tobytes()),'after_visible':int(((fx>0)&(bodies[234][0]==0)).sum()),'before_visible':int(((fx>0)&(fulls[234]==0)).sum())})
 need(set(targets)==set(REFS),'Missing refs');hashes={}
 for n,ls in targets.items():
  hashes[str(n)]={}
  for b,v in ls.items():Image.fromarray(v).save(o/f'{n:03}_bank{b}_indices.png');hashes[str(n)][str(b)]=sha(v.tobytes())
 for form,mask in(('before',15),('after',0)):
  for i,refs in enumerate(((106,107,108,109),(110,111,112,113,114),(233,234,235,236))):
   pics=[]
   for n in refs:pics.extend([(f'{n} old {form}',a.composite(n,mask)[0]),(f'{n} new {form}',compose(a,targets[n],mask))])
   page(pics,a.composite(0,mask)[0],o/f'{form}_effects_{i:02}.png',cols=2,scale=4)
 write(o/'manifest.json',{'parent_sha256':PARENT,'body_source':src.relative_to(ROOT).as_posix(),'body_report_sha256':sha((src/'report.json').read_bytes()),'independent_source_report_sha256':sha(ab),'source_arrays':files,'refs':list(REFS),'targets':hashes,'records':rows,'protected_current_effect_records':fxrecords,'scope':'Ultimate固有출처의새13참조정적후보.옛의상조각과실제효과분리.','original107_108_full_spark_restoration_pending_art_review':True,'arc_written':False,'runtime_verified':False});print(json.dumps({'refs':len(targets),'layers':len(targets)*5,'sha':sha((o/'manifest.json').read_bytes())}))
if __name__=='__main__':main()
