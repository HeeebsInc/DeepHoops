import requests
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm
import time
import socket
import pickle



class NBAStatScraper:
    def __init__(self, season_start_links):
        self.season_start_links = season_start_links
        self.base_url = 'https://www.basketball-reference.com'

        computer_name = socket.gethostname()

        if computer_name == 'samuel-linux':
            self.data_path = '/home/samuel-linux/PycharmProjects/Personal/FantasyBasketball/NN_FantasyBasketball/Data'

    def scrape_stats(self):
        # #get the url for each month in the season
        # self.get_months()
        # # print(self.month_url_dict)
        #
        # #get the game links for each game within each month
        # self.get_game_links()
        # # print(self.full_game_urls)

        #scrape each table in each game and save to dataframe
        self.get_game_stats()

    def get_game_stats(self):
        self.full_game_urls = pickle.load(open(f'{self.data_path}/GameLinks.p', 'rb'))
        for season, game_links in self.full_game_urls.items():
            csv_path = f'{self.data_path}/Stats-{season}.csv'
            stat_df = pd.DataFrame()
            pbar = tqdm(game_links, desc = f'Scraping Games: {season}')
            for link in pbar:
                response = requests.get(link)
                soup = BeautifulSoup(response.text, 'html.parser')
                tables = soup.findAll('tbody')
                print(tables)

                break

    def get_table_info(self):
        pass
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
        pickle.dump(self.full_game_urls, open(f'{self.data_path}/GameLinks.p', 'wb'))
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


            break

        #     month_links = []
        #     response = requests.get(season_page)
        #     soup = BeautifulSoup(response.text, 'html.parser')
        #     season = soup.find('h1').text
        #     print(season)
        #     months = soup.findAll('body')[0].findAll('a', href = True)
        #     for month in months:
        #         month_url= (month.text, f'{self.base_url}{month["href"]}')
        #         month_links.append(month_url)
        #     month_dict[season] = month_links
        # return month_dict







if __name__ == '__main__':
    season_dict = {'https://www.basketball-reference.com/leagues/NBA_2015_games.html',
                   'https://www.basketball-reference.com/leagues/NBA_2017_games.html',
                    'https://www.basketball-reference.com/leagues/NBA_2018_games.html',
                    'https://www.basketball-reference.com/leagues/NBA_2019_games.html',
                    'https://www.basketball-reference.com/leagues/NBA_2020_games.html'}

    nba_stat_scraper = NBAStatScraper(season_dict)

    nba_stat_scraper.scrape_stats()
