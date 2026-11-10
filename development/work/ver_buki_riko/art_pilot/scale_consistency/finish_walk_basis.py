from pathlib import Path
P=Path(__file__).parent
exec((P/'fit_walk_basis.py').read_text(encoding='utf-8').split('s,hl=normalize(Image.open')[0])
worlds={int(k):v.copy() for k,v in np.load(D/'worlds_probe.npz').items()};registration=json.loads((D/'fit_registration.json').read_text());positions=registration['head_positions'];layout=json.loads((D/'cloth_layout.json').read_text())
im=np.array(Image.open(D/'generated_cloth.png').convert('RGBA').resize((96,120),Image.Resampling.NEAREST));m=im[:,:,3]>=180;rgb=im[:,:,:3].astype(np.int32);indices=np.zeros(m.shape,dtype=np.uint8);indices[m]=np.argmin(((rgb[m,None]-colors[None])**2).sum(2),1)+1
local=[]
for rec in layout:
    n=rec['frame'];key=rec['cell'];x0,y0,x1,y1=rec['rect'];ax,ay=rec['anchor'];cell=indices[key//3*40:(key//3+1)*40,key%3*32:(key%3+1)*32];old=worlds[n].copy();safe=geometry[n][2];choices=[]
    if n==27:safe=np.logical_and.reduce([geometry[k][2] for k in range(27,33)])
    if n==33 and rec['kind']=='left_boot':y0-=1;ay-=1
    for dx in range(-5,3):
        for dy in range(-2,3):
            proposal=old.copy();sub=proposal[64+y0:64+y1,64+x0:64+x1];patch=cell[ay-dy:ay-dy+y1-y0,ax-dx:ax-dx+x1-x0]
            if patch.shape!=sub.shape:continue
            original=sub.copy();skin=np.isin(original,[4,5,8,9,11,13,14]);sub[:]=patch;sub[skin]=original[skin]
            hx,hy=positions[str(n)];hs=proposal[64+hy:64+hy+19,64+hx:64+hx+23];hs[hm]=head[hm]
            bad=int(((proposal!=0)&~safe).sum());edge=int((sub[:2]!=original[:2]).sum());islands=component(proposal!=0)
            cost=bad*1000+sum(len(g) for g in islands[1:])*200+edge*3+abs(dx)*4+abs(dy)*5
            choices.append((cost,bad,dx,dy,proposal))
    _,bad,dx,dy,worlds[n]=min(choices,key=lambda t:t[0]);local.append({**rec,'registration':[dx,dy],'remaining_outside_frame':bad})
cleanup=[]
for g in component(worlds[27]!=0)[1:]:
    assert len(g)==1
    for y,x in g:
        assert [int(x-64),int(y-64),int(worlds[27][y,x])]==[23,-23,5]
        cleanup.append([int(x-64),int(y-64),int(worlds[27][y,x])]);worlds[27][y,x]=0
for source,targets in [(22,[23]),(25,[26]),(27,[28,29,30,31,32])]:
    for n in targets:worlds[n]=worlds[source].copy()
high=worlds[147];low=high.copy();low[:80,:]=0;low[1:80,:]=high[:79,:]
# At the lower shin, keep the boots grounded. Torso and pelvis are a rigid unit.
for n in [0,1,2,146]:worlds[n]=low.copy()
blink=high.copy();old_eye=np.array(Image.open(B/'idle_147.png'));blink_eye=np.array(Image.open(B/'idle_148.png'));ys,xs=np.nonzero(old_eye!=blink_eye);hx,hy=positions['147'] if '147' in positions else registration['records'][0]['head_world']
for yy,xx in zip(ys,xs):blink[64+hy+int(yy),64+hx+int(xx)-12]=blink_eye[yy,xx]
worlds[148]=blink;worlds[5]=high.copy();worlds[6]=high.copy();positions['5']=[hx,hy];positions['6']=[hx,hy]
checks=[];fail=[];frames={}
for n,w in sorted(worlds.items()):
    size,b,safe=geometry[n];outside=np.argwhere((w!=0)&~safe);components=component(w!=0);r={'frame':n,'outside':len(outside),'components':[len(g) for g in components],'opaque_pixels':int((w!=0).sum())}
    if len(outside):r['outside_world']=[[int(x-64),int(y-64)] for y,x in outside];fail.append(r)
    if len(components)!=1:fail.append(r)
    checks.append(r);a=w[64+b[1]:64+b[3],64+b[0]:64+b[2]];frames[n]=(a.tobytes(),size);save_image(*frames[n],words,D/f'{"idle" if n in [0,1,2,146,147,148] else "frame"}_{n:03d}.png')
for n in range(7,21):
    # Preserve the user's accepted walk bit-for-bit, including PNG encoding.
    shutil.copyfile(B/f'frame_{n:03d}.png',D/f'frame_{n:03d}.png')
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16)
def rgba(w):
    a=w[20:100,28:100];m=a!=0;r=np.zeros((80,72,4),dtype=np.uint8);r[m,:3]=colors[a[m]-1];r[m,3]=255;return Image.fromarray(r)
nums=[147,7,11,14,21,22,24,25,27,33,34,3,4,0];board=Image.new('RGBA',(5*288,3*340),(42,45,54,255));draw=ImageDraw.Draw(board)
for i,n in enumerate(nums):board.alpha_composite(rgba(worlds[n]).resize((288,320),Image.Resampling.NEAREST),(i%5*288,i//5*340+20));draw.text((i%5*288+4,i//5*340),str(n),font=font,fill='white')
board.save(D/'final_review.png');np.savez(D/'worlds_final.npz',**{str(n):w for n,w in worlds.items()})
print('FAIL',json.dumps(fail));print('LOCAL',json.dumps(local))
(D/'final_fit_checks.json').write_text(json.dumps({'checks':checks,'failures':fail,'local_generated_edits':local,'cape_27_detached_cleanup':cleanup},indent=2))
if fail:raise SystemExit(1)
_,patch_checks=patch_frames(arc,gmeta,gfx,parts,frames,pal)
recipe['frames']={str(n):{'file':f'frame_{n:03d}.png','sha256':hashlib.sha256((D/f'frame_{n:03d}.png').read_bytes()).hexdigest()} for n in range(3,35)}
recipe['body_standard']['head_world_positions']={str(n):positions[str(n)] for n in range(3,35)}
recipe['walk_design_basis']={'source_build':str(B),'walk_preserved_frames':list(range(7,21)),'uniform_source_scales':registration['scales'],'local_edits':'final_fit_checks.json','all_anatomical_lengths_exactly_proven':False,'user_review_pending':True}
recipe['source_art'].update({name:hashlib.sha256((D/name).read_bytes()).hexdigest() for name in ['generated_idle.png','generated_motion.png','generated_cloth.png']})
(D/'recipe.json').write_text(json.dumps(recipe,indent=2,ensure_ascii=False),encoding='utf-8')
revision={'base_reference_sha256':hashlib.sha256(master.read_bytes()).hexdigest(),'file':'idle_147.png','sha256':hashlib.sha256((D/'idle_147.png').read_bytes()).hexdigest(),'head_native_position':[hx+24,hy+24],'palette_sha256':hashlib.sha256(pal).hexdigest(),'authorization':'docs/DECISIONS.md: 2026-10-24 walking design as basis','final_style_user_approved':False}
(D/'idle_revision.json').write_text(json.dumps(revision,indent=2),encoding='utf-8')
print('COMPRESSION',max(c['encoded_bytes'] for c in patch_checks['compression']))
