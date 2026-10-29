# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Gyccc0828 and contributors

"""Local, read-only Codex session meter. No network or credential access."""
from dataclasses import dataclass, field
from datetime import datetime
import json
import os
from pathlib import Path
import time


def timestamp(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp()


@dataclass
class Session:
    thread: str = ''
    ignored: bool = False
    model: str = ''
    effort: str = ''
    started: float = 0
    ended: float = 0
    boundary: float = 0
    pending: object = None
    active: bool = False
    phase: str = '等待聊天'
    first_visible: object = None
    tokens: int = 0
    model_seconds: float = 0
    samples: int = 0
    last_tps: object = None
    seen: set = field(default_factory=set)

    def feed(self, event):
        kind = event.get('type')
        payload = event.get('payload', {})
        subtype = payload.get('type')
        at = timestamp(event['timestamp'])
        if kind == 'session_meta':
            self.thread = payload.get('id', '')
            self.ignored = isinstance(payload.get('source'), dict) and 'subagent' in payload['source']
            return
        if self.ignored:
            return
        if kind == 'event_msg' and subtype == 'task_started':
            self.started = self.boundary = at
            self.ended = 0
            self.pending = None
            self.active = True
            self.phase = '等待 / 生成中'
            self.first_visible = None
            self.tokens = self.samples = 0
            self.model_seconds = 0
            self.last_tps = None
        if not self.started:
            return
        if kind == 'turn_context':
            self.model = payload.get('model', self.model)
            self.effort = payload.get('effort', payload.get('reasoning_effort', self.effort))
        if kind == 'event_msg' and subtype == 'item_completed':
            item = payload.get('item', {})
            if item.get('type') == 'AgentMessage' and self.first_visible is None:
                start_ms = payload.get('started_at_ms')
                if start_ms is not None:
                    self.first_visible = max(0, start_ms / 1000 - self.started)
        if kind == 'response_item':
            model_item = subtype in ('reasoning', 'function_call', 'custom_tool_call') or (
                subtype == 'message' and payload.get('role') == 'assistant')
            if model_item:
                if self.pending is None:
                    self.pending = [self.boundary, at]
                self.pending[1] = at
                if subtype in ('function_call', 'custom_tool_call'):
                    self.phase = '工具执行中'
            elif subtype in ('function_call_output', 'custom_tool_call_output', 'configuration_update'):
                self.boundary = at
                self.phase = '等待 / 生成中'
            elif subtype == 'message' and payload.get('role') in ('user', 'developer'):
                self.boundary = at
        usage = None
        response_id = None
        if kind == 'token_usage_record':
            usage = payload.get('usage')
            response_id = payload.get('response_id')
        elif kind == 'event_msg' and subtype == 'token_count':
            usage = (payload.get('info') or {}).get('last_token_usage')
        if usage is not None and self.pending is not None:
            if response_id is None or response_id not in self.seen:
                elapsed = self.pending[1] - self.pending[0]
                output = usage.get('output_tokens', 0)
                if elapsed > 0 and output > 0:
                    self.tokens += output
                    self.model_seconds += elapsed
                    self.samples += 1
                    self.last_tps = output / elapsed
                if response_id:
                    self.seen.add(response_id)
            self.pending = None
        if kind == 'event_msg' and subtype in ('task_complete', 'turn_aborted'):
            self.active = False
            self.ended = at
            self.phase = '本轮已完成' if subtype == 'task_complete' else '本轮已停止'

    def snapshot(self, now=None):
        now = time.time() if now is None else now
        return {
            'thread': self.thread,
            'model': self.model,
            'effort': self.effort,
            'phase': self.phase,
            'active': self.active,
            'elapsed': max(0, (now if self.active else self.ended) - self.started),
            'first_visible': self.first_visible,
            'tps': self.tokens / self.model_seconds if self.model_seconds else None,
            'last_tps': self.last_tps,
            'tokens': self.tokens,
            'samples': self.samples,
        }


class Journal:
    def __init__(self, path):
        self.path = path
        self.position = 0
        self.session = Session()

    def read(self):
        if self.path.stat().st_size < self.position:
            self.position = 0
            self.session = Session()
        with self.path.open('rb') as handle:
            handle.seek(self.position)
            while True:
                start = handle.tell()
                line = handle.readline()
                if not line.endswith(b'\n'):
                    self.position = start
                    break
                self.position = handle.tell()
                try:
                    self.session.feed(json.loads(line))
                except (ValueError, KeyError, TypeError):
                    continue
                if self.session.ignored:
                    self.position = self.path.stat().st_size
                    break


class Monitor:
    def __init__(self, codex_home=None):
        home = Path(codex_home or os.environ.get('CODEX_HOME') or Path.home() / '.codex')
        self.root = home / 'sessions'
        self.journals = {}

    def poll(self):
        files = []
        for path in self.root.rglob('*.jsonl'):
            try:
                files.append((path.stat().st_mtime, path))
            except OSError:
                continue
        files.sort(key=lambda pair: pair[0], reverse=True)
        # Keep only recent journals in memory; root agents outrank their helper logs.
        selected = []
        for _, path in files:
            reader = self.journals.setdefault(path, Journal(path))
            try:
                reader.read()
            except OSError:
                continue
            if not reader.session.ignored and reader.session.started:
                selected.append(reader)
                if len(selected) == 8:
                    break
        keep = {reader.path for reader in selected}
        self.journals = {p: r for p, r in self.journals.items() if p in keep or r.session.ignored}
        if not selected:
            return None
        return max(selected, key=lambda reader: reader.session.started).session


if __name__ == '__main__':
    session = Monitor().poll()
    print(json.dumps(session.snapshot() if session else {}, ensure_ascii=False, indent=2))
