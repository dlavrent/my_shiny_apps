"""
Code for pulling from nba_api's GameRotation endpoint for games
of a desired season and choice of regular season / play-in / playoffs
Warning that if you call this during a live game, you may get NaNs in the
point differential column for each player stint
"""

import os 
import numpy as np
import pandas as pd
from nba_api.stats.endpoints import leaguegamelog, gamerotation
import time

def pull_and_save_df_grs(season_end_year, data_dir = './', 
                         save_files=True, overwrite=False, 
                         season_type='Regular Season'):
    
    season_str = '{}-{}'.format(season_end_year-1, str(season_end_year)[-2:])
    
    if not os.path.isdir(data_dir):
        os.makedirs(data_dir)
        print('making data directory: {}'.format(os.path.abspath(data_dir)))
              
    season_dir = os.path.join(data_dir, season_str )
    
    if season_type == 'Playoffs':
        season_dir += '_po'
    elif season_type == 'PlayIn':
        season_dir += '_pi'
    
    if not os.path.isdir(season_dir):
        os.makedirs(season_dir)
        print('making season directory: {}'.format(os.path.abspath(season_dir)))
        
    
    lgl = leaguegamelog.LeagueGameLog(league_id='00',
                                      player_or_team_abbreviation='T',
                                      season=season_str,
                                      season_type_all_star=season_type,
                                      ).get_data_frames()[0]
    lgl_matchup = lgl[lgl.MATCHUP.str.contains('@')]
    season_game_ids = lgl_matchup['GAME_ID']
    
    suffix = '' 
    if season_type == 'Playoffs':
        suffix = ' (playoffs)'
    elif season_type == 'PlayIn':
        suffix = ' (play in)'
    
    existing_gr_files = os.listdir(os.path.abspath(season_dir))
    print('~'*50)
    print('{} games played in {}{}'.format(len(lgl_matchup), season_str, suffix))
    print('{} games found in {}'.format(len(existing_gr_files), os.path.abspath(season_dir)))
    print('~'*50)
    
    
    flagged_ids = []
    
    for game_id in season_game_ids:
    
        # check if we already have it
        cur_fname = f'df_gr_{game_id}.csv'
    
        if overwrite or cur_fname not in existing_gr_files:
                
            gr_res = gamerotation.GameRotation(game_id=game_id).get_data_frames()
            
            df_gr = pd.concat(gr_res)
            
            away_team_id = lgl_matchup[lgl_matchup.GAME_ID == game_id].iloc[0]['TEAM_ID']
            df_gr['h_a'] = 'home'
            df_gr.loc[df_gr['TEAM_ID'] == away_team_id, 'h_a'] = 'away'
    
            # check if any suspect data
            if np.any(df_gr['PT_DIFF'].isna()):
                print('flag!')
                print(f'NaN values found in {cur_fname}')
                flagged_ids.append(game_id)
                
            else:
                print(f'saving to {cur_fname}...')
                df_gr.to_csv(os.path.join(season_dir, cur_fname))
        
            time.sleep(0.6)

    return flagged_ids



if __name__ == '__main__':
    
    flagged_ids = pull_and_save_df_grs(2024)
    