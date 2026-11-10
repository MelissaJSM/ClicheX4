"""Export the verified current album without redrawing, resizing, or altering source assets."""
from pathlib import Path
import base64,hashlib,io,json,re,shutil,sys
from PIL import Image
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.build_sprite_style_album import extracted
source=ROOT/'out/sprite_style_unification_20261107/review_v38';dest=ROOT/'out/sprite_style_unification_20261107/final'
dest.mkdir(exist_ok=True);assert not (dest/'SPRITE_INDEX.json').exists()
sha=lambda b:hashlib.sha256(b).hexdigest()
manifest=json.loads((source/'manifest.json').read_text('utf8'));checks=json.loads((source/'browser_checks.json').read_text('utf8'))
html=(source/'ALL_SPRITES_CURRENT.html').read_bytes();assert sha(html)==manifest['sha256']==checks['html_sha256'] and checks['passed']
text=html.decode('utf8');characters=extracted(text,'const DATA=');assets=extracted(text,'const ASSETS=')
if (dest/'ALL_SPRITES_CURRENT.html').exists():assert (dest/'ALL_SPRITES_CURRENT.html').read_bytes()==html
else:(dest/'ALL_SPRITES_CURRENT.html').write_bytes(html)
records=[];parts=[];missing={};counts={}
def put(character,form,ident,key,metadata):
 safe=re.sub('[^A-Za-z0-9_.-]','_',ident);rel=Path('sprites')/character/form/(safe+'.png');p=dest/rel
 data=base64.b64decode(assets[key].split(',',1)[1],validate=True)
 im=Image.open(io.BytesIO(data));im.load();assert im.format=='PNG';p.parent.mkdir(parents=True,exist_ok=True)
 if not p.exists():p.write_bytes(data)
 assert p.read_bytes()==data
 return {'path':rel.as_posix(),'sha256':sha(data),'size':list(im.size),'asset_key':key,**metadata}
for c in characters:
 start=len(records);missing[c['id']]=c['missing']
 for f in c['frames']:
  if f['form']=='partial_fourth':continue
  key=f.get('revised_path',f['path']);meta={k:v for k,v in f.items()if k not in('path','revised_path')}
  records.append(put(c['id'],f['form'],f['id'],key,meta))
 for f in c['partial']:
  for layer,key in f['layers'].items():parts.append(put(c['id'],'partial_fourth_layers/'+layer,f['id'],key,{'id':f['id'],'ref':f['ref'],'layer':layer,'group':f['group']}))
 counts[c['id']]={'assembled_png':len(records)-start,'partial_layers':sum(p['path'].startswith('sprites/'+c['id']+'/')for p in parts),'forms':c['forms']}
assert len(records)==4510 and len(parts)==2736
result={'status':'implemented_and_verified_with_documented_runtime_limits','source_album':source.relative_to(ROOT).as_posix(),'album_sha256':sha(html),'builds':manifest['sources'],'counts':counts,'assembled_count':len(records),'partial_layer_count':len(parts),'modified_display_count':len(manifest['changes']),'image_bytes_unchanged':True,'original_dimensions_preserved':True,'records':records,'partial_layers':parts,'unreconstructed_native_references':missing,'user_accepted':False,'all_gameplay_combinations_verified':False}
(dest/'SPRITE_INDEX.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
shutil.copyfile(source/'manifest.json',dest/'album_manifest.json');shutil.copyfile(source/'browser_checks.json',dest/'album_browser_checks.json')
print(json.dumps({'folder':dest.relative_to(ROOT).as_posix(),'assembled_png':len(records),'part_png':len(parts),'album_sha256':sha(html),'index_sha256':sha((dest/'SPRITE_INDEX.json').read_bytes())}))
