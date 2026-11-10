"""Supplement independent C01 evidence using the hardened builder; no game writes."""
import hashlib
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
WORK=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import BASES,NAMES,read_disc,get_bank,check_arc,verify_native

def expect_rejection(fn):
    try: fn()
    except ValueError as e: return str(e)
    raise AssertionError('Invalid mutation was accepted')

def main():
    path=WORK/'independent.json'
    before=path.read_bytes()
    proof=json.loads(before)
    assert proof['passed']
    cases=[]
    for project,(stem,_) in BASES.items():
        source=ROOT/'out'/project/'selection_unified_20261105_v4'/(stem+'.bin')
        target=ROOT/'out'/project/'c01_x6_sfx_20261105_v1'/(stem+'.bin')
        old,_=read_disc(source,NAMES);new,_=read_disc(target,NAMES)
        positive=verify_native(project,old,new,source)
        assert positive['passed']
        for name in NAMES:
            _,_,q,he,_=get_bank(new[name],3)
            bad=bytearray(new[name]);bad[he['offset']+q['vab_offset']+24]^=1
            reason=expect_rejection(lambda:check_arc(old[name],bytes(bad)))
            cases.append({'project':project,'resource':name,'mutation':'VAB master volume','rejected':True,'reason':reason})
        name=NAMES[0]
        _,_,q,he,_=get_bank(new[name],3)
        for command,tone,label in ((0,1,'hurt command routed to death'),(12,0,'death command routed to hurt')):
            bad=bytearray(new[name]);bad[he['offset']+8+command*4+2]=tone<<4
            reason=expect_rejection(lambda:verify_native(project,old,{**new,name:bytes(bad)},source))
            cases.append({'project':project,'resource':name,'mutation':label,'rejected':True,'reason':reason})
        proof['projects'][project]['hardened_builder_native_dispatcher_cases']=len(positive['cases'])
    proof['hardened_builder_refusal_cases']=cases
    proof['hardened_builder_sha256']=hashlib.sha256((ROOT/'scripts/c01_audio_build.py').read_bytes()).hexdigest()
    proof['preparation_code_sha256']=hashlib.sha256((WORK/'prepare_x6_c01.py').read_bytes()).hexdigest()
    assert path.read_bytes()==before
    archive=WORK/'independent_core_before_extra_refusals.json'
    assert not archive.exists()
    archive.write_bytes(before)
    path.write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'passed':True,'extra_refusals':len(cases),'evidence':str(path)}))

if __name__=='__main__':main()
