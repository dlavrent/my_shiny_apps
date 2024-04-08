# -*- coding: utf-8 -*-
"""
Created on Tue Feb  6 22:05:04 2024

@author: dolavrent@gmail.com
"""
import os
from nba_api.stats.endpoints import leaguegamelog 

def pull_and_save_df_lgl(season_end_year, 
                         data_dir='data/lgls/', 
                         let='T', 
                         overwrite=True,
                         season_type='Regular Season'):

    
    season_str = '{}-{}'.format(season_end_year-1, str(season_end_year)[-2:])
    
    if not os.path.isdir(data_dir):
        os.makedirs(data_dir)
        print('making data directory: {}'.format(os.path.abspath(data_dir)))
        
   
    
    lgl = leaguegamelog.LeagueGameLog(league_id='00',
                                      player_or_team_abbreviation=let,
                                      season=season_str,
                                      season_type_all_star=season_type,
                                      ).get_data_frames()[0]
    
        
    
    if let == 'T':
        lgl = lgl.sort_values(['GAME_DATE', 'GAME_ID', 'TEAM_ID']).reset_index(drop=True)
    else:
        lgl = lgl.sort_values(['GAME_DATE', 'GAME_ID', 'TEAM_ID', 'PLAYER_ID']).reset_index(drop=True)
        
        
    suffix = '' 
    if season_type == 'Playoffs':
        suffix = '_po'
    elif season_type == 'PlayIn':
        suffix = '_pi'
        
    fsave = os.path.join(data_dir, 'df_lgl_{}_{}{}.csv'.format(let, season_str, suffix))
    if overwrite:
        print(f'saving to... {fsave}')
        lgl.to_csv(fsave)
    
    return lgl



if __name__ == '__main__':
    lgl_T = pull_and_save_df_lgl(2024, 'T')
    lgl_P = pull_and_save_df_lgl(2024, 'P')