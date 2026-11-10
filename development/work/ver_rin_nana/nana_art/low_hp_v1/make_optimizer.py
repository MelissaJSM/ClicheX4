from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
s=(ROOT/'work/ver_buki_riko/shibuki_art/low_hp_v1/optimize02.py').read_text('utf8').replace('import json,sys,random,math,itertools','import argparse,json,sys,random,math,itertools').replace('ROOT=Path(__file__).resolve().parents[4]','ROOT=Path(__file__).resolve().parents[1]')
s=s.replace('from src.psx_paired_layout import pack_variant_pair','from src.psx_paired_layout import pack_variant_pair\nfrom src.psx_tile_layout import pack_rectangles')
old="d=Path(__file__).parent;a=d/'production02';parent=ROOT/'out/ver_buki_riko/shibuki_ladder_20261026T150541813461Z';"
new="p=argparse.ArgumentParser();p.add_argument('--art',type=Path,required=True);p.add_argument('--parent',type=Path,required=True);args=p.parse_args();a=args.art.resolve();d=a.parent;parent=args.parent.resolve()\nif not a.is_relative_to(ROOT/'work/ver_rin_nana/nana_art/low_hp_v1') or not parent.is_relative_to(ROOT/'out/ver_rin_nana'):raise ValueError('Isolated Nana paths required')\n"
assert old in s;s=s.replace(old,new)
start=s.index(' def final_cost(packed):');end=s.index(' def encode(r):',start)
s=s[:start]+''' opened=np.array(Image.open(a/f'frame_{n+1:03d}.png'));yy,xx=np.nonzero(opened!=target);left,top=int(xx.min())-2,int(yy.min())-2;overlay=np.zeros_like(target);overlay[yy,xx]=opened[yy,xx]
 def final_cost(packed):
  packed=pack_rectangles(packed,desc['tile_count'],overlay.tobytes(),(96,80),[[left,top]],[7],{7});return encoded_cost(packed)
'''+s[end:]
p=ROOT/'scripts/optimize_nana_low_hp.py';assert not p.exists();p.write_text(s,'utf8')
