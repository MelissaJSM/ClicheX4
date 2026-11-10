"""특수기술 재검수용 포즈 시트를 만든다. 원화는 imagegen으로 수정한다."""
import argparse,json,sys
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_specials import OUT

def main():
    ap=argparse.ArgumentParser();ap.add_argument('group');ap.add_argument('frames',nargs='+',type=int);a=ap.parse_args()
    folder=OUT/a.group;guide=json.loads((folder/'guide.json').read_text('utf-8'));batches=json.loads((OUT/'batches.json').read_text('utf-8'))
    batch=max(q['batch'] for q in batches if q['group']==a.group)+1
    cols=3;rows=(len(a.frames)+3)//3;slots=[None,*a.frames]+[None]*(cols*rows-len(a.frames)-1)
    idle=Image.open(OUT/'master_preview_147.png').convert('RGBA')
    template=Image.new('RGBA',(cols*96,rows*96));poses=Image.new('RGBA',template.size)
    for i,n in enumerate(slots):
        x=i%cols*96;y=i//cols*96
        if n is None:
            template.alpha_composite(idle,(x+20,y+24));poses.alpha_composite(idle,(x+20,y+24));continue
        pic=Image.open(folder/f'prepared_{n:03d}.png').convert('RGBA')
        template.alpha_composite(pic,(x+(96-pic.width)//2,y+24))
        old=Image.open(folder/guide['frames'][str(n)]['before']).convert('RGBA');b=guide['frames'][str(n)]['bounds']
        poses.alpha_composite(old,(x+48+b[0],y+48+b[1]))
    for name,im in [('template',template),('poses',poses)]:im.resize((im.width*6,im.height*6),Image.Resampling.NEAREST).save(folder/f'{name}_{batch}.png')
    prompt=(folder/'prompt_0.txt').read_text('utf-8')
    # Caller supplies a dedicated correction prompt after inspecting this sheet.
    (folder/f'prompt_{batch}.txt').write_text(prompt,'utf-8')
    batches.append({'id':f'{a.group}_{batch}','group':a.group,'batch':batch,'slots':slots,'columns':cols,'rows':rows,**{k:str(folder/f'{v}_{batch}.{ext}') for k,v,ext in [('template','template','png'),('poses','poses','png'),('prompt','prompt','txt'),('output','generated','png')]}})
    (OUT/'batches.json').write_text(json.dumps(batches,indent=2)+'\n','utf-8');print(json.dumps({'batch':batch,'slots':slots}))

if __name__=='__main__':main()
