from pathlib import Path
import sys,json,hashlib
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];N=W/'nana_audit';U=N/'ultimate_hover_repaint'
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,helper
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
P=D/'packed_hover_final01';cp=P/'PL00_U.ARC';FINAL='9c1ff453a2308ddc40f39e5790de0aa6a5cf41dda43165b0fa16808f8c3a643c'
assert sha(cp)==FINAL
m=json.loads((D/'final_targets01/manifest.json').read_text('utf8'));parent=ROOT/m['parent']['path'];old=Archive(parent.read_bytes());new=Archive(cp.read_bytes())
for n in range(221,231,2):
 rows=[]
 for ref in(n,n+1):
  for name,mask in [('basic legs',8),('Fourth',15)]:
   rows.append((f'{name} {ref}',[('approved idle',new.composite(0,mask&7)[0]),('old',old.composite(ref,mask)[0]),('new readback',new.composite(ref,mask)[0])]))
 helper.grid(rows,P/f'readback_{n}.png',5)
plan={'project':'ver_rin_nana','source_bin':'out/ver_rin_nana/sprite_style_unification_20261107_v40/rin_nana.bin','source_sha256':'fdcebed25fb3ffde641d9a6fc5f56180e74f2d3367057eea2f70c5123ac613b9','resources':{'PL00_U.ARC':{'path':cp.relative_to(ROOT).as_posix(),'before':m['parent']['sha256'],'after':FINAL}},'checkpoint_only':True}
(D/'native_components01.json').write_text(json.dumps(plan,indent=2)+'\n','utf8')
# Preserve the verified template and adapt only the form policy and local paths.
s=(U/'make_native_cycle.py').read_text('utf8')
changes=[("D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]","D=Path(__file__).resolve().parent;W=D.parent;N=W/'nana_audit';ROOT=W.parents[1]"),('from pack_native import PARENT,REFS',"PARENT=W/'root_nana_shot87/packed_settle01/PL00_U.ARC';REFS=tuple(range(221,231))"),('native_cycle_v1','native_cycle01'),('packed_hover_candidate_v1/PL02_U.ARC','packed_hover_final01/PL00_U.ARC'),('native_components_v1.json','native_components01.json'),("['ultimate_after']","['fourth']"),('mask=15 if n>=217 else 0','mask=8 if n>=217 else 0'),("ims=[old.composite(n,mask)[0],new.composite(n,mask)[0],old.rgba(old.layer(n,0)[0]),new.rgba(new.layer(n,0)[0]),old.rgba(old.layer(n,5)[0],16),new.rgba(new.layer(n,5)[0],16)]","ims=[old.composite(n,mask)[0],new.composite(n,mask)[0],old.composite(n,15)[0],new.composite(n,15)[0],new.rgba(new.layer(n,0)[0]),new.rgba(new.layer(n,8)[0],16)]"),('나나 Ultimate 호버10 · ARC 재추출','나나 기본/포스 호버10 · ARC 재추출'),('각 줄: 기존 실제 / 새 실제 / 기존0층 / 새0층 / 기존5층 / 새5층. 221~230 실제는 mask15, 연결공중45~48은 획득후 mask0이다. 호버5층은 하체이며 0층 단독을 완성몸체로 보지 않는다.','각 줄: 기존 기본+다리 / 새 기본+다리 / 기존 포스 / 새 포스 / 새0층 / 새8층. 호버는 다리 bit8을 사용하며 Ultimate의 강제mask15 규칙을 적용하지 않는다. 연결공중은 기본0/포스15다. 마지막 두 층은 불완전한 진단표시다.'),('Nana Ultimate hover native review','Nana basic Fourth hover native review')]
for a,b in changes:assert a in s,a;s=s.replace(a,b)
(D/'make_native_cycle01.py').write_text(s,'utf8')
s=(U/'verify_native_cycle.py').read_text('utf8').replace("D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]","D=Path(__file__).resolve().parent;W=D.parent;N=W/'nana_audit';ROOT=W.parents[1]").replace('native_cycle_v1','native_cycle01').replace('원표65~76','원표21~26/133~138').replace('차량물리·입력·손잡이/페달','호버물리·입력·불꽃/총구')
(D/'verify_native_cycle01.py').write_text(s,'utf8')
dirs=['registered01','registered02','registered03_fit01','body_alignment01','body_layers_probe01','shoot_layers_probe02','rearfoot_edit01','rearfoot_registered01','rearfoot_jet_probe02','final_targets01','final_jet_probe01','final_muzzle_probe01']
files=[f for name in dirs for f in(D/name).rglob('*')if f.is_file()]
files += [p for p in D.glob('*.py')]+[D/'input_audit.json']+[D/f'art0{i}_generated.png'for i in(1,2,3)]
files += [ROOT/q['path'] for q in json.loads((N/'base_hover_shot_support01/handoff01/HANDOFF_LOCK.json').read_text('utf8'))['files']]
files += [N/'base_hover_shot_support01/handoff01/HANDOFF_LOCK.json',N/'base_hover_pack_support01/HANDOFF.txt',N/'base_hover_pack_support01/build_candidate.py',N/'base_hover_pack_support01/SUPPORT_LOCK.json',N/'base_hover_pack_support01/native_empty01/report.json',N/'base_hover_pack_support01/report.json',U/'pack_native.py',U/'prepare_targets.py',N/'native_restore/preview_restore.py',N/'base_run_repaint/pack_cycle.py',W/'shibuki_audit/repack_part_records_lossless.py',parent]
files=sorted(set(files));assert all(p.exists()for p in files)
lock={'candidate_sha256':FINAL,'parent_sha256':m['parent']['sha256'],'target_manifest_sha256':sha(D/'final_targets01/manifest.json'),'files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}for p in files],'scope':'나나 기본/포스 새 호버50층, 229/230 신발국소20px 포함. 입력고정만 수행, 미술/독립/원코드/실기 완료와 구분.','frozen_asset_final':False}
f=P/'INPUT_LOCK.json';assert not f.exists();f.write_text(json.dumps(lock,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'candidate':FINAL,'inputs':len(files),'lock':sha(f)}))
