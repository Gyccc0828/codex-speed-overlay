# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Gyccc0828 and contributors

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'plugins' / 'codex-speed-overlay' / 'app'))
from meter import Session, Journal, Monitor


def event(at, kind, **payload):
    return {'timestamp': datetime.fromtimestamp(at, timezone.utc).isoformat(), 'type': kind, 'payload': payload}


def sample_session():
    return [
        event(1, 'session_meta', id='test', source='vscode'),
        event(10, 'event_msg', type='task_started', turn_id='turn'),
        event(11, 'response_item', type='configuration_update'),
        event(15, 'event_msg', type='item_completed', item={'type': 'AgentMessage'}, started_at_ms=14000),
        event(15, 'response_item', type='message', role='assistant'),
        event(16, 'response_item', type='custom_tool_call'),
        event(17, 'token_usage_record', response_id='one', usage={'output_tokens': 100, 'reasoning_output_tokens': 20}),
        event(17.1, 'event_msg', type='token_count', info={'last_token_usage': {'output_tokens': 100}}),
        event(26, 'response_item', type='custom_tool_call_output'),
        event(30, 'response_item', type='reasoning'),
        event(31, 'response_item', type='custom_tool_call'),
        event(32, 'token_usage_record', response_id='two', usage={'output_tokens': 50, 'reasoning_output_tokens': 10}),
    ]


class MeterTests(unittest.TestCase):
    def test_excludes_tools_counts_reasoning_once_and_deduplicates(self):
        state = Session()
        for item in sample_session():
            state.feed(item)
        snap = state.snapshot(now=35)
        self.assertEqual(snap['tokens'], 150)
        self.assertEqual(snap['samples'], 2)
        self.assertEqual(snap['tps'], 15)
        self.assertEqual(snap['last_tps'], 10)
        self.assertEqual(snap['first_visible'], 4)
        self.assertEqual(snap['elapsed'], 25)

    def test_new_turn_resets_metrics_and_completion_stops_timer(self):
        state = Session()
        for item in sample_session():
            state.feed(item)
        state.feed(event(40, 'event_msg', type='task_started', turn_id='two'))
        self.assertIsNone(state.snapshot(now=45)['tps'])
        self.assertIsNone(state.first_visible)
        state.feed(event(50, 'event_msg', type='task_complete'))
        self.assertEqual(state.snapshot(now=100)['elapsed'], 10)
        self.assertFalse(state.active)

    def test_incomplete_json_line_and_truncated_journal(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'test.jsonl'
            complete = json.dumps(event(10, 'event_msg', type='task_started'))
            path.write_text(complete[:-3], encoding='utf-8')
            reader = Journal(path)
            reader.read()
            self.assertEqual(reader.position, 0)
            with path.open('a', encoding='utf-8') as handle:
                handle.write(complete[-3:] + '\n')
            reader.read()
            self.assertEqual(reader.session.started, 10)
            path.write_text('{}\n', encoding='utf-8')
            reader.read()
            self.assertEqual(reader.session.started, 0)

    def test_latest_started_chat_wins_and_subagents_are_ignored(self):
        with tempfile.TemporaryDirectory() as folder:
            sessions = Path(folder) / 'sessions'
            sessions.mkdir()
            for name, start, source in [('old', 10, 'vscode'), ('new', 30, 'vscode'), ('helper', 50, {'subagent': {'other': 'guardian'}})]:
                records = [event(start - 1, 'session_meta', id=name, source=source), event(start, 'event_msg', type='task_started')]
                (sessions / (name + '.jsonl')).write_text(''.join(json.dumps(row) + '\n' for row in records), encoding='utf-8')
            monitor = Monitor(folder)
            self.assertEqual(monitor.poll().thread, 'new')
            with (sessions / 'old.jsonl').open('a', encoding='utf-8') as handle:
                handle.write(json.dumps(event(60, 'event_msg', type='token_count')) + '\n')
            self.assertEqual(monitor.poll().thread, 'new')


if __name__ == '__main__':
    unittest.main()
