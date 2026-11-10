"""작업 후보의 실제 열람 범위와 1~3배 배율 비교를 기록한다."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import write,sha,need
from scripts.export_x_consistency import Archive
from prepare_dash_body_layers import P
def main():
    o=H/'dash_visual_review01';o.mkdir(exist_ok=True);a=Archive(P.read_bytes())
    refs=[67,69,71,75,77,79,81,83,93,94]
    paths=[]
    for folder,pattern in [('dash_detail_contacts02','*_comparison_*.png'),('dash_common_head_probe01','comparison_*.png'),('dash_body_layers01','ownership_*.png'),('dash_body_layers01','partial_*.png'),('dash_barrel_guard02','comparison_*.png'),('dash_recovery_height_native01','*_comparison.png'),('dash_shot_native02','*_comparison.png')]:
        paths.extend(sorted((H/folder).glob(pattern)))
    for form,mask in [('base',0),('fourth',15)]:
        imgs=[('idle0',a.composite(0,mask)[0])]+[(str(n),Image.open(H/f'dash_body_layers01/{n:03}_{form}.png').convert('RGBA'))for n in refs]
        for scale in (1,2,3):
            cellw=64*scale+16;cellh=64*scale+24;out=Image.new('RGBA',(6*cellw,2*cellh),(26,32,42,255));d=ImageDraw.Draw(out)
            for i,(label,im)in enumerate(imgs):
                x=(i%6)*cellw;y=(i//6)*cellh
                d.text((x+2,y+2),f'{label} {scale}x',fill='white')
                # Fixed world window and nearest integer view, never rescale art.
                cut=im.crop((120,128,184,192));need(np.count_nonzero(np.array(cut)[:,:,3])==np.count_nonzero(np.array(im)[:,:,3]),'Clipped visual review')
                cut=cut.resize((64*scale,64*scale),Image.Resampling.NEAREST)
                out.alpha_composite(cut,(x+8,y+20))
            out.save(o/f'{form}_{scale}x.png')
    receipt=H/'dash_shot_inputs02/page01/generation_receipt.json';r=json.loads(receipt.read_text('utf8'));r['native_registration']='dash_shot_native02';write(receipt,r)
    write(o/'visual_review.json',{'parent_sha256':sha(P.read_bytes()),'actually_viewed_prior_to_this_script':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p.read_bytes())}for p in paths],
        'observations':['공통 새 머리와 포스 장식, 앞팔/몸/하체 소유 분리의 16부분 조합에서 새 목·관절 단절이나 얼굴에 소매색이 올라오는 현상을 발견하지 못함.','68/70 새 앞팔은 34 수용 총열 모듈과 연결. 생성된 별도 총열 고리는 원래 새몸이 비어 있던 영역에서만 제거했고 피부 손바닥은 남김.','첫 81/83 후보의 짧은 신장은 국소 재생성 후 접지22로 복구. 83 귀 꼭대기는 원래보다1px 낮음.','79의 머리 꼭대기는 기존보다4px 낮아져 있으므로 최종 원순서 회복 연속 재생에서 다시 확인 필요.'],
        'smallscale_actually_viewed':['base_1x.png','fourth_1x.png','base_2x.png','fourth_2x.png'],'smallscale_observation':'1배와2배에서 머리 덩어리·앞소매·짧은 신체를 읽을 수 있고, 추가 머리 세부가 분리 잡티처럼 보이는 새 결함은 찾지 못함. 정지판 범위이며 연속 원시간표 검토는 아직 필요.','smallscale_view_pending':False,'full_partial_native_cpu_test':False,'packed':False,'in_game_test':False,'all_work_complete':False})
    print(json.dumps({'viewed_files':len(paths),'out':str(o)}))
if __name__=='__main__':main()
