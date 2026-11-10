from pathlib import Path
from PIL import Image
P=Path(__file__).parent
Q=P/'stride_revision'; C=P/'coherent_walk'
C.mkdir(exist_ok=True)
# Only existing Riko-derived pixels are input to the image editor.
sheet=Image.open(Q/'stride_review.png').convert('RGBA')
ref=Image.new('RGBA',(7*256,2*288))
for i in range(14):
    cell=sheet.crop((i%7*256,i//7*304+16,i%7*256+256,i//7*304+304))
    ref.paste(cell,(i%7*256,i//7*288))
ref.save(C/'reference_cycle.png')
