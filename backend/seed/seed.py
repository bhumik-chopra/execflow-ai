"""Idempotent assignment fixture import, with no AI dependency."""
import json
from pathlib import Path
from datetime import datetime
from config import get_settings
from database import MongoDB
from schemas.domain import SourceInput, Observation, Task
from services.repository import Repository

def run():
    fixture=json.loads(Path(__file__).with_name('processed_assignment_fixture.json').read_text(encoding='utf-8'))
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
            repo.save('sources','source_id',{**record,**validated,'created_at':datetime.fromisoformat(record['created_at'])})
        for record in fixture['observations']:
            repo.save('observations','observation_id',Observation.model_validate(record).model_dump())
        for record in fixture['tasks']:
            repo.save('tasks','task_id',Task.model_validate(record).model_dump())
        repo.audit('ASSIGNMENT_SEEDED','assignment-1',{'sources':len(fixture['sources']),'tasks':len(fixture['tasks'])},datetime(2026,9,25,9))
        print(json.dumps({'before':before,'after':repo.counts()}))
    finally:
        connection.close()
if __name__=='__main__': run()
