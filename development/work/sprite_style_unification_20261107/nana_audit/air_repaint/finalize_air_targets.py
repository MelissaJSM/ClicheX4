"""Freeze reviewed v6 artwork plus the accepted source fold-C detail only."""
from pathlib import Path
import sys,json,shutil
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(D.parent/'native_restore')]
from preview_restore import need,sha,write,digest
PBS=(0,5,6,7,8)
def main():
    source=D/'joint_layers_probe_v6';out=D/'joint_layers_final_v1';need(not out.exists(),'Fresh targets');out.mkdir();doc=json.loads((source/'manifest.json').read_text('utf8'));before=np.array(Image.open(source/'full_039.png'));after=np.array(Image.open(D/'fold39_detail_probe_v1/fold_c.png'));mask=before!=after;need(np.array_equal(before>0,after>0),'Fold alpha');need(np.count_nonzero(mask)==46,'Reviewed fold coverage');details=[]
    for r in doc['frames']:
        n=r['ref'];layers={pb:np.array(Image.open(source/f'layer{pb}_{n:03}.png'))for pb in PBS};full=np.array(Image.open(source/f'full_{n:03}.png'));owner=np.array(Image.open(source/f'owner_{n:03}.png'));base=layers[0].copy()
        if n in(39,40):
            need(np.array_equal(full[mask],before[mask]),'Paired lower-body source');full[mask]=after[mask]
            for pb in(5,6,7,8):
                use=mask&(owner==pb);layers[pb][use]=after[use]
            details.append({'ref':n,'changed_pixels':int(np.count_nonzero(mask)),'source_indexed_sha256':sha(before.tobytes()),'fold_indexed_sha256':sha(after.tobytes()),'alpha_exact':True,'base_exact':True})
        merged=layers[0].copy()
        for pb in(8,5,7,6):merged=np.where(layers[pb],layers[pb],merged)
        need(np.array_equal(merged,full),'Final layer composition');need(np.array_equal(base,layers[0]),'Base detail preserved')
        for pb,idx in layers.items():Image.fromarray(idx).save(out/f'layer{pb}_{n:03}.png')
        Image.fromarray(full).save(out/f'full_{n:03}.png');Image.fromarray(owner).save(out/f'owner_{n:03}.png');r['base_sha256']=sha(base.tobytes());r['full_sha256']=sha(full.tobytes());r['layers']={str(pb):sha(layers[pb].tobytes())for pb in(5,6,7,8)}
    doc['source_v6_manifest_sha256']=digest(source/'manifest.json');doc['fold_C_source']={'path':(D/'fold39_detail_probe_v1/manifest.json').relative_to(ROOT).as_posix(),'sha256':digest(D/'fold39_detail_probe_v1/manifest.json'),'accepted_variant':'fold_c','changes':details};doc['scope']='root가 정적 미술로 확인한 기본/포스 공중22. v6와39/40 접힌 다리C만 포함. 실제 게임 수용은 미확인.';doc['ready_to_apply']=False;write(out/'manifest.json',doc);print(json.dumps({'out':str(out),'changes':details}))
if __name__=='__main__':main()
