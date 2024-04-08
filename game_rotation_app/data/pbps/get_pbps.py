# -*- coding: utf-8 -*-
"""
Created on Tue Feb  6 18:28:26 2024

@author: dolavrent@gmail.com
"""
import os 
from nba_api.stats.endpoints import leaguegamelog, playbyplayv2
import time



def pull_and_save_df_pbps(season_end_year, subset=[],
                          data_dir='./', 
                          overwrite=False, 
                          return_dfs=False,
                          season_type='Regular Season'):
    
    season_str = '{}-{}'.format(season_end_year-1, str(season_end_year)[-2:])
    
    if not os.path.isdir(data_dir):
        os.makedirs(data_dir)
        print('making data directory: {}'.format(os.path.abspath(data_dir)))
              
    season_dir = os.path.join(data_dir, season_str )
    
    if season_type == 'Playoffs':
        season_dir += '_po'
    
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
    
    existing_gr_files = os.listdir(season_dir)
    print('~'*50)
    print('{} games played in {}{}'.format(len(lgl_matchup), 
                                           season_str, 
                                           ' (playoffs)' if season_type == 'Playoffs' else ''
                                           ))
    print('{} games found in {}'.format(len(existing_gr_files), os.path.abspath(season_dir)))
    print('~'*50)
    
    
    game_ids_to_pull = subset if len(subset) > 0 else season_game_ids
    
    df_pbps_to_return = []
    
    for game_id in game_ids_to_pull:
    
        # check if we already have it
        cur_fname = f'df_pbp_{game_id}.csv'
    
        if overwrite or cur_fname not in existing_gr_files:
                
            df_pbp = playbyplayv2.PlayByPlayV2(game_id=game_id).get_data_frames()[0]
            
            print(f'saving to {cur_fname}...')
            df_pbp.to_csv(os.path.join(season_dir, cur_fname))
            
            if return_dfs:
                df_pbps_to_return.append(df_pbp)
    
            time.sleep(0.6)

    return df_pbps_to_return

if __name__ == '__main__':
    
    dfs = pull_and_save_df_pbps(2024, subset=['0022300771'])
