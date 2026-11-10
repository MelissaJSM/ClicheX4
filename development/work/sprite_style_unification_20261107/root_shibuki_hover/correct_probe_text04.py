from pathlib import Path
import re,subprocess,sys,json,hashlib
D=Path(__file__).resolve().parent
old=D/'prepare_body_layers03.py';new=D/'prepare_body_layers04.py';assert not new.exists()
s=old.read_text('utf8').replace("out=D/'body_layers_probe03'","out=D/'body_layers_probe04'")
fixed="'shared_hand_rule':'의미창 안의 기본 피부·명암10..13과 포스 피부9 영역을 공통0로 제한한다. 소매·커프·칼라 직사각형 전체를 복사하지 않는다.'"
s,n=re.subn(r"'shared_hand_rule':'[^']*'",fixed,s);assert n==1
new.write_text(s,'utf8');subprocess.run([sys.executable,str(new)],check=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=list((D/'body_layers_probe03').glob('*.png'));assert files
assert all(sha(p)==sha(D/'body_layers_probe04'/p.name)for p in files)
(D/'body_layers_probe04/text_correction.json').write_text(json.dumps({'source_manifest_sha256':sha(D/'body_layers_probe03/manifest.json'),'source_preserved':True,'all_png_files_exact':len(files),'reason':'PowerShell 외부 파이프에서 설명 한 줄이 물음표로 인코딩된 것을 한국어로 복원했다. 새폴더의 그림·층·owner는 모두 이전03과 바이트동일.','geometry_note':'223 오른신발38픽셀의Y−1 국소등록은 목적지 윗행8픽셀 가림을 포함한다. 공통하체 불투명243→235이며 강체이동 전체픽셀수 보존으로 주장하지 않는다.'},ensure_ascii=False,indent=2)+'\n','utf8')
print('설명만 새04에 복원; 기존03 보존; 모든 PNG 동일')
