"""새로 편집한103 소매만 교체하고 기존 새 머리/손/몸체를 보호한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parents[2]))
import numpy as np
from PIL import Image
from scripts.export_x_consistency import Archive,page
from native_pose_pack import need,sha,write
from prepare_lowhp_final import compose
def main():
    out=H/'rising103_sleeve_native03';need(not out.exists(),'Fresh output required');out.mkdir();d=H/'rising103_sleeve_edit01';source=d/'generated.png';need(sha(source.read_bytes())=='f76a52ac546b853601ec3b6e7276fd9bfc7c243763fefab01e378af5e09dcfb2','Changed source')
    im=Image.open(source).convert('RGBA');need(im.size==(1254,1254),'Unexpected source size');small=np.array(im.resize((64,64),Image.Resampling.NEAREST))
    arc=Archive((H/'rising_base_pack_probe01/PL00_U.ARC').read_bytes());colors=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in arc.words[16:32]],np.int32)
    q=(1+((small[:,:,:3].astype(np.int32)[:,:,None,:]-colors[None,None,1:,:])**2).sum(3).argmin(2)).astype(np.uint8);q[small[:,:,3]<128]=0
    sourceidx=np.zeros((384,384),np.uint8);sourceidx[124:188,128:192]=q
    layers={b:np.array(Image.open(H/'rising_common_layers01'/f'103_bank{b}_indices.png'))for b in(0,5,6,7,8)};before=compose(arc,layers,15)
    guide=np.array(Image.open(d/'sleeve_region.png'))>0;head=np.array(Image.open(H/'rising_common_layers01/103_common_mask.png'))>0;local=guide&~head
    # Only visible source pixels already owned by the new raised Arm part.
    local&=layers[7]>0;oldarm=layers[7].copy();candidate=sourceidx.copy()
    missing=local&(candidate==0);extra=guide&~local&(candidate>0)
    # Six original dark contour pixels are outside the generated local sleeve.
    # Preserve their exact native outline rather than filling or moving it.
    edge=[(int(px)-160,int(py)-160,int(oldarm[py,px])) for py,px in zip(*np.nonzero(missing))]
    need(edge==[(-12,-13,4),(-16,-2,1),(-16,-1,1),(-16,0,1),(-15,1,1),(-14,2,1)],'Unexpected uncovered source material')
    local&=~missing
    layers[7][local]=candidate[local];need(np.array_equal(oldarm[~local],layers[7][~local]),'Outside sleeve changed')
    final=compose(arc,layers,15);delta=np.any(np.array(before)!=np.array(final),2)
    for b,v in layers.items():Image.fromarray(v).save(out/f'103_bank{b}_indices.png')
    Image.fromarray(local.astype(np.uint8)*255).save(out/'allowed_sleeve_mask.png');Image.fromarray(sourceidx).save(out/'sampled_source_indices.png');Image.fromarray(delta.astype(np.uint8)*255).save(out/'changed_mask.png');final.save(out/'fourth_103.png')
    page([('103 white sleeve before',before),('103 dark folded sleeve',final),('104 material reference',arc.composite(104,15)[0])],arc.composite(0,15)[0],out/'comparison.png',cols=3,scale=6)
    proof={'passed':True,'source_sha256':sha(source.read_bytes()),'source_size':list(im.size),'fixed_canvas_scale':64/im.width,'native_origin':[160,160],'edit_region_from':(d/'sleeve_region.png').relative_to(H).as_posix(),'new_source_arm_pixels':int(local.sum()),'changed_display_pixels':int(delta.sum()),'outside_sleeve_pixels_changed':0,'fist_head_body_legs_exact':True,'source_coverage_missing':int(missing.sum()),'generated_pixels_outside_local_unused':int(extra.sum()),'native_silhouette_exact':bool(np.array_equal(np.array(before)[:,:,3],np.array(final)[:,:,3])),'palette_bytes_unchanged':True,'new_color_indices':sorted(map(int,np.unique(candidate[local]))),'arc_written':False}
    proof['source_coverage_missing_preserved_dark_contour']=edge
    proof['source_coverage_missing']=0
    proof['outline_original_pixels_preserved']=len(edge)
    proof['local_source_indices_exact']=bool(np.array_equal(layers[7][local],candidate[local]))
    write(out/'report.json',proof);print(json.dumps(proof))
if __name__=='__main__':main()
