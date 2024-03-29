import requests
from bs4 import BeautifulSoup
import pandas as pd
from Medium.mVariables import team_dictionary, month_list, month_dictionary
from Medium.emailFunc import error_sender

month_list = ['september','october', 'november', 'december', 'january', 'february', 'march', 'april', 'may', 'june']
month_dictionary = {'Jan': '01', 'Feb': '02',  'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06', 'Jul': '07', 'Oct': '10', 'Nov': '11', 'Dec': '12'}

def season_stats_getter(start_url):
    '''This function uses basketballreference.com as its retriever.  Go to the website, and find the season you would like to scrape.  Then click on the first month given in the season (october)
    After inputting this link, the program and determine the season and months given, and will scrape each box_score link on each month-page
    It will also create a csv holding the season stats'''
    base_url = 'https://www.basketball-reference.com'   #used for formatting each link correctly
    month_link_array = []
    response = requests.get(start_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    season = soup.find('h1').text
    season = season.strip().split(' ')
    season = season[0]
    body = soup.findAll('body')
    months = body[0].findAll('a', href = True)
    for i in months:
        if i.text.lower() in month_list:
            i = (i.text, f'{base_url}{i["href"]}')
            month_link_array.append(i)  #appending the url for each page to scrape
    #iterating through each month url to scrape the data
    page_tocheck_dict = {'Month': [], 'Url': [], 'Index': []}
    box_link_array = []
    all_dates = []
    for month, page in month_link_array:
        page_link_array = []
        page_date_array = []
        response = requests.get(page)
        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.findAll('tbody')
        box_scores = table[0].findAll('a', href=True)
        for i in box_scores:
            if i.text.strip() == 'Box Score':
                page_link_array.append(f'{base_url}{i["href"]}')
            if ',' in i.text.strip():
                date = i.text.strip()
                date = date.split(', ')
                year = date[2]
                date = date[1].split(' ')
                day = f'0{date[1]}' if len(date[1]) == 1 else date[1]

                mon = month_dictionary[date[0]]
                date = f'{year}{mon}{day}'
                page_date_array.append(date)
        if len(page_link_array) == 0 or len(box_scores) / len(page_link_array) != 4:
            page_tocheck_dict['Url'].append(page)
            page_tocheck_dict['Month'].append(month)
            page_tocheck_dict['Index'].append(len(page_link_array))
        else:
            page_tocheck_dict['Url'].append(page)
            page_tocheck_dict['Month'].append(month)
            page_tocheck_dict['Index'].append(None)
        box_link_array.append(page_link_array)
        all_dates.append(page_date_array)
    print(box_link_array)
    df_columns = ['Date', 'GameID', 'Name', 'Team', 'OPP', 'Home', 'Away', 'MP', 'FG', 'FGA', 'FG%', '3P', '3PA',
                  '3P%', 'FT', 'FTA', 'FT%', 'ORB', 'DRB', 'TRB', 'AST', 'STL', 'BLK',
                  'TOV', 'PF', 'PTS', '+-' ]
    error_df = pd.DataFrame(columns = ['URL', 'Error'])
    stat_df = pd.DataFrame(columns = df_columns)
    print(box_link_array)
    for idx_pos, (l, d) in enumerate(zip(box_link_array, all_dates)):
        for link, date in zip(l, d):
            print(f'{link}\n{date}')
            print(f'{idx_pos}- Currently Scraping {link}')
            try:
                response = requests.get(link)
                soup = BeautifulSoup(response.text, 'html.parser')
                # first table
                tables = soup.find('table', {'class': "sortable stats_table"})
                team1 = tables.text.split('\n')[0]
                parenthesis = team1.find('(')
                team1 = team_dictionary[team1[:parenthesis - 1]]
                table1 = tables.find('tbody')
                table1 = table1.find_all('tr')
                #second table
                tables = soup.findAll('table', {'class': "sortable stats_table"})
                team2 = tables[9].text.split('\n')[0]
                if team2.strip() == 'Table':
                    team2 = tables[10].text.split('\n')[0]
                parenthesis = team2.find('(')
                team2 = team_dictionary[team2[:parenthesis - 1]]
                table2 = tables[9].find('tbody')
                table2 = table2.find_all('tr')
                game_id = f'{date}-{team1}-{team2}'
                print(f'({date})\tH: {team1}\tA: {team2}')
                for idx, t in enumerate([table1, table2]):
                    if idx == 0:
                        opp = team2
                        team = team1
                        home = 1
                        away = 0
                    else:
                        opp = team1
                        team = team2
                        home = 0
                        away = 1
                    rows = []
                    for row in t:
                        name = row.findAll('th')[0].text
                        cols = row.findAll('td')
                        cols = [i.text.strip() for i in cols]
                        cols.append(name)
                        rows.append(cols)
                    for player in rows:
                        if len(player) < 21:
                            if 'Did Not' in player[0]:
                                print(player, len(player))
                                player_dic = {'Date': date, 'GameID': game_id, 'Name': player[-1], 'Team': team, 'OPP': opp,
                                              'Home': home, 'Away': away, 'MP': 0, 'FG': 0, 'FGA': 0, 'FG%': 0, '3P': 0, '3PA': 0,
                                              '3P%': 0, 'FT': 0, 'FTA': 0, 'FT%': 0,'ORB': 0, 'DRB': 0, 'TRB': 0, 'AST': 0,
                                              'STL': 0, 'BLK': 0, 'TOV': 0, 'PF': 0, 'PTS': 0, '+-': 0
                                              }
                                stat_df = stat_df.append(player_dic, ignore_index=True)
                                continue
                            else:
                                print('IGNORE', player)
                                continue
                        else:
                            player = [0 if i == '' else i for i in player]
                            colon = player[0].find(':')
                            time = f'{player[0][:colon]}.{player[0][colon + 1::]}'
                            print(player, len(player))
                            player_dic = {'Date': date, 'GameID': game_id, 'Name': player[-1], 'Team': team, 'OPP': opp,
                                          'Home':home, 'Away': away, 'MP': time, 'FG': player[1], 'FGA': player[2],
                                          'FG%': player[3], '3P': player[4], '3PA': player[5],
                                          '3P%': player[6],  'FT': player[7], 'FTA': player[8], 'FT%': player[9],
                                          'ORB': player[10], 'DRB': player[11], 'TRB': player[12], 'AST': player[13],
                                          'STL': player[14], 'BLK': player[15], 'TOV': player[16], 'PF': player[17],
                                          'PTS': player[18], '+-': player[19]
                                          }
                            stat_df = stat_df.append(player_dic, ignore_index=True)
                            continue
                print(f'Finished Scraping: {link}')
            except Exception as e:
                raise
                print(f'Error Scraping: {link}')
                error = {'URL': {link}, 'Error': str(e)}
                error_df = error_df.append(error, ignore_index=True)
                error_df.to_csv(f'Errors_Season({season}).csv', line_terminator='\n', index=False)
                error_sender(error = str(e))

        stat_df.to_csv(f'Season({season}).csv', line_terminator='\n', index=False)
        message = f'Saved game stats for the {season} season to a csv'
        print(message)

    stat_df.to_csv(f'Season({season}).csv', line_terminator='\n', index=False)
    message = f'Saved game stats for the {season} season to a csv'
    print(message)

season14_15 = 'https://www.basketball-reference.com/leagues/NBA_2015_games.html' #2014-15
season16_17 = 'https://www.basketball-reference.com/leagues/NBA_2017_games.html'
season17_18 = 'https://www.basketball-reference.com/leagues/NBA_2018_games.html'
season18_19 = 'https://www.basketball-reference.com/leagues/NBA_2019_games.html'
season19_20 = 'https://www.basketball-reference.com/leagues/NBA_2020_games.html' #2019-20
season_stats_getter(season19_20)
# link_array = [season16_17, season17_18, season18_19, season19_20]
#
# for link in link_array[::-1]:
#     season_stats_getter(link)