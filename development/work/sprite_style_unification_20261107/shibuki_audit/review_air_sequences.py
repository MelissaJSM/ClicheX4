"""원래 애니메이션 호출표의 첫 순회만 재생하는 검토 자료(실기 아님)."""
from pathlib import Path
import json,sys
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from PIL import Image,ImageDraw,ImageFont
from scripts.export_x_consistency import Archive
from native_pose_pack import need,sha,write

def main():
    d=H/'prepared_air01';o=d/'sequences';need(not o.exists(),'Fresh output required');o.mkdir()
    data=(d/'PL00_U.ARC').read_bytes();need(sha(data)=='c580b371564252fd73cb97aa31d3282dcebabf5855cbec6d5b00acc7f7b7c6be','Wrong candidate');a=Archive(data)
    source=H/'air_detail_inputs01/structure_audit.json';audit=json.loads(source.read_text('utf8'));font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',15)
    result={'scope':'실제 EXE 순서·호출 유지시간에 따른 그림 검토. 실제 게임/물리/이벤트 시뮬레이션이 아님.','arc_sha256':sha(data),'animation_audit_sha256':sha(source.read_bytes()),'presentation_rate_calls_per_second':60,'presentation_rate_is_assumption':True,'terminal_policy':'원표 첫 순회만 재생. 외부 상태 전환을 재현하지 않으며 종단 반복 또는 물리 이동을 만들지 않음.','sequences':[]}
    def panel(n,mask,label):
        im=Image.new('RGB',(300,340),(28,34,44));draw=ImageDraw.Draw(im);draw.text((8,4),label,fill='white',font=font)
        pic=a.composite(n,mask)[0].crop((124,120,188,188)).resize((256,272),Image.Resampling.NEAREST);im.paste(pic,(22,36),pic)
        draw.line((22,196,278,196),fill=(65,65,75));draw.line((166,36,166,308),fill=(65,65,75))
        # Retain origin marks in the background, never over sprite pixels.
        im.paste(pic,(22,36),pic);return im
    for seq in audit['sequences']:
        if seq['id'] not in(10,11,12,122,123,124):continue
        steps=seq['steps'];sheet=Image.new('RGB',((len(steps)+1)*300,680),(28,34,44))
        for row,(form,mask) in enumerate((('base',0),('fourth',15))):
            idle=panel(0,mask,form+' / idle0');sheet.paste(idle,(0,row*340));frames=[];durations=[];calls=0;prev_ms=0
            for j,st in enumerate(steps):
                pic=panel(st['frame'],mask,f"{form} ref{st['frame']} / {st['duration_calls_uninterrupted']} calls")
                sheet.paste(pic,((j+1)*300,row*340));fr=Image.new('RGB',(600,340));fr.paste(idle,(0,0));fr.paste(pic,(300,0));frames.append(fr)
                calls+=st['duration_calls_uninterrupted'];now_ms=round(calls*1000/60);durations.append(now_ms-prev_ms);prev_ms=now_ms
            frames[0].save(o/f'{form}_id{seq["id"]:03}.webp',save_all=True,append_images=frames[1:],duration=durations,loop=1,lossless=True)
        path=o/f'id{seq["id"]:03}_contact.png';sheet.save(path)
        result['sequences'].append({'id':seq['id'],'steps':steps,'original_loop_to_position':seq['loop_to_position'],'contact':path.relative_to(ROOT).as_posix(),'contact_sha256':sha(path.read_bytes()),'native_first_pass_calls':calls,'webp_duration_ms':sum(durations),'actual_gameplay':False})
    write(d/'sequences.json',result);print(json.dumps({'sequences':len(result['sequences']),'output':str(o)}))
if __name__=='__main__':main()
