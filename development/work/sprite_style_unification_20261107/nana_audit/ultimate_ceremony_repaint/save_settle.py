"""등장 끝 두 의상 생성 원본 보존."""
from pathlib import Path
import json,hashlib,shutil
from PIL import Image
import numpy as np
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    src=Path('<LOCAL_PATH>');out=D/'settle_v1';out.mkdir(exist_ok=False);dest=out/'generated.png';shutil.copyfile(src,dest);im=Image.open(dest).convert('RGBA');ar=np.array(im)
    m={'tool':'builtin imagegen','source_output_path':str(src),'source_sha256':sha(src),'workspace_path':dest.relative_to(ROOT).as_posix(),'workspace_sha256':sha(dest),'size':list(im.size),'mode':im.mode,'prompt_path':(D/'settle_inputs_v1/prompt.txt').relative_to(ROOT).as_posix(),'prompt_sha256':sha(D/'settle_inputs_v1/prompt.txt'),'input_manifest_sha256':sha(D/'settle_inputs_v1/manifest.json'),'scope':'Ultimate138 전후2표시 원화. 배경알파와 접점 등록 검사 전.','alpha_histogram':dict(zip(map(int,np.unique(ar[:,:,3])),map(int,np.unique(ar[:,:,3],return_counts=True)[1])))}
    (out/'generation.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'sha256':sha(dest),'size':m['size'],'alpha_minmax':[int(ar[:,:,3].min()),int(ar[:,:,3].max())],'alpha128_count':int((ar[:,:,3]>=128).sum())}))
if __name__=='__main__':main()
