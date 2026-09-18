from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Request
from schemas.domain import SourceInput, ChatInput, Classification, Status
from schemas.system import DEFAULT_AS_OF

router = APIRouter(prefix='/api', tags=['executive'])

@router.post('/sources')
async def create_source(source: SourceInput, request: Request, as_of: datetime = DEFAULT_AS_OF):
    return await request.app.state.engine.ingest(source, as_of)

@router.get('/sources')
async def sources(request: Request, limit: int = Query(200, ge=1, le=1000)):
    return await request.app.state.engine.call('find', 'sources', {}, limit)

@router.post('/sources/{source_id}/process')
async def process_source(source_id: str, request: Request, as_of: datetime = DEFAULT_AS_OF):
    record = await request.app.state.engine.call('one', 'sources', 'source_id', source_id)
    if not record:
        raise HTTPException(404, 'Source not found.')
    source = SourceInput.model_validate({key: value for key, value in record.items() if key in SourceInput.model_fields})
    return await request.app.state.engine.ingest(source, as_of)

@router.get('/sources/{source_id}')
async def source(source_id: str, request: Request):
    record = await request.app.state.engine.call('one', 'sources', 'source_id', source_id)
    if not record:
        raise HTTPException(404, 'Source not found.')
    record['observations'] = await request.app.state.engine.call('find', 'observations', {'source_id': source_id})
    return record

@router.get('/tasks')
async def tasks(request: Request, as_of: datetime = DEFAULT_AS_OF, classification: Classification | None = None, status: Status | None = None, owner: str | None = None):
    result = await request.app.state.engine.tasks(as_of)
    return [t for t in result if (classification is None or t['classification'] == classification) and (status is None or t['status'] == status) and (owner is None or (t['owner'] or '').casefold() == owner.casefold())]

@router.get('/tasks/{task_id}')
async def task(task_id: str, request: Request, as_of: datetime = DEFAULT_AS_OF):
    result = next((t for t in await request.app.state.engine.tasks(as_of) if t['task_id'] == task_id), None)
    if not result:
        raise HTTPException(404, 'Task not found at this reference time.')
    return result

@router.get('/brief')
async def brief(request: Request, as_of: datetime = DEFAULT_AS_OF):
    return await request.app.state.engine.brief(as_of)

@router.get('/conflicts')
async def conflicts(request: Request, as_of: datetime = DEFAULT_AS_OF):
    return {'as_of': as_of, 'conflicts': await request.app.state.engine.conflicts(as_of)}

@router.get('/audit')
async def audit(request: Request, limit: int = Query(200, ge=1, le=1000)):
    records = await request.app.state.engine.call('find', 'audit_logs')
    return sorted(records, key=lambda e: e['created_at'], reverse=True)[:limit]

@router.post('/chat')
async def chat(body: ChatInput, request: Request):
    return await request.app.state.engine.chat(body)
