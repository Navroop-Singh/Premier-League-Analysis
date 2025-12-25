import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# Load Data

df = pd.read_csv('data/epl_final.csv')
df["match_date"] = pd.to_datetime(df["match_date"])


st.title("Premier League 20 Years Analytics") 

# Build season column
df["season"] = df["match_date"].apply(
    lambda d: f"{d.year}/{str(d.year+1)[-2:]}" if d.month >= 8
    else f"{d.year-1}/{str(d.year)[-2:]}"
)

st.title("Team Analysis")

# =======================
# SIDEBAR FILTERS
# =======================
st.sidebar.header("Filters")

seasons = ["All Seasons (2000-2025)"] + sorted(df["season"].unique())
selected_season = st.sidebar.selectbox(
    "Select Season",
    seasons,
    index=len(seasons) - 1
)

# Apply season filter
if selected_season == "All Seasons (2000-2025)":
    ddf = df.copy()
    season_label = "All Seasons"
else:
    ddf = df[df["season"] == selected_season]
    season_label = selected_season

if ddf.empty:
    st.warning("No data available for this season.")
    st.stop()


# Team Selection

order = st.sidebar.radio("Order Teams", ("Ascending", "Descending"), horizontal=True)

teams = sorted(
    pd.concat([ddf["home_team"], ddf["away_team"]]).dropna().unique(),
    key=str.lower,
    reverse=(order == "Descending")
)

team = st.sidebar.selectbox("Select Team", teams)



# Build Matches 

home = ddf[ddf["home_team"] == team].copy()
away = ddf[ddf["away_team"] == team].copy()

home["venue"] = "Home"
away["venue"] = "Away"

home["goals_for"] = home["ft_home_goals"]
home["goals_against"] = home["ft_away_goals"]

away["goals_for"] = away["ft_away_goals"]
away["goals_against"] = away["ft_home_goals"]

matches = (
    pd.concat([home, away], ignore_index=True)
      .sort_values("match_date")
)


matches["result"] = "Loss"
matches.loc[matches["goals_for"] > matches["goals_against"], "result"] = "Win"
matches.loc[matches["goals_for"] == matches["goals_against"], "result"] = "Draw"

# SUMMARY

st.header(f"{team} — {season_label}")

c1, c2, c3 = st.columns(3)

c1.metric("Matches", len(matches))
c1.metric("Goals For", int(matches["goals_for"].sum()))
c1.metric("Goals Against", int(matches["goals_against"].sum()))

c2.metric("Home Goals", int(matches.loc[matches["venue"] == "Home", "goals_for"].sum()))
c2.metric("Away Goals", int(matches.loc[matches["venue"] == "Away", "goals_for"].sum()))

c3.metric("Wins", int((matches["result"] == "Win").sum()))
c3.metric("Draws", int((matches["result"] == "Draw").sum()))
c3.metric("Losses", int((matches["result"] == "Loss").sum()))

# Performance Chart 

st.subheader("Performance Charts")

if not matches.empty: 
    st.write('Goals per match (last 20)') 
    gpm = matches.set_index('match_date')[['goals_for']]
    st.bar_chart(gpm.tail(20), use_container_width=True)
    st.write('Goals by season')
    goals_by_year = ( matches .set_index('match_date')['goals_for'] .resample('Y') .sum() )
    st.line_chart(goals_by_year)

# Pie Chart 

st.write("Win / Draw / Loss Distribution")
pie = matches["result"].value_counts()

if not pie.empty:
    fig, ax = plt.subplots()
    ax.pie(pie.values, labels=pie.index, autopct="%1.1f%%", startangle=90)
    ax.axis("equal")
    st.pyplot(fig)



# DISCIPLINE (MATPLOTLIB)


st.subheader("Discipline")

# Detect discipline columns
discipline_cols = [c for c in matches.columns if "foul" in c or "card" in c]

if discipline_cols:
    discipline_totals = matches[discipline_cols].sum().astype(int)

    # Color logic
    colors = []
    for col in discipline_totals.index:
        if "yellow" in col.lower():
            colors.append("gold")
        elif "red" in col.lower():
            colors.append("red")
        else:
            colors.append("orange")  # fouls or others

    fig, ax = plt.subplots(figsize=(9, 4))
    bars = ax.bar(discipline_totals.index, discipline_totals.values, color=colors)

    ax.set_ylabel("Count")
    ax.set_title("Discipline Summary")

    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            str(int(height)),
            ha="center",
            va="bottom",
            fontsize=10
        )

    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    st.pyplot(fig)

