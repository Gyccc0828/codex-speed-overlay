# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 Gyccc0828 and contributors

import ctypes
from ctypes import wintypes
import queue
import sys
import threading
from PyQt5 import QtCore, QtGui, QtWidgets
from meter import Monitor


class Overlay(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Codex 速度悬浮窗')
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setFixedSize(282, 90)
        screen = QtWidgets.QApplication.desktop().availableGeometry()
        self.move(max(screen.left() + 20, screen.right() - self.width() - 28), screen.top() + 85)
        self.stop = threading.Event()
        self.messages = queue.Queue(maxsize=1)
        self.current = None
        self.drag_offset = None

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(13, 7, 10, 7)
        layout.setSpacing(2)
        top = QtWidgets.QHBoxLayout()
        self.model = self.make_label('正在读取模型…')
        top.addWidget(self.model, 1)
        self.close_button = QtWidgets.QPushButton('×')
        self.close_button.setAccessibleName('关闭悬浮窗')
        self.close_button.setToolTip('关闭悬浮窗')
        self.close_button.setFixedSize(22, 22)
        self.close_button.setCursor(QtCore.Qt.PointingHandCursor)
        self.close_button.setStyleSheet('QPushButton { border: none; border-radius: 5px; background: transparent; color: #374151; font-size: 20px; } QPushButton:hover { background: #d1d5db; color: #111827; } QPushButton:pressed { background: #fca5a5; }')
        self.close_button.clicked.connect(self.close)
        top.addWidget(self.close_button)
        layout.addLayout(top)
        self.speed = self.make_label('本轮有效吞吐 --tokens/s')
        self.status = self.make_label('正在读取 00分00秒')
        layout.addWidget(self.speed)
        layout.addWidget(self.status)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(400)
        threading.Thread(target=self.worker, daemon=True).start()

    def make_label(self, text):
        label = QtWidgets.QLabel(text)
        font = QtGui.QFont('Microsoft YaHei UI')
        font.setPixelSize(14)
        label.setFont(font)
        label.setStyleSheet('color: #111827; background: transparent;')
        label.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        return label

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_Source)
        painter.fillRect(self.rect(), QtCore.Qt.transparent)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceOver)
        painter.setPen(QtCore.Qt.NoPen)
        # Only the light-gray background is translucent; text stays opaque.
        painter.setBrush(QtGui.QColor(232, 234, 237, 232))
        painter.drawRoundedRect(QtCore.QRectF(self.rect()), 12, 12)

    def worker(self):
        monitor = Monitor()
        while not self.stop.is_set():
            try:
                session = monitor.poll()
                value = session.snapshot() if session else None
            except Exception:
                value = {'error': True}
            try:
                self.messages.get_nowait()
            except queue.Empty:
                pass
            self.messages.put(value)
            self.stop.wait(0.8)

    def refresh(self):
        try:
            value = self.messages.get_nowait()
            if value and value.get('error'):
                self.status.setText('读取中断，正在重试')
                return
            self.current = value
        except queue.Empty:
            pass
        if self.current:
            state = self.current
            self.model.setText(f"{state['model'] or 'Codex'} / {state['effort'] or '默认强度'}")
            number = f"{state['tps']:.1f}" if state['tps'] is not None else '--'
            self.speed.setText(f'本轮有效吞吐 {number}tokens/s')
            hours, seconds = divmod(int(state['elapsed']), 3600)
            minutes, seconds = divmod(seconds, 60)
            duration = (f'{hours}小时' if hours else '') + f'{minutes:02d}分{seconds:02d}秒'
            phase = '正在思考' if state['active'] else state['phase']
            self.status.setText(f'{phase} {duration}')

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.drag_offset = event.globalPos() - self.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() & QtCore.Qt.LeftButton and self.drag_offset is not None:
            self.move(event.globalPos() - self.drag_offset)

    def contextMenuEvent(self, event):
        menu = QtWidgets.QMenu(self)
        action = menu.addAction('关闭悬浮窗')
        if menu.exec_(event.globalPos()) == action:
            self.close()

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        self.stop.set()
        self.timer.stop()
        event.accept()


def run():
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
    kernel.CreateMutexW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    mutex = kernel.CreateMutexW(None, False, 'Local\\CodexSpeedOverlay')
    if ctypes.get_last_error() == 183:
        kernel.CloseHandle(mutex)
        return
    try:
        QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_DisableHighDpiScaling)
        app = QtWidgets.QApplication(sys.argv)
        window = Overlay()
        window.show()
        app.exec_()
    finally:
        kernel.CloseHandle(mutex)


if __name__ == '__main__':
    run()
