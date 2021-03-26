from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import pandas as pd
import os
import numpy as np
import pickle
from tqdm import tqdm
import shutil
from sklearn.compose import ColumnTransformer

pd.options.mode.chained_assignment = None
pd.options.display.min_rows = 50



class GetPlayerData:
    def __init__(self, timestep, train_size = .92, train_on_player = 'all'):
        self.train_on_player = train_on_player
        self.train_size = train_size
        self.timestep = timestep
        self.data_dir = '/home/samuel-linux/PycharmProjects/Personal/FantasyBasketball/Data'
        self.bbreff_season_dir = f'{self.data_dir}/bbref-files/cleaned'
        self.player_dir = f'{self.data_dir}/player-bbref'
        self.original_player_dir = f'{self.player_dir}/original'
        self.timestep_player_dir = f'{self.player_dir}/timestepped'

        self.seperate_and_clean()
        #create files with timestep
        self.create_split_timestep()

    def create_timestep(self, player_df, feature_columns, target_column, player):
        # print(player_df.info())
        X = player_df[[i for i in feature_columns]]
        y = player_df[[target_column]]
        x_train, x_test, y_train, y_test = train_test_split(X,y, shuffle=False, train_size=self.train_size)
        ignore = ['Team', 'Against', 'Home', 'Date']

        #right now the the target variable is not being transformed
        ct = ColumnTransformer([
            ('standard_scaler', StandardScaler(), [i for i in feature_columns if i not in ignore])
            ], remainder='passthrough')
        transformed_x_train = ct.fit_transform(x_train)
        transformed_x_test = ct.transform(x_test)
        x_train[[i for i in x_train.columns if i not in ignore]+[i for i in x_train.columns if i in ignore]] = transformed_x_train
        x_test[[i for i in x_test.columns if i not in ignore]+[i for i in x_test.columns if i in ignore]] = transformed_x_test

        tts_dict = {'train': {'x': x_train, 'y': y_train}, 'test': {'x': x_test, 'y': y_test}}
        tts_dict_new = {}
        for key, df_dict in tts_dict.items():
            x = df_dict['x']
            y = df_dict['y']
            feature_timesteps = []
            target_idx = []
            x_dates = []
            y_dates = []
            pbar = tqdm(range(self.timestep, len(x)), desc = f'Creating Timestep | {player}')
            for idx in pbar:
                subset_df = x.iloc[idx - self.timestep: idx]
                feature_df = subset_df[[i for i in subset_df.columns if i != 'Date']].values
                date_df = subset_df[['Date']].values
                target_idx.append(idx)
                feature_timesteps.append(feature_df)
                x_dates.append(date_df)
                y_dates.append(x.iloc[idx][['Date']].values)

            tts_dict_new[f'x_{key}'] = np.array(feature_timesteps)
            tts_dict_new[f'x_{key}_date'] = np.array(x_dates)
            tts_dict_new[f'y_{key}_date'] = np.array(y_dates)
            tts_dict_new[f'y_{key}'] = y.iloc[target_idx]
            pbar.close()
        # tts_dict_new['y_test'], tts_dict_new['y_train'] = y_test, y_train,
        tts_dict_new['scaler'], tts_dict_new['columns'] = ct, [i for i in x_train.columns]

        # print(tts_dict_new)
        # for key, item in tts_dict_new.items():
        #     print(key)
        #     print(item.shape)
        return tts_dict_new

    def create_split_timestep(self):
        for player, player_df in self.player_df_dict.items():
            sub_player_dir = f'{self.timestep_player_dir}/{player}'
            sub_player_pickle_dir = f'{sub_player_dir}/pickles'
            sub_player_model_dir = f'{sub_player_dir}/models'
            sub_player_model_weights_dir = f'{sub_player_dir}/models/weights'
            sub_player_model_graph_dir = f'{sub_player_dir}/models/graphs'

            if not os.path.exists(sub_player_dir):
                os.mkdir(sub_player_dir)
                os.mkdir(sub_player_pickle_dir)
                os.mkdir(sub_player_model_dir)
                os.mkdir(sub_player_model_weights_dir)
                os.mkdir(sub_player_model_graph_dir)

            player_df.fillna(0, inplace=True)
            player_df.Date = pd.to_datetime(player_df.Date)
            player_df = player_df.sort_values(by = 'Date', ascending = True)
            unique_teams = pd.Series(player_df.Team.unique().tolist() + player_df.Against.unique().tolist()).unique()
            unique_teams = {team: idx+1 for idx, team in enumerate(unique_teams)}
            player_df.Against = player_df.Against.map(lambda x: unique_teams[x])
            player_df.Team = player_df.Team.map(lambda x: unique_teams[x])
            ignore = ['Player', 'GameLink', 'FDP', 'FG%', '3P%', 'FT%', 'TRB', '+/-']

            feature_columns = [i for i in player_df.columns if i not in ignore]
            target_column = 'FDP'
            tts_dict = self.create_timestep(player_df, feature_columns, target_column, player)

            pickle.dump(tts_dict, open(f'{sub_player_pickle_dir}/tts_{self.timestep}.p', 'wb'))



    def calculate_fanduel_points(self, player_df):
        player_df['FDP'] = (player_df['3P'] * 3) + (player_df.FG *2) + (player_df.FT) + (player_df.TRB * 1.2) + (player_df.AST * 1.5) \
                                + (player_df.BLK * 3) + (player_df.STL * 3) - (player_df.TOV)
        return player_df
    def seperate_and_clean(self):
        full_df = pd.concat([pd.read_csv(f'{self.bbreff_season_dir}/{i}') for i in os.listdir(self.bbreff_season_dir)])
        self.player_df_dict = {}
        if self.train_on_player == 'all':
            pbar = tqdm(full_df.Player.unique(), desc='Getting CSV for each player..')
            for player in pbar:
                subset_df = full_df[full_df.Player == player]
                subset_df = self.calculate_fanduel_points(subset_df)
                subset_df.to_csv(f'{self.original_player_dir}/{player}.csv', index=False)
                self.player_df_dict[player] = subset_df
            pbar.close()
        else:
            subset_df = full_df[full_df.Player == self.train_on_player]
            subset_df = self.calculate_fanduel_points(subset_df)
            subset_df.to_csv(f'{self.original_player_dir}/{self.train_on_player}.csv', index=False)
            self.player_df_dict[self.train_on_player] = subset_df






if __name__ == '__main__':
    player_data = GetPlayerData(timestep=5, train_on_player='Jrue Holiday')