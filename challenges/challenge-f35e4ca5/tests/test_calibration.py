import importlib.util,tempfile,unittest,json,csv,struct,zlib
from pathlib import Path
s=importlib.util.spec_from_file_location("figure",Path(__file__).parents[1]/"scripts/figure_tool.py")
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def axis(scale="linear"):
 return {"pixel0":0,"pixel1":10,"value0":1 if scale=="log" else 0,"value1":100 if scale=="log" else 10,"scale":scale,"unit":"a.u.","evidence":"synthetic axis"}
def png(path):
 def chunk(t,b):return struct.pack(">I",len(b))+t+b+struct.pack(">I",zlib.crc32(t+b)&0xffffffff)
 raw=b"".join(b"\x00"+bytes([255,0,0])*11 for _ in range(11))
 path.write_bytes(b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",struct.pack(">2I5B",11,11,8,2,0,0,0))+chunk(b"IDAT",zlib.compress(raw))+chunk(b"IEND",b""))
class Checks(unittest.TestCase):
 def test_linear(self):self.assertEqual(m.value_at(5,axis()),5)
 def test_log(self):self.assertAlmostEqual(m.value_at(5,axis("log")),10)
 def test_reverse(self):
  a=axis();a["pixel0"],a["pixel1"]=10,0;self.assertEqual(m.value_at(2,a),8)
 def test_identical_values(self):
  a=axis();a["value1"]=a["value0"]
  with self.assertRaises(ValueError):m.value_at(5,a)
 def test_negative_log(self):
  a=axis("log");a["value0"]=-1
  with self.assertRaises(ValueError):m.value_at(5,a)
 def test_independent_scale(self):
  a=axis("log");a["check_ticks"]=[{"pixel":5,"value":10}]
  self.assertTrue(m.calibration_check(a)["independently_checked"])
 def test_wrong_scale(self):
  a=axis();a["value1"]=100;a["check_ticks"]=[{"pixel":5,"value":10}]
  with self.assertRaises(ValueError):m.calibration_check(a)
 def test_no_check_tick(self):self.assertFalse(m.calibration_check(axis())["independently_checked"])
 def test_asymmetric(self):
  low,high=m.reading_interval(5,axis("log"),1);self.assertGreater(high-10,10-low)
 def test_outside(self):
  with self.assertRaises(ValueError):m.reading_interval(20,axis(),1)
 def test_bad_uncertainty(self):
  with self.assertRaises(ValueError):m.reading_interval(5,axis(),float("nan"))
 def test_pixels_and_reference(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);png(root/"test.png")
   config={"image":"test.png","axes":{"x":axis(),"y":axis("log")},"points":[{"label":"series A","role":"data","x":5,"y":5,"pixel_radius":1},{"label":"legend","role":"reference","x":10,"y":10}]}
   out=m.digitize(root,config,root/"out")
   self.assertEqual(out["points"][0]["rgb"],[255,0,0])
   self.assertAlmostEqual(out["points"][0]["y_value"],10)
   self.assertIsNone(out["points"][1]["y_value"]);self.assertIsNone(out["points"][1]["reading_interval_y"])
   self.assertTrue((root/"out/digitized_points.csv").is_file())
 def test_table_blanks(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/"table.csv").write_text("sample,value\nA,\nB,0\n",encoding="utf-8")
   m.tables(root,root/"out");r=json.loads((root/"out/table_inventory.json").read_text(encoding="utf-8"))
   self.assertEqual(r[0]["rows"][1][1],"");self.assertEqual(r[0]["rows"][2][1],"0")
if __name__=="__main__":unittest.main()
