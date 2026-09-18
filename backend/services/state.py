"""Deterministic evidence replay. Wall-clock time is never used for task state."""
import re
from datetime import datetime

def identity(name):
    return re.sub(r'[^a-z0-9]', '', (name or '').casefold())

def same_person(a, b):
    return bool(a and b and (identity(a) == identity(b)))

def resolve_task(task, observations, as_of, executive):
    evidence = sorted((o for o in observations if o['timestamp'] <= as_of), key=lambda o: (o['timestamp'], o['sequence'], o['observation_id']))
    if not evidence:
        return None
    first = evidence[0]
    owner = None
    ownership_conflict = False
    for o in evidence:
        if o['ownership_clear'] and o['owner']:
            if owner and not same_person(owner, o['owner']):
                ownership_conflict = True
            elif not ownership_conflict:
                owner = o['owner']
    if ownership_conflict:
        owner = None
    classification = 'OWNERSHIP_UNCLEAR' if not owner else ('MY_ACTION' if same_person(owner, executive) else 'WAITING_ON_OTHERS')
    history, current, current_rank = [], None, -1
    completions, contradictions = [], []
    for o in evidence:
        deadline = o.get('normalized_deadline')
        if deadline is not None:
            rank = 3 if o['type'] in ('COMMITMENT', 'DEADLINE_UPDATE') and same_person(o['actor'], owner) else 2 if o['type'] in ('COMMITMENT', 'DEADLINE_UPDATE', 'CONFIRMATION') else 1
            accepted = rank >= current_rank
            history.append({'deadline_text': o['deadline_text'], 'normalized_deadline': deadline, 'precision': o['deadline_precision'], 'assumption': o.get('deadline_assumption'), 'source_id': o['source_id'], 'observation_id': o['observation_id'], 'timestamp': o['timestamp'], 'accepted': accepted})
            if accepted:
                current, current_rank = deadline, rank
        explicit_completion = o['type'] in ('COMPLETION', 'ACKNOWLEDGEMENT', 'EVENT_OCCURRED')
        if o['kind'] == 'SCHEDULING' and o['type'] == 'CONFIRMATION':
            explicit_completion = True
        if o['kind'] == 'EVENT' and o['type'] != 'EVENT_OCCURRED':
            explicit_completion = False
        if explicit_completion and o.get('completion_evidence'):
            completions.append({'source_id': o['source_id'], 'observation_id': o['observation_id'], 'evidence_text': o['completion_evidence'], 'timestamp': o['timestamp']})
        if o['type'] == 'REOPENING' and completions:
            contradictions.append({'type': 'CONTRADICTORY_COMPLETION', 'source_id': o['source_id'], 'observation_id': o['observation_id'], 'explanation': 'Later explicit evidence disputes completion; human verification is needed.'})
    if ownership_conflict:
        contradictions.append({'type': 'OWNERSHIP_CONFLICT', 'explanation': 'Evidence names different owners without a confirmed handoff.'})
    events = [o for o in evidence if o.get('event_start')]
    ended = any((o.get('event_end') or o['event_start']) < as_of for o in events)
    resolved = bool(completions) and not any(c['type'] == 'CONTRADICTORY_COMPLETION' for c in contradictions)
    overdue = bool(current and current < as_of and not resolved)
    due_today = bool(current and current.date() == as_of.date() and not resolved)
    if resolved:
        status, why = 'RESOLVED', 'Explicit completion, receipt acknowledgement, or scheduling confirmation is present for this action.'
    elif any(c['type'] == 'CONTRADICTORY_COMPLETION' for c in contradictions):
        status, why = 'COMPLETION_UNVERIFIED', 'Completion is disputed by later explicit evidence.'
    elif not owner:
        status, why = 'OWNERSHIP_UNCLEAR', 'No confirmed owner. ' + task.get('ownership_note', 'Suggested ownership is not a confirmed assignment.')
    elif (first['kind'] in ('EVENT', 'REVIEW') and ended) or (first['kind'] == 'REVIEW' and overdue):
        status, why = 'COMPLETION_UNVERIFIED', 'The scheduled time passed, but no evidence confirms the event or review actually occurred.'
    elif overdue:
        status, why = 'OVERDUE', 'The supported deadline is before the reference time and completion is not established.'
    elif due_today:
        status, why = 'DUE_TODAY', 'The supported deadline falls on the reference date and completion is not established.'
    elif classification == 'WAITING_ON_OTHERS':
        status, why = 'WAITING', 'This action has an evidenced owner other than the executive and is not resolved.'
    else:
        status, why = 'OPEN', 'The executive owns this action and no completion evidence is available.'
    return {
        'ownership_note': task.get('ownership_note', 'Suggested ownership is not a confirmed assignment.'),
        'task_id': task['task_id'], 'canonical_title': first['title'], 'owner': owner,
        'classification': classification, 'kind': first['kind'], 'action': first['action'], 'object': first['object'],
        'counterparties': sorted({o['counterparty'] for o in evidence if o.get('counterparty')}),
        'current_deadline': current, 'deadline_history': history, 'status': status,
        'completion_evidence': completions, 'evidence_ids': [o['observation_id'] for o in evidence],
        'source_ids': sorted({o['source_id'] for o in evidence}), 'conflicts': contradictions,
        'decision_explanation': why, 'is_overdue': overdue and status != 'COMPLETION_UNVERIFIED',
        'is_due_today': due_today, 'as_of': as_of, 'event_occurred': any(o['type'] == 'EVENT_OCCURRED' for o in evidence),
        'scheduled_events': [{'start': o['event_start'], 'end': o.get('event_end'), 'source_id': o['source_id']} for o in events],
        'resolved_at': completions[-1]['timestamp'] if resolved else None,
        'evidence': [{'observation_id': o['observation_id'], 'source_id': o['source_id'], 'timestamp': o['timestamp'], 'author': o['actor'], 'type': o['type'], 'evidence_text': o['evidence_text']} for o in evidence],
        'created_at': task.get('created_at', first['created_at']), 'updated_at': task.get('updated_at', first['created_at']),
    }

def calendar_conflicts(sources, as_of, executive):
    events = []
    for source in sources:
        if source['timestamp'] > as_of:
            continue
        for event in source.get('metadata', {}).get('events', []):
            participants = event.get('participants', [])
            if not any(same_person(p, executive) for p in participants):
                continue
            start, end = datetime.fromisoformat(event['start']), datetime.fromisoformat(event['end'])
            if end <= start:
                continue
            events.append({**event, 'start': start, 'end': end, 'source_id': source['source_id']})
    result, seen = [], set()
    for i, a in enumerate(events):
        for b in events[i+1:]:
            if (a['title'], a['start'], a['end']) == (b['title'], b['start'], b['end']):
                continue
            start, end = max(a['start'], b['start']), min(a['end'], b['end'])
            if start >= end:
                continue
            key = tuple(sorted((a['title'], b['title']))) + (start, end)
            if key in seen:
                continue
            seen.add(key)
            result.append({'event_a': a, 'event_b': b, 'overlap_start': start, 'overlap_end': end,
                           'overlap_minutes': (end-start).total_seconds()/60, 'source_ids': sorted({a['source_id'], b['source_id']}),
                           'decision_explanation': 'Scheduled intervals overlap. This does not prove either event occurred.'})
    return result
