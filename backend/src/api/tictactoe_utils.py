from __future__ import annotations

from typing import List, Literal, Optional, Sequence, TypedDict

Player = Literal["X", "O"]
Cell = Literal["X", "O", ""]


class Outcome(TypedDict, total=False):
    winner: Optional[Player]
    isDraw: bool
    winningLine: Optional[List[int]]


WINNING_LINES: List[List[int]] = [
    [0, 1, 2],
    [3, 4, 5],
    [6, 7, 8],
    [0, 3, 6],
    [1, 4, 7],
    [2, 5, 8],
    [0, 4, 8],
    [2, 4, 6],
]


def _normalize_cell(value: object) -> Optional[Cell]:
    """Normalize a cell to ''|'X'|'O' or return None if invalid."""
    if value == "" or value is None:
        return ""
    if value == "X" or value == "O":
        return value
    return None


def _normalize_board(board: Sequence[object]) -> Optional[List[Cell]]:
    """Normalize and validate a board into a list of 9 cells or return None."""
    if not isinstance(board, (list, tuple)):
        return None
    if len(board) != 9:
        return None
    normalized: List[Cell] = []
    for v in board:
        cell = _normalize_cell(v)
        if cell is None:
            return None
        normalized.append(cell)
    return normalized


# PUBLIC_INTERFACE
def validate_board(board: Sequence[object]) -> tuple[bool, Optional[str], Optional[List[Cell]]]:
    """Validate the tic-tac-toe board structure and values.

    Args:
        board: Sequence of length 9 containing '', 'X', or 'O' (or None for empty).

    Returns:
        (is_valid, reason, normalized_board)
    """
    normalized = _normalize_board(board)
    if normalized is None:
        return False, "Board must be an array of 9 cells containing '', 'X', or 'O'.", None

    x_count = sum(1 for c in normalized if c == "X")
    o_count = sum(1 for c in normalized if c == "O")
    if o_count > x_count or (x_count - o_count) > 1:
        return False, "Invalid turn counts (X must start and turns must alternate).", None

    # Can't have both players winning simultaneously.
    x_win = check_winner(normalized)["winner"] == "X"
    o_win = check_winner(normalized)["winner"] == "O"
    if x_win and o_win:
        return False, "Invalid board: both players cannot have a winning line.", None

    return True, None, normalized


# PUBLIC_INTERFACE
def check_winner(board: Sequence[object]) -> Outcome:
    """Compute winner/line without enforcing turn-count rules.

    Args:
        board: Sequence of length 9 containing '', 'X', or 'O' (or None for empty).

    Returns:
        Outcome dict with winner (or None), isDraw, and optional winningLine.
    """
    normalized = _normalize_board(board)
    if normalized is None:
        # Keep outcome stable; upstream should call validate_board.
        return {"winner": None, "isDraw": False, "winningLine": None}

    for line in WINNING_LINES:
        a, b, c = line
        if normalized[a] != "" and normalized[a] == normalized[b] == normalized[c]:
            return {"winner": normalized[a], "isDraw": False, "winningLine": list(line)}  # type: ignore[return-value]

    is_draw = all(cell != "" for cell in normalized)
    return {"winner": None, "isDraw": is_draw, "winningLine": None}


# PUBLIC_INTERFACE
def compute_outcome(board: Sequence[object]) -> Outcome:
    """Validate board and compute outcome.

    If the board is invalid, returns a neutral outcome (winner=None, isDraw=False).
    Callers should validate explicitly to get error reasons.

    Args:
        board: Sequence of length 9 containing '', 'X', or 'O' (or None for empty).

    Returns:
        Outcome dict.
    """
    valid, _, normalized = validate_board(board)
    if not valid or normalized is None:
        return {"winner": None, "isDraw": False, "winningLine": None}
    return check_winner(normalized)


# PUBLIC_INTERFACE
def validate_move(
    board: Sequence[object],
    move_index: int,
    player: Player,
) -> tuple[bool, Optional[str]]:
    """Validate whether a move is legal on the given board for the given player.

    Rules:
    - board must be valid (shape/values/turn counts, and not both winners)
    - move_index must be in [0..8]
    - target cell must be empty
    - game must not already be over (winner or draw)
    - player must match expected next player based on counts (X starts)

    Args:
        board: Current board.
        move_index: Index 0..8.
        player: 'X' or 'O'.

    Returns:
        (valid, reason)
    """
    if player not in ("X", "O"):
        return False, "Player must be 'X' or 'O'."

    valid_board, reason, normalized = validate_board(board)
    if not valid_board or normalized is None:
        return False, reason or "Invalid board."

    if not isinstance(move_index, int):
        return False, "moveIndex must be an integer."
    if move_index < 0 or move_index > 8:
        return False, "moveIndex must be between 0 and 8."

    outcome = check_winner(normalized)
    if outcome["winner"] is not None:
        return False, "Game is already over (winner decided)."
    if outcome["isDraw"]:
        return False, "Game is already over (draw)."

    x_count = sum(1 for c in normalized if c == "X")
    o_count = sum(1 for c in normalized if c == "O")
    expected: Player = "X" if x_count == o_count else "O"
    if player != expected:
        return False, f"It is {expected}'s turn."

    if normalized[move_index] != "":
        return False, "Cell is already occupied."

    return True, None
