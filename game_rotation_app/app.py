from functools import partial
from shiny.ui import page_navbar
from shiny import reactive, render
from shiny.express import input, ui

import numpy as np
import pandas as pd
import os

from load_data_utils import get_gr, get_pbp
from plot_utils import make_final_fig

ui.page_opts(title="NBA Rotation Plots", 
             page_fn=partial(page_navbar, id='page'),
             fillable=False)


# load relevant data
data_dir = './data/'
df_team_info = pd.read_csv(os.path.join(data_dir, 'df_team_info.csv'))

tms_byalphabet = np.sort(df_team_info['TEAM_ABBREVIATION'].values)

# TO-DO: ADD MORE YEARS!
season_end_yrs = [2024, 2023]
season_strs = ['{}-{}'.format(season_end_year-1, str(season_end_year)[-2:]) for season_end_year in season_end_yrs]

df_lgl_all = []
for s_str in season_strs:
    cur_lgl = pd.read_csv(os.path.join(data_dir, f'lgls/df_lgl_{s_str}.csv'), 
                            dtype={'GAME_ID': str},
                            index_col=0)
    cur_lgl['season_str'] = s_str
    df_lgl_all.append(cur_lgl)
df_lgl_all = pd.concat(df_lgl_all)

with ui.nav_panel('Main Application'):
    
    with ui.layout_sidebar():
        with ui.sidebar():
            with ui.accordion(id='plot_settings',bg='#f8f8f8', open='Game Selection'):

                with ui.accordion_panel('Game Selection'):
                    ui.input_selectize(
                        "season_str", "Select a season:",
                        {x: x for x in season_strs},
                    )

                    ui.input_selectize(  
                        "away_team",  "Select away team:",  
                        {x: x for x in tms_byalphabet},
                    )  

                    ui.input_selectize(  
                        "home_team",  "Select home team:",  
                        {x: x for x in tms_byalphabet},
                    )  

                    game_choices = []
                    ui.input_selectize(  
                        "game_id", "Select the game:",  
                        {x: x for x in game_choices}
                    )  

                    # update games based on whether away/home have played
                    @reactive.effect 
                    def _():
                            
                        input_season_str = input.season_str()
                        
                        df_lgl = pd.read_csv(os.path.join(data_dir, f'lgls/df_lgl_{input_season_str}.csv'), 
                            dtype={'GAME_ID': str},
                            index_col=0)

                        df_lgl = df_lgl[df_lgl.MATCHUP.str.contains('@')]

                        df_lgl['home_abbrev'] = [x[-3:] for x in df_lgl.MATCHUP]
                        df_lgl['away_abbrev'] = [x[:3] for x in df_lgl.MATCHUP]
                        
                        df_sub = df_lgl[(df_lgl.home_abbrev == input.home_team()) & \
                                        (df_lgl.away_abbrev == input.away_team())# | \
                                        ]

                        game_strs = (df_sub
                            .set_index('GAME_ID')
                            .apply(lambda x: x['GAME_DATE']+': '+x['MATCHUP'].replace('.', ''),axis=1)
                        )

                        ui.update_selectize("game_id", choices={str(game_strs.index[i]):str(game_strs.values[i]) for i in range(len(game_strs))})
                
                with ui.accordion_panel('Plot Settings'):
                    ui.input_checkbox("checkbox_plottext", 
                                "Annotate with shift +/-", 
                                False)  
                    
                    ui.input_selectize("plot_cmap_name", 
                                "Colormap for shift +/-'s", 
                                ['RdBu_r', 'PiYG', 'bwr', 'PuOr'])  
                    
        with ui.card():  
            ui.card_header("Rotation Plot")

            @render.plot(width=1250, height=800, alt='rotation_plot')
            def plot(width='100%', height='100%', fill=False):
                
                g_id = input.game_id()               
                game_info = df_lgl_all[df_lgl_all['GAME_ID'] == g_id]
                
                if len(game_info) > 0:

                    game_info = game_info.iloc[0]
                    df_gr = get_gr(input.season_str(), input.game_id())

                    if len(df_gr) > 0:

                        df_pbp = get_pbp(input.season_str(), input.game_id())

                        if len(df_pbp) > 0:
                            
                            return make_final_fig(df_gr, df_pbp, df_team_info, game_info, 
                                                show_text=input.checkbox_plottext(), 
                                                show_plot=False,
                                                cmap_name=input.plot_cmap_name())

                return None
                
            @render.text
            def text():
                #nbacom_url = f'https://www.nba.com/game/{input.game_id()}/box-score'
                return 'nba.com/stats game ID: {}'.format(input.game_id())
            
                #
                #ui.markdown('nba.com/stats game ID: [{}]({})'.format(input.game_id(), nbacom_url))
                #ui.markdown('yeah')
                #return 

        with ui.card():  
            ui.card_header("Data Availability")
            ui.markdown("Games for 2023-24 regular season up to Feb 13, 2024")

with ui.nav_menu("Contact"):
    with ui.nav_control():
        ui.a("Twitter", href="https://twitter.com/d_lavrent/", target="_blank")