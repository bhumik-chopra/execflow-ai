"""Generic input, observation, task and grounded-answer contracts."""
from datetime import datetime, timezone
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ASSIGNMENT_AS_OF = datetime(2026, 9, 25, 9)
DatasetScope = Literal['assignment', 'personal']

def reference_time(as_of, scope):
    return as_of or (ASSIGNMENT_AS_OF if scope == 'assignment' else datetime.now())

SourceType = Literal['EMAIL', 'MEETING', 'VOICE_NOTE', 'CALENDAR', 'NOTE', 'OTHER']
Classification = Literal['MY_ACTION', 'WAITING_ON_OTHERS', 'OWNERSHIP_UNCLEAR']
Status = Literal['OPEN', 'WAITING', 'DUE_TODAY', 'OVERDUE', 'RESOLVED', 'COMPLETION_UNVERIFIED', 'OWNERSHIP_UNCLEAR']
Kind = Literal['DELIVERY', 'REVIEW', 'SCHEDULING', 'EVENT', 'APPROVAL', 'CLARIFICATION', 'OTHER']
ObservationType = Literal['COMMITMENT', 'REQUEST', 'DEADLINE_UPDATE', 'REMINDER', 'UNCERTAINTY', 'COMPLETION', 'ACKNOWLEDGEMENT', 'CONFIRMATION', 'SCHEDULED_EVENT', 'EVENT_OCCURRED', 'REOPENING']

def wall_time(value: datetime) -> datetime:
    return value.astimezone(timezone.utc).replace(tzinfo=None) if value.tzinfo else value

class SourceInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    source_id: str | None = Field(default=None, max_length=120, pattern=r'^[\w.-]+$')
    source_type: SourceType
    timestamp: datetime = Field(default_factory=datetime.now)
    author: str = Field(min_length=1, max_length=200)
    recipients: list[str] = Field(default_factory=list, max_length=100)
    subject: str = Field(default='', max_length=500)
    content: str = Field(min_length=1, max_length=60000)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator('timestamp')
    @classmethod
    def normalize_time(cls, value):
        return wall_time(value)

    @model_validator(mode='after')
    def validate_calendar(self):
        events = self.metadata.get('events')
        if events is not None:
            if self.source_type != 'CALENDAR' or not isinstance(events, list) or len(events) > 200:
                raise ValueError('events must be a list of at most 200 calendar intervals.')
            for event in events:
                parsed = CalendarEvent.model_validate(event)
                if parsed.evidence_text not in self.content:
                    raise ValueError('Calendar evidence_text must occur exactly in source content.')
            self.metadata['events'] = [CalendarEvent.model_validate(e).model_dump(mode='json') for e in events]
        return self

class CalendarEvent(BaseModel):
    model_config = ConfigDict(extra='forbid')
    title: str = Field(min_length=1)
    start: datetime
    end: datetime
    participants: list[str] = Field(default_factory=list)
    evidence_text: str = Field(min_length=1)

    @field_validator('start', 'end')
    @classmethod
    def normalize_time(cls, value):
        return wall_time(value)

    @model_validator(mode='after')
    def valid_interval(self):
        if self.end <= self.start:
            raise ValueError('Calendar end must be after start.')
        return self

class ExtractedObservation(BaseModel):
    model_config = ConfigDict(extra='forbid')
    type: ObservationType
    kind: Kind
    actor: str | None
    action: str
    object: str
    counterparty: str | None
    owner: str | None
    ownership_clear: bool
    deadline_text: str | None
    completion_evidence: str | None
    evidence_text: str
    confidence: float = Field(ge=0, le=1)
    title: str
    # Resolve deictic dates in Python, not with model-produced timestamps.
    event_start_text: str | None = None
    event_end_text: str | None = None
    participants: list[str] = Field(default_factory=list)

class Extraction(BaseModel):
    model_config = ConfigDict(extra='forbid')
    observations: list[ExtractedObservation] = Field(max_length=80)

class MatchDecision(BaseModel):
    model_config = ConfigDict(extra='forbid')
    task_id: str | None
    same_commitment: bool
    confidence: float = Field(ge=0, le=1)

class Observation(ExtractedObservation):
    observation_id: str
    source_id: str
    timestamp: datetime
    sequence: int
    normalized_deadline: datetime | None
    deadline_precision: str | None
    deadline_assumption: str | None
    event_start: datetime | None = None
    event_end: datetime | None = None
    task_id: str | None = None
    created_at: datetime

class Task(BaseModel):
    model_config = ConfigDict(extra='allow')
    task_id: str
    canonical_title: str
    owner: str | None
    classification: Classification
    kind: Kind
    object: str
    action: str
    counterparties: list[str]
    current_deadline: datetime | None
    deadline_history: list[dict[str, Any]]
    status: Status
    completion_evidence: list[dict[str, Any]]
    evidence_ids: list[str]
    source_ids: list[str]
    conflicts: list[dict[str, Any]]
    decision_explanation: str
    created_at: datetime
    updated_at: datetime

class ChatInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    question: str = Field(min_length=1, max_length=3000)
    scope: DatasetScope = 'assignment'
    as_of: datetime | None = None
    conversation_id: str | None = Field(default=None, max_length=120, pattern=r'^[\w.-]+$')

class Citation(BaseModel):
    model_config = ConfigDict(extra='forbid')
    source_id: str
    evidence_text: str

class GroundedAnswer(BaseModel):
    model_config = ConfigDict(extra='forbid')
    answer: str
    citations: list[Citation]
    unknown: bool
