"""독립 읽기 후 원표/마스크/원MIPS·실제 열람 범위를 별도 결속. 제작 호출 없음."""
from pathlib import Path
import hashlib,json,struct,sys
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;H=D.parent/'shibuki_audit';sys.path[:0]=[str(ROOT),str(D)]
from scripts.export_x_consistency import Archive
from scripts.c01_audio_build import read_disc
from verify_shibuki_ultimate_hurt13_independent import raw
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
for mode in('base','ultimate'):
 u=mode=='ultimate';o=D/f'shibuki_nova_{mode}4_independent01';assert not(o/'evidence.json').exists()
 tracked={}
 def read(p):
  b=p.read_bytes();tracked[rel(p)]=sha(b);return b
 def js(p):return json.loads(read(p))
 r=js(o/'report.json');tracked.update(r['inputs']);a=Archive(read(ROOT/r['candidate']));p=H/f'prepared_nova_{mode}01';v=js(p/'verification.json')
 assert v['total_identical_builds']==3 and len(v['reproduction_sha256'])==2 and set(v['reproduction_sha256'])=={r['candidate_sha256']}
 assert v['rejected_count']==len(v['rejected_inputs'])==(14 if u else 16)and all(q['rejected']for q in v['rejected_inputs'])
 seqdir=H/f'nova_{mode}_sequence{1 if u else 2:02}';s=js(seqdir/'report.json');assert s['candidate_sha256']==r['candidate_sha256']
 bp=ROOT/s['source_bin'];assert sha(read(bp))==s['source_bin_sha256'];exe=read_disc(bp,('SLUS_005.61',))[0]['SLUS_005.61'];assert sha(exe)==s['exe_sha256'];load=struct.unpack_from('<I',exe,0x18)[0]
 m=js(ROOT/'work/sprite_consistency_20261105/coverage/ver_buki_riko/x_animations.json');ss=next(q for q in m['animations']if q['id']==106);assert ss==s['sequences'][0]
 off=lambda x:int(x,16)-load+0x800
 assert struct.unpack_from('<I',exe,off(m['table_address'])+106*4)[0]==int(ss['address'],16)
 for q in ss['steps']:assert exe[off(q['address']):off(q['address'])+4].hex()==q['bytes']
 masks={};pngcount=0
 for name,h in s['native_pngs'].items():
  pp=seqdir/name;assert sha(read(pp))==h;form,ref=name.split('_')[:2];n=int(ref);mask=(15 if n>=217 or form=='before'else 0)if u else(0 if form=='base'else 15)
  assert s['effective_masks'][f'{form}_{n}']==mask;im=a.composite(n,mask)[0];arr=np.array(im);crop=arr[64:256,64:256];assert np.count_nonzero(crop[:,:,3])==np.count_nonzero(arr[:,:,3]);assert np.array_equal(crop,np.array(Image.open(pp)));masks[f'{form}_{n}']=mask;pngcount+=1
 correction=None
 if not u:
  c=js(p/'sequence_mask_correction.json');assert c['candidate_sha256']==r['candidate_sha256']
  for key in('corrected_report','corrected_browser','corrected_html'):
   q=c[key];assert sha(read(ROOT/q['path']))==q['sha256']
  diffs={str(n):int(np.any(np.array(a.composite(n,0)[0])!=np.array(a.composite(n,15)[0]),axis=2).sum())for n in range(217,221)};assert diffs==c['wrong_vs_correct_pixels']
  correction={'path':rel(p/'sequence_mask_correction.json'),'sha256':sha((p/'sequence_mask_correction.json').read_bytes()),'wrong_vs_correct_RGBA_pixels':diffs,'old_sequence01_excluded':True,'candidate_unchanged':True,'corrected16_native_PNGs_recomputed':True}
 nativepath=(o/'native_components_native_checks.json')if u else(D/'shibuki_nova_base4_directory_native01/report.json');nr=js(nativepath);assert nr['passed']
 if u:
  q=nr['resources']['PL02_U.ARC'];assert q['candidate_sha256']==r['candidate_sha256']and q['GPU_part_edge_checks']==64
  for bk in q['banks']:
   for f in bk['native_decoder_checks']:assert f['decoded_sha256']==sha(raw(a,bk['bank'],f['frame']))and f['buffer_outside_and_unused_tail_preserved']
  native_scope='독립 폴더에서 기존 원MIPS 디코더·업로드 검사 새 실행. 4참조64GPU. 이 checker는 graphics pointer를 공급하므로 전체 directory loader 검사라고 부르지 않음.'
 else:native_scope='원 RAM-loader→scratchpad→directory→객체+38/+3c→decode/upload 508참조·1016호출 새 실행. Python 포인터 주입 없음. 실제 CD/게임 프로세스/GPU 실기 아님.'
 for cp in([149]if u else[147,150]):read(D.parent/f'root_review_checkpoint{cp}.json')
 orderpics=[]
 for form in(['before','after']if u else['base','fourth']):
  pp=seqdir/f'{form}_preparation_order.png';read(pp);orderpics.append({'path':rel(pp),'sha256':sha(pp.read_bytes())})
 for q in r['readback_sheets']:assert sha(read(ROOT/q['path']))==q['sha256']
 visual={'actually_viewed':True,'candidate_sha256':r['candidate_sha256'],'own_sheets':r['readback_sheets'],'sequence_sheets':orderpics,'actual_images':8,'observations':['213 낮은 자세와215 위로 든 손의 새 머릿결·커프·의상·무릎/발목 명암이 유지된다. 이 정적 비교 범위에서 새 확정 팔/손/다리 절단을 발견하지 못했다.','부분0/1/2/4/8/15와213214·215216 동형짝을 직접 열람했다. 숫자 일치만으로 미술 수용을 대체하지 않는다.','217 이후는 이번 새 준비4의 수정 대상이 아니며 기존 상세 차이를 준비4의 결함 해결/전체 완료로 묶지 않는다.'],'scope_limits':['원표 순서의 정적 판 열람이며 연속60Hz·실제게임/발동조건 검증은 미실행.','제작자의 최종6판/루트 열람과 이 감사의 새8판은 별도 범위.'],'source_resource_modified':False}
 (o/'visual_review.json').write_text(json.dumps(visual,ensure_ascii=False,indent=2)+'\n','utf8')
 evidence={'passed':True,'report_sha256':sha((o/'report.json').read_bytes()),'candidate_sha256':r['candidate_sha256'],'original_table106_pointer_13steps_byte_exact':True,'native_PNGs_reconstructed':pngcount,'effective_masks':masks,'sequence_mask_correction':correction,'native':{'path':rel(nativepath),'sha256':sha(nativepath.read_bytes()),'scope':native_scope,'executed_separately_by_this_auditor':True},'reproduction_rejection_evidence':{'verification_path':rel(p/'verification.json'),'sha256':sha((p/'verification.json').read_bytes()),'recorded_identical_builds':3,'recorded_rejections':len(v['rejected_inputs']),'all_input_hashes_current_exact':True,'producer_execution_repeated_by_auditor':False,'note':'저장된 3재현/거부16 또는14의 후보·원화·스크립트 잠금과 결과를 대조. 패커를 다시 호출해 재현했다고 주장하지 않음.'},'actually_viewed':True,'visual_sha256':sha((o/'visual_review.json').read_bytes()),'runtime_verified':False,'producer_functions_called':False,'inputs':tracked}
 (o/'evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n','utf8')
 for f in(o/'report.json',o/'visual_review.json',o/'evidence.json',Path(__file__),D/'verify_shibuki_nova_preparation4_independent.py',D/'verify_shibuki_ultimate_hurt13_independent.py',ROOT/'scripts/export_x_consistency.py',ROOT/'src/psx_player.py'):read(f)
 for path,h in tracked.items():assert sha((ROOT/path).read_bytes())==h,path
 lock={'candidate_sha256':r['candidate_sha256'],'files':tracked,'immutable_audit_input_output_hashes':True,'runtime_verified':False}
 (o/'READER_LOCK.json').write_text(json.dumps(lock,ensure_ascii=False,indent=2)+'\n','utf8')
 print(json.dumps({'mode':mode,'report':sha((o/'report.json').read_bytes()),'visual':sha((o/'visual_review.json').read_bytes()),'evidence':sha((o/'evidence.json').read_bytes()),'lock':sha((o/'READER_LOCK.json').read_bytes()),'inputs':len(tracked)}))
