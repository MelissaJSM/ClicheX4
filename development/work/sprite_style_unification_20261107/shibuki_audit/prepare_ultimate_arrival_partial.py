"""보류135를 제외한 Ultimate 등장8 참조. 각 실제 효과 출처를 따로 보존한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,same_rgba
from scripts.export_x_consistency import Archive,page
from prepare_lowhp_final import compose
from prepare_shibuki_hurt_effects import render
P=H/'prepared_ultimate_hurt02/PL02_U.ARC'
PARENT='b43e021b70c055d142521d1c679bef323d76b0b30bf27b41c9988815330b2e94'
D=H.parent/'zero_audit/shibuki_ultimate_arrival_relations01'
AUDIT_SHA='3a7bee18e7625a72dc9e7f76731698b878d1c31ce730822c1f709ec7bea5e96a'
SOURCE=H/'ultimate_arrival_common_probe03';OUT=H/'ultimate_arrival_targets01'
PBS=(0,5,6,7,8);BODIES=(133,136,137,138,139);REFS=(130,131,133,134,136,137,138,139)

def main():
 need(not OUT.exists(),'Fresh targets required');need(sha(P.read_bytes())==PARENT,'Parent changed');a=Archive(P.read_bytes())
 need(sha((D/'report.json').read_bytes())==AUDIT_SHA,'Independent audit changed');audit=json.loads((D/'report.json').read_text('utf8'))
 OUT.mkdir();files={};targets={};bodies={};before={};checks=[];rows=[];fxrecords={}
 def load(p):
  files[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes());return np.load(p)if p.suffix=='.npy'else np.array(Image.open(p))
 def blank():return np.zeros((384,384),np.uint8)
 def save(n,ls):
  targets[n]=ls
  for b,v in ls.items():Image.fromarray(v).save(OUT/f'{n:03}_bank{b}_indices.png')
 for n in BODIES:
  b=load(SOURCE/f'before_{n:03}_indices.png');v=load(SOURCE/f'after_{n:03}_indices.png');need(not ((v>0)&(b==0)).any(),'After outside new jacket')
  ls={0:v,5:np.where(same_rgba(a,b,v),0,b).astype(np.uint8),**{k:blank()for k in(6,7,8)}}
  for k in(6,7,8):need(not a.layer(n,k)[0].any(),'Independent old layer nonempty')
  before[n]=b;bodies[n]=ls;save(n,ls);rows.append({'ref':n,'source_body':n,'policy':'각 자세의 별도 새 원화. 공통 새 머리/사지와 두 의상 차이를 보존하며 구형 몸체를 덮지 않는다.'})
 bg=load(D/'effect_130_historical_background.npy');oldbody=load(D/'effect_130_historical_body.npy');old=np.where(oldbody,9,bg).astype(np.uint8);old[183,159:162]=9
 need(np.array_equal(old,a.layer(130,0)[0]),'Parent130 historical formula differs');checks.append('130 역사 몸체+광선 및 기존 외부3셀 exact')
 # Preserve the existing external three-cell correction in the background,
 # separately from the new body silhouette.
 bg=bg.copy();bg[183,159:162]=9;sil=np.where(bodies[133][0],9,0).astype(np.uint8);Image.fromarray(bg).save(OUT/'130_background_indices.png');Image.fromarray(sil).save(OUT/'130_silhouette_indices.png')
 save(130,{0:np.where(sil,sil,bg).astype(np.uint8),**{k:blank()for k in PBS[1:]}})
 fx=load(D/'effect_131.npy');need(np.array_equal(np.where(a.layer(133,0)[0],9,fx),a.layer(131,0)[0]),'Parent131 formula differs');need(np.array_equal(fx,a.layer(132,0)[0]),'Pure132 differs');checks.append('131 현재133 alpha9+광선 exact;132 순수광선 exact')
 Image.fromarray(fx).save(OUT/'131_background_indices.png');Image.fromarray(sil).save(OUT/'131_silhouette_indices.png');save(131,{0:np.where(sil,sil,fx).astype(np.uint8),**{k:blank()for k in PBS[1:]}})
 orb=load(D/'effect_134_orb.npy');need(np.array_equal(np.where(a.layer(133,0)[0],a.layer(133,0)[0],orb),a.layer(134,0)[0]),'Parent134 base differs');need(np.array_equal(a.layer(133,5)[0],a.layer(134,5)[0]),'Parent134 overlay differs');checks.append('134 각 의상 실제133색+원129구체 exact')
 Image.fromarray(orb).save(OUT/'134_background_indices.png');ls={k:v.copy()for k,v in bodies[133].items()};ls[0]=np.where(ls[0],ls[0],orb).astype(np.uint8);save(134,ls)
 historical=ROOT/'work/overhaul_20261105/sprites/ver_buki_riko/baseline/PL02_U.ARC';files[historical.relative_to(ROOT).as_posix()]=sha(historical.read_bytes());need(files[historical.relative_to(ROOT).as_posix()]==audit['historical_baseline_sha256'],'Historical archive changed');hist=Archive(historical.read_bytes())
 for q in audit['historical136137_effects']:
  n=q['ref'];fx=load(D/f'effect_{n}.npy');ps=q['historical_parts'];need(np.array_equal(render(hist,n,0,ps),fx),'Historical spark reconstruction');need(np.count_nonzero(fx)==46,'Spark count');need(a.words[9]==a.words[25],'Spark palette differs')
  for mask in(0,15):need(np.all(np.array(a.composite(n,mask)[0])[fx>0]==np.array(a.rgba(fx))[fx>0]),'Parent sparks changed')
  ls={k:v.copy()for k,v in bodies[n].items()};ls[0]=np.where(fx,fx,ls[0]).astype(np.uint8);ls[5]=np.where(fx,fx,ls[5]).astype(np.uint8);save(n,ls);Image.fromarray(fx).save(OUT/f'{n:03}_effect_indices.png');fxrecords[n]=ps
  rows.append({'ref':n,'effect_pixels':46,'effect_full_array_sha256':sha(fx.tobytes()),'policy':'역사 tile7 전체와 원 좌표/반전 순서를 보존. 새 몸체 뒤에 번개를 그려 원래 가시 픽셀을 유지한다.','after_overlap':int(((fx>0)&(bodies[n][0]>0)).sum()),'before_overlap':int(((fx>0)&(before[n]>0)).sum())})
 for n in(130,131,134):rows.append({'ref':n,'source_body':133,'policy':'원래 효과 전체를 먼저 그리고 새133 몸체/실루엣을 위에 그린다. 기존색과 효과좌표를 보존.'})
 need(set(targets)==set(REFS),'Target scope differs')
 hashes={str(n):{str(k):sha(v.tobytes())for k,v in ls.items()}for n,ls in targets.items()}
 for form,mask in(('before',15),('after',0)):
  for i,ns in enumerate(((130,131,133,134),(136,137),(138,139))):page([(f'{n} new {form}',compose(a,targets[n],mask))for n in ns],a.composite(0,mask)[0],OUT/f'{form}_targets_{i:02}.png',cols=2,scale=4)
 write(OUT/'manifest.json',{'parent_sha256':PARENT,'source_report_sha256':AUDIT_SHA,'body_report_sha256':sha((SOURCE/'report.json').read_bytes()),'refs':list(REFS),'body_refs':list(BODIES),'targets':hashes,'source_files':files,'protected_effect_records':fxrecords,'historical_source':historical.relative_to(ROOT).as_posix(),'parent_formula_checks':checks,'rows':rows,'excluded_ref135':'국소 편집 도구 거부 후 재시도하지 않음. 부모 raw/5층/조립을 보존하며 미완료.','separate_136_139_art':True,'foot136_registration':(H/'ultimate_arrival136_foot_contacts01/report.json').relative_to(ROOT).as_posix(),'arc_written':False,'runtime_verified':False})
 print(json.dumps({'refs':REFS,'layers':len(REFS)*5,'manifest_sha256':sha((OUT/'manifest.json').read_bytes())}))
if __name__=='__main__':main()
