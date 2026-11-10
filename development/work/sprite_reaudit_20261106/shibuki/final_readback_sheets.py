"""동결 자원을 다시 읽어 최종 전후/변경 픽셀 시트를 만든다."""
from pathlib import Path
import sys,json,hashlib
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(H))
import numpy as np
from PIL import Image
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page
from leg_material_expanded import SRC,REFS
def main():
 folder=H/'prepared_v4';data,_=read_disc(SRC,('PL02_U.ARC',));before=Archive(data['PL02_U.ARC']);raw=(folder/'PL02_U.ARC').read_bytes()
 proposal=json.loads((folder/'proposal.json').read_text('utf8'))
 assert hashlib.sha256(raw).hexdigest()==proposal['files']['PL02_U.ARC']['after']
 after=Archive(raw);sheets=[]
 for group,refs in [('run',range(11,17)),('air',range(33,55)),('wall',range(55,67)),('dash',range(67,85))]:
  for mask,label in ((0,'after'),(15,'before')):
   for start in range(0,len(refs),12):
    selected=list(refs)[start:start+12];items=[]
    for n in selected:
     a=before.composite(n,mask)[0];b=after.composite(n,mask)[0]
     items.extend([(f'{n} old',a),(f'{n} restored',b)])
    name=f'{group}_{label}_{start//12}.png';row=page(items,before.composite(0,mask)[0],folder/name,cols=4,scale=2)
    sheets.append({'refs':selected,'form':label,**row})
 (folder/'readback_sheets.json').write_text(json.dumps({'source_arc_sha256':hashlib.sha256(raw).hexdigest(),'sheets':sheets},ensure_ascii=False,indent=2)+'\n','utf8')
 print(json.dumps({'sheets':len(sheets),'sha256':hashlib.sha256(raw).hexdigest()}))
if __name__=='__main__':main()
