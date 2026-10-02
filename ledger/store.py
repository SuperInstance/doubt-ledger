"""Append-only JSONL doubt store with line checksums."""
import json
import os


def _checksum(line_id, body):
    h = 0xcbf29ce484222325
    for ch in (line_id + "|" + body):
        h ^= ord(ch)
        h = (h * 0x100000001b3) & 0xFFFFFFFFFFFFFFFF
    return "%016x" % h


class Store:
    def __init__(self, path):
        self.path = path
        os.makedirs(path, exist_ok=True)
        self.file = os.path.join(path, "ledger.jsonl")
        self.entries = []
        if os.path.exists(self.file):
            self._load()

    def _load(self):
        seen = set()
        with open(self.file) as f:
            for i, line in enumerate(f.read().splitlines()):
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    raise ValueError(f"ledger truncated/corrupt at line {i} "
                                     f"— refusing to load")
                want = _checksum(rec["id"], json.dumps(rec["entry"],
                                 sort_keys=True, separators=(",", ":")))
                if rec.get("sum") != want:
                    raise ValueError(f"ledger tampered at line {i} "
                                     f"(id {rec.get('id')}) — append-only violated")
                if rec["id"] in seen:
                    raise ValueError(f"duplicate entry id {rec['id']} at line {i}")
                seen.add(rec["id"])
                e = rec["entry"]
                from ledger.entry import Entry
                self.entries.append(Entry(**{k: e[k] for k in e}))

    def add(self, entry):
        if any(e.id == entry.id for e in self.entries):
            raise ValueError(f"duplicate entry id {entry.id} — refusing to add")
        body = json.dumps(entry.to_dict(), sort_keys=True, separators=(",", ":"))
        rec = {"id": entry.id, "sum": _checksum(entry.id, body), "entry": entry.to_dict()}
        with open(self.file, "a") as f:
            f.write(json.dumps(rec, sort_keys=True, separators=(",", ":")) + "\n")
        self.entries.append(entry)

    def open(self):
        return [e.to_dict() for e in self.entries if e.status in ("open", "due")]

    def at(self, needle):
        return [e.to_dict() for e in self.entries
                if e.status in ("open", "due")
                and (needle in e.stopped_checking or needle in e.covered_by)]

    def fire(self, event):
        fired = []
        for e in self.entries:
            if e.status == "open" and (e.revisit_trigger == event or
                                       (e.kind == "condition" and e.expr and event == e.expr)):
                e.status = "due"
                fired.append(e.to_dict())
        self._rewrite()
        return fired

    def discharge(self, entry_id, reason=None):
        if not reason:
            raise ValueError("discharge requires a reason — an unreasoned "
                             "discharge is just blindness again")
        for e in self.entries:
            if e.id == entry_id:
                e.status = "discharged"
                e.discharge_reason = reason
                self._rewrite()
                return
        raise ValueError(f"discharge: no entry with id {entry_id}")

    def _rewrite(self):
        tmp = self.file + ".tmp"
        try:
            with open(tmp, "w") as f:
                for e in self.entries:
                    body = json.dumps(e.to_dict(), sort_keys=True,
                                      separators=(",", ":"))
                    f.write(json.dumps({"id": e.id, "sum": _checksum(e.id, body),
                                        "entry": e.to_dict()},
                                       sort_keys=True, separators=(",", ":")) + "\n")
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, self.file)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
