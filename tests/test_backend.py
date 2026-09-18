import asyncio
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock
import mongomock
import pytest
from schemas.domain import SourceInput
from services.dates import normalize_deadline
from services.engine import Engine, IngestionError, SourceConflict
from services.llm import LLMUnavailable
from services.repository import Repository
from services.state import resolve_task, calendar_conflicts
from seed.data import sources

AS_OF = datetime(2026, 9, 25, 9)

def run(awaitable):
    return asyncio.run(awaitable)

def engine():
    db = mongomock.MongoClient().test
    llm = SimpleNamespace(generate_json=AsyncMock())
    return Engine(Repository(SimpleNamespace(get_database=lambda: db)), llm, 'Arjun Malhotra')

def item(**kwargs):
    result = dict(type='COMMITMENT', kind='DELIVERY', actor='Arjun Malhotra', action='Send', object='proposal',
        counterparty='Kavita', owner='Arjun Malhotra', ownership_clear=True, deadline_text=None,
        completion_evidence=None, evidence_text='I will send the proposal.', confidence=.95, title='Send proposal to Kavita',
        event_start_text=None, event_end_text=None, participants=[])
    result.update(kwargs)
    return result

def observation(index=0, **kwargs):
    result = item()
    result.update(observation_id=f'o{index}', source_id=f's{index}', timestamp=datetime(2026, 9, 21, 9),
        sequence=index, normalized_deadline=None, deadline_precision=None, deadline_assumption=None,
        event_start=None, event_end=None, created_at=AS_OF)
    result.update(kwargs)
    return result

def state(items, as_of=AS_OF):
    return resolve_task({'task_id': 't'}, items, as_of, 'Arjun Malhotra')

def test_generic_unseen_input_and_idempotency():
    async def scenario():
        e = engine()
        body = SourceInput(source_type='MEETING', timestamp='2026-09-25T12:00:00', author='Arjun Malhotra',
            content='I told Kavita I would send the revised proposal by Monday. Rahul said he will confirm pricing tomorrow. The contract still needs someone to review it.')
        e.llm.generate_json.return_value = {'observations': [
            item(object='revised proposal', deadline_text='Monday', evidence_text='I told Kavita I would send the revised proposal by Monday.'),
            item(actor='Rahul', owner='Rahul', object='pricing', action='Confirm', counterparty='Arjun Malhotra', deadline_text='tomorrow', title='Confirm pricing', evidence_text='Rahul said he will confirm pricing tomorrow.'),
            item(type='UNCERTAINTY', kind='REVIEW', actor=None, owner=None, ownership_clear=False, object='contract', action='Review', counterparty=None, title='Review contract', evidence_text='The contract still needs someone to review it.')
        ]}
        result = await e.ingest(body, datetime(2026,9,25,13))
        assert {t['classification'] for t in result['affected_tasks']} == {'MY_ACTION','WAITING_ON_OTHERS','OWNERSHIP_UNCLEAR'}
        assert len(await e.tasks(AS_OF)) == 0  # No future evidence at 09:00.
        before = e.repo.counts()
        assert (await e.ingest(body, datetime(2026,9,25,13)))['duplicate']
        assert before == e.repo.counts()
        assert e.llm.generate_json.await_count == 1
    run(scenario())

def test_vendor_list_deduplicates_and_preserves_deadlines():
    async def scenario():
        e = engine()
        for index, (time, text, deadline) in enumerate([
            ('2026-09-21T09:00:00','I will send the vendor list to Raghav tomorrow.','tomorrow'),
            ('2026-09-22T18:30:00','Will send it Wednesday morning.','Wednesday morning'),
        ]):
            e.llm.generate_json.return_value = {'observations':[item(object='vendor list', counterparty='Raghav Sethi', title='Send vendor list', deadline_text=deadline,evidence_text=text)]}
            await e.ingest(SourceInput(source_type='EMAIL',timestamp=time,author='Arjun Malhotra',content=text), AS_OF)
        tasks = await e.tasks(AS_OF)
        assert len(tasks) == 1
        assert tasks[0]['status'] == 'OVERDUE'
        assert tasks[0]['owner'] == 'Arjun Malhotra'
        assert tasks[0]['current_deadline'] == datetime(2026,9,23,12)
        assert len(tasks[0]['source_ids']) == 2
        assert len(tasks[0]['deadline_history']) == 2
    run(scenario())

def test_mumbai_owner_remains_unknown():
    task = state([observation(kind='APPROVAL', object='Mumbai lease', owner=None, ownership_clear=False,
        type='UNCERTAINTY', normalized_deadline=datetime(2026,9,25,23,59,59), deadline_text='Friday end of day')])
    assert task['owner'] is None and task['classification'] == 'OWNERSHIP_UNCLEAR'
    assert task['current_deadline'] == datetime(2026,9,25,23,59,59)

