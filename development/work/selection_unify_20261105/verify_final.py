"""선택 패널 최종 두 모드의 독립 읽기 검사와 별도 폴더 재현."""
import hashlib,json,struct,subprocess,sys
from collections import deque
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import DiscReader,psx_arc
from scripts.prepare_riko_ui import entry
from src.psx_player import composition_frame
from src.psx_static_effect import compose_static
from src.psx_ui_atlas import local_composition,tile_pixels
from src.psx_sector import validate_checks
WORK=Path(__file__).parent
SPECS={
 'ver_buki_riko':('prepared_v4','selection_unified_20261105_v2','shibuki_riko',('shibuki','riko')),
 'ver_rin_nana':('prepared_v5','selection_unified_20261105_v3','rin_nana',('nana','rin')),
}
POLYGONS=(((1,1),(124,1),(190,158),(1,158)),((1,1),(190,1),(190,158),(52,158)))
BORDERS={'shibuki':(2,3,4,2),'riko':(6,7,8,6),'nana':(7,8,10,7),'rin':(2,7,8,2)}

def sha(b):return hashlib.sha256(b).hexdigest()
def digest(path):
 h=hashlib.sha256()
 with path.open('rb')as f:
  for b in iter(lambda:f.read(8388608),b''):h.update(b)
 return h.hexdigest()
def assets(path):
 with path.open('rb')as f:
  d=DiscReader(f,path.stat().st_size);rs={r['name'].split(';')[0]:r for r in d.inspect()['files']}
  return {n:d.read(rs[n]['lba'],rs[n]['size'])for n in('ST0E_U1.ARC','COL0E_U1.ARC')},rs
def picture(arc,bank,frame):
 ranges=((0,40960),(40960,90112),(90112,116736));lo,hi=ranges[bank]
 c=composition_frame(entry(arc,10),bank,frame)
 p,s,b,cov=compose_static(entry(arc,0x10102)[lo:hi],local_composition(c))
 return np.frombuffer(p,np.uint8).reshape(s[1],s[0]),s,b,c,cov
def regions(mask):
 left=mask.copy();out=[]
 for y,x in zip(*np.where(left)):
  if not left[y,x]:continue
  q=deque([(int(y),int(x))]);left[y,x]=False;points=[]
  while q:
   yy,xx=q.popleft();points.append((yy,xx))
   for ry,rx in((yy-1,xx),(yy+1,xx),(yy,xx-1),(yy,xx+1)):
    if 0<=ry<left.shape[0]and 0<=rx<left.shape[1]and left[ry,rx]:left[ry,rx]=False;q.append((ry,rx))
  out.append(points)
 return out

