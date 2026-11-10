"""전후16몸체의 같은 원시간표 검토판. 기존 게임/원화는 읽기 전용."""
from pathlib import Path
import sys,json,io,base64,re
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import Archive,digest,sha,write,need
from scripts.export_sprite_playback import read_disc,at
AFTER={'a':'after_a_costume_probe_v3','b':'after_b_costume_probe_v2','c':'after_c_costume_probe_v2','d':'after_d_costume_probe_v2'}
def main():
 out=D/'costume_review_v1';out.mkdir(exist_ok=False)
 src=D.parent/'ultimate_dash_repaint/packed_dash_candidate_v1/PL02_U.ARC';need(digest(src)=='d1d25c1677f4b108e6cca373ca8cdc7957f1c4e51a4d8480b37a8f06479607d0','Parent');a=Archive(src.read_bytes())
 previous=json.loads((D/'body_review_v2/manifest.json').read_text('utf8'));source=ROOT/'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin';need(digest(source)=='f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720','EXE source');exe=read_disc(source,['SLUS_005.61'])['SLUS_005.61']
 for q in previous['tables']:
  need(at(exe,int(q['table_address'],16)+q['id']*4,4).hex()==q['pointer_bytes'],'Native pointer')
  for s in q['steps']:need(at(exe,int(s['address'],16),4).hex()==s['bytes'],'Native step')
 paths={}
 for page,folder in AFTER.items():
  reg=json.loads((D/folder/'registration.json').read_text('utf8'))
  for q in reg['frames']:
   bp=ROOT/q['before_path'];ap=D/folder/f"after_{q['ref']:03}.png"
   need(digest(bp)==q['before_sha256'],'Before source');need(sha(np.array(Image.open(ap)).tobytes())==q['native_sha256'],'After source')
   paths[q['ref']]=(bp,ap)
 need(set(paths)==set(range(1,33,2)),'All16')
 proof=[];data={};window=(112,112,208,208);render={}
 for n in(0,*range(1,33,2)):
  before=a.composite(0,15)[0]if not n else a.rgba(np.array(Image.open(paths[n][0])),16)
  after=a.composite(0,0)[0]if not n else a.rgba(np.array(Image.open(paths[n][1])))
  images=[a.composite(0,15)[0],before,a.composite(0,0)[0],after];urls=[];hashes=[]
  for j,im in enumerate(images):
   alpha=np.array(im)[:,:,3].copy();alpha[112:208,112:208]=0;need(not alpha.any(),'No crop loss')
   crop=im.crop(window);crop.save(out/f'{n:03}_{j}.png');aa=np.array(crop);aa[aa[:,:,3]==0]=0;hashes.append(sha(aa.tobytes()));buf=io.BytesIO();crop.save(buf,format='PNG');urls.append('data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode())
  data[str(n)]=urls;render[n]=(before,after);proof.append({'ref':n,'sources':[{ 'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p)}for p in paths[n]]if n else[],'canvas_rgba_sha256':hashes})
 html=(D/'body_review_v2/REVIEW.html').read_text('utf8');prefix,rest=html.split('const DATA=',1);_,suffix=rest.split(';let images=',1)
 prefix=re.sub(r'<h2>.*?</h2>', '<h2>나나 얼티밋 이동 · 전후16몸체 제작 중</h2>',prefix)
 prefix=re.sub(r'<p>대기 / 기존 / 새 후보 순서.*?</p>','<p>전폼 대기 / 전폼 새 몸체 / 후폼 대기 / 후폼 새 몸체 순서. 사격·ARC 패킹·실기는 아직 포함하지 않았습니다.</p>',prefix)
 for size in('small','big'):
  dim=96 if size=='small' else 384;prefix=prefix.replace(f'<canvas id="{size}2" width="{dim}" height="{dim}"></canvas>',f'<canvas id="{size}2" width="{dim}" height="{dim}"></canvas><canvas id="{size}3" width="{dim}" height="{dim}"></canvas>')
 html=prefix+'const DATA='+json.dumps(data,separators=(',',':'))+',CASES='+json.dumps(previous['cases'],ensure_ascii=False,separators=(',',':'))+';let images='+suffix.replace('j<3','j<4')
 (out/'REVIEW.html').write_text(html,'utf8')
 order=(0,1,3,29,31,5,7,9,11,13,15,17,19,21,23,25,27,0)
 for form in range(2):
  for start in(0,9):
   sheet=Image.new('RGB',(1728,240),(186,196,203));draw=ImageDraw.Draw(sheet)
   for j,n in enumerate(order[start:start+9]):
    im=render[n][form].crop(window).resize((192,192),Image.Resampling.NEAREST);sheet.paste(im,(192*j,35),im);draw.text((192*j+5,5),f'{n:03}',fill=(20,25,30))
   sheet.save(out/f'{"before"if form==0 else"after"}_sequence_{start//9+1}.png')
 write(out/'manifest.json',{'source_arc_sha256':digest(src),'exe_sha256':sha(exe),'tables':previous['tables'],'native_table_bytes_exact':True,'cases':previous['cases'],'frames':proof,'canvas_size':[96,96],'columns':4,'html_sha256':digest(out/'REVIEW.html'),'native_packed':False,'runtime_verified':False,'clock_assumption':'60 animation calls/sec; no physics or events','source_policy':'새 전폼/후폼 몸체16. 후폼 의상만 등록하며 새 머리·사지·권총 보호. 고유키16은 사격짝16을 포함하지 않는다.'})
 print(out)
if __name__=='__main__':main()
