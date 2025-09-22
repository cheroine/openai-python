from openai.helpers import battleship


def test_counts_independent_ships_from_strings() -> None:
    board = [
        "X..X",
        "...X",
        "X..X",
    ]

    assert battleship(board) == 3


def test_counts_ships_from_numeric_board() -> None:
    board = [
        [1, 1, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1],
    ]

    assert battleship(board) == 2


def test_single_string_board() -> None:
    board = "XX\n.."

    assert battleship(board) == 1


def test_hit_marker_is_counted_as_ship() -> None:
    board = [
        "H..",
        "..#",
    ]

    assert battleship(board) == 2
