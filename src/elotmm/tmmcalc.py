"""Balance two teams by Elo rating.

``TeamMatchMaking`` takes ``2 * team_size`` players and splits them into two teams whose average Elo
ratings are close, picking at random among the near-even splits so the same players are not paired
the same way every time.
"""

from __future__ import annotations

import logging
import random
from itertools import combinations
from typing import Any

log = logging.getLogger(__name__)

Player = dict[str, Any]

MIN_TEAM_SIZE = 1
MAX_TEAM_SIZE = 5
REQUIRED_FIELDS = ("id", "name", "elo")


class TeamMatchMaking:
    """Collect players, then split them into two evenly matched teams.

    ``team_size`` is the number of players per side (1 to 5, so 5v5 by default). ``tolerance`` is how
    far, in average Elo points, a split may be from perfectly even and still be a candidate for
    ``shuffle_teams``; if no split is that close, the closest one is used. ``rng`` is the random
    source, for repeatable results.
    """

    def __init__(
        self,
        *,
        team_size: int = 5,
        tolerance: float = 20.0,
        rng: random.Random | None = None,
    ) -> None:
        self.player_list: list[Player] = []
        self.team_one: list[Player] = []
        self.team_two: list[Player] = []
        self.team_size = 5
        self.set_team_size(team_size)
        self.tolerance = tolerance
        self._rng = rng or random.Random()  # noqa: S311 - not security related

    @property
    def match_full(self) -> bool:
        return len(self.player_list) >= self.team_size * 2

    def set_team_size(self, team_size: int) -> None:
        """Set the players per side, between 1v1 and 5v5."""
        team_size = int(team_size)
        if not MIN_TEAM_SIZE <= team_size <= MAX_TEAM_SIZE:
            msg = f"Team size must be between {MIN_TEAM_SIZE} and {MAX_TEAM_SIZE}"
            raise ValueError(msg)
        if len(self.player_list) > team_size * 2:
            msg = "There are already more players than the new team size takes"
            raise ValueError(msg)
        self.team_size = team_size
        log.debug("Team size set to %d vs %d", team_size, team_size)

    def add_player(self, player: Player) -> None:
        """Add a player: a dict with ``id``, ``name`` and a numeric ``elo``."""
        for field in REQUIRED_FIELDS:
            if player.get(field) is None:
                msg = f"Missing player field: {field}"
                raise ValueError(msg)
        if isinstance(player["elo"], bool) or not isinstance(player["elo"], int | float):
            msg = "Player field elo must be a number"
            raise ValueError(msg)
        if any(existing["id"] == player["id"] for existing in self.player_list):
            msg = f"Duplicate player id: {player['id']}"
            raise ValueError(msg)
        if self.match_full:
            msg = "The match is full"
            raise ValueError(msg)
        self.player_list.append(player)
        log.debug("Added player: %s", player["name"])

    def remove_player(self, player_id: Any) -> None:
        """Remove the player with this id, if there is one."""
        for i, player in enumerate(self.player_list):
            if player["id"] == player_id:
                del self.player_list[i]
                log.debug("Removed player: %s", player["name"])
                return

    def shuffle_teams(self) -> tuple[list[Player], list[Player]]:
        """Split the players into two teams of near-equal average Elo, and return them.

        Every distinct split is scored by the difference between the two team averages. One is picked
        at random from those within ``tolerance`` of even (or the closest one, if none is), and the
        sides are swapped at random. The result is also kept in ``team_one`` and ``team_two``.
        """
        if len(self.player_list) != self.team_size * 2:
            msg = f"Need exactly {self.team_size * 2} players, have {len(self.player_list)}"
            raise ValueError(msg)
        players = self.player_list
        total = sum(player["elo"] for player in players)
        # The first player is always on team one, so a split and its mirror image count once.
        splits = [
            (gap(total, sum(players[i]["elo"] for i in (0, *rest)), self.team_size), (0, *rest))
            for rest in combinations(range(1, len(players)), self.team_size - 1)
        ]
        best = min(g for g, _ in splits)
        candidates = [indexes for g, indexes in splits if g <= max(best, self.tolerance)]
        chosen = set(self._rng.choice(candidates))
        one = [player for i, player in enumerate(players) if i in chosen]
        two = [player for i, player in enumerate(players) if i not in chosen]
        if self._rng.random() < 0.5:  # noqa: PLR2004 - a coin toss for the sides
            one, two = two, one
        self.team_one, self.team_two = one, two
        log.debug("Teams: %s vs %s", [p["name"] for p in one], [p["name"] for p in two])
        return one, two


def team_average(team: list[Player]) -> float:
    """The average Elo of a team."""
    return sum(player["elo"] for player in team) / len(team)


def gap(total: float, team_total: float, team_size: int) -> float:
    """How far apart the two team averages are, given the total Elo and one team's total."""
    return abs(team_total - (total - team_total)) / team_size
