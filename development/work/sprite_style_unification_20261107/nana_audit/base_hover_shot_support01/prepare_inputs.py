"""루트 새 몸체는 읽기 전용. 사격팔 국소 입력/원US 공통 발사표 검증."""
from pathlib import Path
import sys,json,struct
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;W=N.parent;ROOT=W.parents[1]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need
from scripts.c01_audio_build import read_disc

def main():
 r=W/'root_nana_hover';audit=json.loads((r/'input_audit.json').read_text('utf8'));p=ROOT/audit['input']['path'];need(digest(p)==audit['input']['sha256'],'부모');a=Archive(p.read_bytes())
 old,_=read_disc(ROOT/'MegaMan X4.bin',['SLUS_005.61','PL00_U.ARC','PL02_U.ARC']);exe=old['SLUS_005.61'];off=lambda v:v-0x80010000+2048;ua={k:Archive(old[k])for k in ('PL00_U.ARC','PL02_U.ARC')}
 cm=N/'ultimate_hover_repaint/canonical_cases_probe_v4/manifest.json';coords=json.loads(cm.read_text('utf8'))['canonical_source_texels'];need(len(coords)==20,'정본20')
 origins={};checks=[]
 for n,expected in [(222,[-27,-9]),(224,[-29,-8]),(226,[-20,-10]),(228,[-17,-10])]:
  xy=list(struct.unpack_from('<bb',exe,off(0x8011b230+n*2)));need(xy==expected,'발사표');origins[n]=xy;mouth=[]
  for name,arc in ua.items():
   z=arc.layer(n)[0];v=[int(z[y+160,xy[0]+161])for y in range(xy[1]-2,xy[1]+3)];need(all(v[1:4]),'원US 기본 총입구 세행');full=np.array(arc.composite(n,15)[0]);opacity=[int(full[y+160,xy[0]+161,3])for y in range(xy[1]-2,xy[1]+3)];need(all(opacity),'원US 풀아머 총입구 다섯행');mouth.append({'archive':name,'mouth_x':xy[0]+1,'rows':list(range(xy[1]-2,xy[1]+3)),'base_indices':v,'full_armor_alpha':opacity})
  checks.append({'ref':n,'origin_xy':xy,'original_PL00_PL02_mouth_checks':mouth})
 write(D/'muzzle_source_audit.json',{'original_exe_sha256':sha(exe),'original_archives':{k:sha(old[k])for k in ua},'original_muzzle_code_sha256':sha(exe[off(0x80092e2c):off(0x80092f08)]),'frame_table':'0x8011B230','shared_code_no_archive_branch':True,'checks':checks,'scope':'원US 동일 EXE의 참조별 signedXY 직접 읽기 및 PL00/PL02 실제 총입구5행 확인. 새MIPS/실기 미실행.'})
 for page,refs in [('a',[222,224]),('b',[226,228])]:
  out=D/f'inputs_{page}01';out.mkdir(exist_ok=False);boards={name:Image.new('RGBA',(1536,1536))for name in ('current_bodies','target_pistols','target_overlay','style85')};frames=[]
  for row,n in enumerate(refs):
   for col,(form,start,mask)in enumerate([('base_legs',0,0),('fourth',16,15)]):
    i=row*2+col;src=r/f'body_alignment01/{form}_{n-1}_indices.png';z=np.array(Image.open(src));ox,oy=origins[n];dx,dy=ox+23,oy+9;gun=np.zeros_like(z)
    for x,y,v in coords:gun[y+dy+160,x+dx+160]=v
    overlay=z.copy();overlay[gun>0]=gun[gun>0];pos=(col*768,row*768)
    for name,v in [('current_bodies',z),('target_pistols',gun),('target_overlay',overlay)]:boards[name].alpha_composite(a.rgba(v,start).crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),pos)
    boards['style85'].alpha_composite(a.composite(85,mask)[0].crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),pos)
    Image.fromarray(gun).save(out/f'{form}_{n}_gun.png');frames.append({'ref':n,'body_ref':n-1,'form':form,'palette_start':start,'cell':i,'body_source':src.relative_to(ROOT).as_posix(),'body_source_sha256':digest(src),'body_indices_sha256':sha(z.tobytes()),'engine_origin':origins[n],'canonical_translation':[dx,dy],'target_mouth_x':ox+1,'barrel_rows':[oy-1,oy],'target_gun_indices_sha256':sha(gun.tobytes())})
  for name,im in boards.items():im.save(out/f'{name}.png')
  reach='The two upper sprites and two lower sprites must reach farther LEFT and slightly UP with a natural elbow bend.'if page=='a'else'The forward arm should be compact, with a visibly bent elbow below the wrist; do not extend a long straight arm.'
  prompt=f'''Edit FIRST transparent adult action-game character sheet. Preserve exactly four figures, same 2x2 arrangement, same square canvas and cell margins, fixed character scale and position. LEFT column is the black cap outfit; RIGHT column is the black veil outfit. This is ONLY a forward shooting arm edit, with existing face, head, hat or veil, hair shading, torso, waist, both legs and shoes fixed. The other raised/back arm remains fixed. Each figure has exactly TWO arms and ONE small pistol.
SECOND image contains the required tiny pink-and-black pistol at its precise destination in each matching cell. THIRD shows that target pistol over the unchanged body for spatial context; the existing lowered hand/gun on the first sheet is to be replaced, not duplicated. FOURTH shows the accepted sleeve/hand/pistol pixel style and arm thickness. Replace only the forward arm from its existing shoulder through elbow, cuff and hand so the hand grips the SECOND pistol at exactly that location. Keep the barrel horizontal, pointing LEFT, and retain the SECOND pistol size and silhouette. Never shift the torso/head/legs or enlarge the gun to reach the target. {reach}
Both outfits have long black sleeves: make the sleeve's small charcoal/purple highlights and dark lower contour clear, with a small pale cuff where shown by that outfit and a skin-colored hand. Use the same readable wrist/elbow thickness as FOURTH; no thin 1-pixel wrist, no oversized fist, no straight black chest bar. Preserve fine hair details and garment shading. Do not remove clothing, change coverage, or add flesh at the sleeve. Do not introduce a third arm or leave the original lower gun behind. No projectiles, flames, effects, glows, labels, guide marks or background. Transparent RGBA. Only the forward sleeve, wrist, hand and pistol change.'''
  (out/'prompt.txt').write_text(prompt,'utf8');write(out/'manifest.json',{'parent_arc':str(p.relative_to(ROOT)).replace('\\','/'),'parent_sha256':digest(p),'frames':frames,'canonical_source':cm.relative_to(ROOT).as_posix(),'canonical_source_sha256':digest(cm),'canonical_source_texels':coords,'native_cell':[96,96],'canvas':[1536,1536],'root_sources_read_only':True,'final_art_accepted':False,'native_packed':False,'runtime_verified':False,'files':[{'path':q.relative_to(ROOT).as_posix(),'sha256':digest(q)}for q in sorted(out.iterdir())if q.is_file()]})
 print('기본/포스 사격팔 2페이지 입력과 원US PL00/02 발사표 대조 저장')
if __name__=='__main__':main()
