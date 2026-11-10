"""실제 창 녹화만 잘라 조밀한 시간별 미술 비교 시트를 만든다."""
import hashlib,json,math
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[3]
RUNTIME=ROOT/'work/sprite_consistency_20261105/runtime'
HERE=Path(__file__).resolve().parent/'art_review/runtime_dense'
FONT=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',13)

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def decode(path):
    im=Image.open(path);frames=[];t=0
    for i in range(im.n_frames):
        im.seek(i);im.load();duration=im.info['duration']
        frames.append((t/1000,duration/1000,i,im.convert('RGB').copy()));t+=duration
    return frames

def main():
    HERE.mkdir(parents=True,exist_ok=True);proof=[]
    tasks=[('shibuki_fourth_arrival','arrival',[(6.5,8.3),(8.3,10.05)],(75,205,240,425),6),
           ('shibuki_fourth_special_sync/recording','fire',[(0.44,1.25),(2.12,3.25),(6.70,7.50),(7.50,8.30),(11.70,12.50),(12.50,13.30)],(50,30,380,425),4)]
    for folder,name,ranges,box,cols in tasks:
        source=RUNTIME/folder/'play.webp';before=sha(source);frames=decode(source)
        for start,end in ranges:
            selected=[x for x in frames if start<=x[0]<end]
            cw,ch=box[2]-box[0]+4,box[3]-box[1]+24
            sheet=Image.new('RGB',(cols*cw,math.ceil(len(selected)/cols)*ch+30),'#161c27');draw=ImageDraw.Draw(sheet)
            draw.text((5,7),f'Actual ePSXe window recording | {name} {start:.2f}..{end:.2f}s | original-pixel crop',font=FONT,fill='white')
            for j,(time,dur,index,im) in enumerate(selected):
                x=j%cols*cw;y=30+j//cols*ch
                sheet.paste(im.crop(box),(x,y+22));draw.text((x+3,y+3),f'{time:.3f}s +{dur*1000:.0f}ms webp#{index}',font=FONT,fill='white')
            target=HERE/f'{name}_{start:.2f}_{end:.2f}.png';sheet.save(target)
            proof.append({'source':source.relative_to(ROOT).as_posix(),'source_sha256':before,
              'range_seconds':[start,end],'crop_box':box,'scale':1,'frames':len(selected),
              'encoded_frame_indices':[x[2] for x in selected],'timestamps_seconds':[x[0] for x in selected],
              'sheet':target.relative_to(ROOT).as_posix(),'sheet_sha256':sha(target)})
        assert sha(source)==before
    report={'sources_are_actual_window_recordings':True,'source_recordings_unchanged':True,
       'timing':'WebP의 실제 frame duration 누적으로 시각을 복원. 중복 프레임 병합 때문에 원래 캡처 개수와 인코딩된 프레임 개수는 다름.',
       'no_art_generated_or_replaced':True,'sheets':proof}
    (HERE/'capture.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({'sheets':len(proof),'captured_frames':sum(x['frames'] for x in proof)}))

if __name__=='__main__':main()
