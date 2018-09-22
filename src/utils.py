"""Utility functions."""
import json


def load_word_list(path):
    with open(path) as f:
        return [line.strip().lower() for line in f
                if line.strip() != "" and not line.startswith("#")]


def load_results(path):
    with open(path) as f:
        return json.load(f)


def save_results(results, path):
    with open(path, "wt") as f:
        json.dump(results, f)
