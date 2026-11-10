from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];d=Path(__file__).parent
s=(ROOT/'scripts/prepare_shibuki_hurt.py').read_text(encoding='utf-8')
s=s.replace('X 피격106..114를 교체하며 공유 효과·아머·CLUT·다른 동작을 보존한다.','X 체력 부족 대기120..125를 교체하며 입 오버레이와 아머를 분리한다.')
s=s.replace('set(range(106,115))','set(range(120,126))').replace('{106:[106,107,108],109:[109],110:[110,111],112:[112],113:[113],114:[114]}','{120:[120,121],122:[122,123],124:[124,125]}')
s=s.replace("{r['frame'] for r in art['frames']}!=PRIMARY","{r['frame'] for r in art['frames']}!=FRAMES").replace('len(packing)!=6','len(packing)!=3').replace('Incomplete hurt art','Incomplete low HP art')
s=s.replace(" if list(struct.unpack('<16H',palette[64:96]))!=art['effect_palette_words']:raise ValueError('Effect palette mismatch')\n",'').replace('expected_clut=2 if n in (112,113,114) else 0','expected_clut=0')
start=s.index('  # Aliases share the body,');end=s.index('  old,_,_=indexed_atlas',start)
s=s[:start]+'''  alias=n+1;ac=composition_frame(parts,0,alias);primary_signature=lambda q:(q['flags'],q['tile'],q['x'],q['y']);old_body=comp['parts'];body=[q for q in ac['parts'] if q['tile']!=7];mouth=[q for q in ac['parts'] if q['tile']==7]
  if list(map(primary_signature,old_body))!=list(map(primary_signature,body)) or len(mouth)!=1 or ac['parts'][-1]!=mouth[0] or 7 in armor:raise ValueError('Mouth overlay structure changed')
  for old,new in zip(body,composition_frame(np_,0,n)['parts']):
   off=old['record_offset'];np_[off:off+4]=np_[new['record_offset']:new['record_offset']+4];allowed_records.update(range(off,off+4))
  ar=next(q for q in art['frames'] if q['frame']==alias);ap=(d/ar['image']).resolve()
  if not ap.is_relative_to(d):raise ValueError('Alias image escaped art directory')
  im=Image.open(ap);opened=np.array(im)
  if im.mode!='P' or im.size!=(96,80) or opened.max()>15:raise ValueError('Invalid mouth image')
  art_hashes[ar['image']]=sha256(ap.read_bytes());yy,xx=np.nonzero(opened!=target)
  if not len(xx) or np.any(opened[yy,xx]==0) or np.any(target[yy,xx]==0):raise ValueError('Mouth overlay changed silhouette')
  left,top=int(xx.min())-2,int(yy.min())-2
  if xx.max()-left>=16 or yy.max()-top>=16:raise ValueError('Mouth patch exceeds tile')
  overlay=np.zeros_like(target);overlay[yy,xx]=opened[yy,xx];raw=pack_rectangles(raw,desc['tile_count'],overlay.tobytes(),(96,80),[[left,top]],[7],{7});q=mouth[0]
  if q['page'] or q['clut'] or q['unknown_flags']:raise ValueError('Unsupported mouth flags')
  struct.pack_into('<BBbb',np_,q['record_offset'],0,7,left-48,top-40);allowed_records.update(range(q['record_offset'],q['record_offset']+4))
  if not np.array_equal(world_canvas(raw,desc['tile_count'],composition_frame(np_,0,alias)),opened):raise ValueError('Mouth readback mismatch')
  if not np.array_equal(world_canvas(raw,desc['tile_count'],composition_frame(np_,0,n)),target):raise ValueError('Mouth changed base body')
  writable=writable|{7}
''' + s[end:]
s=s.replace("'shibuki_hurt'","'shibuki_low_hp'").replace("'base_hurt_9'","'base_low_hp_6'").replace("'wall_frames_preserved':True","'wall_frames_preserved':True,'hurt_frames_preserved':True,'ladder_frames_preserved':True").replace("'shared_effect_tiles_parts_preserved':True","'mouth_overlay_verified':True")
(ROOT/'scripts/prepare_shibuki_low_hp.py').write_text(s,encoding='utf-8')
s=(d.parent/'hurt_v1/optimize03.py').read_text(encoding='utf-8').replace('production03','production02').replace('shibuki_wall_20261026T135224131979Z','shibuki_ladder_20261026T150541813461Z').replace("for q in plan['groups']:","for q in [q for q in plan['groups'] if q['frame'] in (120,122,124)]:")
(d/'optimize02.py').write_text(s,encoding='utf-8')
