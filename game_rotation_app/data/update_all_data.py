# -*- coding: utf-8 -*-
"""
Created on Tue Feb 13 15:30:45 2024

@author: dolavrent@gmail.com
"""

from lgls.get_lgls import pull_and_save_df_lgl
from pbps.get_pbps import pull_and_save_df_pbps
from game_rotations.get_game_rotations import pull_and_save_df_grs

season_end_year = 2024
pull_and_save_df_lgl(season_end_year, 
                     data_dir='lgls/',
                     let='T',
                     overwrite=True)
pull_and_save_df_lgl(season_end_year, 
                     data_dir='lgls/',
                     let='P',
                     overwrite=True)
pull_and_save_df_pbps(season_end_year, 
                      #subset=['0022300771', '0022300772', '0022300773'],
                      data_dir = 'pbps/', 
                      overwrite=False)
flagged_gameids = pull_and_save_df_grs(season_end_year, 
                                       #subset=['0022300857'],
                                       data_dir = 'game_rotations/', 
                                       overwrite=False)