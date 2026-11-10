"""새 43번 원화에서 맨어깨 6texel을 복원한다. 머리/포즈/다른 색은 보존."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent;N=D.parent
sys.path[:0]=[str(ROOT),str(D),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
a=Archive((N/'native_restore/nova_sync_v1/PL02_U.ARC').read_bytes());out=D/'costume43_boundary_v3';out.mkdir(exist_ok=False)
bp=D/'costume_pair_probe_v2/after_043.png';sp=D/'after_second_registered_v1/after_043.png';b=np.array(Image.open(bp));src=np.array(Image.open(sp));t=b.copy();coords=[(3,-9),(4,-9),(5,-9),(6,-8),(7,-8),(9,-7)]
for x,y in coords:
 need(int(b[y+160,x+160])in(8,13)and int(src[y+160,x+160])==12,'Source garment/skin changed')
 t[y+160,x+160]=src[y+160,x+160]
need(np.array_equal(b>0,t>0),'Alpha');Image.fromarray(t).save(out/'after_043.png')
helper.grid([('43 shoulder boundary',[('current v2',a.rgba(b,0)),('same-pose new after source',a.rgba(src,0)),('source skin 6px restored',a.rgba(t,0))])],out/'comparison.png',10)
write(out/'verification.json',{'passed':True,'source_body_sha256':digest(bp),'source_registered_art_sha256':digest(sp),'source_generated_art_sha256':digest(D/'after_second_v1/generated.png'),'coordinates_xy':coords,'changed_pixels':6,'source_values':12,'alpha_exact':True,'other_pixels_exact':True,'note':'37 목 뒤 붉은 면은 원화의 머리로 확인하여 유지. 43 어깨 윗선만 새 맨팔 원화의 피부6texel로 등록.','runtime_verified':False,'native_packed':False})
