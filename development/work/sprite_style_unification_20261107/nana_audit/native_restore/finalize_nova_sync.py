from pathlib import Path
import sys,json,copy
ROOT=Path(__file__).resolve().parents[4];sys.path[:0]=[str(ROOT),str(Path(__file__).parent)]
from preview_restore import Archive,sha,write,need,data
from prepare_nova_hair_sync import build,PARENT,BASE
import numpy as np
D=Path(__file__).parent;O=D/'nova_sync_v1'
def main():
    assets,_=data();original=assets['PL02_U.ARC'];parent=(D/'prepared_v1/PL02_U.ARC').read_bytes();actual=(O/'PL02_U.ARC').read_bytes();again,tt,proof,*_=build(original,parent);need(again==actual,'Reproduction differs');bad=[]
    for case in('source_sha','parent_sha','missing_ref','body_edit','extra_ref','wrong_hair_color'):
        aa=original;bb=parent;t={k:v.copy()for k,v in tt.items()}
        if case=='source_sha':aa=bytes([original[0]^1])+original[1:]
        elif case=='parent_sha':bb=bytes([parent[0]^1])+parent[1:]
        elif case=='missing_ref':del t[217,0]
        elif case=='extra_ref':t[219,0]=t[217,0]
        elif case=='body_edit':t[217,0][180,160]=1
        else:
            y,x=np.nonzero(t[217,0]);t[217,0][y[0],x[0]]=15
        try:build(aa,bb,t)
        except ValueError as e:bad.append({'case':case,'rejected':True,'reason':str(e)})
        else:raise AssertionError('Invalid input accepted '+case)
    prior=json.loads((D/'prepared_v1/proposal.json').read_text('utf8'));f=copy.deepcopy(prior['files']['PL02_U.ARC']);f.update(path=(O/'PL02_U.ARC').relative_to(ROOT).as_posix(),after=sha(actual));f.update(sequential_input_sha256=PARENT,new_refs=[217,218,220],changed_parts_banks=[0],changed_pixels_per_ref=101,included_previous_dash_hair_restore=True)
    proposal={k:prior[k]for k in('project','baseline','baseline_sha256')};proposal.update(files={'PL02_U.ARC':f},candidate_only=True,runtime_verified=False,new_art_generated=False)
    write(O/'proposal.json',proposal);write(O/'reproduction.json',{'passed':True,'after_sha256':sha(actual),'reproduced_bytes_identical':True,'rejected_inputs':bad})
    print(json.dumps({'sha':sha(actual),'rejects':len(bad),'proposal':str(O/'proposal.json')}))
if __name__=='__main__':main()
