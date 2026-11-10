import unittest,struct
import numpy as np
from src.psx_xa_audio import encode_groups,decode_groups,replace_audio_groups,validate_audio_sector
from src.psx_sector import edc

class XaAudioTests(unittest.TestCase):
    def sector(self):
        s=bytearray(2352);s[:12]=b'\0'+b'\xff'*10+b'\0';s[15]=2
        s[16:24]=bytes([1,0,0x64,1])*2
        return bytes(s)
    def test_zero_and_stereo_channel_isolation(self):
        pcm=np.zeros((2016,2),np.int16);pcm[:,0]=np.rint(np.sin(np.arange(2016)*.13)*18000)
        data,_=encode_groups(pcm);restored,_=decode_groups(data)
        self.assertTrue(np.all(restored[:,1]==0))
        self.assertLess(np.sqrt(np.mean((restored[:,0].astype(float)-pcm[:,0])**2)),650)
    def test_history_survives_group_boundaries(self):
        pcm=np.zeros((224,2),np.int16);pcm[:,0]=np.rint(np.sin(np.arange(224)*.09)*22000);pcm[:,1]=pcm[:,0]//2
        data,_=encode_groups(pcm)
        full,_=decode_groups(data);a,h=decode_groups(data[:128]);b,_=decode_groups(data[128:],h)
        self.assertTrue(np.array_equal(full,np.vstack((a,b))))
    def test_same_size_sector_and_edc(self):
        original=self.sector();data,_=encode_groups(np.full((2016,2),500,np.int16))
        changed=replace_audio_groups(original,data)
        validate_audio_sector(changed,allow_absent_edc=False)
        self.assertEqual(changed[:24],original[:24]);self.assertEqual(changed[2328:2348],original[2328:2348])
        self.assertEqual(len(changed),2352)
        corrupt=bytearray(changed);corrupt[35]^=1
        with self.assertRaises(ValueError):validate_audio_sector(corrupt)
    def test_reject_unsupported_inputs(self):
        for pcm in [np.zeros(112),np.zeros((113,2)),np.ones((112,2))*float('nan'),np.ones((112,2))*40000]:
            with self.assertRaises(ValueError):encode_groups(pcm)
        for index,value in [(17,1),(19,5),(18,8)]:
            bad=bytearray(self.sector());bad[index]=value;bad[index+4]=value
            with self.assertRaises(ValueError):validate_audio_sector(bad)
        with self.assertRaises(ValueError):replace_audio_groups(self.sector(),bytes(128))
        bad=bytearray(128);bad[4]=0x40
        with self.assertRaises(ValueError):decode_groups(bad)

if __name__=='__main__':unittest.main()
