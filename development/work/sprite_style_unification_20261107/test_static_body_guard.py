"""낙봉파 몸체 한정 쓰기 검사의 실제 후보와 잘못된 입력 거부를 확인한다."""
from pathlib import Path
import sys,json,hashlib,copy
ROOT=Path(__file__).resolve().parents[2];W=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from scripts.build_sprite_style_unification import check_static_body
from scripts.prepare_riko_ui import entry,replace_entry
from src.psx_player import composition_frame
sha=lambda b:hashlib.sha256(b).hexdigest()
source=W/'riko/prepared_ceremony_v2/PL01_U.ARC'
candidate=W/'riko/prepared_air_special_v1'
old=source.read_bytes();new=(candidate/'PL01_U.ARC').read_bytes()
proposal=json.loads((candidate/'proposal.json').read_text('utf8'))
positive=check_static_body(old,new,proposal['static_body_patch'])
scratch=W/'static_guard_cases';scratch.mkdir(exist_ok=False)
recipe=json.loads((candidate/'static_effects.json').read_text('utf8'))
for n in ['palette.bin','effect_23.png','effect_24.png']:(scratch/n).write_bytes((candidate/n).read_bytes())
results=[]
def rejected(name,data,r=None,bound_override=None):
    p=scratch/(name+'.json');p.write_text(json.dumps(recipe if r is None else r,indent=2)+'\n','utf8')
    bound={'recipe':str(p.relative_to(ROOT)),'sha256':sha(p.read_bytes())}
    if bound_override:bound.update(bound_override)
    try:check_static_body(old,data,bound)
    except (RuntimeError,ValueError,AssertionError,KeyError) as e:results.append({'name':name,'rejected':True,'reason':str(e)})
    else:raise AssertionError('Invalid case accepted: '+name)
rejected('bad_bound_hash',new,bound_override={'sha256':'0'*64})
r=copy.deepcopy(recipe);r['frames']['27']=r['frames']['23'];rejected('scope_expansion',new,r)
r=copy.deepcopy(recipe);r['parts_sha256']='0'*64;rejected('wrong_parts',new,r)
r=copy.deepcopy(recipe);r['palette_file']='../riko/prepared_air_special_v1/palette.bin';rejected('art_outside_recipe',new,r)
texture=bytearray(entry(new,0x10206));parts=entry(new,3)
bodytiles={p['page']*256+p['tile']for f in [23,24]for p in composition_frame(parts,6,f)['parts']}
projectile=next(p for p in composition_frame(parts,6,27)['parts'] if p['page']*256+p['tile'] not in bodytiles)
t=projectile['page']*256+projectile['tile'];offset=t//16*16*128+t%16*8;texture[offset]^=1
r=copy.deepcopy(recipe);r['modified_texture_sha256']=sha(texture)
rejected('projectile_changed_even_with_updated_hash',replace_entry(new,0x10206,texture),r)
assert len(results)==5
report={'passed':True,'positive':positive,'rejections':results,'output_discs_written':False}
(W/'static_guard_checks.json').write_text(json.dumps(report,indent=2)+'\n','utf8')
print(json.dumps(report))
