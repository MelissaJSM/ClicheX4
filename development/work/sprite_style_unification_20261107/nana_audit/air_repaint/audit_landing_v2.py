"""새 착지 부츠의 출처, 좌표, 연결 및 변경 범위를 확인한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy.ndimage import label
D=Path(__file__).resolve().parent; ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import Archive,sha,need,write

def main():
    p=json.loads((D/'inputs.json').read_text('utf8'))
    a=Archive((ROOT/p['parent_arc']).read_bytes())
    need(sha(a.data)==p['parent_arc_sha256'],'Parent ARC')
    out=D/'key_anchor_audit_v2'; out.mkdir(exist_ok=True)
    rows=[]
    def spans(im):
        y=int(np.where(im>0)[0].max()); x=np.flatnonzero(im[y]>0)
        return {'y':y-160,'spans':[(v-160).tolist() for v in np.split(x,np.flatnonzero(np.diff(x)>1)+1)]}
    for n in (33,39,47,51):
        v1=np.array(Image.open(D/'basic_registered_v1'/f'base_{n:03}.png'))
        v2=np.array(Image.open(D/'basic_registered_v2'/f'base_{n:03}.png'))
        count=label(v2>0,np.ones((3,3)))[1]
        need(count==1,'Disconnected new art')
        need(np.array_equal(v1[:177],v2[:177]),'Pixels above ankle changed')
        if n!=51: need(np.array_equal(v1,v2),'Other key changed')
        rows.append({'ref':n,'old_foot':spans(a.layer(n)[0]),'v1_foot':spans(v1),'v2_foot':spans(v2),
                     'changed_pixels':int(np.count_nonzero(v1!=v2)), 'components_8':count,
                     'above_ankle_exact':True,'indexed_sha256':sha(v2.tobytes())})
    report={'passed':True,'source_arc_sha256':sha(a.data),'frames':rows,
            'idle_foot':spans(a.layer(0)[0]),'scope':'51만 같은 새 원화의 발목 아래를 등록. 머리·몸·무릎 및 다른3키 불변. 원배율/정수배 정적 확인이며 패킹·실기 검증 아님.',
            'art_change_method':'기존 원화 소스 좌표만 국소 재등록. 옛 그림 덮기/단색 채움 없음.'}
    write(out/'verification.json',report)
    board=Image.new('RGB',(1200,570),(187,199,205));draw=ImageDraw.Draw(board)
    font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',19)
    items=[('대기0',a.layer(0)[0]),('기존51',a.layer(51)[0]),
           ('새 원화51 v1',np.array(Image.open(D/'basic_registered_v1/base_051.png'))),
           ('부츠 정합51 v2',np.array(Image.open(D/'basic_registered_v2/base_051.png')))]
    for i,(title,idx) in enumerate(items):
        draw.text((i*300+8,8),title,font=font,fill='black')
        im=a.rgba(idx).crop((140,143,185,186))
        for scale,y in [(1,42),(2,92),(5,210)]:
            scaled=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST)
            board.paste(scaled,(i*300+30,y),scaled)
        floor=spans(idx);summary=' / '.join(f'{v[0]}..{v[-1]} ({len(v)}px)' for v in floor['spans'])
        draw.text((i*300+8,450),summary,font=font,fill='black')
    board.save(out/'landing_contact.png')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
