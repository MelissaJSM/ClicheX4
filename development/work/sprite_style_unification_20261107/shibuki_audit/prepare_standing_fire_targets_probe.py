"""88의 현재 효과83셀/전체2타일을 분리하고 새89로40층 후보를 만든다."""
from pathlib import Path
import sys,json,copy
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
from src.psx_player import composition_frame,compose_indices,decode_stream,indexed_atlas
from prepare_lowhp_final import compose
PBS=(0,5,6,7,8)
def main():
    d=H/'standing_fire_targets_probe01';need(not d.exists(),'Fresh target probe');d.mkdir();s=H/'standing_fire_layers_probe02';p=H/'prepared_standing_special_base01/PL00_U.ARC';a=Archive(p.read_bytes());cp=composition_frame(a.c,0,88);fxcp=copy.deepcopy(cp);fxcp['parts']=[r for r in cp['parts']if r['tile']in(7,8)];need(len(fxcp['parts'])==2,'FX parts');f=a.banks[0]['frames'][88];raw=decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128).data;pix,size,bb,_=compose_indices(raw,f['tile_count'],fxcp,allowed_cluts={0});sm=np.frombuffer(pix,np.uint8).reshape(size[1],size[0]);fx=np.zeros((384,384),np.uint8);yy,xx=np.nonzero(sm);fx[yy+bb[1]+160,xx+bb[0]+160]=sm[yy,xx];need(np.count_nonzero(fx)==83 and set(np.unique(fx))=={0,6},'FX pixels/color');need(np.array_equal(a.layer(88,0)[0],np.where(fx>0,fx,np.roll(a.layer(89,0)[0],-1,1))),'Current base relationship')
    for b in PBS[1:]:need(np.array_equal(a.layer(88,b)[0],np.roll(a.layer(89,b)[0],-1,1)),'Current armor relationship')
    targets={n:{b:np.array(Image.open(s/f'{n:03}_bank{b}_indices.png'))for b in PBS}for n in(85,86,87,89,90,91,92)};targets[88]={b:np.roll(v,-1,1)for b,v in targets[89].items()};overlaps={str(b):int(((targets[88][b]>0)&(fx>0)).sum())for b in PBS};targets[88][0][fx>0]=fx[fx>0]
    for b in PBS[1:]:targets[88][b][fx>0]=0
    for n,ll in targets.items():
        for b,v in ll.items():Image.fromarray(v).save(d/f'{n:03}_bank{b}_indices.png')
        for form,mask in [('base',0),('fourth',15)]:compose(a,ll,mask).save(d/f'{form}_{n:03}.png')
    Image.fromarray(fx).save(d/'088_effect_indices.png');a.rgba(fx).save(d/'088_effect.png');atlas=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256);tiles={}
    for t in(7,8):
        tile=atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16];Image.fromarray(tile).save(d/f'088_effect_tile{t}.png');tiles[str(t)]={'all256_nibble_sha256':sha(tile.tobytes()),'opaque':int((tile>0).sum())}
    for form,mask in [('base',0),('fourth',15)]:page([(f'88 old {form}',a.composite(88,mask)[0]),(f'89 new body {form}',compose(a,targets[89],mask)),(f'88 new / original FX {form}',compose(a,targets[88],mask))],a.composite(0,mask)[0],d/f'effect_{form}_comparison.png',cols=3,scale=5)
    write(d/'manifest.json',{'parent':{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())},'source_joint_report_sha256':sha((s/'report.json').read_bytes()),'refs':list(range(85,93)),'target_layers':40,'targets':{str(n):{str(b):sha(v.tobytes())for b,v in ll.items()}for n,ll in targets.items()},'effect88':{'source_records':fxcp['parts'],'original_order_body6_effect2_body_duplicate1':True,'all_effect_tiles':tiles,'visible_pixels':83,'color_index':6,'current_full_relationship_exact':True,'new_body_translation':[-1,0],'new_body_overlaps_hidden_by_effect':overlaps,'armor_effect_exclusion_policy':'기본층의 원효과83셀을 가리지 않도록 새88 head5겹침2셀만효과좌표에서투명으로등록. 원화89의두셀은그대로보존. 효과앞뒤관계에따른가림이며 품질삭감 아님.','all16_effect_RGBA_exact':all(np.array_equal(np.array(compose(a,targets[88],mask))[fx>0],np.array(a.rgba(fx))[fx>0])for mask in range(16))},'scope':'8참조40층 미패킹 후보. 총열후보/발접점/부분 소유 최종수용 전이며 88효과는원전체타일/좌표/색을보호한다.','root_review_pending':True,'arc_written':False})
    print(json.dumps({'overlaps':overlaps,'effect_tiles':tiles}))
if __name__=='__main__':main()
