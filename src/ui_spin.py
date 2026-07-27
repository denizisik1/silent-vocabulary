from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QDoubleSpinBox,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLayout,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QWidget,
)

SPIN_STEP_BUTTON = "spinStepButton"
_COMPACT_SPIN = "spinBox"


def _step_button(label: str, parent: QWidget) -> QPushButton:
    button = QPushButton(label, parent)
    button.setObjectName(SPIN_STEP_BUTTON)
    button.setAutoDefault(False)
    button.setDefault(False)
    button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    button.setFlat(False)
    button.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    return button


def _put_container_in_layout(layout: QLayout, spin: QWidget, container: QWidget) -> bool:
    if isinstance(layout, QFormLayout):
        for row in range(layout.rowCount()):
            field = layout.itemAt(row, QFormLayout.ItemRole.FieldRole)
            if field is None or field.widget() is not spin:
                continue
            layout.removeWidget(spin)
            layout.setWidget(row, QFormLayout.ItemRole.FieldRole, container)
            return True
        return False

    if isinstance(layout, QGridLayout):
        for index in range(layout.count()):
            item = layout.itemAt(index)
            if item is None or item.widget() is not spin:
                continue
            row, column, row_span, column_span = layout.getItemPosition(index)
            layout.removeWidget(spin)
            layout.addWidget(container, row, column, row_span, column_span)
            return True
        return False

    for index in range(layout.count()):
        item = layout.itemAt(index)
        if item is None or item.widget() is not spin:
            continue
        layout.removeWidget(spin)
        layout.insertWidget(index, container)
        return True
    return False


def _install_stepper(spin: QSpinBox | QDoubleSpinBox) -> None:
    if bool(spin.property("silentVocabularyStepperWrapped")):
        return
    parent = spin.parentWidget()
    if parent is None:
        return
    layout = parent.layout()
    if layout is None:
        return

    compact = spin.objectName() == _COMPACT_SPIN
    container = QWidget(parent)
    row = QHBoxLayout(container)
    row.setContentsMargins(0, 0, 0, 0)
    row.setSpacing(0 if compact else 2)

    minus = _step_button("-", container)
    plus = _step_button("+", container)
    minus.clicked.connect(spin.stepDown)
    plus.clicked.connect(spin.stepUp)

    if not _put_container_in_layout(layout, spin, container):
        container.deleteLater()
        return

    spin.setParent(container)
    spin.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
    spin.setProperty("silentVocabularyStepperWrapped", True)
    if compact:
        spin.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        container.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        minus.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        plus.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        steps = QWidget(container)
        steps_row = QHBoxLayout(steps)
        steps_row.setContentsMargins(0, 0, 0, 0)
        steps_row.setSpacing(2)
        steps_row.addWidget(minus)
        steps_row.addWidget(plus)
        row.addWidget(spin)
        row.addWidget(steps)
        row.setAlignment(spin, Qt.AlignmentFlag.AlignVCenter)
        row.setAlignment(steps, Qt.AlignmentFlag.AlignVCenter)
    else:
        row.addWidget(spin, 1)
        row.addWidget(minus)
        row.addWidget(plus)


def install_spin_steppers(window: QMainWindow) -> None:
    spins: list[QSpinBox | QDoubleSpinBox] = []
    spins.extend(window.findChildren(QSpinBox))
    spins.extend(window.findChildren(QDoubleSpinBox))
    for spin in spins:
        _install_stepper(spin)
