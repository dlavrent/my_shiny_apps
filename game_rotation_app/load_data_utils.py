'''
Utility functions for loading in data
(dataframes for game rotations and play by plays)

These dataframes are pulled from nba.com/stats 
using a script in data/.

The functions here simply load in the saved dataframes
for use in the shiny app.
'''

import os 
import pandas as pd
import numpy as np


def get_gr(season_str, game_id,
           season_type='Regular Season'):
    '''
    Given a season string (i.e. 2023-24),
    and an nba.com/stats game_id (i.e. '0022300408'),
    retrieves game_rotations dataframe 
    from internal data directory
    if it exists.

    This directory is updated daily to add new
    game_rotation dataframes.    
    '''
    df_gr = pd.DataFrame()

    suffix = ''
    if season_type == 'Playoffs':
        suffix = '_po'
    elif season_type == 'PlayIn': 
        suffix = '_pi'
    season_dir = os.path.join(f'data/game_rotations/{season_str}{suffix}')
    if os.path.isdir(season_dir):

        existing_files = os.listdir(season_dir)

        cur_fname = f'df_gr_{game_id}.csv'

        if cur_fname in existing_files:
            df_gr = pd.read_csv(os.path.join(season_dir, cur_fname),
                                index_col=0,
                                dtype={'GAME_ID': 'string'})

    return df_gr

def clean_pbp(df_pbp):
    '''
    Utility function to clean up the SCOREMARGIN column in a play by play dataframe,
    notably changing 'TIE' to 0, and making it all numeric
    '''
    newscores = df_pbp['SCOREMARGIN'].str.replace('TIE', '0')
    df_pbp = df_pbp.drop(columns='SCOREMARGIN')
    df_pbp['SCOREMARGIN'] = [np.nan if pd.isna(x) else int(x) for x in newscores]
    return df_pbp

def get_pbp(season_str, game_id,
            season_type='Regular Season'):
    '''
    Given a season string (i.e. 2023-24),
    and an nba.com/stats game_id (i.e. '0022300408'),
    retrieves play by play dataframe 
    from internal data directory
    if it exists.

    This directory is updated daily to add new
    play by play dataframes.    
    '''

    df_pbp = pd.DataFrame()

    suffix = ''
    if season_type == 'Playoffs':
        suffix = '_po'
    elif season_type == 'PlayIn': 
        suffix = '_pi'
    season_dir = os.path.join(f'data/pbps/{season_str}{suffix}')
    if os.path.isdir(season_dir):

        existing_files = os.listdir(season_dir)

        cur_fname = f'df_pbp_{game_id}.csv'

        if cur_fname in existing_files:
            df_pbp = pd.read_csv(os.path.join(season_dir, cur_fname),
                                index_col=0,
                                dtype={'GAME_ID': 'string', 'SCOREMARGIN': 'string'})
            
            df_pbp = clean_pbp(df_pbp)
            
    return df_pbp


if __name__ == '__main__':

    # example game
    season_str = '2023-24'
    game_id = '0022300063'

    df_pbp = get_pbp(season_str, game_id)
    df_gr = get_gr(season_str, game_id)
    
    print('pbp:')
    print(df_pbp.head())
    
    print('game rotations:')
    print(df_gr.head())