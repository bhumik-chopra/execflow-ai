"""Complete supplied four-page data pack, transcribed as raw sources.

Typography/whitespace is normalized, content is not summarized. Calendar dates
are explicit ISO wall times. The data pack gives no calendar publication time;
its snapshot is made available at assignment-week start, marked as an assumption.
"""
PEOPLE = {
    'Arjun Malhotra': 'arjun.malhotra@veridian-corp.example',
    'Neha Kapoor': 'neha.kapoor@veridian-corp.example',
    'Raghav Sethi': 'raghav.sethi@veridian-corp.example',
    'Divya Rao': 'divya.rao@veridian-corp.example',
    'Priya Nair': 'priya.nair@meridianlogistics.example',
    'Facilities': 'facilities@veridian-corp.example',
}

MEETING = '''Attendees: Arjun Malhotra, Neha Kapoor, Raghav Sethi, Divya Rao
Arjun: Let’s keep this quick. Neha, where are we on the Q3 campaign deck?
Neha: Draft is 80% done. I’ll send it to Arjun for review by Wednesday.
Arjun: Good. Also, remind me — I told Raghav I’d send him the updated vendor list. I’ll get that to him by end of day tomorrow.
Raghav: Appreciated. Separately, the Mumbai office renewal paperwork needs someone to sign off this week. Not sure whose desk that’s on right now.
Divya: I think that’s supposed to be Facilities, but I haven’t seen anyone pick it up.
Arjun: Okay, flag it, don’t assume. Divya, can you also pull the July expense variance report before Thursday’s board prep?
Divya: Yes, I’ll have it ready Wednesday evening.
Arjun: One more thing — client call with Meridian Logistics got pushed. I need to reconfirm the new time with their team myself.
Neha: Also, just a reminder, the campaign deck review — I said Wednesday, but realistically Thursday morning is safer.
Arjun: Noted. Let’s close here.'''

CALENDARS = {
    'Arjun Malhotra': [
        (21, '09:00', '09:35', 'Leadership Sync'),
        (21, '14:00', '14:30', '1:1 with Neha'),
        (21, '16:00', '17:00', 'Blocked'),
        (22, '11:00', '12:00', 'Internal Budget Review'),
        (22, '15:00', '15:30', 'Blocked'),
        (23, '15:00', '15:30', 'Call — Meridian Logistics'),
        (23, '18:00', '18:15', 'Blocked'),
        (24, '09:00', '10:00', 'Board Prep Session'),
        (24, '16:00', '17:00', 'Hiring Panel — Sales Associate'),
        (25, '10:00', '10:30', 'Facilities Check-in'),
        (25, '13:00', '14:00', 'Blocked'),
    ],
    'Neha Kapoor': [
        (21, '10:00', '11:00', 'Blocked'),
        (21, '14:00', '14:30', '1:1 with Arjun'),
        (22, '13:00', '14:00', 'Campaign Vendor Call'),
        (23, '10:00', '10:30', 'Deck Prep'),
        (23, '13:00', '15:00', 'Blocked'),
        (24, '09:30', '10:00', 'Deck Review with Arjun'),
        (25, '11:00', '12:00', 'Blocked'),
    ],
    'Raghav Sethi': [
        (21, '09:00', '09:35', 'Leadership Sync'),
        (21, '13:00', '14:00', 'Blocked'),
        (22, '11:00', '12:00', 'Internal Budget Review'),
        (22, '15:30', '16:00', 'Ops Standup'),
        (23, '09:00', '11:00', 'Blocked'),
        (24, '14:00', '15:00', 'Blocked'),
        (25, '10:00', '10:30', 'Facilities Check-in'),
        (25, '15:00', '16:00', 'Blocked'),
    ],
    'Divya Rao': [
        (21, '14:30', '15:00', 'Budget Prep'),
        (21, '16:00', '17:00', 'Blocked'),
        (22, '09:00', '09:15', 'Quick Call with Arjun'),
        (22, '11:00', '12:00', 'Internal Budget Review'),
        (23, '13:00', '14:00', 'Blocked'),
        (24, '09:00', '10:00', 'Board Prep Session'),
        (24, '14:00', '15:00', 'Blocked'),
        (25, '10:00', '11:00', 'Blocked'),
    ],
}

