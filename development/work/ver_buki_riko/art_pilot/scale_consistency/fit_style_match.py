"""Composite generated surface colors through fixed native material/pose masks."""
from pathlib import Path
P=Path(__file__).parent
exec((P/'fit_probe.py').read_text(encoding='utf-8').split('run_slots=')[0])
import hashlib,shutil
from collections import deque
D=P/'idle_style_match';B=P/'zero_based_rebuild'
recipe=json.loads((B/'recipe.json').read_text(encoding='utf-8'))
sheet=Image.open(D/'generated_style.png').convert('RGBA')
head=np.array(Image.open(master))[:19,12:35]
WHITE=[7,12,15];SKIN=[9,11,13];CAPE=[2,6,10];DARK=[1,3]
def groups(a):
    unseen=set(map(tuple,np.argwhere(a)));result=[]
    while unseen:
        seed=unseen.pop();todo=deque([seed]);group=[seed]
        while todo:
            y,x=todo.popleft()
            for dy,dx in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
                q=(y+dy,x+dx)
                if q in unseen:unseen.remove(q);todo.append(q);group.append(q)
        result.append(group)
    return sorted(result,key=len,reverse=True)
def rgba(a):
    r=np.zeros((*a.shape,4),dtype=np.uint8);m=a!=0;r[m,:3]=colors[a[m]-1];r[m,3]=255;return Image.fromarray(r)
