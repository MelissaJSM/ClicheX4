import hashlib,json
from PIL import Image,ImageDraw
def sha(b):return hashlib.sha256(b).hexdigest()
def write(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
def board(items,path,cols=5):
 result=Image.new('RGB',(cols*300,((len(items)+cols-1)//cols)*320),(31,38,50));d=ImageDraw.Draw(result)
 for i,(label,im)in enumerate(items):
  crop=im.crop((112,120,208,200)).resize((288,240),Image.Resampling.NEAREST);x=i%cols*300;y=i//cols*320;result.paste(crop,(x+6,y+42),crop);d.text((x+8,y+8),label,fill='white')
 result.save(path)