# Each tuple is one complete email, not a precomputed action.
THREADS = [
('Vendor List', [
    (21, '09:50', 'Raghav Sethi', ['Arjun Malhotra'], 'Following up from the sync — can you send the updated vendor list today?'),
    (21, '17:40', 'Arjun Malhotra', ['Raghav Sethi'], 'Running behind, will send first thing tomorrow morning instead.'),
    (22, '09:15', 'Raghav Sethi', ['Arjun Malhotra'], 'No worries, whenever you get a chance today works.'),
    (22, '18:30', 'Arjun Malhotra', ['Raghav Sethi'], 'Sorry, got pulled into board prep — will send by tomorrow (Wednesday) morning for sure.'),
    (23, '08:45', 'Raghav Sethi', ['Arjun Malhotra'], 'Just checking — still good for this morning?'),
]),
('Q3 Campaign Deck', [
    (21, '11:00', 'Neha Kapoor', ['Arjun Malhotra'], 'Deck’s coming together, still targeting Wednesday for your review.'),
    (22, '16:15', 'Neha Kapoor', ['Arjun Malhotra'], 'Heads up — shifting the review to Thursday morning instead of Wednesday, need one more day on the data slides.'),
    (23, '10:00', 'Arjun Malhotra', ['Neha Kapoor'], 'Understood, Thursday morning works. What time exactly?'),
    (23, '10:20', 'Neha Kapoor', ['Arjun Malhotra'], 'Let’s say 9:30 AM Thursday, before your board prep block.'),
    (24, '08:00', 'Neha Kapoor', ['Arjun Malhotra'], 'Deck is ready, attaching the draft ahead of our 9:30 review.'),
]),
('Call Reschedule', [
    (21, '13:00', 'Priya Nair', ['Arjun Malhotra'], 'Our scheduled call this week got bumped from our side — can you propose a new time? We’re flexible Tuesday–Thursday afternoons.'),
    (22, '15:00', 'Arjun Malhotra', ['Priya Nair'], 'Apologies for the delay — how about Wednesday 3:00 PM?'),
    (22, '17:45', 'Priya Nair', ['Arjun Malhotra'], 'Wednesday 3 PM works on our end, confirmed.'),
    (23, '13:30', 'Priya Nair', ['Arjun Malhotra'], 'Quick check — still on for 3 PM today?'),
    (23, '14:00', 'Arjun Malhotra', ['Priya Nair'], 'Yes, confirmed, see you at 3.'),
]),
('Expense Variance Report', [
    (21, '14:30', 'Divya Rao', ['Arjun Malhotra'], 'Starting on the July variance numbers, targeting Thursday morning for board prep as discussed.'),
    (22, '09:00', 'Arjun Malhotra', ['Divya Rao'], 'Actually, can I get it by Wednesday evening instead? Want time to review before Thursday.'),
    (22, '09:40', 'Divya Rao', ['Arjun Malhotra'], 'Wednesday evening is tight but doable, I’ll prioritize it.'),
    (23, '18:00', 'Divya Rao', ['Arjun Malhotra'], 'Report attached, sent as promised.'),
    (23, '18:10', 'Arjun Malhotra', ['Divya Rao'], 'Got it, thank you — exactly what I needed before tomorrow.'),
]),
('Mumbai Office Lease Renewal', [
    (21, '10:15', 'Facilities', ['All Staff'], 'Reminder: the Mumbai office lease renewal requires an authorized signature by Friday, 25 September.'),
    (22, '11:00', 'Raghav Sethi', ['Arjun Malhotra', 'Divya Rao'], 'Following up from the sync — has anyone confirmed who’s signing off on the Mumbai renewal? Don’t think it’s been assigned.'),
    (23, '09:30', 'Divya Rao', ['Raghav Sethi', 'Arjun Malhotra'], 'Not on my end — I believe this typically sits with Facilities directly, not us.'),
    (24, '16:00', 'Facilities', ['All Staff'], 'Second reminder: signature is still pending. Deadline is Friday, 25 September, end of day.'),
    (24, '16:45', 'Raghav Sethi', ['Arjun Malhotra'], 'This is now one day out and still unowned — can you confirm who’s handling it?'),
]),
]

