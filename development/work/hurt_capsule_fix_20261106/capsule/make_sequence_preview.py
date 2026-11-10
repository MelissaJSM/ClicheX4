"""네이티브 추적 순서와 현재 픽셀로 분석용 재생물을 만든다(실기 아님)."""
from pathlib import Path
import hashlib,json,sys
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.export_x_consistency import Archive

def main():
 a=Archive((H/'PL02_U.ARC').read_bytes())
 trace=json.loads((H/'native_timeline.json').read_text('utf8'))['cases'][0]['sequence']
 pal=np.array([(0,0,0,0),(255,255,255,255),(100,220,255,255),(120,140,255,255)]+[(255,110,90,255)]*12,np.uint8)
 colors={mask:a.composite(0,mask)[0] for mask in (0,15)}
 def build(row,mirrored=False):
  ref=row['effect_ref'];mask=row['body_mask'];body=colors[mask].crop((112,112,208,208))
  px,_=a.layer(ref,18,10);fx=Image.fromarray(pal[px%16]).crop((112,112,208,208))
  if mirrored:
   body=body.transpose(Image.Transpose.FLIP_LEFT_RIGHT);fx=fx.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
  overlay=Image.alpha_composite(body,fx)
  board=Image.new('RGB',(864,338),'#263642');d=ImageDraw.Draw(board)
  d.text((8,6),'EXTRACTED ASSET SIMULATION / not an emulator capture / neutral effect palette',fill='white')
  d.text((8,22),f"native tick {row['tick']:03d}, effect {ref}, body0 mask{mask}, {'left' if mirrored else 'right'}",fill='white')
  for i,(im,label) in enumerate(((body,'CURRENT BODY'),(fx,'CURRENT EFFECT'),(overlay,'SAME ORIGIN OVERLAY'))):
   d.text((i*288+6,40),label,fill='white');im=im.resize((288,288),Image.Resampling.NEAREST);board.paste(im,(i*288,50),im)
  return board
 frames=[build(row) for row in trace]
 durations=[max(10,round(row['calls']*1000/60/10)*10) for row in trace]
 frames[0].save(H/'capsule_full_sequence.gif',save_all=True,append_images=frames[1:],duration=durations,loop=0,optimize=False)
 post=[(row,build(row)) for row in trace if row['body_mask']==0]
 post[0][1].save(H/'capsule_post_grant.gif',save_all=True,append_images=[im for _,im in post[1:]],duration=[max(10,round(r['calls']*1000/60/10)*10) for r,_ in post],loop=0,optimize=False)
 postleft=[build(row,True) for row,_ in post]
 postleft[0].save(H/'capsule_post_grant_left.gif',save_all=True,append_images=postleft[1:],duration=[max(10,round(r['calls']*1000/60/10)*10) for r,_ in post],loop=0,optimize=False)
 selected=[r for r in trace if r['body_mask']==0 and r['effect_ref'] in (5,9,10)]
 selected=list({r['effect_ref']:r for r in selected}.values())
 board=Image.new('RGB',(864,338*len(selected)),'#263642')
 for i,r in enumerate(selected):board.paste(build(r),(0,338*i))
 board.save(H/'post_grant_comparison.png')
 meta={'source_arc_sha256':hashlib.sha256((H/'PL02_U.ARC').read_bytes()).hexdigest(),
       'source_native_timeline_sha256':hashlib.sha256((H/'native_timeline.json').read_bytes()).hexdigest(),
       'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in H.glob('capsule_*.gif')},
       'comparison':'post_grant_comparison.png','body_ref':0,'native_origin':[160,160],
       'visualization_only':['현재 실제 인덱스 픽셀을 원점 동일하게 겹친 추출 표시 미리보기이며 게임 캡처가 아님.','효과는 팔레트 인덱스 구별용 중립 흰색/청록/파랑이며 실제 CLUT·GPU 반투명 합성을 재현하지 않음.','유지시간은 실제 MIPS 호출 수. GIF는60호출/초 가정과10ms단위 반올림으로 재생하고 반복종료 뒤 처음으로 복귀한다.','왼쪽판은 원점 축을 기준으로 좌우반전한 정적 래스터이며 실제 GPU 표시 검증은 아님.'],
       'game_modified':False}
 (H/'preview_manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n','utf8')
 print(json.dumps({'files':list(meta['files']),'comparison':meta['comparison']}))
if __name__=='__main__':main()
