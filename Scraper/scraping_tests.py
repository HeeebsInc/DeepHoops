import requests
from bs4 import BeautifulSoup
import pandas as pd

def get_table_info(link):
    response = requests.get(link)
    soup = BeautifulSoup(response.text, 'html.parser')

    columns = ['Player', 'Team', 'Against', 'Home', 'MP', 'FG', 'FGA', 'FG%', '3P', '3PA', '3P%', 'FT', 'FTA', 'FT%', 'ORB',
               'DRB', 'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS', '+/-']
    # column_2 = ['TS%', 'eFG%',
    #            'FTr', 'ORB%', 'DRB%', 'TRB%', 'AST%', 'STL%', 'BLK%', 'TOV%', 'USG%', 'ORtg', 'DRtg', 'BPM']
    header = soup.findAll('h1')[0].text.split(',')
    date = ''.join(header[-2:]).strip()
    teams = header[0].split('at')
    print(teams)
    away_team = teams[0].strip()
    home_team = teams[-1][:teams[-1].find('Box Score')].strip()
    if home_team == '':
        home_team = teams[-2][:teams[-2].find('Box Score')].strip()
    tables = soup.findAll('tbody')
    print(away_team, '|', home_team)
    print('~' * 50)
    # get unqiue players
    player_dict = {}
    away_idx = [0]
    home_idx = [8]
    for idx, table in enumerate(tables):
        # print(idx)
        # print(table)
        # print('~'*50)
        if idx not in away_idx + home_idx:
            continue
        if idx in away_idx:
            team = away_team
            opp = home_team
            home = 0
        else:
            team = home_team
            opp = away_team
            home = 1
        for row in table:
            try:
                name = row.findAll('th')[0].text
                if name == 'Reserves':
                    continue
                player_dict[name] = [name, date, team, opp, home]
            except AttributeError:
                continue
    for idx, table in enumerate(tables):
        if idx not in away_idx + home_idx:
            continue
        for row in table:
            try:
                name = row.findAll('th')[0].text
                cols = row.findAll('td')
                if len(cols) == 0:
                    continue
                cols = [i.text.strip() for i in cols]
                for c in cols:
                    player_dict[name].append(c)
                player_dict[name].append(link)
            except AttributeError:
                continue
    game_df_pieces = []
    for name, l in player_dict.items():
        row_dict = {col :value for col, value in zip(columns, l)}
        row_df = pd.DataFrame(row_dict, index = [0])
        game_df_pieces.append(row_df)
    game_df = pd.concat(game_df_pieces)
    # game_df.to_csv('Tester.csv', index = False)
    return game_df


link = 'https://www.basketball-reference.com/boxscores/201601130DEN.html'
get_table_info(link)

link = 'https://www.basketball-reference.com/boxscores/201601130OKC.html'
get_table_info(link)

link = 'https://www.basketball-reference.com/boxscores/201602030DAL.html'
get_table_info(link)



link = 'https://www.basketball-reference.com/boxscores/201512070MIA.html'
get_table_info(link)

link = 'https://www.basketball-reference.com/boxscores/201606100CLE.html'
get_table_info(link)

link = 'https://www.basketball-reference.com/boxscores/201511010MIA.html'
get_table_info(link)

link = 'https://www.basketball-reference.com/boxscores/201512180GSW.html'
get_table_info(link)