def test_expense_delivery_resolved_not_review():
    delivery = [observation(owner='Divya Rao', actor='Divya Rao', object='expense report'),
        observation(1, owner='Divya Rao', actor='Divya Rao', object='expense report', timestamp=datetime(2026,9,23,18), type='COMPLETION', completion_evidence='Report attached, sent as promised.'),
        observation(2, owner='Divya Rao', actor='Arjun Malhotra', object='expense report', timestamp=datetime(2026,9,23,18,10),type='ACKNOWLEDGEMENT',completion_evidence='Got it, thank you.')]
    assert state(delivery)['status'] == 'RESOLVED'
    assert state(delivery,datetime(2026,9,23,17))['status'] == 'WAITING'
    assert state([observation(kind='REVIEW', object='expense report')])['status'] != 'RESOLVED'

def test_meridian_confirmation_not_event_occurrence():
    task = state([observation(kind='SCHEDULING',object='Meridian call',type='CONFIRMATION',completion_evidence='Yes, confirmed, see you at 3.', event_start=datetime(2026,9,23,15))])
    assert task['status'] == 'RESOLVED' and task['event_occurred'] is False
    event = state([observation(kind='EVENT', type='SCHEDULED_EVENT',object='Meridian call', event_start=datetime(2026,9,23,15), event_end=datetime(2026,9,23,15,30))])
    assert event['status'] == 'COMPLETION_UNVERIFIED'

def test_campaign_delivery_does_not_complete_review():
    assert state([observation(owner='Neha Kapoor',actor='Neha Kapoor',type='COMPLETION',completion_evidence='Deck is ready, attaching the draft.')])['status'] == 'RESOLVED'
    review = state([observation(kind='REVIEW',event_start=datetime(2026,9,24,9,30),event_end=datetime(2026,9,24,10))])
    assert review['status'] == 'COMPLETION_UNVERIFIED'

def test_calendar_conflict_and_complete_dataset():
    raw = sources()
    assert len(raw) == 32
    assert sum(len(s['metadata'].get('events',[])) for s in raw) == 34
    calendar = [{**s, 'timestamp': datetime.fromisoformat(s['timestamp'])} for s in raw if s['source_type']=='CALENDAR']
    conflicts = calendar_conflicts(calendar,AS_OF,'Arjun Malhotra')
    overlap = [c for c in conflicts if {c['event_a']['title'],c['event_b']['title']} == {'Board Prep Session','Deck Review with Arjun'}]
    assert len(overlap) == 1 and overlap[0]['overlap_minutes'] == 30

@pytest.mark.parametrize('text,expected',[
    ('today',datetime(2026,9,21,23,59,59)), ('tomorrow',datetime(2026,9,22,23,59,59)),
    ('tomorrow morning',datetime(2026,9,22,12)), ('Wednesday morning',datetime(2026,9,23,12)),
    ('Wednesday evening',datetime(2026,9,23,20)), ('Thursday morning',datetime(2026,9,24,12)),
    ('Friday',datetime(2026,9,25,23,59,59)), ('end of day',datetime(2026,9,21,23,59,59)),
    ('Friday, 25 September, end of day',datetime(2026,9,25,23,59,59)),
    ('Wednesday 3:00 PM',datetime(2026,9,23,15)),
])
def test_relative_dates(text,expected):
    assert normalize_deadline(text,datetime(2026,9,21,9))[0] == expected

def test_old_reminder_cannot_erase_completion_and_contradiction_is_visible():
    complete = observation(type='COMPLETION',completion_evidence='Sent.',timestamp=datetime(2026,9,22))
    remind = observation(1,type='REMINDER',timestamp=datetime(2026,9,23))
    assert state([complete,remind])['status'] == 'RESOLVED'
    assert state([complete,observation(2,type='REOPENING',timestamp=datetime(2026,9,24))])['status'] == 'COMPLETION_UNVERIFIED'

def test_raw_source_survives_ai_failure_and_invalid_quotes():
    async def scenario():
        e=engine()
        source=SourceInput(source_type='NOTE',timestamp=AS_OF,author='Arjun Malhotra',content='Remember the proposal.')
        e.llm.generate_json.side_effect=LLMUnavailable()
        with pytest.raises(IngestionError):
            await e.ingest(source,AS_OF)
        assert e.repo.counts()['sources']==1 and e.repo.counts()['observations']==0
        assert e.repo.find('sources')[0]['processing_status']=='PENDING'
        e.llm.generate_json.side_effect=None
        e.llm.generate_json.return_value={'observations':[item(evidence_text='Invented quotation')]}
        with pytest.raises(IngestionError):
            await e.ingest(source,AS_OF)
        assert e.repo.counts()['observations']==0
    run(scenario())
