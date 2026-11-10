from pathlib import Path
import json,hashlib,shutil
H=Path(__file__).resolve().parent;W=H.parent;ROOT=W.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
bound=lambda p:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
read=lambda p:json.loads(p.read_text('utf8'))
write=lambda p,r:p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8')
def main():
 d=H/'prepared01';assert not d.exists();a=H/'sync_spares01';b=H/'sync_spares02';final='55b5d04d9a3452f2f12fe5ab21024de58c61f43eaa8b078f873ce4c7d2182f52'
 assert sha(a/'ST0E_U1.ARC')==sha(b/'ST0E_U1.ARC')==final
 cap=W/'zero_audit/nana_selection8_capacity01/conclusions.json';assert sha(cap)=='9e1daae55eff2c23e81ed3aeca55eb94b60dcf5146e8f62b2df12189ac34c1ae'
 c=read(cap);r=read(b/'report.json');assert c['additional_unconsumed_slots']==r['spare_slots'];assert r['passed']
 guard=W/'selection_standing_v5_checks.json';assert sha(guard)=='378cae09f9fd41b5b212fb24635b0892fb658db56135a287f6f246bfd7542478'
 d.mkdir();shutil.copy2(b/'ST0E_U1.ARC',d/'ST0E_U1.ARC')
 images=[]
 for n in range(1,9):
  name=f'copy_{n:02}.png';assert sha(a/name)==sha(b/name);shutil.copy2(b/name,d/name);images.append(dict(bound(a/name),actually_viewed=True))
 root={'checkpoint':141,'candidate_sha256':final,'actually_viewed_files':images,'observations':['選択1..8の旧表示・新表示・対応新ゲーム85..92の8比較を実際に閲覧した。','선택 사본이 현재 게임 몸체의 얼굴·머리갈래·손·소매·신발을 같은 원점에 유지한다. 추가 확정 절단을 찾지 못했다.'],'origin':{'flip_x':False,'dx':0,'dy':0},'runtime_verified':False,'whole_project_complete':False}
 root['observations'][0]='선택1..8의 기존 표시·새 표시·대응 새 게임85..92의8비교를 실제 열람했다.'
 rp=W/'root_review_checkpoint141.json';assert not rp.exists();write(rp,root)
 proposal={'kind':'nana_selection_standing_8','candidate':bound(d/'ST0E_U1.ARC'),'parent':r['inputs'][0],'game_old':r['inputs'][1],'game_new':r['inputs'][2],'source_report':bound(b/'report.json'),'source_code':bound(H/'sync_standing_selection_spares.py'),'mapping':r['mapping'],'unused_capacity_native_proof':bound(cap),'shared_tiles_preserved':c['shared_tiles_keep_whole_exact'],'spare_slots_used':r['spare_slots_used'],'unchanged_all_entries_sizes_offsets':True,'unchanged_banks':True,'identical_reproductions':2,'root_visual':bound(rp),'builder_v5_guard':bound(guard),'native_capacity_review_complete':True,'independent_candidate_pending':True,'runtime_verified':False,'whole_project_complete':False}
 write(d/'proposal.json',proposal)
 files=[Path(__file__),H/'sync_standing_selection_spares.py',H/'pack_selection_spares.py',a/'report.json',b/'report.json',W/'nana_selection8_origins.json',rp,guard,ROOT/'scripts/build_sprite_style_selection_v5.py',ROOT/'scripts/build_sprite_style_selection_v3.py',W/'pack_selection_mirrors.py',cap,*[(ROOT/rw['path'])for rw in r['inputs']]]
 files += [p for p in cap.parent.iterdir() if p.is_file()]
 files += [ROOT/f for f in ('src/psx_ui_atlas.py','src/psx_player.py','src/psx_static_effect.py','scripts/prepare_riko_ui.py','scripts/prepare_shibuki_ultimate_production.py','scripts/export_x_consistency.py')]
 write(d/'INPUT_LOCK.json',{'files':[bound(p)for p in sorted(set(files))]})
 write(d/'PREPARED_LOCK.json',{'files':[bound(p)for p in sorted(d.iterdir())if p.is_file()],'not_frozen':True})
 print(json.dumps({'candidate':final,'root141':sha(rp),'proposal':sha(d/'proposal.json'),'input_count':len(set(files))}))
if __name__=='__main__':main()
