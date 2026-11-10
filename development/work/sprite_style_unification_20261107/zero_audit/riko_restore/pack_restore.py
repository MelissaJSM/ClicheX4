"""현재 PL01의 최상층 가시 texel에만 원화 중간명암을 재등록한다."""
from pathlib import Path
from collections import defaultdict
import json,hashlib,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT));D=Path(__file__).parent
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_frame_edit import frame_coverage
from src.psx_compress import encode_stream
from src.psx_bank_repack import repack_graphics_bank
from scripts.overhaul_sprites_costume_pack import repack_variable
from scripts.ultimate_costume_swap import replace_entry
from prepare_restore import preview,SOURCE,EXPECTED,TARGET
def sha(b):return hashlib.sha256(b).hexdigest()
def need(v,m):
 if not v:raise ValueError(m)
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n','utf8')
def build(arc,targets,proof):
 need(sha(arc)=='949f1066ed1471f8ad64a275f82020ab9109dd525a1d172628c0b7a3cd8e6178','Parent ARC mismatch')
 need(set(targets)==set(TARGET),'Unexpected frame targets')
 g,c=entry(arc,2),entry(arc,3);bank=graphics_bank(g,0);groups=defaultdict(list)
 for f in bank['frames']:groups[f['offset']].append(f['index'])
 replacements={};packing=[]
 for off,refs in groups.items():
  chosen=[n for n in refs if n in targets]
  if not chosen:continue
  f=bank['frames'][refs[0]];raw=decode_stream(g,off,f['limit'],f['tile_count']*128).data;writes={}
  for n in chosen:
   before=render(arc,0,0,n)[0];want=targets[n];changed=before!=want
   need(want.shape==(384,384),'Canvas differs');need(np.all(before[changed]==15)and np.all(want[changed]==12),'Unexpected colors/alpha')
   documented=set(tuple(v)for v in proof[n]['world_pixels']);actual={(int(x-160),int(y-160))for y,x in np.argwhere(changed)};need(documented==actual,'Restoration mask changed')
   cp=composition_frame(c,0,n);coverage,size,bb=frame_coverage(raw,f['tile_count'],cp)
   for wx,wy in actual:
    local=(wy-bb[1])*size[0]+wx-bb[0];sources=coverage[local];visible=[s for s in sources if (raw[s[0]]>>s[1])&15]
    need(bool(visible),'Changed pixel has no visible source');s=visible[-1];need(((raw[s[0]]>>s[1])&15)==15,'Visible source differs')
    need(s not in writes or writes[s]==12,'Shared texel conflict');writes[s]=12
  new=bytearray(raw)
  for (offset,shift),value in writes.items():new[offset]=(new[offset]&~(15<<shift))|(value<<shift)
  new=bytes(new);need(all((a==0)==(b==0)for a,b in zip(np.frombuffer(raw,np.uint8)&15,np.frombuffer(new,np.uint8)&15)),'Low-nibble alpha changed');need(all((a==0)==(b==0)for a,b in zip(np.frombuffer(raw,np.uint8)>>4,np.frombuffer(new,np.uint8)>>4)),'High-nibble alpha changed')
  code=encode_stream(new)
  for n in refs:replacements[n]=new if n in chosen else raw
  packing.append({'refs':refs,'edited_refs':chosen,'native_texels_changed':len(writes),'tile_count':f['tile_count'],'compressed_size':len(code)})
 ng,layout=repack_variable(g,replacements,{n:bank['frames'][n]['tile_count']for n in replacements});out=replace_entry(arc,2,ng);checks=[]
 for b in (0,1):
  ob=graphics_bank(g,b);nb=graphics_bank(ng,b)
  for a,z in zip(ob['frames'],nb['frames']):
   n=a['index'];need(a['tile_count']==z['tile_count']<=32,'Tile buffer changed');old=decode_stream(g,a['offset'],a['limit'],a['tile_count']*128).data;new=decode_stream(ng,z['offset'],z['limit'],z['tile_count']*128).data
   if b==1 and 42<=n<=49:need(old==new,'Partial-VRAM data changed');continue
   before=render(arc,b,0 if b==0 else 5,n)[0];after=render(out,b,0 if b==0 else 5,n)[0];want=targets[n]if b==0 and n in targets else before
   need(np.array_equal(after,want),f'Final target mismatch: {b}/{n}')
   if not(b==0 and n in targets):need(old==new,f'Non-target raw changed:{b}/{n}')
   checks.append({'bank':b,'frame':n,'changed_pixels':int(np.count_nonzero(after!=before))})
 need(replace_entry(out,2,g)==arc,'Other entries changed')
 return out,{'references_total':444,'displayed_checked':len(checks),'unchanged_displayed':sum(v['changed_pixels']==0 for v in checks),'target9_exact':True,'partial8_raw_preserved':True,'parts_palette_audio_static_timing_exact':True,'native_alpha_all_preserved':True,'max_tiles':32,'packing':packing,'bank_layout':layout,'frames':checks}
def main():
 arc=(D/'baseline_PL01_U.ARC').read_bytes();data=np.load(D/'targets.npz');targets={int(n):data[n]for n in data.files};i=json.loads((D/'inspection.json').read_text('utf8'));proof={r['frame']:r for r in i['proof']}
 changed,report=build(arc,targets,proof);out=D/'prepared_v1';out.mkdir(exist_ok=True)
 (out/'PL01_U.ARC').write_bytes(changed);preview(arc,{n:render(changed,0,0,n)[0]for n in TARGET},out/'readback.png')
 # Reproducibility and narrow input rejection, no mutations outside this directory.
 again,_=build(arc,targets,proof);need(again==changed,'Non-reproducible')
 rejected=[]
 for name in ('wrong_parent','alpha_change','wrong_color','wrong_mask'):
  a=arc;t={n:v.copy()for n,v in targets.items()}
  if name=='wrong_parent':a=bytes([a[0]^1])+a[1:]
  else:
   x,y=proof[111]['world_pixels'][0]
   if name=='alpha_change':t[111][160+y,160+x]=0
   if name=='wrong_color':t[111][160+y,160+x]=9
   if name=='wrong_mask':t[111][160+y,160+x]=15
  try:build(a,t,proof)
  except ValueError as e:rejected.append({'case':name,'reason':str(e)})
  else:raise ValueError('Accepted invalid '+name)
 proposal={'project':'ver_buki_riko','source_bin':str(SOURCE.relative_to(ROOT)),'source_sha256':EXPECTED,'source_arc_sha256':sha(arc),'resource':str((out/'PL01_U.ARC').relative_to(ROOT)),'after_sha256':sha(changed),'scope':'리코 지상3타의 기존 원화 회청색 중간명암 재등록. 새 원화/머리 교체 없음.','restored_display_pixels':sum(r['restored_pixels']for r in i['proof']),'frames':list(TARGET),'verification':report,'reproducible':True,'rejection_tests':rejected,'game_bin_written':False,'runtime_verified':False,'visual_acceptance_required':True,'art_source':i}
 dump(out/'proposal.json',proposal);print(json.dumps({'ARC':sha(changed),'rejections':len(rejected),'native_texels':sum(r['native_texels_changed']for r in report['packing']),'displayed':report['displayed_checked']}))
if __name__=='__main__':main()
