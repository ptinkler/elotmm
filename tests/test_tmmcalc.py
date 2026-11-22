import random
from itertools import combinations

import pytest

from elotmm import TeamMatchMaking, team_average
from elotmm.example import PLAYERS


def make(players=PLAYERS, **kwargs):
    tmm = TeamMatchMaking(rng=random.Random(1), **kwargs)
    for player in players:
        tmm.add_player(dict(player))
    return tmm


def best_gap(players, size):
    total = sum(p["elo"] for p in players)
    return min(abs(total - 2 * sum(p["elo"] for p in team)) / size for team in combinations(players, size))


def test_teams_partition_the_players():
    one, two = make().shuffle_teams()
    assert len(one) == len(two) == 5
    assert sorted(p["id"] for p in one + two) == sorted(p["id"] for p in PLAYERS)


def test_zero_tolerance_gives_the_best_split():
    tmm = make(tolerance=0)
    for _ in range(20):
        one, two = tmm.shuffle_teams()
        assert abs(team_average(one) - team_average(two)) == pytest.approx(best_gap(PLAYERS, 5))


def test_tolerance_bounds_the_gap():
    tmm = make(tolerance=30)
    for _ in range(50):
        one, two = tmm.shuffle_teams()
        assert abs(team_average(one) - team_average(two)) <= 30


def test_tolerance_gives_variety():
    tmm = make(tolerance=30)
    splits = {frozenset(p["id"] for p in tmm.shuffle_teams()[0]) for _ in range(100)}
    assert len(splits) > 2


def test_falls_back_to_closest_when_nothing_is_within_tolerance():
    players = [{"id": str(i), "name": f"p{i}", "elo": e} for i, e in enumerate([1000, 2000, 1000, 2000])]
    tmm = make(players, team_size=2, tolerance=0)
    one, two = tmm.shuffle_teams()
    assert team_average(one) == team_average(two) == 1500


def test_result_is_kept_on_the_object():
    tmm = make(team_size=1, players=PLAYERS[:2])
    one, two = tmm.shuffle_teams()
    assert (tmm.team_one, tmm.team_two) == (one, two)


def test_both_sides_get_picked_for_team_one():
    players = PLAYERS[:2]
    tmm = make(players, team_size=1)
    firsts = {tmm.shuffle_teams()[0][0]["id"] for _ in range(40)}
    assert firsts == {"1", "2"}


def test_seeded_rng_is_repeatable():
    first = [p["id"] for p in make().shuffle_teams()[0]]
    again = [p["id"] for p in make().shuffle_teams()[0]]
    assert first == again


@pytest.mark.parametrize("size", [1, 2, 3, 4, 5])
def test_every_team_size(size):
    tmm = make(PLAYERS[: size * 2], team_size=size)
    one, two = tmm.shuffle_teams()
    assert len(one) == len(two) == size


def test_wrong_number_of_players_cannot_shuffle():
    with pytest.raises(ValueError, match="Need exactly 10 players, have 9"):
        make(PLAYERS[:9]).shuffle_teams()


@pytest.mark.parametrize("size", [0, 6, -1])
def test_team_size_is_validated(size):
    with pytest.raises(ValueError, match="between 1 and 5"):
        TeamMatchMaking(team_size=size)


def test_team_size_cannot_drop_below_the_players_already_added():
    tmm = make()
    with pytest.raises(ValueError, match="more players"):
        tmm.set_team_size(4)


@pytest.mark.parametrize("field", ["id", "name", "elo"])
def test_missing_field_is_rejected(field):
    player = {"id": "x", "name": "x", "elo": 1500}
    del player[field]
    with pytest.raises(ValueError, match=f"Missing player field: {field}"):
        make([]).add_player(player)


def test_elo_of_zero_is_a_valid_rating():
    tmm = make([])
    tmm.add_player({"id": "x", "name": "x", "elo": 0})
    assert len(tmm.player_list) == 1


@pytest.mark.parametrize("elo", ["1500", None, True])
def test_elo_must_be_a_number(elo):
    with pytest.raises(ValueError, match="elo"):
        make([]).add_player({"id": "x", "name": "x", "elo": elo})


def test_duplicate_id_is_rejected():
    tmm = make(PLAYERS[:2])
    with pytest.raises(ValueError, match="Duplicate player id: 1"):
        tmm.add_player({"id": "1", "name": "again", "elo": 1500})


def test_full_match_rejects_more_players():
    tmm = make()
    assert tmm.match_full
    with pytest.raises(ValueError, match="full"):
        tmm.add_player({"id": "99", "name": "late", "elo": 1500})


def test_remove_player_frees_a_slot():
    tmm = make()
    tmm.remove_player("3")
    assert not tmm.match_full
    assert "3" not in [p["id"] for p in tmm.player_list]
    tmm.add_player({"id": "99", "name": "late", "elo": 1500})
    assert tmm.match_full


def test_removing_an_unknown_player_does_nothing():
    tmm = make()
    tmm.remove_player("nope")
    assert len(tmm.player_list) == 10
