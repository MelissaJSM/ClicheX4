"""이전214 장부를 보존하고 실제 동결240 및 잔여75의 의미를 갱신한다."""
from pathlib import Path
import json,hashlib,sys,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
D=Path(__file__).parent/'rin_extension';P=D/'prepared_bank1_recovery128';O=D/'remaining240_review';O.mkdir(exist_ok=True)
read=lambda p:json.loads(p.read_text('utf8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
def dump(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
lp=D/'progress_ledger.json';j=read(lp);assert j['prepared_count']==214
snapshot=D/'progress_ledger214_before240_snapshot.json'
if snapshot.exists():assert snapshot.read_bytes()==lp.read_bytes()
else:snapshot.write_bytes(lp.read_bytes())
done=set(j['new_art_prepared_refs']);proof=[]
for name in ['prepared_dash_saber01','prepared_bank1_special01','prepared_bank1_special02','prepared_bank1_recovery128']:
 p=D/name;q=read(p/'proposal.json');f=read(p/'FROZEN.json');assert f['technical_checks_passed']and f['candidate_sha256']==sha(p/'PL01_U.ARC')
 done.update(q['new_art_refs']);proof.append({'proposal':rel(p/'proposal.json'),'proposal_sha256':sha(p/'proposal.json'),'frozen':rel(p/'FROZEN.json'),'frozen_sha256':sha(p/'FROZEN.json'),'incremental_refs':q['new_art_refs']})
assert len(done)==240
body={x for g in j['groups']for x in g['body_or_head_refs']};remaining=body-done;assert len(body)==315 and len(remaining)==75
a=(P/'PL01_U.ARC').read_bytes();old=(D/'prepared_dash_saber01/PL01_U.ARC').read_bytes();pal=struct.unpack_from('<16H',entry(a,9));idle=rgba(render(a,0,0,0)[0],pal)
groups=[];source_identity=[];small=[]
for g in j['groups']:
 allrefs=set(g['body_or_head_refs']);g['new_art_prepared']=sorted(allrefs&done);g['remaining']=sorted(allrefs-done)
 if not g['remaining']:continue
 refs=g['remaining'];name=g['group'];status='needs_art_review'
 reason='새 원화와 원래 접점을 함께 검토한다.'
 if name in ['idle','raijingeki_shared','run']:status='preserve_accepted_baseline';reason='기준 대기/동일 머리의 준비·전환이다. 무조건 새 그림으로 덮지 않는다.'
 if name=='victory_return_body':status='preserve_accepted_idle_duplicate';reason='b1_000은 빈 그림이 아니라 대기 사본이다. 실제 재추출로 이전 요약의 빈 표시 오기재를 정정한다.'
 if name=='rakuhouha_static_body':status='already_synchronized_derived_not_new_art';reason='정적23/24는 새185/182에 이미 동기화한 파생 효과다. 새 원화240 수에는 넣지 않았다.'
 if name=='ride_armor_head':status='new_art_generation_saved_registration_pending';reason='5각도의16×16 머리를19위치에서 공유. 새 원화 저장했으며 아직 등록/ARC 미적용이다.'
 if name=='ride_chaser':status='needs_repaint_four_body_angles';reason='4기울기의 몸체와4리본 파형·원래 상하 움직임을28참조로 공유한다. 손·시트 접점 보존 필요.'
 records=[]
 for ref in refs:
  rec={'ref':ref,'status':status}
  if ref.startswith('static'):records.append(rec);continue
  b,n=int(ref[1]),int(ref.split('_')[1]);z=render(a,b,b*5,n)[0];assert np.array_equal(z,render(old,b,b*5,n)[0]);source_identity.append(ref)
  if name=='arrival_body':rec['status']='preserve_intended_white_flash'if n in(247,248)else'needs_repaint_arrival_body'
  if name=='victory_return_body':assert np.array_equal(z,render(a,0,0,147)[0]);rec['exact_same_as']='b0_147'
  records.append(rec)
  if name not in ['ride_chaser','ride_armor_head']:small.append((ref,rgba(z,pal)))
 groups.append({'group':name,'count':len(refs),'reason':reason,'refs':records})
pages=[]
for at in range(0,len(small),6):
 subset=small[at:at+6];sheet=Image.new('RGB',(960,3*352),(28,34,45));draw=ImageDraw.Draw(sheet)
 for i,(ref,im)in enumerate(subset):
  x=(i%2)*480;y=(i//2)*352;draw.text((x+5,y+5),ref+' / idle0 -> current',fill='white')
  for col,pic in enumerate((idle,im)):
   v=pic.crop((112,112,192,192)).resize((240,240),Image.Resampling.NEAREST);sheet.paste(v,(x+col*240,y+30),v)
 path=O/f'other_remaining_{at//6:02}.png';sheet.save(path);pages.append({'path':rel(path),'sha256':sha(path),'refs':[r for r,_ in subset],'actually_viewed':False})
manifest={'candidate_sha256':sha(P/'PL01_U.ARC'),'frozen':rel(P/'FROZEN.json'),'frozen_sha256':sha(P/'FROZEN.json'),'original_body_head_classification':315,'new_art_refs_with_aliases_and_effect_derivations':240,'remaining_ledger_refs':75,'completion_percentage_not_claimed':True,'groups':groups,'prior222_render_exact':source_identity,'reuse_prior_ride_sheets':'remaining222_review/ride_armor_head_00..03.png and ride_chaser_00..04.png; all9 actually viewed this turn; current73 nonstatic remaining exact','additional_sheets':pages,'static_synchronized_proof':rel(D/'rin240_static_binding_check.json'),'runtime_verified_all_refs':False,'user_accepted':False,'limitations':['315는 원래 분류이며 필요한 새 원화 수가 아니다.','고정240은 참조/공유/파생을 포함한 수이며 품질 완료율이 아니다.','실제 게임 관측 범위는 루트 runtime 기록을 별도로 따른다.']}
dump(O/'manifest.json',manifest)
j.update(current_arc=rel(P/'PL01_U.ARC'),current_sha256=sha(P/'PL01_U.ARC'),new_art_prepared_refs=sorted(done),remaining_refs_in_original_audit=sorted(remaining),prepared_count=240,latest_scope=read(P/'FROZEN.json')['scope'],latest_proof='final240_readback_audit.json',latest_native='rin240_components_native_checks.json',latest_frozen=rel(P/'FROZEN.json'),update_proofs=proof,remaining_classification=rel(O/'manifest.json'),next_page='ride_head01',next_page_scope='다섯 탑승 머리19참조 등록 후 체이서4각도28참조, 등장249..253와 낙봉파 잔여를 검토한다.',next_authored_inputs=[{'directory':rel(D/'ride_head01'),'refs':[66,75,77,78,81],'bank':1,'reason':'작은 머리5각도의 내부명암/눈 세부 통일. 생성됨, 아직 등록/패킹되지 않음.'}])
j['limitations']=[x for x in j['limitations']if'누적214'not in x]+['새 원화 누적240의 전수 실제 플레이와 사용자 최종 수용은 미확인. 루트 정적 미술과 원MIPS/GPU 검사를 구분한다.']
dump(lp,j);dump(D/'progress_ledger240_snapshot.json',j)
print(json.dumps({'prepared':len(done),'remaining':len(remaining),'groups':[(g['group'],g['count'])for g in groups],'sheets':len(pages)}))
