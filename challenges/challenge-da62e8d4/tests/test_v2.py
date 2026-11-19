import sys,tempfile,unittest,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import repro_tool as r
class Regression(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.b=Path(self.t.name);self.root=self.b/'input';self.root.mkdir();(self.root/'data.txt').write_text('original');(self.root/'a.py').write_text("from pathlib import Path;print(Path('data.txt').read_text());Path('data.txt').write_text('mutated')")
  self.work=self.b/'work';self.out=self.b/'out';self.plan=self.b/'plan.json'
 def tearDown(self):self.t.cleanup()
 def plan_runs(self,runs):self.plan.write_text(json.dumps({'runs':runs}));return r.run(self.root,self.work,self.out,self.plan)
 def test_runs_are_isolated(self):
  self.plan_runs([{'script':'a.py'},{'script':'a.py'}]);self.assertEqual((self.out/'run-logs/run-2.stdout.txt').read_text().strip(),'original')
 def test_invalid_later_run_no_execution(self):
  with self.assertRaises(ValueError):self.plan_runs([{'script':'a.py'},{'script':'missing.py'}])
  self.assertFalse((self.out/'run-logs/run-1.stdout.txt').exists())
 def test_previous_logs_not_overwritten(self):
  logs=self.out/'run-logs';logs.mkdir(parents=True);f=logs/'run-1.stdout.txt';f.write_text('prior evidence')
  with self.assertRaises(ValueError):self.plan_runs([{'script':'a.py'}])
  self.assertEqual(f.read_text(),'prior evidence')
if __name__=='__main__':unittest.main()
