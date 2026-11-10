"""포스 아머 파츠와 기본형 공유 관계를 읽기 전용으로 조사한다."""
import json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import psx_arc,sha256
from scripts.project import load_project,inspect_references,validate_bin,write_json
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets
from src.psx_sprite_batch import canvas_from_parts
from scripts.extract_zero import save_image

PARENT='out/ver_buki_riko/shibuki_arrival_victory_style_20261026T235455012767Z'
EXTRACT='work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z'
OUT='work/ver_buki_riko/shibuki_art/fourth_armor_v1/analysis'

def entries(arc):return {int(e['type'],16):arc[e['offset']:e['offset']+e['size']] for e in psx_arc(arc)}

def main():
 from capstone import Cs,CS_ARCH_MIPS,CS_MODE_MIPS32,CS_MODE_LITTLE_ENDIAN
 out=ROOT/OUT;out.mkdir(exist_ok=False)
 cfg=json.loads((ROOT/'config/shibuki_x_us.json').read_text());project=load_project(ROOT,'ver_buki_riko');refs=inspect_references(ROOT,project)
 validate_bin(ROOT/project['source_bin'],cfg['source_sha256'])
 pm=json.loads((ROOT/PARENT/'manifest.json').read_text());validate_bin(ROOT/PARENT/'shibuki_riko.bin',pm['modified_bin']['sha256'])
 old=(ROOT/EXTRACT/'original.arc').read_bytes();current=(ROOT/PARENT/'modified.arc').read_bytes();exe=(ROOT/EXTRACT/'original.exe').read_bytes()
 if sha256(old)!=cfg['archive']['sha256'] or sha256(current)!=pm['modified_archive_sha256'] or sha256(exe)!=cfg['executable']['sha256']:raise ValueError('Unexpected input')
 es=entries(current);og=entries(old);g,c,p=es[2],es[3],es[9];bank=graphics_bank(g,0,allow_bank_aliases=True);rows=[]
 # The renderer requests composition banks 5..8 in call order leg,head,arm,body.
 mapping=[('head',1,5),('body',2,6),('arm',4,7),('leg',8,8)]
 for f in bank['frames']:
  n=f['index'];stream=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128);base=composition_frame(c,0,n);tiles={r['tile'] for r in base['parts']};parts={}
  for name,bit,bi in mapping:
   cp=composition_frame(c,bi,n);ats={r['tile'] for r in cp['parts']}
   parts[name]={'bit':bit,'composition_bank':bi,'part_count':len(cp['parts']),'tiles':sorted(ats),'base_shared_tiles':sorted(tiles&ats),'parts':cp['parts']}
  rows.append({'frame':n,'offset':f['offset'],'tile_count':f['tile_count'],'encoded_bytes':stream.end-f['offset'],'stream_capacity':f['limit']-f['offset'],'base_tiles':sorted(tiles),'armor':parts})
 # Keep exact US instructions as evidence; no decomp code copied into a patch.
 cs=Cs(CS_ARCH_MIPS,CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN);s,e=0x800257bc,0x80025cdc
 ins=list(cs.disasm(exe[s-0x80010000+2048:e-0x80010000+2048],s))
 (out/'US_armor_renderer.txt').write_text('\n'.join(f'{i.address:08X} {i.mnemonic} {i.op_str}' for i in ins),encoding='utf-8')
 expected={0x800257DC:'andi',0x80025824:'andi',0x80025948:'lw'}
 if any(next(i.mnemonic for i in ins if i.address==addr)!=name for addr,name in expected.items()):raise ValueError('Renderer signature differs')
 palettes=[list(struct.unpack_from('<16H',p,i*32)) for i in range(len(p)//32)]
 layers={};pictures=[]
 for label,gs,cs_,ps in [('original',og[2],og[3],og[9]),('accepted_base_with_original_armor',g,c,p)]:
  f=graphics_bank(gs,0,allow_bank_aliases=True)['frames'][0];raw=decode_stream(gs,f['offset'],f['limit'],f['tile_count']*128).data
  layer_images={}
  for bi in (0,5,6,7,8):
   layer=canvas_from_parts(raw,f['tile_count'],composition_frame(cs_,bi,0));words=list(struct.unpack_from('<16H',ps,0 if bi==0 else 32));im=save_image(layer.tobytes(),(160,160),words,out/f'{label}_bank{bi}.png').convert('RGBA');layer_images[bi]=im
  for mask in range(16):
   im=layer_images[0].copy()
   for bit,bi in ((8,8),(1,5),(4,7),(2,6)):
    if mask&bit:im.alpha_composite(layer_images[bi])
   im.save(out/f'{label}_mask{mask:02}.png')
   if mask in (0,1,2,4,8,15):pictures.append((f'{label} / {mask:02X}',im))
 sheet=Image.new('RGB',(6*240,2*280),'#253546');draw=ImageDraw.Draw(sheet)
 for i,(label,im) in enumerate(pictures):
  im=im.crop((40,40,120,120)).resize((240,240),Image.Resampling.NEAREST);x,y=i%6*240,i//6*280;sheet.paste(im,(x,y+35),im);draw.text((x+6,y+6),label,fill='white')
 sheet.save(out/'original_partial_armor_review.png')
 report={'task':'fourth_armor_shibuki','parent_build':PARENT,'parent_bin_sha256':pm['modified_bin']['sha256'],'parent_arc_sha256':sha256(current),'source_sha256':cfg['source_sha256'],'reference':next(r for r in refs if r['task_id']=='fourth_armor_shibuki') if isinstance(refs,list) else refs,'frames':rows,'palettes':palettes,'composition_bank_count':len(bank_offsets(c)),'renderer_US_range':[s,e],'renderer_call_order':[8,1,4,2],'armor_composition_banks':[5,6,7,8],'armor_clut_default':'0x7843','armor_clut_arm_type2':'0x7844','base_body_is_drawn_separately':True,'new_art_applied':False,'runtime_verified':False,'partial_composites_are_static_not_runtime':True}
 write_json(out/'analysis.json',report)
 print(json.dumps({'output':str(out),'frames':len(rows),'palette_rows':len(palettes),'base_shared_armor_refs':sum(any(v['base_shared_tiles'] for v in r['armor'].values()) for r in rows)}))

if __name__=='__main__':main()
