"""Utility helpers for working with Battleship-style board layouts."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import Any


def battleship(board: Sequence[Sequence[Any] | str] | str) -> int:
    """Count the number of ships present in a Battleship board.

    Parameters
    ----------
    board
        A representation of the Battleship board.  The board can be provided as
        one of the following:

        * A sequence of strings, where each string represents a row.
        * A sequence of sequences containing arbitrary cell markers
          (e.g. ``[[1, 0], [0, 1]]``).
        * A single string containing newlines.  Each newline separates rows.

    Returns
    -------
    int
        The number of distinct ships on the board.  A ship is defined as a set
        of orthogonally connected cells whose markers represent a ship
        component.  Cells that are connected only diagonally are treated as
        belonging to separate ships.

    Notes
    -----
    The function is intentionally tolerant about the markers that represent a
    ship so that it works with a wide range of common Battleship
    representations.  The following markers are treated as ship parts:

    * ``"x"`` (uppercase or lowercase)
    * ``"s"`` (uppercase or lowercase)
    * ``"b"`` (uppercase or lowercase)
    * ``"h"`` (uppercase or lowercase, often used for hits)
    * ``"#"`` or ``"*"``
    * Any string representation of a non-zero integer

    Empty cells are identified by common placeholders such as ``"."``,
    ``"0"``, ``"o"``, ``"~"``, ``"-"`` and whitespace.  Any other marker is
    considered empty by default.
    """

    normalized = _normalize_board(board)
    if not normalized:
        return 0

    ships = 0
    visited: set[tuple[int, int]] = set()

    for row_index, row in enumerate(normalized):
        for col_index, cell in enumerate(row):
            if (row_index, col_index) in visited:
                continue

            if not _is_ship_marker(cell):
                continue

            ships += 1
            _flood_fill(normalized, row_index, col_index, visited)

    return ships


def _normalize_board(board: Sequence[Sequence[Any] | str] | str) -> list[list[str]]:
    if isinstance(board, str):
        rows: Iterable[Sequence[Any] | str] = board.splitlines()
    else:
        rows = board

    normalized: list[list[str]] = []
    for row in rows:
        if isinstance(row, str):
            normalized.append(list(row))
        elif isinstance(row, Iterable):
            normalized.append([str(cell) for cell in row])
        else:
            raise TypeError("Board rows must be strings or iterables of cell markers")

    return normalized


def _flood_fill(
    board: Sequence[Sequence[str]],
    start_row: int,
    start_col: int,
    visited: set[tuple[int, int]],
) -> None:
    stack: list[tuple[int, int]] = [(start_row, start_col)]

    while stack:
        row, col = stack.pop()
        if (row, col) in visited:
            continue

        if not _cell_is_ship(board, row, col):
            continue

        visited.add((row, col))

        neighbors = (
            (row - 1, col),
            (row + 1, col),
            (row, col - 1),
            (row, col + 1),
        )

        for neighbor_row, neighbor_col in neighbors:
            if _cell_is_ship(board, neighbor_row, neighbor_col):
                stack.append((neighbor_row, neighbor_col))


def _cell_is_ship(board: Sequence[Sequence[str]], row: int, col: int) -> bool:
    if row < 0 or row >= len(board):
        return False

    row_data = board[row]
    if col < 0 or col >= len(row_data):
        return False

    return _is_ship_marker(row_data[col])


def _is_ship_marker(cell: Any) -> bool:
    marker = str(cell).strip()
    if not marker:
        return False

    normalized = marker.lower()

    ship_markers = {"x", "s", "b", "h", "#", "*"}
    empty_markers = {".", "0", "o", "~", "-", " "}

    if normalized in ship_markers:
        return True

    if normalized in empty_markers:
        return False

    if normalized.isdigit():
        return int(normalized) != 0

    return False

