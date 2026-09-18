"""Conservative lexical candidates without AI calls."""
import json
import re
from difflib import SequenceMatcher
from schemas.domain import MatchDecision
from services.state import same_person

STOP = set('the a an to for of with on in by updated revised draft send get prepare provide confirm review sign off it this that my your our'.split())

def tokens(text):
    return {word.rstrip('s') for word in re.findall(r'[a-z0-9]+', (text or '').casefold()) if word not in STOP}

def compatible(observation, task):
    if observation['kind'] != task['kind']:
        return False
    if observation.get('owner') and task.get('owner') and not same_person(observation['owner'], task['owner']):
        return False
    if observation['kind'] == 'EVENT':
        old_starts = {str(e['start']) for e in task.get('scheduled_events', [])}
        if old_starts and str(observation.get('event_start')) not in old_starts:
            return False
    return True

async def match_task(observation, tasks, llm):
    candidates = []
    a = tokens(observation['object'])
    for task in tasks:
        if not compatible(observation, task):
            continue
        b = tokens(task['object'])
        lexical = len(a & b) / max(1, len(a | b))
        similar = SequenceMatcher(None, observation['object'].casefold(), task['object'].casefold()).ratio()
        if a & b or similar >= .65:
            score = max(lexical, similar * .7)
            candidates.append((score, task))
    candidates.sort(key=lambda pair: pair[0], reverse=True)
    if not candidates:
        return None
    if candidates[0][0] >= .6 and (len(candidates) == 1 or candidates[0][0] - candidates[1][0] >= .15):
        return candidates[0][1]['task_id']
    return None
