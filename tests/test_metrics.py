import pandas as pd
from metrics import get_team_matches, summary


def make_sample():
    data = [
        {"match_date": "2024-08-10", "home_team": "A", "away_team": "B", "ft_home_goals": 2, "ft_away_goals": 1},
        {"match_date": "2024-08-17", "home_team": "C", "away_team": "A", "ft_home_goals": 0, "ft_away_goals": 0},
    ]
    df = pd.DataFrame(data)
    df["match_date"] = pd.to_datetime(df["match_date"])
    return df


def test_get_team_matches_and_summary():
    df = make_sample()
    matches = get_team_matches(df, "A")
    s = summary(matches)
    assert s["matches"] == 2
    assert s["goals_for"] == 2  # 2 at home + 0 away
    assert s["wins"] == 1
    assert s["draws"] == 1
    assert s["losses"] == 0