records=[];frames={};worlds={};oldworlds={}
for i,n in enumerate(range(7,21)):
    size,b,safe=geometry[n];old=np.zeros((72,64),dtype=np.uint8)
    native=np.array(Image.open(B/f'frame_{n:03d}.png'));original_world=np.zeros((128,128),dtype=np.uint8);original_world[64+b[1]:64+b[3],64+b[0]:64+b[2]]=native;old=original_world[24:96,32:96].copy()
    gen=np.array(sheet.crop((round(i%4*sheet.width/4),round(i//4*sheet.height/4),round((i%4+1)*sheet.width/4),round((i//4+1)*sheet.height/4))).resize((64,72),Image.Resampling.NEAREST))
    gm=gen[:,:,3]>=180;gr=gen[:,:,:3].astype(np.int32);gi=np.zeros((72,64),dtype=np.uint8);gi[gm]=np.argmin(((gr[gm,None]-colors[None])**2).sum(2),1)+1
    # Registration affects only the proposed surface colors, never native geometry.
    choices=[]
    for dy in range(-2,3):
        for dx in range(-2,3):
            q=np.zeros((76,68),dtype=np.uint8);q[2+dy:74+dy,2+dx:66+dx]=gi;q=q[2:74,2:66]
            same_material=(np.isin(old,WHITE)&np.isin(q,WHITE))|(np.isin(old,SKIN)&np.isin(q,SKIN))|(np.isin(old,CAPE)&np.isin(q,CAPE))
            score=int(same_material.sum())*3-int(((old!=0)!=(q!=0)).sum())-abs(dx)-abs(dy)
            choices.append((score,dx,dy,q))
    score,dx,dy,gi=max(choices,key=lambda v:v[0]);new=old.copy()
    white=np.isin(old,WHITE);cape=np.isin(old,CAPE)
    nearwhite=np.zeros_like(white);nearcape=np.zeros_like(cape)
    for yy,xx in [(0,1),(0,-1),(1,0),(-1,0)]:
        p=np.pad(white,1);nearwhite|=p[1+yy:73+yy,1+xx:65+xx]
        p=np.pad(cape,1);nearcape|=p[1+yy:73+yy,1+xx:65+xx]
    # Material masks prevent generative redrawing from changing anatomy or skin.
    use=white&np.isin(gi,WHITE);new[use]=gi[use]
    use=cape&np.isin(gi,CAPE);new[use]=gi[use]
    use=np.isin(old,DARK)&nearwhite&np.isin(gi,WHITE);new[use]=7
    use=np.isin(old,DARK)&~nearwhite&nearcape&np.isin(gi,CAPE);new[use]=2
    # Approved head/neck and every skin pixel remain exact.
    hx,hy=recipe['body_standard']['head_world_positions'][str(n)];sub=new[40+hy:40+hy+19,32+hx:32+hx+23];sub[head!=0]=head[head!=0]
    assert np.array_equal(new[np.isin(old,SKIN)],old[np.isin(old,SKIN)])
    removed=[]
    for g in groups(new!=0)[1:]:
        assert n==17 and len(g)==3, (n,len(g))
        for y,x in g:new[y,x]=0;removed.append([int(x-32),int(y-40)])
    assert len(groups(new!=0))==1
    diffalpha=np.argwhere((new!=0)!=(old!=0));assert len(diffalpha)==len(removed)
    world=np.zeros((128,128),dtype=np.uint8);world[24:96,32:96]=new;assert not np.any((world!=0)&~safe)
    a=world[64+b[1]:64+b[3],64+b[0]:64+b[2]];frames[n]=(a.tobytes(),size);save_image(*frames[n],words,D/f'frame_{n:03d}.png')
    records.append({'frame':n,'changed_color_pixels':int(((new!=old)&(new!=0)).sum()),'removed_detached_pixels_world':removed,'pose_alpha_preserved_except_removed_speck':True,'surface_registration':[dx,dy],'head_foreground_exact':True,'skin_exact':True,'dark_before':int(np.isin(old,DARK).sum()),'dark_after':int(np.isin(new,DARK).sum()),'white_shades_before':[int((old==v).sum()) for v in WHITE],'white_shades_after':[int((new==v).sum()) for v in WHITE]})
    worlds[n]=new;oldworlds[n]=old
for n in range(3,35):
    if n not in worlds:shutil.copyfile(B/f'frame_{n:03d}.png',D/f'frame_{n:03d}.png');frames[n]=read_indexed_png(D/f'frame_{n:03d}.png',words)
_,checks=patch_frames(arc,gmeta,gfx,parts,frames,pal)
recipe['frames']={str(n):{'file':f'frame_{n:03d}.png','sha256':hashlib.sha256((D/f'frame_{n:03d}.png').read_bytes()).hexdigest()} for n in range(3,35)}
recipe['surface_style']={'base_recipe':str(B/'recipe.json'),'method':'Generated surface colors composited through existing native white/cape/adjacent-outline masks; alpha, skin, canonical head and pose registration locked. Detached 3-pixel frame17 cape artifact removed.','records':records,'generated_source':'generated_style.png','source_sha256':hashlib.sha256((D/'generated_style.png').read_bytes()).hexdigest(),'user_accepted_base_gait':True,'new_style_review_pending':True}
recipe['source_art']['generated_style.png']=recipe['surface_style']['source_sha256']
(D/'recipe.json').write_text(json.dumps(recipe,indent=2,ensure_ascii=False),encoding='utf-8')
(D/'style_checks.json').write_text(json.dumps({'records':records,'compression':checks['compression'],'all_14_connected':True,'native_timing_ticks':recipe['run_ticks']},indent=2),encoding='utf-8')
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16);board=Image.new('RGBA',(7*256,2*308),(42,45,54,255));animated=[]
for i,n in enumerate(range(7,21)):
    tile=rgba(worlds[n]);board.alpha_composite(tile.resize((256,288),Image.Resampling.NEAREST),(i%7*256,i//7*308+20));ImageDraw.Draw(board).text((i%7*256+5,i//7*308),str(n),font=font,fill='white')
    canvas=Image.new('RGBA',(840,325),(42,45,54,255));d=ImageDraw.Draw(canvas)
    for x,label,t in [(0,'기본 자세',Image.open(master).convert('RGBA')),(280,'수정 전',rgba(oldworlds[n])),(560,'수정 후',tile)]:
        d.text((x+8,5),label,font=font,fill='white')
        if x==0:
            base=Image.new('RGBA',(64,72));base.alpha_composite(t,(8,16));t=base
        canvas.alpha_composite(t.resize((256,288),Image.Resampling.NEAREST),(x+8,30))
    animated.append(canvas.convert('RGB'))
board.save(D/'native_review.png');animated[0].save(D/'comparison.png')
animated[0].save(D/'style_comparison.gif',save_all=True,append_images=animated[1:],duration=[round(t/60*1000) for t in recipe['run_ticks']],loop=0,disposal=2)
print(json.dumps({'records':records,'compression_max':max(c['encoded_bytes'] for c in checks['compression'])}))
