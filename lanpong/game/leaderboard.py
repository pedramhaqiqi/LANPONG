import csv

from collections import defaultdict
from itertools import chain, islice
from operator import neg
from threading import Lock

from sortedcontainers import SortedDict, SortedSet


class ThreadSafeLeaderboard:
    """A thread-safe leaderboard."""

    def __init__(self, filename="leaderboard.csv"):
        # Efficiently maintain reverse-ordered dict of score to names.
        self._filename = filename
        self._lock = Lock()
        self._score_to_names = SortedDict(key=neg)
        self._name_to_score = defaultdict(int)
        with open(filename, "r") as f:
            reader = csv.reader(f)
            for row in reader:
                name = row[0]
                score = int(row[1])
                # Use SortedSet instead of set to maintain alphabetical order.
                self._score_to_names.setdefault(score, SortedSet()).add(name)
                self._name_to_score[name] = score

    def add(self, name, score):
        with self._lock:
            if name in self._name_to_score:
                self._score_to_names[self._name_to_score[name]].remove(name)
            self._score_to_names.setdefault(score, SortedSet()).add(name)
            self._name_to_score[name] = score

    def remove(self, name):
        with self._lock:
            if name in self._name_to_score:
                self._score_to_names[self._name_to_score[name]].remove(name)
                if not self._score_to_names[self._name_to_score[name]]:
                    del self._score_to_names[self._name_to_score[name]]
                del self._name_to_score[name]

    def get_top(self, n):
        with self._lock:
            return islice(chain.from_iterable(self._score_to_names.values()), n)

    def get_score(self, name):
        with self._lock:
            return self._name_to_score[name]

    def save(self):
        with self._lock:
            with open(self._filename, "w") as f:
                writer = csv.writer(f)
                for score, names in self._score_to_names.items():
                    for name in names:
                        writer.writerow([name, score])
