"""이번 대시 사격 생성 원본/프롬프트와 읽기 검수 이력을 기록."""
from pathlib import Path
import json,sys
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
FILES={2:('exec-57de1a2c-5bf0-463d-b574-b6977c2cf9f1.png','1d3c19af2d4a381614f3b34a760e2e630d85fb45f60d06260300a601827dc4ff'),3:('exec-fd3868c0-3fc5-4e0a-abcc-0328647b0d29.png','d3548106c95428943871e3eef7d582d849a0cbe5cbae192bafa1d13c6b60879f'),4:('exec-62b3cc13-100e-4a51-bfeb-4735a5ba4384.png','d210d73a7ec85a38a39b0ad52b7cf0bc0560f59b33b2bba61cb9f00a964e0827')}
def main():
    for pn,(name,digest)in FILES.items():
        d=H/f'dash_shot_inputs02/page{pn:02}';need(sha((d/'generated.png').read_bytes())==digest,'Source changed');prompt=(d/'prompt.txt').read_text('utf8').strip();(d/'prompt_used.txt').write_text(prompt,encoding='utf8');write(d/'generation_receipt.json',{'tool':'builtin imagegen','original_filename':name,'source_sha256':digest,'prompt_sha256':sha(prompt.encode()),'inputs_sha256':{n:sha((d/n).read_bytes())for n in('edit_target.png','arm_guide_matte.png')},'packed':False,'page4_ref82_requires_local_retry':pn==4})
    plates=[]
    for d,patterns in {'dash_shot_page02_registered01':['*_comparison.png'],'dash_shot_page03_registered05':['*_comparison.png'],'dash_shot_layers01':['ownership_*.png','partial_*.png']}.items():
        for pattern in patterns:plates.extend(sorted((H/d).glob(pattern)))
    write(H/'dash_shot_layers01/visual_review.json',{'actually_viewed':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p.read_bytes())}for p in plates],'observations':['68/70/72/76 앞팔은 두 의상·16부분 조합에서 목/손목/무릎 단절이나 추가 손을 새로 발견하지 못함.','78/80의 오래된 팔 제거 마스크는 새 무릎과 총열 옆 새 머리2픽셀을 침범하지 않도록 제한했다.','82 생성은 원총구보다 왼쪽으로6px 이동해 보류. 짧고 접힌 회복 팔을 국소 재작화 예정.'],'partial_rgba_checks':128,'native_cpu_checked':False,'resource_packed':False})
    print(json.dumps({'receipts':len(FILES),'viewed_plates':len(plates)}))
if __name__=='__main__':main()