else:
    st.info("No discipline data available.")


# Shots & Accuracy 

st.subheader("Shots & Accuracy")

shots = [c for c in matches.columns if "shot" in c]
if shots:
    totals = {c: int(matches[c].sum()) for c in shots}
    st.json(totals)

    shots_total = sum(matches[c].sum() for c in shots if "on" not in c)
    shots_on = sum(matches[c].sum() for c in shots if "on" in c)

    if shots_total > 0:
        st.write(f"**Shot Accuracy:** {shots_on / shots_total:.1%}")
else:
    st.info("No shot data available.")

# Team Comparison

st.subheader('Team Comparison')

team_b = st.selectbox(
    'Compare with',
    [t for t in teams if t != team]
)

def team_stats(team_name):
    h = ddf[ddf['home_team'] == team_name]
    a = ddf[ddf['away_team'] == team_name]

    gf = h['ft_home_goals'].sum() + a['ft_away_goals'].sum()
    ga = h['ft_away_goals'].sum() + a['ft_home_goals'].sum()

    wins = (
        (h['ft_home_goals'] > h['ft_away_goals']).sum() +
        (a['ft_away_goals'] > a['ft_home_goals']).sum()
    )

    draws = (
        (h['ft_home_goals'] == h['ft_away_goals']).sum() +
        (a['ft_away_goals'] == a['ft_home_goals']).sum()
    )

    points = wins * 3 + draws
    matches = len(h) + len(a)

    return matches, gf, ga, wins, draws, points

stats_a = team_stats(team)
stats_b = team_stats(team_b)

comparison = pd.DataFrame(
    [stats_a, stats_b],
    columns=['Matches', 'Goals For', 'Goals Against', 'Wins', 'Draws', 'Points'],
    index=[team, team_b]
)

st.table(comparison)

# Head to Head Matches 

st.subheader("Head to Head Matches")

h2h = ddf[
    ((ddf['home_team'] == team) & (ddf['away_team'] == team_b)) |
    ((ddf['home_team'] == team_b) & (ddf['away_team'] == team))
].copy()

if h2h.empty:
    st.info("No head to head matches this season.")
else:
    # Format date → remove 00:00:00
    h2h['match_date'] = h2h['match_date'].dt.strftime('%Y-%m-%d')

    # Reset index → remove left side numbers
    h2h = h2h.reset_index(drop=True)

    st.dataframe(
        h2h[['match_date','home_team','away_team','ft_home_goals','ft_away_goals']],
        use_container_width=True
    )

# Head to head Summary

st.subheader("Head to Head Summary")

h2h = ddf[
    ((ddf['home_team'] == team) & (ddf['away_team'] == team_b)) |
    ((ddf['home_team'] == team_b) & (ddf['away_team'] == team))
].copy()

if h2h.empty:
    st.info("No head to head matches.")
else:
    # Determine result from TEAM A perspective
    def h2h_result(row):
        if row['home_team'] == team:
            return 'Win' if row['ft_home_goals'] > row['ft_away_goals'] else \
                   'Loss' if row['ft_home_goals'] < row['ft_away_goals'] else 'Draw'
        else:
            return 'Win' if row['ft_away_goals'] > row['ft_home_goals'] else \
                   'Loss' if row['ft_away_goals'] < row['ft_home_goals'] else 'Draw'

    h2h['result'] = h2h.apply(h2h_result, axis=1)

    # Overall H2H record
    st.write("Overall H2H Record")
    st.write(h2h['result'].value_counts())

    # Last H2H matches (clean table)
    st.write("Last Head to Head Matches for this season")
    last_5_h2h = h2h.sort_values('match_date', ascending=False).head(5).copy()
    last_5_h2h['match_date'] = last_5_h2h['match_date'].dt.date  # remove time
    st.dataframe(
        last_5_h2h[
            ['match_date','home_team','away_team','ft_home_goals','ft_away_goals','result']
        ].reset_index(drop=True),
        use_container_width=True
    )

# =======================
# DOWNLOAD

st.download_button(
    "Download Team Data (CSV)",
    matches.to_csv(index=False),
    file_name=f"{team}_{season_label}.csv",
    mime="text/csv"
)