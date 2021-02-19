import requests
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm
import time
import socket
import pickle
import os



class NBAStatScraper:
    def __init__(self, season_start_links):
        self.season_start_links = season_start_links
        self.base_url = 'https://www.basketball-reference.com'

        computer_name = socket.gethostname()

        if computer_name == 'samuel-linux':
            self.data_path = '/NN_FantasyBasketball/Scraper/Data'
        elif computer_name == 'samuel-pi':
            self.data_path = f'/home/pi/FantasyBasketball/NN_FantasyBasketball/Data'
        # self.data_path = '/NN_FantasyBasketball/Scraper/Data'

        if not os.path.exists(self.data_path):
            os.mkdir(self.data_path)
            os.mkdir(f'{self.data_path}/pickles')
            os.mkdir(f'{self.data_path}/bbref-files')

        self.team_dictionary = {
            'Atlanta Hawks': 'Atl', 'Boston Celtics': 'Bos',
            'Brooklyn Nets': 'Bkn', 'Charlotte Hornets': 'Cha',
            'Chicago Bulls': 'Chi', 'Cleveland Cavaliers': 'Cle',
            'Dallas Mavericks': 'Dal', 'Denver Nuggets': 'Den',
            'Detroit Pistons': 'Det', 'Golden State Warriors': 'GSW',
            'Houston Rockets': 'Hou', 'Indiana Pacers': 'Ind',
            'Los Angeles Lakers': 'LAL', 'Los Angeles Clippers': 'LAC',
            'Memphis Grizzlies': 'Mem', 'Miami Heat': 'Mia',
            'Milwaukee Bucks': 'Mil', 'Minnesota Timberwolves': 'Min',
            'New Orleans Pelicans': 'Nor', 'New York Knicks': 'NYK',
            'Oklahoma City Thunder': 'OKC', 'Orlando Magic': 'Orl',
            'Philadelphia 76ers': 'Phi', 'Phoenix Suns': 'Pho',
            'Portland Trail Blazers': 'Por', 'Sacramento Kings': 'Sac',
            'San Antonio Spurs': 'SAS', 'Toronto Raptors': 'Tor',
            'Utah Jazz': 'Uta', 'Washington Wizards': 'Was'
        }


    def scrape_stats(self):
        #get the url for each month in the season
        self.get_months()
        # print(self.month_url_dict)

        #get the game links for each game within each month
        self.get_game_links()
        # print(self.full_game_urls)

        #scrape each table in each game and save to dataframe
        self.get_game_stats()

    def get_game_stats(self):
        # self.full_game_urls = pickle.load(open(f'{self.data_path}/pickles/GameLinks.p', 'rb'))
        for season, game_links in self.full_game_urls.items():
            pieces = []
            pbar = tqdm(game_links, desc = f'Scraping Games: {season}')
            # total = 0
            for link in pbar:
                response = requests.get(link)
                soup = BeautifulSoup(response.text, 'html.parser')

                table_df = self.get_table_info(soup)
                pieces.append(table_df)
                # total += 1
                # if total == 50:
                #     break
            full_season_df = pd.concat(pieces)
            full_season_df.to_csv(f'{self.data_path}/bbref-files/{season}.csv', index = False)

    def get_table_info(self, soup):
        column_add = ['Player', 'Team', 'Against', 'Home']
        column_1 = ['MP', 'FG', 'FGA', 'FG%', '3P', '3PA', '3P%', 'FT', 'FTA', 'FT%', 'ORB',
                   'DRB', 'TRB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS', '+/-']
        # column_2 = ['TS%', 'eFG%',
        #            'FTr', 'ORB%', 'DRB%', 'TRB%', 'AST%', 'STL%', 'BLK%', 'TOV%', 'USG%', 'ORtg', 'DRtg', 'BPM']
        header = soup.findAll('h1')[0].text.split(',')
        date = ''.join(header[-2:]).strip()
        teams = header[0].split('at')
        away_team = teams[0].strip()
        home_team = teams[1][:teams[1].find('Box Score')].strip()
        tables = soup.findAll('tbody')

        away_team_stats = [tables[0], tables[1]]
        home_team_stats = [tables[2], tables[3]]

        #get unqiue players
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
                    player_dict[name] = [name, team, opp, home]
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
                except AttributeError:
                    continue
        game_df_pieces = []
        for name, l in player_dict.items():
            row_dict = {col:value for col, value in zip(column_add+column_1, l)}
            row_df = pd.DataFrame(row_dict, index = [0])
            game_df_pieces.append(row_df)
        game_df = pd.concat(game_df_pieces)
        # game_df.to_csv('Tester.csv', index = False)
        return game_df


        # cols = row.findAll('td')
        # if len(cols) == 0:
        #     continue
        # cols = [name, team, opp, home] + [i.text.strip() for i in cols]
        # print(cols)


        # table_1_pieces = []
        # for idx, table in enumerate(tables):
        #     # print(table)
        #     if idx in [0,1]:
        #         team = away_team
        #         opp = home_team
        #         home = 0
        #     else:
        #         team = home_team
        #         opp = away_team
        #         home = 1
        #     table_df_pieces = []
        #     for row in table:
        #         row_dict = {}
        #         try:
        #             name = row.findAll('th')[0].text
        #             cols = row.findAll('td')
        #             if len(cols) == 0:
        #                 continue
        #             cols = [name, team, opp, home] + [i.text.strip() for i in cols]
        #             print(cols)
        #         except AttributeError:
        #             continue
        #         # print(name)

    def get_game_links(self):
        self.full_game_urls = {}
        pbar = tqdm((enumerate(self.month_url_dict.items())), total = len(self.month_url_dict))
        for idx, (season, month_url_list) in pbar:
            pbar.set_description(f'({idx+1}-{len(self.month_url_dict)}) | Getting Game URLs: {season}')
            season_game_urls = []
            for month_url in month_url_list:
                response = requests.get(month_url)
                soup = BeautifulSoup(response.text, 'html.parser')
                time.sleep(1)
                table = soup.findAll('tbody')
                # print(table)
                game_links = table[0].findAll('a', href = True)
                for idx, link in enumerate(game_links):
                    if (idx + 1) % 4 != 0:
                        continue
                    full_url = f'{self.base_url}{link["href"]}'
                    season_game_urls.append(full_url)
            self.full_game_urls[season] = season_game_urls
            pbar.update()
        pbar.close()
        # pickle.dump(self.full_game_urls, open(f'{self.data_path}/pickles/GameLinks.p', 'wb'))
        del self.month_url_dict

    def get_months(self):
        months = ['october', 'november', 'december', 'january', 'february', 'march', 'april', 'may', 'june']
        self.month_url_dict = {}
        for season_start_link in self.season_start_links:
            response = requests.get(season_start_link)
            soup = BeautifulSoup(response.text, 'html.parser')
            season = soup.find('h1').text.split(' ')[0].strip()
            year = f'20{season[season.find("-")+1:]}'
            season_month_list = []
            for month in months:
                base_url = f'https://www.basketball-reference.com/leagues/NBA_{year}_games-{month}.html'
                season_month_list.append(base_url)
            self.month_url_dict[season] = season_month_list



if __name__ == '__main__':
    season_dict = ['https://www.basketball-reference.com/leagues/NBA_2015_games.html',
                   'https://www.basketball-reference.com/leagues/NBA_2017_games.html',
                    'https://www.basketball-reference.com/leagues/NBA_2018_games.html',
                    'https://www.basketball-reference.com/leagues/NBA_2019_games.html',
                    'https://www.basketball-reference.com/leagues/NBA_2020_games.html'][::-1]

    nba_stat_scraper = NBAStatScraper(season_dict)

    nba_stat_scraper.scrape_stats()
