"""재삽입한 게임 자원에서 발끝까지 포함한 비교 시트를 만든다."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from PIL import Image,ImageDraw
from scripts.project import digest
from scripts.prepare_nana_fourth_pilot import render,require,write
B=ROOT/'out/ver_rin_nana/nana_fourth_vehicle_20261030T120015393777Z'
require(digest(B/'rin_nana.bin')=='5618ee1ab54f16bfee9b0a1b4d3472be3508da4babd8dce2ac7676f7c66d0e6d','Wrong build')
out=B/'vehicle_comparison_4x.png';require(not out.exists(),'Fresh review output required');arc=(B/'modified.arc').read_bytes();board=Image.new('RGB',(320,264),'#242934');draw=ImageDraw.Draw(board)
for i,n in enumerate((0,37,94,162,166,170,174,184,193,195,196,199)):
 im=render(arc,n,True)[0];bb=im.getbbox();require(40<=bb[0] and 32<=bb[1] and bb[2]<=120 and bb[3]<=112,'Review crop clips sprite');tile=im.crop((40,32,120,112));board.paste(tile,(i%4*80,i//4*88+8),tile);draw.text((i%4*80+1,i//4*88),str(n),fill='white')
board.resize((1280,1056),Image.Resampling.NEAREST).save(out)
tools=B/'vehicle_source_tools.json';rows=json.loads(tools.read_text('utf8'));rows.append({'path':Path(__file__).relative_to(ROOT).as_posix(),'sha256':digest(Path(__file__))});write(tools,rows);print(str(out))
