"""Git-backed doubt ledger: checkpoints so relocated trust survives session death."""
import os
import subprocess

from ledger.entry import Entry
from ledger.store import Store


class Gitback(Store):
    def __init__(self, path):
        super().__init__(path)
        self.n_since = 0

    def add(self, entry):
        super().add(entry)
        self.n_since += 1
        if self.n_since >= 5:
            self.checkpoint()

    def checkpoint(self):
        if self.n_since == 0 and os.path.exists(self.file):
            pass
        subprocess.run(["git", "-C", self.path, "add", "ledger.jsonl"],
                       check=True, capture_output=True)
        n = len(self.entries)
        subprocess.run(["git", "-C", self.path, "commit", "-q", "-m",
                        f"ledger: checkpoint {n} entries — trust relocated, not deleted"],
                       check=True, capture_output=True)
        self.n_since = 0

    def resume(self):
        """reload from disk — the only state that outlives a session."""
        self.entries = []
        self._load()
        return self.open()
