import sys,json,gzip
from pathlib import Path
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R))
from scripts.prepare_nana_life_revision import PARENT,PARENT_SHA,entry,require
from scripts.project import digest
from src.psx_ui_atlas import tile_pixels
D=R/'work/ver_rin_nana/checkpoints/before_nana_life_face_20261030';source=D/'final_progress';s=gzip.decompress(source.read_bytes());vram=2569183
ptr=json.loads((R/'projects/ver_rin_nana/current_build.json').read_text('utf8'));B=R/ptr['build'];require(digest(B/'rin_nana.bin')==ptr['sha256']and digest(PARENT/'rin_nana.bin')==PARENT_SHA,'BIN binding differs');require(len(s)==4254418,'Unexpected state length')
probe=json.loads((D/'tile_probe.json').read_text('utf8'));require(len(probe['common_page2_bases'])==1,'Atlas location ambiguous');base=probe['common_page2_bases'][0];old=entry((PARENT/'modified.arc').read_bytes(),0x10206);new=entry((B/'modified.arc').read_bytes(),0x10206)
changed=[t for t in range(len(old)//128)if tile_pixels(old,t)!=tile_pixels(new,t)];require(changed==[657,658,659,660,662,663,665,667,669,670,672,673,675,676],'Unexpected face scope');dst=bytearray(s);allowed=set();reports=[]
for t in changed:
 require(t//256==2,'Unexpected page')
 for y in range(16):
  p=((t//16)*16+y)*128+(t%16)*8;pos=base+((t//16%16)*16+y)*2048+(t%16)*8;require(vram<=pos<pos+8<=vram+1048576 and s[pos:pos+8]==old[p:p+8],'Old face tile differs from checkpoint');dst[pos:pos+8]=new[p:p+8];allowed.update(range(pos,pos+8))
 reports.append(t)
require(all(a==b or i in allowed for i,(a,b)in enumerate(zip(s,dst))),'Non-face state changed')
out=D/'refreshed_final_face_v2';out.mkdir(exist_ok=False);target=out/'SLUS_005.61.000';target.write_bytes(gzip.compress(bytes(dst),mtime=0));record={'source_sha256':digest(source),'output_sha256':digest(target),'build':ptr['build'],'build_sha256':ptr['sha256'],'changed_tiles':reports,'changed_bytes':sum(a!=b for a,b in zip(s,dst)),'vram_page2_base':base,'all_other_state_bytes_exact':True,'full_static_texture_present_in_ram':False,'kind':'bounded VRAM-only checkpoint refresh; fresh disc pickup reload not yet tested'};(out/'refresh.json').write_text(json.dumps(record,indent=2)+'\n','utf8');print(record)
