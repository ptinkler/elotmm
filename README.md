# elotmm

Splits players into two evenly matched teams by Elo rating. It takes `2 * team_size` players (1v1 up to
5v5), scores every distinct split by the difference between the two team averages, and picks one at random
from the splits within a tolerance of even, so the same players are not paired the same way every time. If
no split is within the tolerance, the closest one is used.

```python
from elotmm import TeamMatchMaking

tmm = TeamMatchMaking(team_size=5, tolerance=20)
tmm.add_player({"id": "1", "name": "PeteT", "elo": 1723})
# ... nine more
team_one, team_two = tmm.shuffle_teams()
```

`tolerance` is in average Elo points per team. Pass `rng=random.Random(seed)` for repeatable results.
Try it with `uv run python -m elotmm.example`.

## Development

```
uv sync
uv run pytest
uv run ruff check . && uv run ruff format --check .
```

Dependabot opens PRs only for security fixes and GitHub Actions; they merge themselves once the `check`
status passes.
