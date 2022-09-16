from PyQt6 import QtCore as core
from PyQt6 import QtGui as gui
from PyQt6 import QtWidgets as widget


# TODO: complex rules
class TextHightlight(gui.QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)

        keywordfmt = gui.QTextCharFormat()
        keywordfmt.setForeground(gui.QColor("darkMagenta"))
        keywordfmt.setFontWeight(gui.QFont.Weight.Bold)

        # fmt: off
        keywords = [
            "abort", "action", "add", "after", "all", "alter", "always", "analyze", "and", "as", "asc", "attach",
            "autoincrement", "before", "begin", "between", "by", "cascade", "case", "cast", "check", "collate",
            "column", "commit", "conflict", "constraint", "create", "cross", "current", "current_date",
            "current_time", "current_timestamp", "database", "default", "deferrable", "deferred", "delete", "desc",
            "detach", "distinct", "do", "drop", "each", "else", "end", "escape", "except", "exclude", "exclusive",
            "exists", "explain", "fail", "filter", "first", "following", "for", "foreign", "from", "full", "generated",
            "glob", "group", "groups", "having", "if", "ignore", "immediate", "in", "index", "indexed", "initially",
            "inner", "insert", "instead", "intersect", "into", "is", "isnull", "join", "key", "last", "left", "like",
            "limit", "match", "materialized", "natural", "no", "not", "nothing", "notnull", "null", "nulls", "of",
            "offset", "on", "or", "order", "others", "outer", "over", "partition", "plan", "pragma", "preceding",
            "primary", "query", "raise", "range", "recursive", "references", "regexp", "reindex", "release",
            "rename", "replace", "restrict", "returning", "right", "rollback", "row", "rows", "savepoint", "select",
            "set", "table", "temp", "temporary", "then", "ties", "to", "transaction", "trigger", "unbounded", "union",
            "unique", "update", "using", "vacuum", "values", "view", "virtual", "when", "where", "window", "with",
            "without"
        ]
        # fmt: on

        self.highlightingRules = [(f"\\b{key}\\b", keywordfmt) for key in keywords]

    def highlightBlock(self, text):
        for pattern, fmt in self.highlightingRules:
            regex = core.QRegularExpression(pattern, core.QRegularExpression.PatternOption.CaseInsensitiveOption)
            i = regex.globalMatch(text)
            while i.hasNext():
                match = i.next()
                start = match.capturedStart()
                length = match.capturedLength()
                self.setFormat(start, length, fmt)
