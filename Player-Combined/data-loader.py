import pandas as pd
import numpy as np
import shutil
import os
from tqdm import tqdm
from sklearn.preprocessing import StandardScaler
from sklearn.compose import ColumnTransformer
import pickle

pd.options.mode.chained_assignment = None


class DataLoader:
    def __init__(self, columns_to_include, book_type = 'FDP'):
        self.columns_to_include = columns_to_include + ['book']
        self.book_type = book_type
        self.player_data_dir = f'../../Data/player-bbref/original'
        self.player_data_dict = {i[:i.find('.csv')]: pd.read_csv(f'{self.player_data_dir}/{i}') for i in tqdm(os.listdir(self.player_data_dir),
                                                                                                              desc = 'Loading Player Files..')}

        combined_df = pd.concat([i[1] for i in self.player_data_dict.items()])
        self.unique_teams = {team: i for team, i in zip(combined_df.Team.unique(), range(1, len(combined_df.Team.unique())+1))}

    def get_data(self, timestep):
        pbar = tqdm(self.player_data_dict.items())
        self.timestep_player_dict = {}
        for player, player_df in pbar:
            pbar.set_description(f'Getting Timestep: {player}')
            player_season_dict = self.calculate_book_and_categorize_teams(player_df)
            combined_df = pd.concat([i[1] for i in player_season_dict.items()])
            # combined_df.to_csv('test/Test.csv')
            season_timestep_dict = self.get_timestep(player_season_dict, timestep)
            # pickle.dump(season_timestep_dict, open(f'test/Test.p', 'wb'))
            self.timestep_player_dict[player] = season_timestep_dict
        pbar.close()
        return self.timestep_player_dict
    def get_timestep(self, player_season_dict, timestep, train_size = .85):
        '''This function will create a timestep for each player and their givin seasons'''
        self.timestep = timestep
        feature_columns_transform = ['MP', 'FG', 'FGA', '3P', '3PA', 'FT',
               'FTA', 'ORB', 'DRB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS', 'book']
        feature_columns_nontransform = ['Date', 'season', 'Team', 'Against', 'Home', 'injured']
        # combined_col = ['Date', 'season'] + [i for i in feature_columns_nontransform if i in self.columns_to_include] + [i for i in feature_columns_transform if i in self.columns_to_include]
        # combined_col2 = [i for i in feature_columns_transform if i in self.columns_to_include] + ['Date', 'season'] + [i for i in feature_columns_nontransform if i in self.columns_to_include]
        timestep_dict = {'x_train': [], 'x_test': [], 'y_train': [], 'y_test': [], 'date_train': [], 'date_test': []}
        for season, season_df in player_season_dict.items():
            season_df.Date = pd.to_datetime(season_df.Date)
            season_df.sort_values('Date', ascending = True)
            player_df_len = len(season_df)
            train_len = int(train_size * player_df_len)
            train_df = season_df[:train_len]
            test_df = season_df[train_len:]
            ct = ColumnTransformer([
                ('standard_scaler', StandardScaler(), [i for i in feature_columns_transform if i in self.columns_to_include])
            ], remainder='passthrough')
            # train_df = ct.fit_transform(train_df)
            # test_df = ct.transform(test_df)
            # train_df, test_df = pd.DataFrame(train_df, columns= combined_col2), pd.DataFrame(test_df, columns=combined_col2)
            # train_df= train_df[[i for i in combined_col if i in self.columns_to_include or i in ['Date', 'Season']]]
            # test_df = test_df[[i for i in combined_col if i in self.columns_to_include or i in ['Date', 'Season']]]
            tts_dict = {'train': train_df, 'test': test_df}
            ignore = ['Date', 'season', 'book']
            for key, split_df in tts_dict.items():
                # x_values = []
                # y_values = []
                # dates = []
                for idx in range(timestep, len(split_df)):
                    subset_df = split_df[idx-timestep: idx]
                    date = split_df.iloc[idx].Date
                    y = split_df.iloc[idx].book
                    x = subset_df[[i for i in subset_df.columns if i not in ignore]].values
                    timestep_dict[f'date_{key}'].append(date)
                    timestep_dict[f'x_{key}'].append(x)
                    timestep_dict[f'y_{key}'].append(y)
                    # dates.append(date)
                    # x_values.append(x)
                    # y_values.append(y)
                # tts_dict[key] = {'x': np.array(x_values), 'y': np.array(y_values), 'date': np.array(dates)}
            # season_timestep_dict[season] = tts_dict
        timestep_dict = {key: np.array(item) for key, item in timestep_dict.items()}
        return timestep_dict

    def calculate_book_and_categorize_teams(self, player_df):
        '''This function is for calculating the formula for the book (FanDuel, etc.)
        The function will also categorize the teams so that it is a number instead of a string and remove unwanted columns.
        The function will also add a column (injured 1 v 0)

        The function will return a list where each index corresponds to a seperate season that the player played.  '''
        if self.book_type == 'FDP':
            player_df['book'] = (player_df['3P'] * 3) + (player_df.FG *2) + player_df.FT + (player_df.TRB * 1.2) + (player_df.AST * 1.5) \
                                    + (player_df.BLK * 3) + (player_df.STL * 3) - player_df.TOV
        else:
            raise Exception(f'You Have Not Made A Formula for book {self.book_type}')

        player_df.Team = player_df.Team.map(lambda x: self.unique_teams[x])
        player_df.Against = player_df.Against.map(lambda x: self.unique_teams[x])

        #get the rows where the player was injured or missed game
        def get_injured(row):
            is_nan = row.isnull()
            if is_nan.any():
                return 1
            return 0
        player_df['injured'] = player_df.apply(get_injured, axis = 1)
        player_df.fillna(0, inplace=True)
        # columns = ['Date', 'season', 'Team', 'Against', 'Home', 'injured', 'MP', 'FG', 'FGA', '3P', '3PA', 'FT',
        #  'FTA', 'ORB', 'DRB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS',  'book']
        # ignore = ['Player', 'GameLink', 'FDP', 'FG%', '3P%', 'FT%', 'TRB', '+/-']
        player_df = player_df[['Date', 'season'] + [i for i in self.columns_to_include]]
        unique_seasons = player_df.season.unique()
        player_season_dict = {season: player_df[player_df.season == season] for season in unique_seasons}
        return player_season_dict

    def create_pickle(self):
        pickle.dump(self.timestep_player_dict, open(f'../../Data/combined-bbref/{self.timestep}.p', 'wb'))


if __name__ == '__main__':
    columns = ['Team', 'Against', 'Home', 'injured', 'MP', 'FG', 'FGA', '3P', '3PA', 'FT',
               'FTA', 'ORB', 'DRB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS']
    data_loader = DataLoader(columns_to_include=columns)
    timestep_dict = data_loader.get_data(timestep = 10)
    data_loader.create_pickle()