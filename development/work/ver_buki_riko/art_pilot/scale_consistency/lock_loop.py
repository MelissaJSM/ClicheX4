exec((__import__('pathlib').Path(__file__).with_name('fit_native.py')).read_text(encoding='utf-8').split("print('FAILURES'")[0])
# Keep the new anatomical scale and preserve contact continuity at both cycle seams.
all_worlds={n:w.copy() for key,r in records.items() for n in r['slots'] for w in [worlds[r['slots'][0]]]}
changes=[]
for n,anchor,dx in [(12,11,0),(13,14,0),(20,7,0)]:
 w=all_worlds[anchor].copy();w[72:88,48:64]=all_worlds[n][72:88,48-dx:64-dx]
 size,b,safe=geometry[n];bad=np.argwhere((w!=0)&~safe);print('loop',n,'bad',len(bad))
 if len(bad):raise ValueError(bad)
 all_worlds[n]=w;canvas=w[64+b[1]:64+b[3],64+b[0]:64+b[2]];frames[n]=(canvas.tobytes(),size);save_image(*frames[n],words,P/f'locked_frame_{n:03d}.png')
 changes.append({'frame':n,'anchor':anchor,'front_leg_dx':dx,'region':[-16,8,0,24]})
_,checks=patch_frames(arc,gmeta,gfx,parts,frames,pal)
for n in frames:save_image(*frames[n],words,P/f'locked_frame_{n:03d}.png')
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16);board=Image.new('RGBA',(6*256,2*320),(42,45,54,255));d=ImageDraw.Draw(board)
for k,n in enumerate([11,12,13,14,15,16,18,19,20,7,8,9]):
 a=all_worlds[n][24:96,32:96];mask=a!=0;rgba=np.zeros((72,64,4),dtype=np.uint8);rgba[mask,:3]=colors[a[mask]-1];rgba[mask,3]=255;x=k%6*256;y=k//6*320;board.alpha_composite(Image.fromarray(rgba).resize((256,288),Image.Resampling.NEAREST),(x,y+32));d.text((x+4,y+4),str(n),font=font,fill='white')
board.save(P/'locked_boundary_board.png');print('compressed_max',max(c['encoded_bytes'] for c in checks['compression']))
(P/'loop_lock.json').write_text(json.dumps(changes,indent=2),encoding='utf-8')

(P/"final_native_registration.json").write_text(json.dumps(records,indent=2),encoding="utf-8")
