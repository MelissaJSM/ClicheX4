"""Ultimate7 고정 입력의 재제작 및 잘못된 입력 거부."""
from pathlib import Path
import sys,json,copy
import numpy as np
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D))
import pack_ultimate as production
from preview_restore import digest,sha,write,need

def main():
    p=production.load_packer();target,meta=production.targets();data=p.PARENT.read_bytes();out=D/'packed_ultimate_candidate_v1';candidate=(out/'PL02_U.ARC').read_bytes();rejected=[]
    def reject(name,fn):
        try:fn()
        except(ValueError,KeyError,TypeError):rejected.append(name)
        else:raise ValueError('Bad input accepted: '+name)
    bad=bytearray(data);bad[-1]^=1;reject('wrong_parent',lambda:p.build(bytes(bad),target,meta))
    for name,change in(('wrong_manifest_parent',lambda m:m.update(source_arc_sha256='0'*64)),('duplicate_ref',lambda m:m['frames'].__setitem__(0,m['frames'][1])),('target_hash',lambda m:m['frames'][0].update(base_sha256='0'*64))):
        m=copy.deepcopy(meta);change(m);reject(name,lambda m=m:p.validate_targets(target,m))
    t=dict(target);t.pop((100,0));reject('missing_target',lambda:p.validate_targets(t,meta))
    t=dict(target);t[105,0]=t[100,0];reject('unexpected_target',lambda:p.validate_targets(t,meta))
    for name,v in(('changed_texel',target[100,0].copy()),('wrong_shape',np.zeros((383,384),np.uint8)),('wrong_depth',target[100,0].astype(np.uint16)),('invalid_index',target[100,0].copy())):
        if name=='changed_texel':v[160,160]^=1
        if name=='invalid_index':v[0,0]=16
        t=dict(target);t[100,0]=v;reject(name,lambda t=t:p.validate_targets(t,meta))
    for name,key,pos in(('outside_registration_window',(100,0),(0,0)),('broken231_232_identity',(232,0),(160,160))):
        t=dict(target);t[key]=target[key].copy();t[key][pos]^=1;m=copy.deepcopy(meta);next(q for q in m['frames']if q['ref']==key[0])['base_sha256']=sha(t[key].tobytes());reject(name,lambda t=t,m=m:p.validate_targets(t,m))
    lock=json.loads((out/'INPUT_FROZEN.json').read_text('utf8'))
    for q in lock['files']:need(digest(production.ROOT/q['path'])==q['sha256'],'Input drift '+q['path'])
    rebuilt,proof=p.build(data,target,meta);need(rebuilt==candidate,'Byte-identical reproduction')
    write(out/'reproduction.json',{'passed':True,'candidate_sha256':sha(candidate),'parent_sha256':sha(data),'negative_cases':rejected,'input_files_verified':len(lock['files']),'same_process_rebuild_byte_identical':True,'full7296_recheck':proof['rgba_combinations'],'separate_process_reproduction':False,'runtime_verified':False})
    print(json.dumps({'passed':True,'negative_cases':len(rejected),'candidate_sha256':sha(candidate)}))
if __name__=='__main__':main()
