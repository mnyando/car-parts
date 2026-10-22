"""Minimal Firestore-like JSON store used when Firebase isn't configured (local development).

Supports the subset of the Firestore API the app uses:
    db.collection(name).document(id=None) -> .id, .set(data), .update(data), .get(), .delete()
    db.collection(name).stream(), db.collection(name).limit(n).stream()
    snapshot.id, snapshot.exists, snapshot.to_dict()
plus document.increment(field, delta) as the local stand-in for firestore.Increment.
"""
import json
import threading
import uuid


class LocalStore:
    def __init__(self, path, legacy_path=None):
        self.path = path
        self._lock = threading.Lock()
        self._data = {}
        # Fall back to the old file name (local_orders.json) the first time
        for candidate in (path, legacy_path):
            if not candidate:
                continue
            try:
                with open(candidate, 'r') as f:
                    self._data = json.load(f)
                break
            except (OSError, ValueError):
                continue
        # Older versions stored orders at the top level: {order_id: order}
        if self._data and all(isinstance(v, dict) and 'status' in v for v in self._data.values()):
            self._data = {'orders': self._data}

    def _save(self):
        with open(self.path, 'w') as f:
            json.dump(self._data, f, indent=2)

    def collection(self, name):
        return LocalCollection(self, name)


class LocalCollection:
    def __init__(self, store, name):
        self.store = store
        self.name = name

    def document(self, doc_id=None):
        # generate an id similar to Firestore when none is given
        return LocalDocument(self.store, self.name, doc_id or str(uuid.uuid4()))

    def stream(self, _limit=None):
        with self.store._lock:
            docs = list(self.store._data.get(self.name, {}).items())
        if _limit is not None:
            docs = docs[:_limit]
        return iter([LocalSnapshot(doc_id, data) for doc_id, data in docs])

    def limit(self, n):
        collection = self

        class _Limited:
            def stream(self):
                return collection.stream(_limit=n)
        return _Limited()


class LocalDocument:
    def __init__(self, store, collection, doc_id):
        self.store = store
        self.collection = collection
        self.id = doc_id

    def set(self, data):
        with self.store._lock:
            self.store._data.setdefault(self.collection, {})[self.id] = dict(data)
            self.store._save()

    def update(self, data):
        with self.store._lock:
            docs = self.store._data.setdefault(self.collection, {})
            docs.setdefault(self.id, {}).update(data)
            self.store._save()

    def delete(self):
        with self.store._lock:
            self.store._data.get(self.collection, {}).pop(self.id, None)
            self.store._save()

    def increment(self, field, delta):
        with self.store._lock:
            doc = self.store._data.get(self.collection, {}).get(self.id)
            if doc is None:
                return
            doc[field] = doc.get(field, 0) + delta
            self.store._save()

    def get(self):
        with self.store._lock:
            data = self.store._data.get(self.collection, {}).get(self.id)
        return LocalSnapshot(self.id, data)


class LocalSnapshot:
    def __init__(self, doc_id, data):
        self.id = doc_id
        self._data = data

    @property
    def exists(self):
        return self._data is not None

    def to_dict(self):
        return dict(self._data) if self._data is not None else None
