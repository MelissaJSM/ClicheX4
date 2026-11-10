"""US 원본9속도선 파츠와 현재73/74의 몸체 차이를 분리한다. 읽기 전용."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
from src.psx_player import composition_frame,decode_stream
from src.psx_sprite_batch import canvas_from_parts
def main():
    d=H/'dash_speed_streak_audit02';need(not d.exists(),'Fresh audit required');d.mkdir()
    p=ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/original.arc'
    need(sha(p.read_bytes())=='92b2a3209ad6603cf519616dc580400434271f87e8e7129495430c04d0d1c35a','Original US extraction changed');orig=Archive(p.read_bytes())
    current=[('PL00',H/'prepared_rising_right_base01/PL00_U.ARC','13a29023365419d32475cf5a6551adc4658116c8f03622d962d5b8071744e8b8'),('PL02',H/'prepared_ultimate_air01/PL02_U.ARC','3ae1d8d56c595b04e59abf735ac377ab381c73673c2eaade99679031f3fc65f7')]
    rows=[];pictures=[]
    for first,second in((71,73),(72,74)):
        cp=composition_frame(orig.c,0,first);cq=composition_frame(orig.c,0,second)
        sig=lambda part:(part['flags'],part['tile'],part['x'],part['y'])
        need(sorted(sig(q)for q in cp['parts'])==sorted(sig(q)for q in cq['parts'][:len(cp['parts'])]),'Original alias body records differ')
        tail=cq['parts'][len(cp['parts']):];need(len(tail)==9 and {v['tile']for v in tail}=={6},'Unexpected original streaks')
        f=orig.banks[0]['frames'][second];raw=decode_stream(orig.g,f['offset'],f['limit'],f['tile_count']*128).data
        streak=canvas_from_parts(raw,f['tile_count'],dict(cq,parts=tail),size=(384,384),origin=(160,160))
        oldbody=orig.layer(first)[0];prefix=canvas_from_parts(raw,f['tile_count'],dict(cq,parts=cq['parts'][:len(cp['parts'])]),size=(384,384),origin=(160,160));want=prefix.copy();want[streak>0]=streak[streak>0]
        need(np.array_equal(want,orig.layer(second)[0]),'Original draw order not exact')
        Image.fromarray(streak).save(d/f'{second:03}_original_streak_indices.png')
        base_row={'first':first,'second':second,'original_extra_parts':[sig(v)for v in tail],'original_streak_pixels':int(np.count_nonzero(streak)),'draw_order':'본체 이후9속도선 파츠; 비투명 속도선 픽셀은 몸체 위에 표시','original_body_prefix_order_changed':True,'original_body_prefix_index_differences':int(np.count_nonzero(prefix!=oldbody)),'original_full_index_exact':True,'original_tile6_sha256':sha(raw[6*128:7*128]),'samples':[]}
        for name,path,digest in current:
            need(sha(path.read_bytes())==digest,'Changed current arc');a=Archive(path.read_bytes())
            for form,mask in([('base',0),('fourth',15)]if name=='PL00'else[('ultimate_after',0),('ultimate_before',15)]):
                body=np.array(a.composite(first,mask)[0]);existing=np.array(a.composite(second,mask)[0]);rgba=np.array(a.rgba(streak));expected=body.copy();expected[streak>0]=rgba[streak>0]
                if mask:
                    # Engine armor overlays occur after base+streak. Preserve their
                    # actual original order and let garments cover streak texels.
                    for bit,pb in((8,8),(1,5),(4,7),(2,6)):
                        if mask&bit:
                            layer=np.array(a.rgba(a.layer(second,pb)[0],32 if pb==7 else 16));m=layer[:,:,3]>0;expected[m]=layer[m]
                off=np.any(expected!=existing,axis=2);outside=off&(streak==0)
                Image.fromarray(expected).save(d/f'{form}_{second:03}_same_body_original_streak.png')
                Image.fromarray(outside.astype(np.uint8)*255).save(d/f'{form}_{second:03}_body_difference_mask.png')
                base_row['samples'].append({'archive':name,'form':form,'source_sha256':digest,'expected_body_plus_original_streak_exact':not bool(off.any()),'difference_pixels':int(off.sum()),'outside_streak_pixels':int(outside.sum()),'world_difference_bbox':None if not off.any()else[int(np.nonzero(off)[1].min()-160),int(np.nonzero(off)[0].min()-160),int(np.nonzero(off)[1].max()+1-160),int(np.nonzero(off)[0].max()+1-160)]})
                pictures.extend([(f'{form} {first} body',Image.fromarray(body)),(f'{form} {second} current',Image.fromarray(existing)),(f'{form} same body + native streak',Image.fromarray(expected))])
        rows.append(base_row)
    for i in range(0,len(pictures),12):page(pictures[i:i+12],orig.composite(0)[0],d/f'comparison_{i//12:02}.png',cols=3,scale=4)
    write(d/'report.json',{'original_us_arc':p.relative_to(ROOT).as_posix(),'original_sha256':sha(p.read_bytes()),'rows':rows,'notes':'원래9파츠의 위치·색인·표시순서로 재합성했다. 원US74는72와본체레코드집합은같지만순서로인한겹침1픽셀이달라순서를별도로보존해야한다. 현재 Ultimate 후폼의73/74는 속도선 밖 본체 차이가 있어 단순별칭으로 취급하지 않는다. 이 파일은 진단이며 자원/게임/시간표를 변경하지 않았다.','rejected_trial':'audit01은 원US72/74의 본체가 순서까지 같다는잘못된가정을검출해중단했다. 그부분출력은채택하지않는다.','prepared_resource':False,'visual_review_pending':True})
    print(json.dumps(rows))
if __name__=='__main__':main()
