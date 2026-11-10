"""Grow the head record bank only into verified unreferenced body-bank slack."""
import struct,hashlib
from src.psx_player import bank_offsets,composition_frame
from scripts.prepare_shibuki_ultimate_production import records
def grow_head(c,amount):
 assert amount>0 and amount%4==0
 starts=bank_offsets(c);lo,hi=starts[6:8]
 count=composition_frame(c,6,0)['bank_frame_count']
 used=lo+count*4
 for n in range(count):
  word=struct.unpack_from('<I',c,lo+n*4)[0]
  used=max(used,lo+(word>>16)*4+(word&65535)*4)
 assert used<=hi-amount,('Referenced body records would be removed',used,hi,amount)
 original={(pb,n):records(c,pb,n)for pb in range(len(starts))for n in range(composition_frame(c,pb,0)['bank_frame_count'])}
 out=bytearray(c)
 out[lo+amount:hi]=c[lo:hi-amount]
 struct.pack_into('<I',out,6*4,lo+amount)
 after=bank_offsets(out);assert after[:6]==starts[:6]and after[7:]==starts[7:]
 for (pb,n),v in original.items():assert records(out,pb,n)==v,(pb,n)
 assert len(c)==len(out)
 return bytes(out),{'head_bank_extra_bytes':amount,'body_bank_before':[lo,hi],'body_bank_after':[lo+amount,hi],'body_last_referenced_byte':used,'consumed_unreferenced_tail_sha256':hashlib.sha256(c[hi-amount:hi]).hexdigest(),'consumed_tail_nonzero_bytes':sum(x!=0 for x in c[hi-amount:hi]),'all_native_record_sequences_before_art_edits_identical':True,'only_directory_bank6_changed':True,'other_bank_absolute_positions_preserved':True,'entry_length_preserved':True}