def verify_mode(project,spec):
 prepared,build,stem,characters=spec;folder=WORK/prepared/project
 proposal=json.loads((folder/'proposal.json').read_text('utf8'))
 source=ROOT/proposal['source'];target=ROOT/'out'/project/build/(stem+'.bin')
 assert digest(source)==proposal['source_sha256']
 before,source_records=assets(source);built,built_records=assets(target)
 old=before['ST0E_U1.ARC'];new=(folder/'ST0E_U1.ARC').read_bytes()
 assert sha(old)==proposal['original_resource_sha256'] and sha(new)==proposal['resource_sha256']
 assert built['ST0E_U1.ARC']==new and before['COL0E_U1.ARC']==built['COL0E_U1.ARC']
 assert source_records==built_records and source.stat().st_size==target.stat().st_size
 old_rows,new_rows=psx_arc(old),psx_arc(new)
 clean=lambda rows:[{k:v for k,v in r.items()if k!='sha256'}for r in rows]
 assert clean(old_rows)==clean(new_rows)
 for r in old_rows:
  kind=int(r['type'],16)
  if kind not in(10,0x10102):assert entry(old,kind)==entry(new,kind)
 ot,nt=entry(old,0x10102),entry(new,0x10102)
 assert ot[:40960]==nt[:40960]and ot[90112:]==nt[90112:]
 parts=entry(old,10);newparts=entry(new,10);protected=0;portraits={};cursor=[]
 for bank in range(3):
  count=composition_frame(parts,bank,0)['bank_frame_count']
  assert composition_frame(newparts,bank,0)['bank_frame_count']==count
  for n in range(count):
   a,sz,bb,co,_=picture(old,bank,n);b,ns,nb,cn,_=picture(new,bank,n)
   assert sz==ns and bb==nb
   if bank==1 and n in(0,1):
    name=characters[n];mask_data=np.array(Image.open(folder/(name+'_figure_mask.png')).convert('L'))
    assert set(map(int,np.unique(mask_data)))<={0,255};mask=mask_data>0
    assert mask.shape==(160,192)and np.all(a[mask]!=0)
    indices=np.frombuffer((folder/(name+'_indices.bin')).read_bytes(),np.uint8).reshape(160,192)
    assert np.array_equal(b,indices) and np.array_equal(a[mask],b[mask])
    assert mask.sum()==proposal['portraits'][name]['preserved_figure_pixels']
    old_clut={p['clut']for p in co['parts']};new_clut={p['clut']for p in cn['parts']}
    assert old_clut==new_clut and len(old_clut)==1
    # Independently compose the agreed solid panel and four border bands,
    # then place the unchanged figure pixels over it.
    base=Image.new('L',(192,160));dr=ImageDraw.Draw(base);dr.polygon(POLYGONS[n],fill=1)
    for width,color in zip((4,3,2,1),BORDERS[name][::-1]):dr.polygon(POLYGONS[n],outline=color,width=width)
    expected=np.array(base);expected[mask]=a[mask];assert np.array_equal(expected,b)
    if name in('shibuki','riko'):
     # Authenticated old figure-only source, not the edited panel mask itself.
     if name=='shibuki':
      from scripts.prepare_shibuki_ui import native,D
      art=native(D/'selection_generated.png',(192,160),(190,158),(0,2))
     else:
      from scripts.prepare_riko_illustrations import native,D
      art=native(D/'selection_generated.png',(192,160),(190,158),(1,1))
     assert np.array_equal(mask,(art>0)&(a==art)&(a>0))
    if name=='rin':
     expected_regions={(52,(86,79,95,90)),(83,(51,80,66,94)),(38,(87,90,95,100))};found=[]
     for pts in regions(a==3):
      yy,xx=zip(*pts);key=(len(pts),(min(xx),min(yy),max(xx)+1,max(yy)+1))
      if key in expected_regions:
       assert all(mask[y,x]and a[y,x]==b[y,x]for y,x in pts);found.append(key)
     assert len(found)==3
    portraits[name]={'size':list(sz),'bounds':list(bb),'figure_pixels_exact':int(mask.sum()),
     'palette_row':4+next(iter(old_clut)),'same_figure_indices_and_RGBA':True,
     'specified_panel_and_border_exact':True,'Rin_three_wardrobe_components_preserved':173 if name=='rin'else None}
    continue
   assert np.array_equal(a,b)
   wanted=co['parts']
   if project=='ver_buki_riko'and(bank,n)==(1,5):
    assert len(wanted)==47 and len(cn['parts'])==35
    for p in wanted[25:37]:assert(p['x'],p['y'])==(112,8)and not any(tile_pixels(ot[40960:90112],p['page']*256+p['tile']))
    wanted=wanted[:25]+wanted[37:]
   def normalized(records):return[{k:v for k,v in p.items()if k not in('index','record_offset')}for p in records]
   assert normalized(wanted)==normalized(cn['parts'])
   if bank==1 and 8<=n<=13:cursor.append({'frame':n,'pixels_geometry_draw_order_CLUT_and_RGBA_exact':True})
   protected+=1
 # All non-portrait tiles, including direct name/cursor users, remain byte exact.
 reserved={p['page']*256+p['tile']for n in range(14)if n not in(0,1)for p in composition_frame(parts,1,n)['parts']}
 for tile in reserved:assert tile_pixels(ot[40960:90112],tile)==tile_pixels(nt[40960:90112],tile)
 changes=0;count=0;rec=source_records['ST0E_U1.ARC'];last=rec['lba']+(rec['size']+2047)//2048
 with source.open('rb')as f,target.open('rb')as g:
  while a:=f.read(2352):
   b=g.read(2352);assert len(a)==len(b)
   if a!=b:
    assert rec['lba']<=count<last and a[:24]==b[:24];validate_checks(b);changes+=1
   count+=1
  assert not g.read(1)
 return {'source_BIN':str(source.relative_to(ROOT)),'source_sha256':digest(source),
  'target_BIN':str(target.relative_to(ROOT)),'target_sha256':digest(target),
  'prepared_ARC_sha256':sha(new),'portraits':portraits,'protected_frames':protected,
  'cursor_frames':cursor,'nonportrait_reserved_tiles_exact':len(reserved),
  'all_palettes_and_background_resources_exact':True,'small_sprite_banks_exact':True,
  'all_unrelated_disc_sectors_exact':True,'all_disc_sectors_compared':count,
  'changed_sectors':changes,'edc_ecc_checked':True,'full_Korean_name_pixels_RGBA_and_anchors_exact':True}

