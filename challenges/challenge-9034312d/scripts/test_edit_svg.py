import copy,hashlib,pathlib,tempfile,unittest,xml.etree.ElementTree as ET
from edit_svg import edit
class T(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.d=pathlib.Path(self.tmp.name);self.src=self.d/'source.svg';self.raw=b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect id="bar" x="10" y="20" width="20" height="30" fill="#006D77"/><text id="label" x="10" y="70">Old</text><text id="untouched" x="20" y="90">Keep</text></svg>';self.src.write_bytes(self.raw);self.plan={'source_sha256':hashlib.sha256(self.raw).hexdigest(),'edits':[{'id':'label','kind':'text','old':'Old','new':'New','workorder_id':'W1','reason':'Synthetic label change.'},{'id':'bar','kind':'fill','old':'#006D77','new':'#D1495B','workorder_id':'W2','reason':'Synthetic styling change.'}]}
 def tearDown(self):self.tmp.cleanup()
 def go(self):return edit(self.src,self.plan,self.d/'out')
 def test_real_edit_preserves_other_structure_and_source(self):
  r=self.go();self.assertEqual(r['status'],'edited_requires_visual_and_scientific_review');d=ET.parse(self.d/'out/edited.svg').getroot();byid={x.get('id'):x for x in d.iter() if x.get('id')};self.assertEqual(byid['label'].text,'New');self.assertEqual(byid['bar'].get('fill'),'#D1495B');self.assertEqual(byid['untouched'].text,'Keep');self.assertEqual(self.src.read_bytes(),self.raw)
 def test_stale_hash(self):
  self.plan['source_sha256']='bad'
  with self.assertRaises(ValueError):self.go()
 def test_wrong_target(self):
  self.plan['edits'][0]['id']='absent'
  with self.assertRaises(ValueError):self.go()
 def test_duplicate_target(self):
  self.plan['edits'].append(copy.deepcopy(self.plan['edits'][0]))
  with self.assertRaises(ValueError):self.go()
 def test_wrong_old(self):
  self.plan['edits'][0]['old']='wrong'
  with self.assertRaises(ValueError):self.go()
 def test_invalid_fill(self):
  self.plan['edits'][1]['new']='url(http://example.com)'
  with self.assertRaises(ValueError):self.go()
 def test_missing_reason(self):
  self.plan['edits'][0]['reason']=''
  with self.assertRaises(ValueError):self.go()
 def test_unknown_kind(self):
  self.plan['edits'][0]['kind']='transform'
  with self.assertRaises(ValueError):self.go()
 def test_noop(self):
  self.plan['edits'][0]['new']='Old'
  with self.assertRaises(ValueError):self.go()
 def test_existing_output(self):
  (self.d/'out').mkdir()
  with self.assertRaises(ValueError):self.go()
 def test_nested_text_rejected(self):
  raw=self.raw.replace(b'>Old</text>',b'><tspan>Old</tspan></text>');self.src.write_bytes(raw);self.plan['source_sha256']=hashlib.sha256(raw).hexdigest()
  with self.assertRaises(ValueError):self.go()
if __name__=='__main__':unittest.main()
