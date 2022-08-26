import PyQt6.QtCore as core
import PyQt6.QtWidgets as widget


class QLineEdit(widget.QLineEdit):
    keyPressed = core.pyqtSignal(int)

    def keyPressEvent(self, event):
        super().keyPressEvent(event)
        self.keyPressed.emit(event.key())

    def makeError(self, *, placeholder: str | None = None, revert: bool = False):
        if placeholder is not None:
            self.setPlaceholderText(placeholder)
        self.setProperty("class", "" if revert else "error")
        self.style().polish(self)

        if not revert:
            self.revert = lambda x: self.makeError(revert=True, placeholder="" if placeholder is not None else None)
            self.keyPressed.connect(self.revert)
            self.textChanged.connect(self.revert)
        else:
            self.keyPressed.disconnect(self.revert)
            self.textChanged.disconnect(self.revert)
