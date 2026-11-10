"""Resolve original capture indices through lossless WebP merged-frame timing."""
from pathlib import Path
import argparse,bisect,json,math,hashlib
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def decode_mapping(play):
 rec=json.loads((play/'evidence.json').read_text('utf8'));times=rec['capture_times']
 durations=[max(1,round((b-a)*1000))for a,b in zip(times,times[1:])]+[100]
 starts=[];total=0
 for d in durations:starts.append(total);total+=d
 im=Image.open(play/'play.webp');encoded=[]
 for i in range(im.n_frames):
  im.seek(i);im.load();encoded.append({'frame':i,'timestamp':im.info['timestamp'],'duration':im.info['duration']})
 assert encoded[0]['timestamp']==0 and encoded[-1]['timestamp']+encoded[-1]['duration']==total
 assert all(a['timestamp']+a['duration']==b['timestamp']for a,b in zip(encoded,encoded[1:]))
 es=[e['timestamp']for e in encoded];mapping=[]
 for i,t in enumerate(starts):
  j=bisect.bisect_right(es,t)-1;e=encoded[j]
  assert e['timestamp']<=t and t+durations[i]<=e['timestamp']+e['duration']
  mapping.append(j)
 assert set(mapping)==set(range(im.n_frames))
 return rec,im,{'recorded_frames':len(times),'encoded_frames':im.n_frames,'total_duration_ms':total,'encoded_intervals':encoded,'capture_to_encoded_frame':mapping,'all_capture_intervals_contained':True}
def main():
 p=argparse.ArgumentParser();p.add_argument('--name',required=True);p.add_argument('--groups',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 play=R/(a.name+'_play');rec,im,mapping=decode_mapping(play);out=a.output.resolve();assert out.is_relative_to(R.resolve())and not out.exists();out.mkdir()
 groups=json.loads(a.groups.read_text('utf8'));pages=[]
 for label,g in groups.items():
  lo,hi=g['range'];box=tuple(g['crop']);cw,ch=box[2]-box[0],box[3]-box[1]
  ids=[i for i,t in enumerate(rec['capture_times'])if lo<=t<=hi]
  for part,start in enumerate(range(0,len(ids),12)):
   selected=ids[start:start+12];board=Image.new('RGB',(cw*4,(ch+24)*math.ceil(len(selected)/4)),'#202630');draw=ImageDraw.Draw(board)
   for j,index in enumerate(selected):
    ei=mapping['capture_to_encoded_frame'][index];im.seek(ei);x,y=j%4*cw,j//4*(ch+24);board.paste(im.convert('RGB').crop(box),(x,y+24));draw.text((x+4,y+5),f'{label} capture#{index} / webp#{ei} {rec["capture_times"][index]:.3f}s',fill='white')
   f=out/f'{label}_{part:02}.png';board.save(f);pages.append({'path':f.as_posix(),'sha256':sha(f),'capture_indices':selected,'encoded_frame_indices':[mapping['capture_to_encoded_frame'][i]for i in selected],'crop':list(box)})
 result={'source':(play/'play.webp').as_posix(),'source_sha256':sha(play/'play.webp'),'capture_metadata_sha256':sha(play/'evidence.json'),'mapping':mapping,'pages':pages,'actual_window_crops':True,'sprite_pixels_edited':False,'resampled':False,'reason':'WebP encoder can merge identical captures. Map by verified accumulated integer-ms durations; never seek original capture index directly.'}
 (out/'manifest.json').write_text(json.dumps(result,indent=2)+'\n','utf8');print(json.dumps({'pages':len(pages),'recorded':mapping['recorded_frames'],'encoded':mapping['encoded_frames'],'mapping_valid':True}))
if __name__=='__main__':main()
