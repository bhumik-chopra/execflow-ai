"""Idempotent assignment fixture import, with no AI dependency."""
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from config import get_settings
from database import MongoDB
from schemas.domain import SourceInput, Observation, Task
from services.repository import Repository, stable_id

def current_demo_fixture(fixture, today=None):
    # Keep weekday relationships intact and make all demo evidence available now.
    today = today or datetime.now()
    reference = (today - timedelta(days=(today.weekday() - 4) % 7)).replace(hour=9, minute=0, second=0, microsecond=0)
    original = datetime(2026, 9, 25, 9)
    offset = reference - original
    start = reference - timedelta(days=4)
    def shift(value):
        if isinstance(value, list):
            return [shift(item) for item in value]
        if isinstance(value, dict):
            return {key: shift(item) for key, item in value.items()}
        if not isinstance(value, str):
            return value
        value = value.replace('21-25 September 2026', f'{start.day} {start:%B} - {reference.day} {reference:%B %Y}')
        value = re.sub(r'\b(2[1-5]) September\b', lambda m: (datetime(2026, 9, int(m[1])) + offset).strftime('%d %B').lstrip('0'), value)
        return re.sub(r'\b2026-09-\d{2}(?!\d)', lambda m: (datetime.fromisoformat(m[0]) + offset).strftime('%Y-%m-%d'), value)
    return shift(fixture), reference

def run():
    fixture=json.loads(Path(__file__).with_name('processed_assignment_fixture.json').read_text(encoding='utf-8'))
    fixture, reference = current_demo_fixture(fixture)
    connection=MongoDB(get_settings())
    try:
        repo=Repository(connection)
        before=repo.counts()
        demo_ids=[s['source_id'] for s in fixture['sources']]
        fixture_obs={o['observation_id'] for o in fixture['observations']}
        stale=[o for o in repo.find('observations', {'source_id': {'$in': demo_ids}}) if o['observation_id'] not in fixture_obs]
        for o in stale:
            repo.db.observations.delete_one({'observation_id':o['observation_id']})
        for tid in {o.get('task_id') for o in stale} - {None}:
            if repo.db.observations.count_documents({'task_id':tid}) == 0:
                repo.db.tasks.delete_one({'task_id':tid})
        for record in fixture['sources']:
            validated=SourceInput.model_validate({k:v for k,v in record.items() if k in SourceInput.model_fields}).model_dump()
            fingerprint = stable_id('source', {k:v for k,v in validated.items() if k != 'source_id'})
            repo.save('sources','source_id',{**record,**validated,'fingerprint':fingerprint,'created_at':datetime.fromisoformat(record['created_at'])})
        for record in fixture['observations']:
            repo.save('observations','observation_id',Observation.model_validate(record).model_dump())
        for record in fixture['tasks']:
            repo.save('tasks','task_id',Task.model_validate(record).model_dump())
        repo.audit('ASSIGNMENT_SEEDED','assignment-1',{'sources':len(fixture['sources']),'tasks':len(fixture['tasks'])},reference)
        print(json.dumps({'demo_reference':reference.isoformat(),'before':before,'after':repo.counts()}))
    finally:
        connection.close()
if __name__=='__main__': run()
