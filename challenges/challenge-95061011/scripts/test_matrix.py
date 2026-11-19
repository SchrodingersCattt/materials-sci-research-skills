import copy,json,pathlib,unittest
from check_matrix import check
p=pathlib.Path(__file__).parent.parent/'examples';t=json.loads((p/'targets.json').read_text());s=json.loads((p/'sources.json').read_text());r=json.loads((p/'results.json').read_text())
class T(unittest.TestCase):
 def test_equal_context_still_requires_scientific_review(self):
  e,c=check(t,s,r);self.assertEqual(e,[]);self.assertEqual(c[0]['status'],'comparable_subject_to_scientific_review');self.assertEqual(c[0]['difference_second_minus_first'],'5')
 def test_pollutant_mismatch_never_synthesized(self):
  e,c=check(t,s,r);self.assertIn('pollutant',c[1]['differing_context']);self.assertNotIn('difference_second_minus_first',c[1])
 def test_missing_context_not_comparable(self):
  x=copy.deepcopy(r);del x['records'][0]['context']['budget'];e,c=check(t,s,x);self.assertIn('budget',c[0]['missing_context']);self.assertNotIn('difference_second_minus_first',c[0])
 def test_wrong_source_blocks_all_arithmetic(self):
  x=copy.deepcopy(r);x['records'][0]['evidence'][0]['document_id']='B';e,c=check(t,s,x);self.assertTrue(e);self.assertTrue(all(q['status']=='blocked_by_validation_error' for q in c));self.assertTrue(all('difference_second_minus_first' not in q for q in c))
 def test_wrong_quote(self):
  x=copy.deepcopy(r);x['records'][0]['evidence'][0]['quote']='invented';self.assertTrue(check(t,s,x)[0])
 def test_wrong_value(self):
  x=copy.deepcopy(r);x['records'][0]['value']=999;self.assertTrue(check(t,s,x)[0])
 def test_missing_cell(self):
  x=copy.deepcopy(r);x['records'].pop();self.assertTrue(check(t,s,x)[0])
 def test_duplicate_cell(self):
  x=copy.deepcopy(r);x['records'].append(copy.deepcopy(x['records'][0]));self.assertTrue(check(t,s,x)[0])
 def test_not_reported_is_not_zero(self):
  x=copy.deepcopy(r);x['records'][0].update(status='not_reported',value=0,reason='missing');self.assertTrue(check(t,s,x)[0])
 def test_reported_requires_value(self):
  x=copy.deepcopy(r);x['records'][0]['value']=None;self.assertTrue(check(t,s,x)[0])
 def test_unit_mismatch(self):
  x=copy.deepcopy(r);x['records'][1]['context']['unit']='mg/L';e,c=check(t,s,x);self.assertIn('unit',c[0]['differing_context']);self.assertNotIn('difference_second_minus_first',c[0])
 def test_missing_budget(self):
  x=copy.deepcopy(r);x['records'][1]['context']['budget']='';e,c=check(t,s,x);self.assertIn('budget',c[0]['missing_context'])
 def test_conflict_without_two_quotes(self):
  x=copy.deepcopy(r);x['records'][0]['status']='source_conflict';self.assertTrue(check(t,s,x)[0])
if __name__=='__main__':unittest.main()
