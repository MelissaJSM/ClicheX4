"""136/139의 실제 별도 자세를 보존한 원화 입력. 기존135 편집의 재시도가 아니다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,metrics

def main():
    d=H/'ultimate_arrival_separate_inputs02';need(not d.exists(),'Fresh separate pose inputs')
    parent=H/'prepared_ultimate_hurt02/PL02_U.ARC';need(sha(parent.read_bytes())=='b43e021b70c055d142521d1c679bef323d76b0b30bf27b41c9988815330b2e94','Parent changed')
    rel=H.parent/'zero_audit/shibuki_ultimate_arrival_relations01';need(sha((rel/'report.json').read_bytes())=='3a7bee18e7625a72dc9e7f76731698b878d1c31ce730822c1f709ec7bea5e96a','Relation changed')
    fx=np.load(rel/'effect_136.npy');need(int(np.count_nonzero(fx))==46,'136 original FX source changed')
    a=Archive(parent.read_bytes());target=Image.new('RGBA',(1536,1024));styles=Image.open(H/'ultimate_arrival_inputs01/page01/accepted_ultimate_style.png').convert('RGBA');rows=[]
    for row,(form,mask) in enumerate((('before',15),('after',0))):
        for col,n in enumerate((136,139)):
            current=a.composite(n,mask)[0];v=np.array(current);removed=0
            if n==136:
                removed=int(((v[:,:,3]>0)&(fx>0)).sum());v[fx>0]=0
            pic=Image.fromarray(v);cut=pic.crop((112,124,208,188));need(np.count_nonzero(np.array(cut)[:,:,3])==np.count_nonzero(v[:,:,3]),'Original pose clips')
            target.alpha_composite(cut.resize((768,512),Image.Resampling.NEAREST),(col*768,row*512))
            rows.append({'ref':n,'form':form,'current_rgba_sha256':sha(current.tobytes()),'body_only_sha256':sha(v.tobytes()),'body_metrics':metrics(pic),'removed_effect_samples':removed,'pose_replaced_by_neighbour':False})
    d.mkdir();target.save(d/'edit_target.png');target.save(d/'old_coordinate_reference.png');styles.save(d/'accepted_ultimate_style.png')
    prompt='''Use Image1 as the exact pose and cell-position reference for four game sprites, and Image2 as the accepted character detail/style reference. Produce a transparent 1536x1024 pixel-art sheet in exactly the same 2x2 cells. Each 768x512 cell represents a fixed 96x64 logical pixel area enlarged 8x, with origin(48,36). Preserve each original pose's head angle, hand positions, elbow directions, knee and ankle positions, feet and compact body proportions. Do not replace either pose by an idle or another neighbouring animation frame, and do not enlarge the full body. Draw clear native-sized pixel clusters: layered lavender hair locks, fox ears with inner planes, small gold glasses on the head, restrained facial details and garment folds matched to Image2. Keep the existing short torso and limbs, softly rounded proportions and distinct sandals.
Top row wears the accepted pale lavender/white cropped jacket with navy collar/cuff shadows, pink center trim and the swimsuit beneath. Bottom row wears the accepted pale lavender one-piece swimsuit with pink chest accent, bare shoulders and bare arms. Preserve the exact two arms and two legs in each cell. Bottom row has no jacket sleeves or cuffs. Costume details differ while the respective same-pose heads, hands and legs remain aligned between rows.
Left column is pose136: preserve the original raised bent fists close to the chest, the particular shoulder and elbow angles, slightly bent knees and spread stance visible in Image1. This is its own transitional pose, not pose135 or idle. Right column is pose139: preserve the close feet and both hands meeting above the head at their original height, with the original turned head and overhead forearm directions. Retain each bottom costume's own torso shape and upper-body twist from Image1 rather than replacing it by the adjacent frame138. Keep the hands distinct from the ears and use the reference's shoulder-to-elbow anatomy without long vertical pole-like arms. No beam, lightning, aura, weapon, text, new accessory or background. Do not add glows or scribbled black outlines. The detail should read cleanly at actual 1x size.'''
    (d/'prompt.txt').write_text(prompt+'\n','utf8')
    write(d/'input.json',{'refs':[136,139],'ultimate_parent':{'path':parent.relative_to(ROOT).as_posix(),'sha256':sha(parent.read_bytes())},'relation_report':{'path':(rel/'report.json').relative_to(ROOT).as_posix(),'sha256':sha((rel/'report.json').read_bytes())},'source_layout':{'size':[1536,1024],'native_cell':[96,64],'native_origin':[48,36],'scale':0.125,'crop':[112,124,208,188]},'rows':rows,'source_policy':'현재136/139 각폼 자체 포즈를 보존한 상세 재작화 입력.135/138의 평행이동 복사가 아님.136효과46셀만 입력에서 분리하며 숨은 몸체는 추출했다고 주장하지 않는다.','canvas_crop_change':'139의 가장 높은 손이 셀 윗변에 붙지 않도록 원점만4px아래에 두었다. 전신그림 이동/크기변환이 아니며 등록 때crop124..188로 되돌린다.','blocked135_edit_retry':False,'raw_original_game_art_sent':False,'effect_pixels_sent_to_generation':False,'new_art_generated':False,'arc_written':False,'files':{p.name:sha(p.read_bytes())for p in d.iterdir()if p.is_file()}})
    print(json.dumps({'path':d.relative_to(ROOT).as_posix(),'rows':rows},ensure_ascii=False))
if __name__=='__main__':main()
