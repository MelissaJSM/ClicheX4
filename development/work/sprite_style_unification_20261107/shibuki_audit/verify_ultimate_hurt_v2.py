"""Ultimate 피격13 재현/입력거부 후 검토용 준비본 생성."""
from pathlib import Path
import sys,json,shutil
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,SOURCE_SHA
from pack_ultimate_hurt import build,validate,P,PARENT,FINAL,LOCK,LOCK_SHA,D,REFS

def main():
 out=H/'prepared_ultimate_hurt02';need(not out.exists(),'Fresh output');old=P.read_bytes();probe=H/'ultimate_hurt_pack_probe02';candidate=(probe/'PL02_U.ARC').read_bytes();need(sha(candidate)==FINAL,'Changed probe')
 for i in range(2):
  rebuilt,proof=build(old,lambda row:None);need(rebuilt==candidate,'Reproduction differs');print(json.dumps({'reproduction':i+2,'sha256':sha(rebuilt)}),flush=True)
 tests=[]
 def reject(name,data,read=lambda p:p.read_bytes()):
  try:validate(data,read)
  except ValueError as e:tests.append({'test':name,'rejected':True,'reason':str(e)});return
  raise ValueError('Invalid accepted '+name)
 bad=bytearray(old);bad[100]^=1;reject('wrong_parent',bytes(bad));reject('truncated_parent',old[:-1])
 names=['ultimate_hurt_locked_inputs02/LOCK.json','ultimate_hurt_effect_probe02/manifest.json','ultimate_hurt_effect_probe02/235_bank0_indices.png','ultimate_hurt_common_probe02/after_234_indices.png','ultimate_hurt_inputs01/page01/generated.png','ultimate_hurt_inputs01/page02/generated.png','ultimate_hurt234_arm01/generated.png','ultimate_hurt234_arm01/prompt.txt','probe_ultimate_hurt_common.py','prepare_ultimate_hurt_effects.py']
 for n in names:
  selected=(H/n).resolve()
  def reader(p,selected=selected):
   v=p.read_bytes();return bytes([v[0]^1])+v[1:]if p.resolve()==selected else v
  reject('changed_'+n,old,reader)
 need(sha(P.read_bytes())==PARENT,'Parent modified');meta=json.loads((D/'manifest.json').read_text('utf8'))
 proof.update({'reproduction_runs':3,'reproduced_sha256':[FINAL]*3,'rejection_count':len(tests),'rejection_cases':tests,'body_keys':[106,110,233,234],'generated_pages':2,'local_arm_edit_pages':1,'registered_costume_images':8,'effect_policies':meta['records'],'actual_art_review':{'agent':'overhaul_ui','actual_viewed_readback':[f'{form}_readback_{i:02}.png'for form in('before','after')for i in range(4)],'observation':'새머리/금색안경·의상구획·손목/무릎과오라가재추출에도유지.8판에서새확정몸분리/축소는찾지못했다.','gameplay_claim':False},'independent_pending':True,'native_cpu_pending':True,'root_final_packed_review_pending':True,'limitations':['110샌들끝은이전보다1px낮고몸체축소/확대는없음.접점미술검토와실기검증은분리한다.','107/108은원US99/76 전기타일/파트를전체보존해새몸위에표시하므로기존합성의22~25px가림과다름.','111은현재PL02의194px CLUT2효과이며기본형202와다름.원색index3은CLUT0/1/2에서RGB555가같다.','109는각의상106의실루엣,112..114는현재정책과같은공통재킷110의CLUT2실루엣.','235/236은원시부키256/464백색/청색오라뒤에새234를그린다.옛수영복/재킷조각은복사하지않음.','전후공통부는새재킷머리/사지의원CLUT대응이며구형그림덮기아님.','111 새 layer5의 U경계 실패 v1은 제외하고, 동일 원 효과 tile16을31로 복제해 v2에서 해결했다. 원 base16과 표시 픽셀은 그대로다.','원순서/원MIPS/실제피격은별도미검증.']})
 out.mkdir();(out/'PL02_U.ARC').write_bytes(candidate)
 for p in sorted(probe.glob('*_readback_*.png')):shutil.copyfile(p,out/p.name)
 write(out/'verification.json',proof)
 proposal={'project':'ver_buki_riko','baseline_sha256':SOURCE_SHA,'files':{'PL02_U.ARC':{'path':(out/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':'98ab01e8581d6bca15d75d703e7605899f2a871e042f5b09b13c5f2e07cf132e','after':FINAL}},'sequential_parent':{'path':P.relative_to(ROOT).as_posix(),'sha256':PARENT},'targets':(D/'manifest.json').relative_to(ROOT).as_posix(),'target_lock':LOCK.relative_to(ROOT).as_posix(),'target_lock_sha256':LOCK_SHA,'source_art':json.loads(LOCK.read_text('utf8'))['files'],'selected_refs':list(REFS),'scope':'Ultimate피격13 새4몸체전후8표시+234맨팔국소.현재은행경계/원효과전체타일을유지하는재삽입.','runtime_verified':False,'native_cpu_pending':True,'frozen':False}
 write(out/'proposal.json',proposal);write(out/'PREPARED_LOCK.json',{'candidate_assets_fixed':True,'final_approval_pending':True,'files':{p.name:sha(p.read_bytes())for p in sorted(out.iterdir())if p.is_file()},'source_scripts':{n:sha((H/n).read_bytes())for n in('pack_ultimate_hurt.py','verify_ultimate_hurt_v2.py')}})
 write(H/'ultimate_hurt_v2_components.json',{'project':'ver_buki_riko','source_bin':'out/ver_buki_riko/sprite_reaudit_20261106_v1/shibuki_riko.bin','source_sha256':SOURCE_SHA,'resources':proposal['files'],'checkpoint_only':True})
 print(json.dumps({'candidate':FINAL,'proposal':sha((out/'proposal.json').read_bytes()),'prepared_lock':sha((out/'PREPARED_LOCK.json').read_bytes()),'rejections':len(tests)}))
if __name__=='__main__':main()