def main():
 report_path=WORK/'final_independent.json';assert not report_path.exists()
 code=ROOT/'scripts/selection_unify.py';code_sha=digest(code);results={}
 for project,spec in SPECS.items():
  results[project]=verify_mode(project,spec)
  prepared=WORK/spec[0]/project;repro=WORK/'independent_repro'/project
  assert not repro.exists()
  run=subprocess.run([sys.executable,str(code),'prepare','--project',project,'--output',str(repro)],cwd=ROOT,capture_output=True,text=True)
  assert run.returncode==0,run.stderr
  compared=[]
  for p in prepared.iterdir():
   if p.is_file()and p.name!='proposal.json':
    assert p.read_bytes()==(repro/p.name).read_bytes(),p.name;compared.append(p.name)
  results[project]['independent_prepare_reproduced_files']=sorted(compared)
 assert digest(code)==code_sha
 # Reject bad source/prepared bindings before any BIN output directory exists.
 from scripts import selection_unify as maker
 rejected=[]
 negative=WORK/'independent_negative';negative.mkdir(exist_ok=False)
 for project,spec in SPECS.items():
  original=json.loads((WORK/spec[0]/project/'proposal.json').read_text('utf8'))
  for field,message in [('source_sha256','Source mismatch'),('resource_sha256','Prepared resource changed')]:
   modified={**original,field:'0'*64};p=negative/(project+'_'+field+'.json');p.write_text(json.dumps(modified),'utf8')
   output=ROOT/'out'/project/('selection_independent_reject_'+field);assert not output.exists()
   try:maker.build(project,p,output)
   except ValueError as error:assert str(error)==message
   else:raise AssertionError('Invalid binding accepted')
   assert not output.exists();rejected.append(project+'/'+field)
 report={'passed':True,'modes':results,'negative_cases_rejected_without_BIN_write':rejected,
  'production_code_sha256':code_sha,'production_code_unchanged':True,
  'current_cursor_metadata_and_colors_preserved_not_repaired':True,
  'mask_crops_visually_reviewed':True,'Nana_Rin_complete_semantic_subject_segmentation_not_proven':True,
  'active_savestate_cards_or_emulator_written':False,'runtime_verified':False}
 report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
 print(json.dumps({'passed':True,'modes':2,'portraits':4,'protected_frames':sum(v['protected_frames']for v in results.values()),
  'cursor_frames':12,'negative_cases':len(rejected),'target_hashes':{k:v['target_sha256']for k,v in results.items()}}))
if __name__=='__main__':main()
