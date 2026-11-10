from pathlib import Path
import hashlib,json
R=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent;H=W/'shibuki_audit';O=D/'shibuki_nova_strike_ultimate4_independent01';P=H/'prepared_nova_strike_ultimate01'
sha=lambda b:hashlib.sha256(b).hexdigest();tracked={}
def read(p):
 b=p.read_bytes();tracked[p.relative_to(R).as_posix()]=sha(b);return b
def js(p):return json.loads(read(p))
rep=js(O/'report.json');assert rep['passed'];tracked.update(rep['inputs'])
for p,h in rep['inputs'].items():assert sha((R/p).read_bytes())==h,p
for row in rep['readback_sheets']:assert sha(read(R/row['path']))==row['sha256']
root=js(W/'root_review_checkpoint155.json');assert root['candidate_sha256']==rep['candidate_sha256']
v=js(P/'verification.json');assert v['rejected_count']==14
for p in(D/'verify_shibuki_nova_strike_ultimate4_independent01.py',D/'verify_shibuki_ultimate_hurt13_independent.py',Path(__file__),R/'scripts/export_x_consistency.py',R/'src/psx_player.py',R/'src/psx_ui_atlas.py',R/'scripts/c01_audio_build.py'):read(p)
visual={'actually_viewed':True,'candidate_sha256':rep['candidate_sha256'],'images':rep['readback_sheets'],'actual_images':4,'observations':['独立再抽出217/218の比較で新しい髪・金色装飾・肩・曲げた腕・サンダルの詳細が確認でき、追加の明確な切断は見つからなかった。','219は新しい頭・背中・足の輪郭に追従するシルエットで、220は大きな元エネルギー外形と新身体が接続して見える。','218/220のbody0・effect5分離板を実際に見た。218の遠い3点を身体の孤立画素と誤認せず、220の新身体内部に古い白ジャケットの残像があるという追加確定欠陥は見つからなかった。'],'limitations':['정적4판이며 실제 게임·60Hz·모든부분조합의 시각전수 검토는 아니다.','실제217..220는mask15. 부분128조합은 저장/조합 진단이며128실제상태가 아니다.','Root155 원순서 등은 루트의 실제열람으로 분리 결속한다.'],'new_confirmed_defect':False}
visual['observations']=['독립 재추출217/218 비교에서 새 머릿결·금색 장식·어깨·접힌 팔·샌들 세부가 확인되며 추가 확정 절단은 찾지 못했다.','219는 새 머리·등·발의 외곽을 따르는 실루엣이며,220은 넓은 원에너지 바깥 형상과 새몸이 이어져 보인다.','218/220 body0·effect5 분리판을 실제 보았다.218의 떨어진3점을 몸체 고립점으로 오인하지 않았고,220 새몸 내부에 옛 흰 재킷 잔상이 남는 추가 확정 결함은 찾지 못했다.']
evidence={'passed':True,'candidate_sha256':rep['candidate_sha256'],'independent_report_sha256':sha((O/'report.json').read_bytes()),'source_reconstruction':'신규128고정셀 원화1개를 독립 재양자화하여776몸체와20목표층/실제ARC exact. 역사BIN에서직접추출한ARC로218/220현재효과를먼저재현하고새정책을분리검사. 제작함수 미호출.','effects':'218현재3점 전체world/index exact; 숨은옛발끝(12,13)색1 재노출안미채택.219새몸Manhattan2.220새몸가림93셀변화/외부보호영역exact이며전체rawexact아님.','storage':'512raw 중508비대상·1120층·1771조립·다른항목/은행/팔레트 exact.66GPU파트와128진단부분.220staging이동최종world0.','producer_evidence_only':{'native4_decode_hashes_bound_not_reexecuted':True,'reproduction3_rejections14_read_not_rerun':True,'original_sequence106_browser200_read_not_rerun':True,'root155_art_review_bound':True},'resources_modified':False,'runtime_verified':False}
for name,z in [('visual_review.json',visual),('evidence.json',evidence)]:
 p=O/name;assert not p.exists();p.write_text(json.dumps(z,ensure_ascii=False,indent=2)+'\n',encoding='utf8');read(p)
p=O/'READER_LOCK.json';assert not p.exists();p.write_text(json.dumps({'scope':'독립reader/원화/역사효과/실제열람 결속. 후보FROZEN아님','files':tracked},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({n:sha((O/n).read_bytes())for n in('report.json','visual_review.json','evidence.json','READER_LOCK.json')}))
