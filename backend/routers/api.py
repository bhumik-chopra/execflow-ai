from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query, Request
from schemas.domain import SourceInput, ChatInput, Classification, Status, DatasetScope, reference_time

router = APIRouter(prefix='/api', tags=['executive'])

@router.post('/sources')
async def create_source(source: SourceInput, request: Request, as_of: datetime = Query(default_factory=datetime.now)):
    if source.metadata.get('dataset') == 'assignment-1' or (source.source_id or '').startswith('demo-'):
        raise HTTPException(422, 'Assignment sources are read-only. Add a source to My Sources instead.')
    return await request.app.state.engine.ingest(source, as_of)

@router.get('/sources')
async def sources(request: Request, scope: DatasetScope = 'assignment', limit: int = Query(200, ge=1, le=1000)):
    return await request.app.state.engine.call('find', 'sources', request.app.state.engine.source_filter(scope), limit)

@router.post('/sources/{source_id}/process')
async def process_source(source_id: str, request: Request, as_of: datetime = Query(default_factory=datetime.now)):
    record = await request.app.state.engine.call('one', 'sources', 'source_id', source_id)
    if not record:
        raise HTTPException(404, 'Source not found.')
    source = SourceInput.model_validate({key: value for key, value in record.items() if key in SourceInput.model_fields})
    if source.metadata.get('dataset') == 'assignment-1' or (source.source_id or '').startswith('demo-'):
        raise HTTPException(422, 'Assignment sources are read-only. Add a source to My Sources instead.')
    return await request.app.state.engine.ingest(source, as_of)

@router.get('/sources/{source_id}')
async def source(source_id: str, request: Request):
    record = await request.app.state.engine.call('one', 'sources', 'source_id', source_id)
    if not record:
        raise HTTPException(404, 'Source not found.')
    record['observations'] = await request.app.state.engine.call('find', 'observations', {'source_id': source_id})
    return record

@router.get('/tasks')
async def tasks(request: Request, scope: DatasetScope = 'assignment', as_of: datetime | None = None, classification: Classification | None = None, status: Status | None = None, owner: str | None = None):
    as_of = reference_time(as_of, scope)
    result = await request.app.state.engine.tasks(as_of, scope)
    return [t for t in result if (classification is None or t['classification'] == classification) and (status is None or t['status'] == status) and (owner is None or (t['owner'] or '').casefold() == owner.casefold())]

@router.get('/tasks/{task_id}')
async def task(task_id: str, request: Request, scope: DatasetScope = 'assignment', as_of: datetime | None = None):
    as_of = reference_time(as_of, scope)
    result = next((t for t in await request.app.state.engine.tasks(as_of, scope) if t['task_id'] == task_id), None)
    if not result:
        raise HTTPException(404, 'Task not found at this reference time.')
    return result

@router.get('/brief')
async def brief(request: Request, scope: DatasetScope = 'assignment', as_of: datetime | None = None):
    as_of = reference_time(as_of, scope)
    return await request.app.state.engine.brief(as_of, scope)

@router.get('/conflicts')
async def conflicts(request: Request, scope: DatasetScope = 'assignment', as_of: datetime | None = None):
    as_of = reference_time(as_of, scope)
    return {'as_of': as_of, 'conflicts': await request.app.state.engine.conflicts(as_of, scope)}

@router.get('/audit')
async def audit(request: Request, scope: DatasetScope = 'assignment', limit: int = Query(200, ge=1, le=1000)):
    records = await request.app.state.engine.call('find', 'audit_logs')
    engine = request.app.state.engine
    sources = await engine.call('find', 'sources', engine.source_filter(scope))
    source_ids = {s['source_id'] for s in sources}
    observations = await engine.call('find', 'observations', {'source_id': {'$in': list(source_ids)}})
    entity_ids = source_ids | {o.get('task_id') for o in observations}
    if scope == 'assignment':
        entity_ids.add('assignment-1')
    records = [r for r in records if r.get('entity_id') in entity_ids or r.get('details', {}).get('source_id') in source_ids or bool(source_ids & set(r.get('details', {}).get('source_ids', [])))]
    for record in records:
        # PyMongo returns naive UTC; identify it so browsers show local time.
        record['created_at'] = record['created_at'].replace(tzinfo=timezone.utc)
    return sorted(records, key=lambda e: e['created_at'], reverse=True)[:limit]

@router.post('/chat')
async def chat(body: ChatInput, request: Request):
    return await request.app.state.engine.chat(body)
