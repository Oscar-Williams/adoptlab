import copy
import json
from pathlib import Path
import pytest
from scripts.build_static_site import validate_upgrade


def test_upgrade_publication_rejects_mislabelled_or_incomparable_evidence():
    original=json.loads((Path(__file__).parents[1]/'public-site/workbench-evidence.json').read_text(encoding='utf-8'))
    validate_upgrade(original)
    changes=[('cohort','human_observed'),('status','failed'),('condition','a'*64),('task_hash','a'*64)]
    for field,value in changes:
        report=copy.deepcopy(original)
        report['cases'][0]['runs'][1][field]=value
        with pytest.raises(ValueError):validate_upgrade(report)
    report=copy.deepcopy(original)
    report['cases'][1]['runs'][0]['id']=report['cases'][0]['runs'][0]['id']
    with pytest.raises(ValueError):validate_upgrade(report)
    report=copy.deepcopy(original)
    report['cases'][0]['runs'][1]['material_hash']=report['cases'][0]['runs'][0]['material_hash']
    with pytest.raises(ValueError):validate_upgrade(report)
