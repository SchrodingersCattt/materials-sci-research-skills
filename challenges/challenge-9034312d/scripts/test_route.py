import copy,json,pathlib,tempfile,unittest,xml.etree.ElementTree as ET
from route_svg import generate
p=pathlib.Path(__file__).parent.parent/'examples/synthetic-plan.json';base=json.loads(p.read_text())
class T(unittest.TestCase):
 def setUp(self):self.t=tempfile.TemporaryDirectory();self.out=pathlib.Path(self.t.name)/'out';self.plan=copy.deepcopy(base)
 def tearDown(self):self.t.cleanup()
 def go(self):return generate(self.plan,self.out)
 def test_valid_editable_svg(self):
  r=self.go();self.assertEqual(r['status'],'generated_requires_visual_and_scientific_review');root=ET.parse(self.out/'route.svg').getroot();ids={x.get('id') for x in root.iter()};self.assertTrue({'sample','analysis','report','flow','data'}<=ids);self.assertTrue((self.out/'route-source.py').is_file())
 def test_duplicate_node(self):
  self.plan['nodes'].append(copy.deepcopy(self.plan['nodes'][0]));self.assertRaises(ValueError,self.go)
 def test_overlap(self):
  self.plan['nodes'][1]['x']=100;self.assertRaises(ValueError,self.go)
 def test_outside_canvas(self):
  self.plan['nodes'][0]['x']=-1;self.assertRaises(ValueError,self.go)
 def test_bad_font(self):
  self.plan['font_size']=100;self.assertRaises(ValueError,self.go)
 def test_label_overflow_estimate(self):
  self.plan['nodes'][0]['label']='W'*35;self.assertRaises(ValueError,self.go)
 def test_missing_node_evidence(self):
  self.plan['nodes'][0]['evidence']=[];self.assertRaises(ValueError,self.go)
 def test_bad_edge_target(self):
  self.plan['edges'][0]['target']='missing';self.assertRaises(ValueError,self.go)
 def test_reverse_direction(self):
  self.plan['edges'][0]['points'].reverse();self.assertRaises(ValueError,self.go)
 def test_diagonal_rejected(self):
  self.plan['edges'][0]['points']=[[200,100],[250,110],[310,100]];self.assertRaises(ValueError,self.go)
 def test_crossing_other_node(self):
  self.plan['nodes'].append({'id':'block','label':'Block','x':230,'y':70,'w':50,'h':60,'evidence':[{'source':'synthetic','locator':'p'}]});self.assertRaises(ValueError,self.go)
 def test_missing_legend(self):
  del self.plan['legend'];self.assertRaises(ValueError,self.go)
 def test_legend_overlaps_node(self):
  self.plan['legend']['y']=80;self.assertRaises(ValueError,self.go)
 def test_bad_edge_kind(self):
  self.plan['edges'][0]['kind']='unknown';self.assertRaises(ValueError,self.go)
 def test_missing_edge_evidence(self):
  self.plan['edges'][0]['evidence']=[];self.assertRaises(ValueError,self.go)
 def test_duplicate_edge(self):
  self.plan['edges'].append(copy.deepcopy(self.plan['edges'][0]));self.assertRaises(ValueError,self.go)
 def test_existing_output(self):
  self.out.mkdir();self.assertRaises(ValueError,self.go)
 def test_explicit_edge_label_rendered(self):
  self.plan['edges'][0].update(label='flow',label_x=255,label_y=80);self.go();root=ET.parse(self.out/'route.svg').getroot();self.assertIn('flow',[x.text for x in root.iter()])
 def test_edge_label_missing_position(self):
  self.plan['edges'][0]['label']='flow';self.plan['edges'][0].pop('label_x');self.assertRaises(ValueError,self.go)
 def test_edge_label_overlaps_node(self):
  self.plan['edges'][0].update(label='flow',label_x=100,label_y=100);self.assertRaises(ValueError,self.go)
if __name__=='__main__':unittest.main()
