"""Negative-input checks for the locally built Ultimate pilot."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.analyze_shibuki_ultimate import D,load
from scripts.build_shibuki_ultimate_idle import validate_candidate
from scripts.prepare_shibuki_ultimate_idle import prepare

def main():
    rec,src=load();source=D/'pilot01';out=D/'negative_checks';out.mkdir(exist_ok=False)
    recipe=json.loads((source/'recipe.json').read_text());check=json.loads((source/'regression.json').read_text());data=(source/'PL02_U.ARC').read_bytes();cases=[]
    for name in ('corrupt_bytes','wrong_parent','wrong_record','wrong_regression','expanded_scope'):
        d=out/name;d.mkdir();r=json.loads(json.dumps(recipe));c=dict(check);b=data
        if name=='corrupt_bytes':b=data[:100]+bytes([data[100]^1])+data[101:]
        if name=='wrong_parent':r['parent_bin_sha256']='0'*64
        if name=='wrong_record':r['source_record']['lba']+=1
        if name=='wrong_regression':c['archive_sha256']='0'*64
        if name=='expanded_scope':r['resources_relocated']=True
        (d/'recipe.json').write_text(json.dumps(r));(d/'regression.json').write_text(json.dumps(c));(d/'PL02_U.ARC').write_bytes(b)
        try:validate_candidate(d,rec['PL02_U.ARC'],src['parent']['PL02_U.ARC'])
        except ValueError as exc:cases.append({'case':name,'rejected':True,'reason':str(exc)})
        else:raise AssertionError('Invalid candidate accepted')
    for name,path in [('outside_task',ROOT/'out'),('overwrite_existing',source)]:
        try:
            if name=='outside_task':validate_candidate(path,rec['PL02_U.ARC'],src['parent']['PL02_U.ARC'])
            else:prepare(path,D/'normalized03')
        except ValueError as exc:cases.append({'case':name,'rejected':True,'reason':str(exc)})
        else:raise AssertionError('Invalid path accepted')
    (out/'report.json').write_text(json.dumps(cases,indent=2));print(json.dumps({'rejected':len(cases),'all_passed':True,'report':str(out/'report.json')}))

if __name__=='__main__':main()
