from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import pandas as pd
import os
import numpy as np
import pickle
from tqdm import tqdm
import shutil

pd.options.mode.chained_assignment = None
pd.options.display.min_rows = 50



class GetPlayerData:
    def __init__(self, timestep, train_size = .8, train_on_player = 'all'):
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

    def create_timestep(self, subset_x, subset_y):

        # pbar = tqdm(subset_x.iterrows(), total = len(subset_x), )
        pass

    def create_split_timestep(self):
        for player, player_df in self.player_df_dict.items():
            sub_player_dir = f'{self.timestep_player_dir}/{player}'
            if not os.path.exists(sub_player_dir):
                os.mkdir(sub_player_dir)

            player_df.fillna(0, inplace=True)
            player_df.Date = pd.to_datetime(player_df.Date)
            player_df = player_df.sort_values(by = 'Date', ascending = True)
            unique_teams = pd.Series(player_df.Team.unique().tolist() + player_df.Against.unique().tolist()).unique()
            unique_teams = {team: idx+1 for idx, team in enumerate(unique_teams)}
            player_df.Against = player_df.Against.map(lambda x: unique_teams[x])
            player_df.Team = player_df.Team.map(lambda x: unique_teams[x])
            ignore = ['Player', 'GameLink', 'FDP']
            X = player_df[[i for i in player_df.columns if i not in ignore]]
            y = player_df[['FDP']]

            x_train, x_test, y_train, y_test = train_test_split(X, y, shuffle= False, train_size=self.train_size)

            x_train = self.create_timestep(x_train, y_train)
            x_test = self.create_timestep(x_test, y_test)



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
                break
            pbar.close()
        else:
            subset_df = full_df[full_df.Player == self.train_on_player]
            subset_df = self.calculate_fanduel_points(subset_df)
            subset_df.to_csv(f'{self.original_player_dir}/{self.train_on_player}.csv', index=False)
            self.player_df_dict[self.train_on_player] = subset_df






if __name__ == '__main__':
    player_data = GetPlayerData(10, train_on_player='Jrue Holiday')