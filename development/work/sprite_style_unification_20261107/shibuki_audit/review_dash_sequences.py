"""원 대시 호출표의 첫 순회를 연결한다. 물리/이벤트/실기 재현이 아니다."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive
def main():
    o=H/'dash_sequence_review01';need(not o.exists(),'Fresh output');o.mkdir();p=H/'prepared_dash_base01/PL00_U.ARC';need(sha(p.read_bytes())=='dd8504d31ed2f169825fd6daf8e0eae236e6a97f045d0b476e9f83c250824d3b','Wrong candidate');a=Archive(p.read_bytes());source=H/'dash_followup_audit01/report.json';audit=json.loads(source.read_text('utf8'));font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14);out=[]
    def panel(n,m,label):
        im=a.composite(n,m)[0];crop=im.crop((112,124,208,188));need(np.count_nonzero(np.array(crop)[:,:,3])==np.count_nonzero(np.array(im)[:,:,3]),'Clipped art')
        cell=Image.new('RGB',(288,224),(28,34,44));dr=ImageDraw.Draw(cell);dr.text((6,2),label,fill='white',font=font);dr.line((144,20,144,212),fill=(54,60,70));dr.line((0,128,288,128),fill=(54,60,70));crop=crop.resize((288,192),Image.Resampling.NEAREST);cell.paste(crop,(0,20),crop);return cell
    for seq in audit['animation_sequences']:
        steps=seq['steps'];sheet=Image.new('RGB',((len(steps)+1)*288,448),(28,34,44));files=[]
        for row,(form,m)in enumerate((('base',0),('fourth',15))):
            idle=panel(0,m,form+' accepted idle');sheet.paste(idle,(0,row*224));frames=[];dur=[];calls=0;prev=0
            for j,st in enumerate(steps):
                cell=panel(st['frame'],m,f'{form} ref{st["frame"]} / {st["duration_calls_uninterrupted"]} calls');sheet.paste(cell,((j+1)*288,row*224));frame=Image.new('RGB',(576,224));frame.paste(idle);frame.paste(cell,(288,0));frames.append(frame);calls+=st['duration_calls_uninterrupted'];now=round(calls*1000/60);dur.append(now-prev);prev=now
            f=o/f'{form}_{seq["id"]:03}.webp';frames[0].save(f,save_all=True,append_images=frames[1:],duration=dur,loop=1,lossless=True);files.append({'path':f.relative_to(ROOT).as_posix(),'sha256':sha(f.read_bytes())})
        pth=o/f'id{seq["id"]:03}_contact.png';sheet.save(pth);out.append({'id':seq['id'],'steps':steps,'source_loop_to_position':seq['loop_to_position'],'first_pass_calls':calls,'contact':pth.relative_to(ROOT).as_posix(),'contact_sha256':sha(pth.read_bytes()),'animations':files})
    write(o/'report.json',{'scope':'원 실제 EXE 애니메이션 표에서 읽은 프레임 순서·유지호출을 첫 순회로 연결한 검토 자료. 캐릭터 이동·속도·분기 이벤트는 재현하지 않는다.','source_audit_sha256':sha(source.read_bytes()),'source_animation':audit['animation_source'],'candidate_sha256':sha(p.read_bytes()),'presentation_calls_per_second':60,'presentation_rate_assumption':True,'original_loop_preserved_in_metadata':True,'webp_first_pass_only':True,'actual_gameplay':False,'sequences':out,'actual_contact_visual_review_pending':True,'animated_live_visual_reviewed':False});print(json.dumps({'sequences':len(out),'first_pass_steps':sum(len(s['steps'])for s in out),'output':str(o)}))
if __name__=='__main__':main()
