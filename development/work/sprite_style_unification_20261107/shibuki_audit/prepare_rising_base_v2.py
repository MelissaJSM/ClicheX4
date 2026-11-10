"""포스103 소매를 별도 잠금 입력으로 만들고 원 패커의 새 버전을 준비한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parents[2]))
import numpy as np
from PIL import Image
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive
from prepare_lowhp_final import compose

def main():
    old=H/'rising_common_layers01';new=H/'rising_common_layers02';fix=H/'rising103_sleeve_native03'
    need(not new.exists(),'Fresh native version required')
    lock=json.loads((old/'LOCK.json').read_text('utf8'));need(sha((old/'LOCK.json').read_bytes())=='a931eb6b16eb1782ec80c220b30ae1db82a3408256fc3bf44c22c78b67ee69f9','Old lock changed')
    for name,digest in lock['files'].items():need(sha((old/name).read_bytes())==digest,'Old locked input changed')
    report=json.loads((fix/'report.json').read_text('utf8'));need(report['passed'] and report['native_silhouette_exact'],'Local correction failed')
    oldarm=np.array(Image.open(old/'103_bank7_indices.png'));newarm=np.array(Image.open(fix/'103_bank7_indices.png'));allowed=np.array(Image.open(fix/'allowed_sleeve_mask.png'))>0
    need(np.array_equal(oldarm[~allowed],newarm[~allowed]),'Outside sleeve changed')
    need(np.array_equal(oldarm>0,newarm>0),'Sleeve alpha changed')
    need(np.count_nonzero(oldarm!=newarm)==58,'Unexpected local difference')
    new.mkdir()
    for name in lock['files']:(new/name).write_bytes((old/name).read_bytes())
    (new/'103_bank7_indices.png').write_bytes((fix/'103_bank7_indices.png').read_bytes())
    lock['files']={name:sha((new/name).read_bytes())for name in lock['files']}
    for name in ['register_rising103_sleeve.py','rising103_sleeve_edit01/generated.png','rising103_sleeve_edit01/sleeve_region.png','rising103_sleeve_native03/allowed_sleeve_mask.png','rising103_sleeve_native03/report.json','prepare_rising_base_v2.py']:
        lock['source_files'][name]=sha((H/name).read_bytes())
    lock['replaces']='rising_common_layers01/LOCK.json';lock['revision']='Fourth103 소매만 새 검정/보라 원화로 교체. 원래 어두운 외곽6픽셀과 나머지 모든 층/실루엣 보존.'
    write(new/'LOCK.json',lock);digest=sha((new/'LOCK.json').read_bytes())
    packer=H/'pack_rising_base_probe.py'
    first=json.loads((H/'prepared_rising_fire_base01/INPUT_FROZEN.json').read_text('utf8'));need(sha(packer.read_bytes())==first['producer_scripts'][packer.name],'Old packer changed')
    source=packer.read_text('utf8');need(source.count("'rising_common_layers01'")==1 and source.count("default='rising_base_pack_probe01'")==1,'Unexpected producer source')
    source=source.replace("'rising_common_layers01'","'rising_common_layers02'").replace("default='rising_base_pack_probe01'","default='rising_base_pack_probe02'").replace("LOCK_SHA='a931eb6b16eb1782ec80c220b30ae1db82a3408256fc3bf44c22c78b67ee69f9'",f"LOCK_SHA='{digest}'")
    dest=H/'pack_rising_base_v2.py';need(not dest.exists(),'Fresh producer required');dest.write_text(source,encoding='utf8')
    write(new/'revision_proof.json',{'passed':True,'old_lock':sha((old/'LOCK.json').read_bytes()),'new_lock':digest,'changed_layer_files':['103_bank7_indices.png'],'changed_native_pixels':58,'alpha_exact':True,'all_other_native_layers_exact':True,'new_source_report':str(fix.relative_to(H)/'report.json'),'original_producer_hash':sha(packer.read_bytes()),'new_producer_hash':sha(dest.read_bytes())})
    print(json.dumps({'lock':digest,'packer':str(dest)}))
if __name__=='__main__':main()
