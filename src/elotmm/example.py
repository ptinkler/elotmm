"""Run with ``uv run python -m elotmm.example``."""

from elotmm import TeamMatchMaking
from elotmm.tmmcalc import team_average

PLAYERS = (
    {"id": "1", "name": "PeteT", "elo": 1723},
    {"id": "2", "name": "MattT", "elo": 1489},
    {"id": "3", "name": "AlexB", "elo": 1616},
    {"id": "4", "name": "RobF", "elo": 1618},
    {"id": "5", "name": "ChrisF", "elo": 1564},
    {"id": "6", "name": "ChrisH", "elo": 1644},
    {"id": "7", "name": "AlexH", "elo": 1430},
    {"id": "8", "name": "RichB", "elo": 1512},
    {"id": "9", "name": "MarkG", "elo": 1309},
    {"id": "10", "name": "TimH", "elo": 1829},
)


def main() -> None:
    tmm = TeamMatchMaking(team_size=5)
    for player in PLAYERS:
        tmm.add_player(player)
    one, two = tmm.shuffle_teams()
    for label, team in (("Team one", one), ("Team two", two)):
        names = ", ".join(player["name"] for player in team)
        print(f"{label} (average Elo {team_average(team):.1f}): {names}")


if __name__ == "__main__":
    main()
