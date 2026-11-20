from __future__ import annotations

from .interfaces import ISearchService


class SearchEngine(ISearchService):
    def find(
        self,
        lines: list[str],
        start_row: int,
        start_col: int,
        query: str,
        forward: bool,
    ) -> tuple[int, int] | None:
        if not query or not lines:
            return None

        n = len(lines)

        if forward:
            for r in range(start_row, n):
                s = lines[r]
                from_col = start_col if r == start_row else 0
                idx = s.find(query, from_col)
                if idx != -1:
                    return (r, idx)
        else:
            for r in range(start_row, -1, -1):
                s = lines[r]
                to_col = start_col if r == start_row else len(s)
                idx = s.rfind(query, 0, to_col)
                if idx != -1:
                    return (r, idx)
        return None