"""과거 색 병합 전 자료를 복구 후보로 복사/정확 재현한다. 게임·아트 원본은 불변."""
import importlib.util
import json
from pathlib import Path
import struct
import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('cov',ROOT/'scripts/audit_sprite_consistency_coverage.py')
cov=importlib.util.module_from_spec(spec);spec.loader.exec_module(cov)
from scripts.prepare_shibuki_run_cycle import quantize
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices

OUT=Path(__file__).resolve().parent/'shibuki_special'
OLD=ROOT/'work/ver_buki_riko/shibuki_art/remaining_v1'
OUT.mkdir(exist_ok=True)
source=ROOT/'out/ver_buki_riko/ultimate_costumes_swapped_20261105_v1/shibuki_riko.bin'
assert cov.file_sha(source)==cov.EXPECTED['ver_buki_riko'][1]
assets,_=cov.read_assets(source,['PL00_U.ARC']);arc=assets['PL00_U.ARC']
g,c,p=[cov.unique_entry(arc,t)for t in(2,3,9)]
words=struct.unpack_from('<16H',p)
assert list(words)==json.loads((OLD/'production14/art.json').read_text())['palette_words']
(OUT/'palette.bin').write_bytes(p[:32])
rgb=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in words],np.int32)
bank=graphics_bank(g,0,allow_bank_aliases=True)

