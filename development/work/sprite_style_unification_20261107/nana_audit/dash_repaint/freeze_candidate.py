from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent;OUT=D/'packed_dash_candidate_v1'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
arc=OUT/'PL00_U.ARC';assert digest(arc)=='cbe6996784a901363abab2d93c81dca49ade8574ac0d5c378af398651f2f6cfa'
ind=ROOT/'work/sprite_style_unification_20261107/zero_audit/nana_dash20_independent.json'
assert digest(ind)=='58d99d259470ac0c8ccc6615a783d611cd8954cdac960193831581df3ba59814'
assert json.loads(ind.read_text('utf8'))['passed']
paths=[arc,OUT/'proposal.json',OUT/'verification.json',OUT/'mask_verification.json',OUT/'reproduction_and_guards.json',D/'joint_layers_candidate_v1/manifest.json',D/'native_cycle_v1/verification.json',ind]
record={'frozen':True,'character':'nana','forms':['base','fourth'],'refs':list(range(67,85))+[93,94],
 'asset_sha256':digest(arc),'parent_asset_sha256':'721457a50ea48e76c1ac592eec21db274b43c5863cc5b3df310ac981d5890dca',
 'files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p)}for p in paths],
 'producer_reproduction_passed':True,'independent_readback_passed':True,'producer_7296_combinations_passed':True,
 'independent_640_direct_target_combinations':True,'independent_non_target_6656_proven_via_exact_layers_and_palette':True,
 'body_pair_note':'67..84의9쌍은실제동일압축참조.93/94는같은raw라도원래디렉터리주소가다른전환자세이며사격짝이아니다.',
 'offline_preview_only':True,'root_actual_mips_check_is_separate':True,'gameplay_verified_here':False,'all_nana_art_complete':False}
target=OUT/'FROZEN.json';assert not target.exists();target.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'path':str(target),'sha256':digest(target)}))
