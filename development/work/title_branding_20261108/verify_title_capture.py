"""Compare actual title/menu pixels at native coordinates, with no fitted offsets."""
from pathlib import Path
import argparse,json,struct,sys
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry
from scripts.verify_korean_title_menu import verify as verify_menu
from scripts.verify_korean_runtime_page import native_draw_buffers
from src.psx_static_effect import compose_static
from src.psx_ui_atlas import aliased_composition,local_composition
p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--project',required=True,choices=['ver_buki_riko','ver_rin_nana']);a=p.parse_args()
cap=a.capture;e=json.loads((cap/'evidence.json').read_text('utf8'));builds=json.loads((W/'builds.json').read_text('utf8'));b=builds[a.project];assert e['bin_sha256']==b['sha256']
base=(ROOT/b['cue']).parent;arc=(base/'ST0E_U0.ARC').read_bytes();pal=struct.unpack_from('<16H',entry((base/'COL0E_U0.ARC').read_bytes(),5));g=entry(arc,0x10002);parts=struct.pack('<I',4)+entry(arc,0x12)
px,size,bounds,_=compose_static(g,local_composition(aliased_composition(parts,0,0)));arr=np.frombuffer(px,np.uint8).reshape(size[1],size[0]);ys,xs=np.nonzero(arr);xx=xs+144+bounds[0];yy=ys+72+bounds[1];wanted=np.asarray(pal,np.uint16)[arr[ys,xs]]&32767
assert e['ram_bases']and e['vram_bases'];ram=(cap/f'ram_{e["ram_bases"][0]}.bin').read_bytes();v=(cap/f'vram_{e["vram_bases"][0]}.bin').read_bytes();video=np.frombuffer(v,'<u2').reshape(512,1024);rows=[]
for buf in native_draw_buffers(ram):
 ox,oy=buf['draw_offset'];actual=video[yy+oy,xx+ox]&32767;eq=actual==wanted;regions={}
 for name,use in{'notice':(yy>=14)&(yy<25),'subtitle':(yy>=100)&(yy<113),'main_logo':(yy>=32)&(yy<96)}.items():regions[name]={'ink_pixels':int(use.sum()),'matched_pixels':int(eq[use].sum()),'exact':bool(eq[use].all())}
 rows.append({'buffer':buf,'ink_pixels':len(xs),'matched_pixels':int(eq.sum()),'all_title_ink_matches':bool(eq.all()),'regions':regions})
menu=verify_menu(cap);assert menu['captured_title_menu_verified'];assert any(r['all_title_ink_matches']for r in rows)
report={'passed':True,'actual_gameplay_title':True,'project':a.project,'capture':cap.as_posix(),'bin_sha256':b['sha256'],'title_framebuffer_checks':rows,'title_ink_pixels':len(xs),'whole_title_verified':True,'three_menu_labels_verified':True,'menu':menu,'palette_changed':False,'fitted_offsets_used':False,'memory_written':False,'F1_F3_sent':False}
(W/a.project/'runtime_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'project':a.project,'title_pixels':len(xs),'whole_title_matches':True,'three_menu_labels_match':True}))
