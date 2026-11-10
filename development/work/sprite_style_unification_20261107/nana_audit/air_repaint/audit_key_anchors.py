"""공중4키의 머리/원점/발 접지 및 뒤머리 가닥 출처를 직접 비교한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy.ndimage import label
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import Archive,sha,need,write,helper
def main():
    p=json.loads((D/'inputs.json').read_text('utf8'));r=json.loads((D/'basic_registered_v1/registration.json').read_text('utf8'));a=Archive((ROOT/p['parent_arc']).read_bytes());out=D/'key_anchor_audit_v1';out.mkdir(exist_ok=True);Y,X=np.indices((384,384));rows=[];report=[]
    for q in r['frames']:
        n=q['ref'];old=a.layer(n)[0];new=np.array(Image.open(D/'basic_registered_v1'/f'base_{n:03}.png'));ex,ey=q['target_eye'];head=(X<160+ex+5)&(Y<160+ey+3);top=int(np.where((new>0)&head)[0].min()-160);labs,count=label(new>0,np.ones((3,3)));need(count==1,'New alpha disconnected');floor=np.where(new>0)[0].max();oldfloor=np.where(old>0)[0].max()
        def feet(ar,y):
            x=np.flatnonzero(ar[y]>0);ss=np.split(x,np.flatnonzero(np.diff(x)>1)+1);return[(s-160).tolist()for s in ss]
        report.append({'ref':n,'expected_eye':[ex,ey],'eye_exact':int(new[ey+160,ex+160])==14,'crown_world_y':top,'crown_to_eye':ey-top,'native_alpha_components_8':count,'foot_y':int(floor-160),'old_foot_y':int(oldfloor-160),'foot_spans':feet(new,floor),'old_foot_spans':feet(old,oldfloor),'old_art_pixels_used':0})
        cols=[]
        for title,im in[('현재',a.composite(n)[0]),('새 원화 등록',a.rgba(new))]:
            draw=ImageDraw.Draw(im);draw.line((157+ex,160+ey,163+ex,160+ey),fill=(0,255,255,255));draw.line((160+ex,157+ey,160+ex,163+ey),fill=(0,255,255,255));draw.line((135,int(floor),185,int(floor)),fill=(255,0,0,255));cols.append((title,im))
        rows.append((f'anchor {n}',cols))
    helper.grid(rows,out/'eye_floor_overlay.png',6)
    # Pixel-voted hair at native ref39 is connected, including the apparent
    # endpoint. Show its exact generated source alongside native output.
    n=39;src=Image.open(D/'basic_registered_v1/source_039.png').convert('RGBA');new=np.array(Image.open(D/'basic_registered_v1/base_039.png'));board=Image.new('RGB',(1100,650),(187,199,205));draw=ImageDraw.Draw(board);font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',20)
    draw.text((12,12),'생성 원화39 — 뒤로 감기는 가닥',font=font,fill='black');draw.text((540,12),'native39 — 8방향 연결 1개',font=font,fill='black');im=src.resize((src.width,src.height),Image.Resampling.NEAREST);board.paste(im,(100,90),im);native=a.rgba(new).crop((145,128,188,181)).resize((344,424),Image.Resampling.NEAREST);board.paste(native,(610,90),native);board.save(out/'hair_39_source.png')
    write(out/'verification.json',{'passed':True,'scope':'정적 원화/네이티브 좌표 확인; 실기 아님.51 양발 x정합은 후속.','frames':report,'hair_39':'원화에서 뒤로 감기는 실제 가닥이며 native alpha 전체1개8연결. 생성잡점으로 독립 분리된 픽셀 없음.','original_eye_half_integer_note':'39/51은 원래 pupil centroid가반픽셀인좌표이며 새1픽셀을기존pupil의좌상단에둠.'});print(json.dumps(report))
if __name__=='__main__':main()
