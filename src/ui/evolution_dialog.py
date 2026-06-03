from __future__ import annotations

from functools import partial
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from cognition.fallback_engine import FallbackHypothesis, FallbackOptions


class EvolutionDialog(QDialog):
    """
    Frameless thought-bubble dialog for resolving evolutionary doubt.

    Emits the selected fallback action_type and then hides/deletes itself.
    """

    actionSelected = Signal(str)

    def __init__(self, fallback_options: FallbackOptions, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._fallback_options = fallback_options
        self._options_layout: Optional[QVBoxLayout] = None

        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.Tool
            | Qt.WindowStaysOnTopHint
            | Qt.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setModal(False)
        self.setMinimumWidth(420)
        self.setMaximumWidth(560)

        self._build_ui()
        self.set_options(fallback_options)

    def set_options(self, fallback_options: FallbackOptions) -> None:
        if not isinstance(fallback_options, FallbackOptions):
            raise TypeError("fallback_options must be a FallbackOptions instance")

        self._fallback_options = fallback_options
        self._clear_options()

        for hypothesis in fallback_options.hypotheses:
            button = self._create_option_button(hypothesis)
            self._options_layout.addWidget(button)

        self.adjustSize()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(14, 14, 14, 14)

        bubble = QFrame(self)
        bubble.setObjectName("evolutionBubble")
        bubble.setFrameShape(QFrame.NoFrame)
        bubble.setGraphicsEffect(self._build_shadow())

        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(22, 20, 22, 22)
        bubble_layout.setSpacing(14)

        title = QLabel("Duda evolutiva", bubble)
        title.setObjectName("bubbleTitle")
        title.setTextFormat(Qt.PlainText)
        title.setWordWrap(True)
        bubble_layout.addWidget(title)

        subtitle = QLabel("Elige el siguiente destino seguro para Greys.", bubble)
        subtitle.setObjectName("bubbleSubtitle")
        subtitle.setTextFormat(Qt.PlainText)
        subtitle.setWordWrap(True)
        bubble_layout.addWidget(subtitle)

        self._options_layout = QVBoxLayout()
        self._options_layout.setContentsMargins(0, 6, 0, 0)
        self._options_layout.setSpacing(10)
        bubble_layout.addLayout(self._options_layout)

        root_layout.addWidget(bubble)
        self.setStyleSheet(self._style_sheet())

    def _create_option_button(self, hypothesis: FallbackHypothesis) -> QPushButton:
        button = QPushButton(self._format_option_text(hypothesis), self)
        button.setObjectName(f"fallbackOption_{hypothesis.action_type}")
        button.setCursor(QCursor(Qt.PointingHandCursor))
        button.setMinimumHeight(76)
        button.setCheckable(False)
        button.setAutoDefault(False)
        button.setDefault(False)
        button.clicked.connect(partial(self._handle_selection, hypothesis.action_type))
        button.setToolTip(hypothesis.description)
        return button

    @staticmethod
    def _format_option_text(hypothesis: FallbackHypothesis) -> str:
        return f"{hypothesis.label}\n{hypothesis.description}"

    def _handle_selection(self, action_type: str) -> None:
        self.actionSelected.emit(action_type)
        self.hide()
        self.deleteLater()

    def _clear_options(self) -> None:
        if self._options_layout is None:
            return

        while self._options_layout.count():
            item = self._options_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    @staticmethod
    def _build_shadow() -> QGraphicsDropShadowEffect:
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 10)
        shadow.setColor(Qt.black)
        return shadow

    @staticmethod
    def _style_sheet() -> str:
        return """
        QFrame#evolutionBubble {
            background-color: rgba(12, 18, 28, 226);
            border: 1px solid rgba(126, 214, 255, 116);
            border-radius: 18px;
        }

        QLabel#bubbleTitle {
            color: #e9fbff;
            font-size: 20px;
            font-weight: 700;
            letter-spacing: 0px;
        }

        QLabel#bubbleSubtitle {
            color: rgba(220, 238, 244, 205);
            font-size: 13px;
            letter-spacing: 0px;
        }

        QPushButton {
            background-color: rgba(24, 38, 54, 216);
            border: 1px solid rgba(142, 211, 255, 86);
            border-radius: 12px;
            color: #f4fbff;
            font-size: 13px;
            font-weight: 500;
            line-height: 1.35;
            padding: 12px 14px;
            text-align: left;
            letter-spacing: 0px;
        }

        QPushButton:hover {
            background-color: rgba(36, 58, 78, 236);
            border-color: rgba(148, 230, 255, 168);
        }

        QPushButton:pressed {
            background-color: rgba(18, 31, 45, 245);
        }

        QPushButton#fallbackOption_abort {
            border-color: rgba(255, 165, 150, 136);
        }

        QPushButton#fallbackOption_sandbox_code {
            border-color: rgba(185, 179, 255, 136);
        }

        QPushButton#fallbackOption_ask_human {
            border-color: rgba(145, 226, 190, 136);
        }
        """
