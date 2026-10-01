import copy
import importlib.util
import json
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('static_build',ROOT/'scripts/build_static_site.py')
builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)

def test_public_snapshots_have_separate_complete_denominators():
    v2=json.loads((ROOT/'public-site/report.json').read_text())
    v1=json.loads((ROOT/'public-site/report-v1.json').read_text())
    builder.validate_report(v1);builder.validate_report(v2)
    assert len(v1['cases'])==72
    assert sum(r['mode']=='protocol' for r in v2['cases'])==48
    assert sum(r['mode']=='model' for r in v2['cases'])==144
    for material,passed in {'AA':23,'AB':35,'BA':36,'BB':36}.items():
        rows=[r for r in v2['cases'] if r['material']==material and r['mode']=='model']
        assert len(rows)==36 and sum(r['passed'] for r in rows)==passed
    assert sum(r['mode']=='model' and not r['responder'] for r in v2['cases'])==1

@pytest.mark.parametrize('change',[{'cost_upper_cny':float('nan')},{'cost_upper_cny':float('inf')},{'condition':'missing'},{'private_note':'hidden'}])
def test_public_case_rejects_invalid_values(change):
    report=json.loads((ROOT/'public-site/report.json').read_text())
    report=copy.deepcopy(report);report['cases'][0].update(change)
    with pytest.raises(ValueError):builder.validate_report(report)
