"""
Script that should bring all necessary data in 
(i.e. league game logs, play by plays, and game rotation info)
for shiny app.

I use crontab to run this script once a day, in the deep of night,
so that the information is complete
(if you call GameRotation while a game is still live, you may not get
     all the player stint point differentials)
"""

import os
file_path = os.path.abspath(__file__)
file_dir = os.path.abspath(os.path.join(file_path, os.pardir))


from lgls.get_lgls import pull_and_save_df_lgl
from pbps.get_pbps import pull_and_save_df_pbps
from game_rotations.get_game_rotations import pull_and_save_df_grs

season_end_year = 2024

season_types = ['Regular Season', 'PlayIn', 'Playoffs']

for season_type in season_types:
    
    pull_and_save_df_lgl(season_end_year, 
                         data_dir=os.path.join(file_dir, 'lgls/'),
                         let='T',
                         overwrite=True,
                         season_type=season_type)
    pull_and_save_df_lgl(season_end_year, 
                         data_dir=os.path.join(file_dir, 'lgls/'),
                         let='P',
                         overwrite=True,
                         season_type=season_type)
    pull_and_save_df_pbps(season_end_year, 
                          data_dir=os.path.join(file_dir, 'pbps/'), 
                          overwrite=False,
                          season_type=season_type)
    flagged_gameids = pull_and_save_df_grs(season_end_year, 
                                           data_dir = os.path.join(file_dir, 'game_rotations/'), 
                                           overwrite=False,
                                           season_type=season_type)