def native(n):
 f=bank['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
 comp=composition_frame(c,0,n);assert all(q['clut']==0 for q in comp['parts'])
 pix,size,box,_=compose_indices(raw,f['tile_count'],comp)
 arr=np.zeros((160,160),np.uint8);arr[80+box[1]:80+box[3],80+box[0]:80+box[2]]=np.frombuffer(pix,np.uint8).reshape(size[1],size[0]);return arr

def old(n,stage):return np.array(Image.open(OLD/f'production{stage:02}/frame_{n:03}.png'))
def save(arr,path):save_image(arr.tobytes(),(160,160),words,path)
def source_info(path):return {'path':path.relative_to(ROOT).as_posix(),'sha256':cov.file_sha(path)}

current={n:native(n)for n in[0,85,95,96,97,98,99,100,101,102,103,104,231,232,233,234,235,236]}
proof={}
for n in current:
 save(current[n],OUT/f'current_{n:03}.png')
 if n in[95,96,100,101,102,103,104,231,232,233,234,235,236]:
  assert np.array_equal(current[n],old(n,14)),f'Historical final differs {n}'
  proof[str(n)]={'production14_indices_exact':True,'source':source_info(OLD/f'production14/frame_{n:03}.png')}

normalization=next(q for q in json.loads((OLD/'production14/last_three_normalization.json').read_text())if q['frame']==103)
generated=Image.open(OLD/'last_three_generated.png').convert('RGBA').crop(normalization['source_box']).crop(normalization['crop'])
# Reuse the original area-weighted palette quantizer and stored registration.
# This is recovery from an existing local source, not new image generation.
small=quantize(generated,normalization['size'],rgb,128)
full103=np.zeros((160,160),np.uint8);x,y=normalization['offset'];full103[y:y+small.shape[0],x:x+small.shape[1]]=small
ops=json.loads((OLD/'production14/cluster_cleanup_103.json').read_text())['operations']
pre103=full103.copy()
for x,y,before,after in ops:
 assert pre103[y,x]==before
 pre103[y,x]=after
mapped=pre103.copy();protected=np.isin(pre103,[7,12,13,15])
tone103=json.loads((OLD/'production14/tone_103.json').read_text())
for before,after in tone103['mapping'].items():mapped[(pre103==int(before))&~protected]=after
assert np.array_equal(mapped,current[103])
assert np.array_equal(full103!=0,current[103]!=0)

minimal={102:old(102,11),103:pre103,104:old(104,11)}
full={101:old(101,6),102:old(102,4),103:full103,104:old(104,6),231:old(231,6),232:old(232,6)}
for n in[102,104]:
 before=minimal[n];masked=np.isin(before,[7,12,13]);pad=np.pad(masked,1)
 protected=masked|pad[:-2,1:-1]|pad[2:,1:-1]|pad[1:-1,:-2]|pad[1:-1,2:]|(before==15)
 mapped=before.copy();tone=json.loads((OLD/f'production14/tone_{n:03}.json').read_text())
 for v,w in tone['mapping'].items():mapped[(before==int(v))&~protected]=w
 assert np.array_equal(mapped,current[n]),f'Forward tone differs {n}'

rows=[]
for kind,choices in [('minimal_pre_tone',minimal),('full_detail',full)]:
 for n,arr in choices.items():
  assert np.array_equal(arr!=0,current[n]!=0)
  path=OUT/f'{kind}_{n:03}.png';save(arr,path)
  changes=arr!=current[n];yy,xx=np.where(changes)
  rows.append({'frame':n,'kind':kind,'path':path.relative_to(ROOT).as_posix(),'png_sha256':cov.file_sha(path),
    'indices_sha256':cov.sha(arr.tobytes()),'changed_pixels':int(changes.sum()),'alpha_and_world_coordinates_exact':True,
    'changed_bbox_world':[int(xx.min()-80),int(yy.min()-80),int(xx.max()+1-80),int(yy.max()+1-80)],
    'source':source_info(OLD/'last_three_generated.png') if n==103 else source_info(OLD/f'production{(11 if kind=="minimal_pre_tone" else 4 if n==102 else 6):02}/frame_{n:03}.png'),
    'canvas_size':[160,160],'origin':[80,80],'palette_sha256':cov.sha(p[:32]),
    'not_repacked_or_game_applied':True})

def rgba(arr):
 colors=np.array([[*r,0 if i==0 else 255]for i,r in enumerate(rgb)],np.uint8)
 return Image.fromarray(colors[arr])

board=Image.new('RGB',(4*256,6*310),(29,34,42));dr=ImageDraw.Draw(board)
for ri,n in enumerate([101,102,103,104,231,232]):
 images=[('IDLE 0',current[0]),(f'CURRENT {n}',current[n]),('PRE TONE'if n in minimal else 'NO TONE CANDIDATE',minimal.get(n,current[n])),('PRE CLEANUP DETAIL',full[n])]
 for col,(label,arr)in enumerate(images):
  im=rgba(arr).crop((48,38,112,110)).resize((256,288),Image.Resampling.NEAREST)
  board.paste(im,(col*256,ri*310+20),im);dr.text((col*256+5,ri*310+3),label,fill='white')
board.save(OUT/'current_pre_tone_detail_4x.png')
metadata={'source_bin':source_info(source),'archive_sha256':cov.sha(arc),'current_equals_historical':proof,
 'palette':[{'index':i,'word':hex(w),'rgb5':[(w>>s)&31 for s in(0,5,10)],'rgb8':rgb[i].tolist()}for i,w in enumerate(words)],
 'palette_meanings_confirmed_by_render':{'1':'dark red clothing shadow','5':'pale lavender hair','7':'gold eye','9':'near-white fabric/highlight','12':'skin shadow','13':'light skin','14':'mid lavender hair shadow','15':'dark purple outline'},
 'candidates':rows,'frame103_reconstruction':{'source':source_info(OLD/'last_three_generated.png'),'registration':normalization,
  'quantizer':'scripts/prepare_shibuki_run_cycle.py::quantize(edge_threshold=128)','replayed_cleanup_operations':len(ops),
  'every_operation_input_matched':True,'forward_cleanup_then_tone_exactly_equals_current':True,'original_opaque_pixels':int((full103>0).sum())},
 'tone_records':{str(n):json.loads((OLD/f'production14/tone_{n:03}.json').read_text())for n in[102,103,104]},
 'limitations':['Static local recovery candidates only; no new generated artwork or game changes.',
  'Same silhouette means these candidates cannot fix large face or incorrect pose mechanics.',
  'Body base CLUT0 only; gameplay flash/effects need separate runtime inspection.']}
cov.write(OUT/'recovery_manifest.json',metadata)
print(json.dumps({'output':OUT.relative_to(ROOT).as_posix(),'candidates':len(rows),'forward_103_exact':True,'all_alpha_exact':True}))
