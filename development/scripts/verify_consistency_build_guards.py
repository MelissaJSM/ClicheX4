"""Exercise final build rejection paths without creating or altering a disc."""
import json, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.build_sprite_consistency import build, check_resource
from scripts.c01_audio_build import read_disc
from scripts.discover_inputs import psx_arc

def main():
    work=ROOT/'work/sprite_consistency_20261105'
    plan=json.loads((work/'ver_rin_nana_plan.json').read_text('utf8'))
    data,_=read_disc(ROOT/plan['source_bin'],('PL00_U.ARC','MOJIPAT.ARC'))
    tests=[]
    def reject(name,fn):
        try:fn()
        except ValueError as e:tests.append({'case':name,'rejected':True,'reason':str(e)})
        else:raise AssertionError('Accepted bad input: '+name)
    arc=data['PL00_U.ARC'];palette=next(e for e in psx_arc(arc) if int(e['type'],16)==9)
    bad=bytearray(arc);bad[palette['offset']]^=1
    reject('resource_length',lambda:check_resource('PL00_U.ARC',arc,arc+b'\0'))
    reject('non_graphics_palette',lambda:check_resource('PL00_U.ARC',arc,bytes(bad)))
    reject('unapproved_resource',lambda:check_resource('SLUS_005.61',arc,arc))
    menu=data['MOJIPAT.ARC'];badmenu=bytearray(menu);badmenu[4]^=1
    reject('save_directory',lambda:check_resource('MOJIPAT.ARC',menu,bytes(badmenu)))
    with tempfile.TemporaryDirectory(dir=work,prefix='guard_') as tmp:
        target=Path(tmp)/'plan.json'
        for label,change in [('parent_hash',{'source_sha256':'0'*64}),('input_output_collision',{'output':str((ROOT/plan['source_bin']).parent)}),('output_outside_mode',{'output':'character/forbidden_output'})]:
            target.write_text(json.dumps(plan|change),'utf8')
            reject(label,lambda:build(target))
        q=json.loads(json.dumps(plan));q['output']='out/ver_rin_nana/consistency_guard_must_not_exist'
        assert not (ROOT/q['output']).exists()
        q['resources']['PL00_U.ARC']['after']='0'*64
        target.write_text(json.dumps(q),'utf8');reject('prepared_hash',lambda:build(target))
        assert not (ROOT/q['output']).exists()
    report={'passed':True,'rejections':tests,'discs_created_or_modified':False}
    (work/'build_guard_checks.json').write_text(json.dumps(report,indent=2)+'\n','utf8')
    print(json.dumps({'passed':True,'rejected_cases':len(tests)}))

if __name__=='__main__':main()
