"""Refined rear four masters -> exact13 whole-body aliases; Rin62 parent."""
from pathlib import Path
import sys,json,hashlib,shutil
import numpy as np
D=Path(__file__).parent;sys.path.insert(0,str(D))
import pack_rin_priority_body as core
core.P=D/'rin_extension/prepared_third_saber_v1/PL01_U.ARC';core.SHA='11d4c88a17983dd3e106d13af3938075803186c59045b0b372b0f813b3aa09ae'
core.ART=D/'rin_extension/rear_registered_grips_v1';core.OUT=D/'rin_extension/prepared_rear_continuation_v1'
core.EXPECTED_SHA={'b0_178':'82d103d469676b701c187b7f1bc68a2180918f76bb9e7a75af720b028ef277ff','b0_182':'cd76069916e1cb1fc6e8673d3fcc9a34ffc4b8e6b49405178f32cf3f1273fa70','b0_186':'5c2df1fc2324e36abd8cddac48ea6bee43f7ddcfdb06105095441e021c7e9b88','b0_190':'d18ec0f788307bb1898bad6d974551cf0f007a17a1d3e7145a4a77f799392a9a'}
core.MAP={(0,n):(f'b0_{master:03}',flip)for master,refs in [(178,[(178,False),(179,False),(180,True),(181,True)]),(182,[(182,False),(183,False),(184,True),(185,True)]),(186,[(186,False),(188,False),(187,True),(189,True)]),(190,[(190,False)])]for n,flip in refs}
CACHE=D/'rin_extension/rear_pack_cache_v2'
ordinary_pack=core.pack
original_repack=core.engine.native.packer.repack_raw

def pack(c,b,n,raw,count,target):
 if (b,n) not in core.MAP:return ordinary_pack(c,b,n,raw,count,target)
 key,flip=core.MAP[b,n];master=int(key[3:])
 canonical=core.mirror(target) if flip else target
 digest=hashlib.sha256(core.SHA.encode()+raw+core.engine.records(c,b*5,master)+canonical.tobytes()+b'rear-canonical-v2').hexdigest()
 file=CACHE/f'b{b}_{master:03}_{digest}.json'
 if file.exists():
  data=json.loads(file.read_text('utf8'));nr=bytes.fromhex(data['raw']);rec=bytes.fromhex(data['records']);method=data['method']
 else:
  nr,rec,method=ordinary_pack(c,b,master,raw,count,canonical)
  CACHE.mkdir(exist_ok=True);file.write_text(json.dumps({'raw':nr.hex(),'records':rec.hex(),'method':method},indent=2)+'\n','utf8')
 core.engine.native.need(len(rec)==len(core.engine.records(c,b*5,n)),'Canonical alias part count differs')
 if flip:
  rr=bytearray(rec)
  for j in range(0,len(rr),4):
   x=rr[j+2] if rr[j+2]<128 else rr[j+2]-256
   rr[j]^=0x40;rr[j+2]=(-x-16)&255
  rec=bytes(rr)
 return nr,rec,{'type':'canonical_exact_reflection' if flip else 'canonical_exact_alias','master':master,'x_reflection':'319-x' if flip else None,'canonical_method':method,'hidden_global_cleanup':False}

def repack(g,b,replacements):
 from src.psx_compress import encode_stream
 native=core.engine.native;bank=native.graphics_bank(g,b);groups={};rows=[]
 for f in bank['frames']:groups.setdefault(f['offset'],[]).append(f)
 for off,fs in groups.items():
  if not any(f['index'] in replacements for f in fs):continue
  f=fs[0];d=native.decode_stream(g,off,f['limit'],f['tile_count']*128);variants={}
  for f in fs:
   raw=replacements.get(f['index'],d.data);h=native.sha(raw)
   if h not in variants:variants[h]={'refs':[],'compressed_bytes':len(encode_stream(raw)) if raw!=d.data else d.end-off}
   variants[h]['refs'].append(f['index'])
  rows.append({'old_refs':[f['index']for f in fs],'old_compressed_bytes':d.end-off,'variants':list(variants.values())})
 CACHE.mkdir(exist_ok=True);(CACHE/f'packing_bank{b}.json').write_text(json.dumps(rows,indent=2)+'\n','utf8')
 return original_repack(g,b,replacements)

core.pack=pack
core.engine.native.packer.repack_raw=repack
def main():
 assert not core.OUT.exists(),'Choose a new candidate directory'
 for folder,h in[('rear_continuation01','67f1a95bd572aaef9f0417828e77bb0e916c5ab44cdbd6e9891c8554d1b141dd'),('rear_leg_fix_186','b079b9f7220371ef15d0bc6c3473396df73f3d710fc1d8cd8b81a5a581a13089'),('rear_leg_fix_190','e83cd48ddd3facb5a6aa931225724954dabc4c311bcc1763b16c5562107bb195')]:assert hashlib.sha256((D/'rin_extension'/folder/'generated.png').read_bytes()).hexdigest()==h
 core.main();p=core.OUT/'proposal.json';j=json.loads(p.read_text('utf8'))
 j['cumulative_main_refs']=75;j['previous_frozen_art_refs']=62;j['verification'].pop('previous42_exact',None);j['verification']['previous62_exact']=True
 j.update({'static_burst24_sync_required':False,'static_burst23_sync_required':False,'victory5_included':True,'user_accepted':False,'root_review_only':True,'root_review_pending':True,'registration':str((core.ART/'registration.json').relative_to(core.ROOT)),'native_master_sha256':core.EXPECTED_SHA,'scope':'후면 사다리 새 원화4키와 국소 다리보완2키를 정확 동일/반전13참조에 등록. 기존62·비대상191·부분VRAM8·음향·시간표 보존.'})
 recipe=json.loads((core.P.parent/'static_effects.json').read_text('utf8'));recipe['parts_sha256']=core.engine.native.sha(core.engine.native.entry((core.OUT/'PL01_U.ARC').read_bytes(),3))
 for f in('palette.bin','effect_23.png','effect_24.png'):shutil.copyfile(core.P.parent/f,core.OUT/f)
 rp=core.OUT/'static_effects.json';rp.write_text(json.dumps(recipe,ensure_ascii=False,indent=2)+'\n','utf8');j['static_body_patch']={'recipe':str(rp.relative_to(core.ROOT)),'sha256':hashlib.sha256(rp.read_bytes()).hexdigest()};j['static_body_images_and_texture_unchanged_from62']=True
 p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'candidate':str(core.OUT),'sha256':j['after_sha256'],'count':75}))
if __name__=='__main__':main()
