from __future__ import annotations

from typing import List, Literal, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.api.tictactoe_utils import compute_outcome, validate_move

Player = Literal["X", "O"]

openapi_tags = [
    {
        "name": "Health",
        "description": "Basic service health checks.",
    },
    {
        "name": "TicTacToe",
        "description": (
            "Minimal tic-tac-toe helpers.\n\n"
            "Design choice: Option (A) stateless utility endpoints.\n"
            "This keeps the backend minimal and robust while allowing the frontend "
            "to manage state locally or implement its own storage later."
        ),
    },
]

app = FastAPI(
    title="Tic Tac Toe Backend",
    description="FastAPI backend providing minimal tic-tac-toe validation and outcome computation.",
    version="0.1.0",
    openapi_tags=openapi_tags,
)

# Keep existing permissive CORS, but explicitly include frontend localhost:3000 compatibility.
# (allow_origins=["*"] cannot be used with allow_credentials=True in strict CORS setups,
# but Starlette historically allows it; we keep it to avoid breaking existing behavior.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ValidateMoveRequest(BaseModel):
    """Request payload for validating a move on a given board."""

    board: List[Literal["X", "O", ""]] = Field(
        ...,
        min_length=9,
        max_length=9,
        description="Board cells as an array of 9 strings: 'X', 'O', or '' (empty).",
        examples=[["X", "", "O", "", "X", "", "", "O", ""]],
    )
    moveIndex: int = Field(
        ...,
        ge=0,
        le=8,
        description="0-based index into the 9-cell board where the move is attempted.",
        examples=[4],
    )
    player: Player = Field(
        ...,
        description="Player attempting the move.",
        examples=["X"],
    )


class ValidateMoveResponse(BaseModel):
    """Response payload describing whether a move is valid and optional reason when invalid."""

    valid: bool = Field(..., description="True if the move is legal; otherwise false.")
    reason: Optional[str] = Field(
        default=None,
        description="If valid=false, a human-readable reason explaining why the move is invalid.",
        examples=["Cell is already occupied."],
    )


class ComputeOutcomeRequest(BaseModel):
    """Request payload for computing the outcome of a given board."""

    board: List[Literal["X", "O", ""]] = Field(
        ...,
        min_length=9,
        max_length=9,
        description="Board cells as an array of 9 strings: 'X', 'O', or '' (empty).",
        examples=[["X", "X", "X", "O", "O", "", "", "", ""]],
    )


class ComputeOutcomeResponse(BaseModel):
    """Response payload describing the game outcome."""

    winner: Optional[Player] = Field(
        default=None,
        description="Winner of the game if there is one; otherwise null.",
        examples=["X", None],
    )
    isDraw: bool = Field(..., description="True if the game is a draw (no winner, board full).")
    winningLine: Optional[List[int]] = Field(
        default=None,
        description="If there is a winner, the 3 indices of the winning line.",
        examples=[[0, 1, 2]],
    )


@app.get("/", tags=["Health"], summary="Health check", operation_id="health_check")
def health_check():
    """Health check endpoint.

    Returns:
        JSON object indicating the service is running.
    """
    return {"message": "Healthy"}


@app.post(
    "/validate-move",
    tags=["TicTacToe"],
    summary="Validate a tic-tac-toe move",
    description=(
        "Validates whether a move is legal given the current board and player.\n\n"
        "Rules enforced:\n"
        "- board shape/values\n"
        "- turn order based on counts (X starts, alternate)\n"
        "- move index in range\n"
        "- target cell empty\n"
        "- game not already finished"
    ),
    operation_id="validate_move",
    response_model=ValidateMoveResponse,
)
def validate_move_endpoint(payload: ValidateMoveRequest) -> ValidateMoveResponse:
    """Validate whether a move is legal for tic-tac-toe.

    Args:
        payload: Board, move index, and player.

    Returns:
        ValidateMoveResponse indicating validity and optional reason.
    """
    valid, reason = validate_move(payload.board, payload.moveIndex, payload.player)
    return ValidateMoveResponse(valid=valid, reason=reason)


@app.post(
    "/compute-outcome",
    tags=["TicTacToe"],
    summary="Compute tic-tac-toe outcome from a board",
    description=(
        "Computes winner/draw information from the given board.\n\n"
        "If the board is invalid (turn counts, etc.), the endpoint returns "
        "winner=null and isDraw=false."
    ),
    operation_id="compute_outcome",
    response_model=ComputeOutcomeResponse,
)
def compute_outcome_endpoint(payload: ComputeOutcomeRequest) -> ComputeOutcomeResponse:
    """Compute winner/draw information for tic-tac-toe.

    Args:
        payload: Board.

    Returns:
        ComputeOutcomeResponse containing winner, draw flag, and optional winning line.
    """
    outcome = compute_outcome(payload.board)
    return ComputeOutcomeResponse(
        winner=outcome.get("winner"),
        isDraw=bool(outcome.get("isDraw", False)),
        winningLine=outcome.get("winningLine"),
    )
