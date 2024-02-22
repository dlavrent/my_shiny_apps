# -*- coding: utf-8 -*-
"""
Created on Tue Feb  6 22:05:04 2024

@author: dolavrent@gmail.com
"""
import os
from nba_api.stats.endpoints import leaguegamelog 

def pull_and_save_df_lgl(season_end_year, data_dir='data/lgls/', overwrite=True):

    
    season_str = '{}-{}'.format(season_end_year-1, str(season_end_year)[-2:])
    
    if not os.path.isdir(data_dir):
        os.makedirs(data_dir)
        print('making data directory: {}'.format(os.path.abspath(data_dir)))
        
   
    
    lgl = leaguegamelog.LeagueGameLog(league_id='00',
                                      player_or_team_abbreviation='T',
                                      season=season_str,
                                      season_type_all_star='Regular Season'
                                      ).get_data_frames()[0]
        
    lgl = lgl.sort_values(['GAME_DATE', 'GAME_ID']).reset_index(drop=True)
    
    fsave = os.path.join(data_dir, f'df_lgl_{season_str}.csv')
    if overwrite:
        print(f'saving to... {fsave}')
        lgl.to_csv(fsave)
    
    return lgl

'''
import pandas as pd
df_lgl = pd.read_csv('df_lgl_2023-24.csv', 
                     index_col=0, 
                     dtype={'GAME_ID': 'string'}
)

df_lgl[['TEAM_ID', 'TEAM_ABBREVIATION', 'TEAM_NAME']].drop_duplicates().to_csv('df_team_info_simple.csv')
df_lgl = df_lgl[df_lgl.MATCHUP.str.contains('vs.')]
df_lgl['home_abbrev'] = [x[:3] for x in df_lgl.MATCHUP]
df_lgl['away_abbrev'] = [x[-3:] for x in df_lgl.MATCHUP]

print(df_lgl.iloc[0]['GAME_ID'])
game_strs = (df_lgl
 .set_index('GAME_ID')
 .apply(lambda x: x['GAME_DATE']+': '+x['MATCHUP'].replace('.', ''),axis=1)
 )

print(game_strs)
'''

if __name__ == '__main__':
    lgl = pull_and_save_df_lgl(2024)