VOICE_NOTES = [
    (21, '18:40', 'Quick note to self — need to get Raghav that vendor list, I think I said today but it might slip to tomorrow morning, remind me. Also still haven’t heard back on the Mumbai lease thing, someone needs to own that, I don’t think it’s me.'),
    (23, '08:15', 'Reminder — expense variance report from Divya needs to be in my hands by Wednesday evening, not Thursday, I want time to go through it before board prep. Also Meridian call — I owe Priya a time, need to lock that in today.'),
]

def sources():
    common = {'dataset': 'assignment-1', 'people': PEOPLE, 'provenance': 'Assignment 1_DataPack_ExecutiveProductivityAgent.pdf'}
    result = [{'source_id': 'demo-leadership-sync', 'source_type': 'MEETING', 'timestamp': '2026-09-21T09:35:00',
        'author': 'Leadership Sync transcript', 'recipients': [], 'subject': 'Leadership Sync', 'content': MEETING,
        'metadata': {**common, 'start': '2026-09-21T09:00:00', 'end': '2026-09-21T09:35:00'}}]
    for index, (owner, rows) in enumerate(CALENDARS.items()):
        events = []
        for day, start, end, title in rows:
            line = f'2026-09-{day} {start}-{end} {title}'
            participants = [owner]
            for person in PEOPLE:
                if f'with {person.split()[0]}' in title and person not in participants:
                    participants.append(person)
            events.append({'title': title, 'start': f'2026-09-{day}T{start}:00', 'end': f'2026-09-{day}T{end}:00',
                           'participants': participants, 'evidence_text': line})
        result.append({'source_id': f'demo-calendar-{index+1}', 'source_type': 'CALENDAR', 'timestamp': '2026-09-21T00:00:00',
            'author': owner, 'recipients': [], 'subject': f'{owner} calendar, 21-25 September 2026',
            'content': '\n'.join(e['evidence_text'] for e in events),
            'metadata': {**common, 'events': events, 'timestamp_basis': 'Assignment-week snapshot availability assumption; original publication timestamp is not supplied.'}})
    for thread_index, (subject, emails) in enumerate(THREADS):
        for email_index, (day, time, author, recipients, content) in enumerate(emails):
            result.append({'source_id': f'demo-email-{thread_index+1}-{email_index+1}', 'source_type': 'EMAIL',
                'timestamp': f'2026-09-{day}T{time}:00', 'author': author, 'recipients': recipients, 'subject': subject, 'content': content,
                'metadata': {**common, 'thread_id': f'demo-thread-{thread_index+1}', 'from_email': PEOPLE[author], 'to_emails': [PEOPLE.get(p, p) for p in recipients]}})
    for index, (day, time, content) in enumerate(VOICE_NOTES):
        result.append({'source_id': f'demo-voice-{index+1}', 'source_type': 'VOICE_NOTE', 'timestamp': f'2026-09-{day}T{time}:00',
            'author': 'Arjun Malhotra', 'recipients': [], 'subject': f'Personal voice note {index+1}', 'content': content,
            'metadata': {**common, 'personal_memo': True, 'location': 'cab' if index == 0 else None}})
    return sorted(result, key=lambda s: (s['timestamp'], s['source_id']))
