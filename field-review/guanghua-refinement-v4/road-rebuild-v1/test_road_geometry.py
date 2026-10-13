import json,unittest
from pathlib import Path
from shapely.geometry import Polygon,LineString
from road_geometry import *

class GeneratorTests(unittest.TestCase):
    def check(self,p,z=lambda x,y:.1,components=1):
        v,f,p=triangulate(p,.4);r,_=topology(v,f,p)
        self.assertEqual(r['components'],components)
        for k in ['nonmanifold_edges','degenerate_or_reversed_faces','duplicate_faces','internal_open_edges']:self.assertEqual(r[k],0)
        self.assertLess(r['coverage_error_area'],1e-6);self.assertLess(abs(r['overlap_area']),1e-6)
        vv,ff=extrude([(x,y,z(x,y)) for x,y in v],f);solid=check_solid(vv,ff)
        self.assertEqual(solid['open_edges'],0);self.assertEqual(solid['nonmanifold_edges'],0);self.assertGreater(solid['signed_volume'],0)
        v2,f2,_=triangulate(p,.4);self.assertEqual(v,v2);self.assertEqual(f,f2)
    def test_straight(self):self.check(road_domain([(0,0),(5,0)],1.6))
    def test_bend(self):self.check(road_domain([(0,0),(3,0),(3,3)],1.6))
    def test_t_junction(self):self.check(S.union_all([road_domain([(-3,0),(3,0)],1.6),road_domain([(0,0),(0,3)],1.8)]))
    def test_y_junction(self):self.check(S.union_all([road_domain([(0,-3),(0,0)],1.6),road_domain([(-3,3),(0,0),(3,3)],1.6)]))
    def test_variable_width(self):self.check(road_domain([(0,0),(3,0),(6,0)],[1.2,2.4,1.8]))
    def test_island(self):self.check(Polygon([(0,0),(5,0),(5,5),(0,5)],holes=[[(2,2),(2,3),(3,3),(3,2)]]))
    def test_disconnected(self):
        es=[{'layer':'ground','nodes':['a','b'],'points':[(0,0),(5,0)],'width':1},{'layer':'ground','nodes':['c','d'],'points':[(0,1.1),(5,1.1)],'width':1}]
        self.assertEqual(len(network_domains(es)),2)
    def test_illegal_crossing(self):
        es=[{'layer':'ground','nodes':['a','b'],'points':[(-3,0),(3,0)],'width':1},{'layer':'ground','nodes':['c','d'],'points':[(0,-3),(0,3)],'width':1}]
        with self.assertRaises(ValueError):network_domains(es)
        es[1]['layer']='upper';self.assertEqual(len(network_domains(es)),2)
    def test_grade_and_landing(self):
        self.check(road_domain([(0,0),(5,0)],1.6),lambda x,y:profile(x,[(0,.1),(4,1.2),(5,1.2)]))
        self.assertEqual(profile(4.5,[(0,.1),(4,1.2),(5,1.2)]),1.2)
    def test_step_contact(self):
        self.check(road_domain([(0,0),(5,0)],1.8),lambda x,y:profile(x,[(0,1.75),(5,.095)]))
        self.assertEqual(profile(0,[(0,1.75),(5,.095)]),1.75)

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(GeneratorTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    Path(__file__).with_name('generator-tests.json').write_text(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'passed':result.wasSuccessful()},indent=2))
    raise SystemExit(0 if result.wasSuccessful() else 1)
