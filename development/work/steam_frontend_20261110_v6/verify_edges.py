import importlib.util,json,sys,hashlib
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.steam_frontend_texture import decode,replace_region
from src.steam_arc import SteamArc
from scripts.build_steam_frontend import banner,STEAM
D=Path(__file__).parent;OUT=ROOT/'out/steam_frontend_20261110_v6'
spec=importlib.util.spec_from_file_location('previous_frontend_texture',D/'steam_frontend_texture_before.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
a=SteamArc((STEAM/'nativeDX10/RXC1/romPC/MenuGUIRXCRes.arc').read_bytes());e=next(e for e in a.entries if e.name.endswith('con_img_rxc1_ID_HQ'))
im=banner();rect=(0,1348,1344,1800);px=np.asarray(im);clear=px[:,:,3]==0
previous=old.decode(old.replace_region(e.payload,rect,im)).crop(rect)
current=decode(replace_region(e.payload,rect,im)).crop(rect);p=np.asarray(previous);c=np.asarray(current)
assert np.all(c[:,:,3][clear]==0)
report={'passed':True,'same_art_before_after_codec':True,'source_fully_transparent_pixels':int(clear.sum()),'previous_false_opaque_gt32':int(np.count_nonzero(p[:,:,3][clear]>32)),'previous_max_alpha_on_clear':int(p[:,:,3][clear].max()),'corrected_nonzero_alpha_on_clear':int(np.count_nonzero(c[:,:,3][clear])),'corrected_max_alpha_on_clear':int(c[:,:,3][clear].max())}
board=Image.new('RGB',(1260,820),'#236baf');draw=ImageDraw.Draw(board)
for y,title,pic in [(0,'OLD ENCODER / SAME NEW ART',previous),(410,'FIXED ENCODER / SAME NEW ART',current)]:
    crop=pic.crop((20,10,650,200)).resize((1260,380),Image.Resampling.NEAREST);board.paste(crop,(0,y+28),crop);draw.text((10,y+5),title,fill='white')
board.save(OUT/'edge_comparison.png');(D/'edge_verification.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
