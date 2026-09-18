"""Small synchronous PyMongo repository; callers run it in a worker thread."""
from datetime import datetime, timezone
from hashlib import sha256
import json

def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

def stable_id(prefix, value):
    return prefix + '_' + sha256(json.dumps(value, sort_keys=True, default=str, ensure_ascii=False).encode()).hexdigest()[:24]

class Repository:
    def __init__(self, connection):
        self.connection = connection
        self._indexed = False

    @property
    def db(self):
        database = self.connection.get_database()
        if not self._indexed:
            for collection, key in [('sources', 'source_id'), ('observations', 'observation_id'), ('tasks', 'task_id'), ('conversations', 'conversation_id'), ('audit_logs', 'audit_id')]:
                database[collection].create_index(key, unique=True)
            database.observations.create_index([('task_id', 1), ('timestamp', 1)])
            database.sources.create_index([('timestamp', 1)])
            database.audit_logs.create_index([('created_at', -1)])
            self._indexed = True
        return database

    def find(self, collection, query=None, limit=0):
        cursor = self.db[collection].find(query or {}, {'_id': 0})
        if limit:
            cursor = cursor.limit(limit)
        return list(cursor)

    def one(self, collection, key, value):
        return self.db[collection].find_one({key: value}, {'_id': 0})

    def save(self, collection, key, record):
        self.db[collection].update_one({key: record[key]}, {'$set': record}, upsert=True)

    def insert_source(self, record):
        return self.db.sources.update_one({'source_id': record['source_id']}, {'$setOnInsert': record}, upsert=True).upserted_id is not None

    def patch_source(self, source_id, **changes):
        self.db.sources.update_one({'source_id': source_id}, {'$set': changes})

    def audit(self, event, entity_id, details, effective_at):
        audit_id = stable_id('audit', [event, entity_id, details, effective_at])
        self.db.audit_logs.update_one({'audit_id': audit_id}, {'$setOnInsert': {
            'audit_id': audit_id, 'event': event, 'entity_id': entity_id, 'details': details,
            'effective_at': effective_at, 'created_at': now(),
        }}, upsert=True)

    def counts(self):
        return {name: self.db[name].count_documents({}) for name in ['sources', 'observations', 'tasks', 'conversations', 'audit_logs']}
