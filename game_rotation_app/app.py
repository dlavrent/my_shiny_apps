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

df_lgl_T_all = []
df_lgl_P_all = []
for s_str in season_strs:
    cur_lgl_T = pd.read_csv(os.path.join(data_dir, f'lgls/df_lgl_T_{s_str}.csv'), 
                            dtype={'GAME_ID': str},
                            index_col=0)
    cur_lgl_T['season_str'] = s_str
    df_lgl_T_all.append(cur_lgl_T)
    cur_lgl_P = pd.read_csv(os.path.join(data_dir, f'lgls/df_lgl_P_{s_str}.csv'), 
                            dtype={'GAME_ID': str},
                            index_col=0)
    cur_lgl_P['season_str'] = s_str
    df_lgl_P_all.append(cur_lgl_P)
df_lgl_T_all = pd.concat(df_lgl_T_all)
df_lgl_P_all = pd.concat(df_lgl_P_all)

with ui.nav_panel('Main Application'):
    
    with ui.layout_sidebar():
        with ui.sidebar():
            with ui.accordion(id='plot_settings',
                              color='#f8f8f8', 
                              open=[#'Data Availability', 
                                    'Game Selection',
                                    'Plot Settings']):
                

                #with ui.accordion_panel('Data Availability'):            
                #    @render.text(inline=True)  
                #    def lastupdate():
                #        last_date = df_lgl_T_all['GAME_DATE'].max()
                #        return f'Games through: {last_date}'
                    
                with ui.accordion_panel('Game Selection', 
                                        ):
                    ui.input_selectize(
                        "season_str", "Select a season:",
                        {x: x for x in season_strs},
                    )

                    tm_choices = np.concatenate((['All'], tms_byalphabet))
                    ui.input_selectize(  
                        "team1",  "Filter for team:",  
                        {x: x for x in tm_choices},
                    )  

                    ui.input_radio_buttons(
                        'team1_homestat', 'Filter team playing',
                        ['either home or away', 'home only', 'away only']
                    )

                    ui.input_selectize(  
                        "team2",  "Filter for opponent:",  
                        {x: x for x in ['All']},
                    )  

                    game_choices = []
                    ui.input_selectize(  
                        "game_id", "Select the game:",  
                        {x: x for x in game_choices}
                    )  

                    # update games based on team1 / home status

                    @reactive.effect 
                    def _():
                            
                        input_season_str = input.season_str()
                        tm1 = input.team1()
                        tm1_homestat = input.team1_homestat()
                        
                        df_lgl = pd.read_csv(os.path.join(data_dir, f'lgls/df_lgl_T_{input_season_str}.csv'), 
                            dtype={'GAME_ID': str},
                            index_col=0)

                        df_lgl = df_lgl[df_lgl.MATCHUP.str.contains('@')]
                        df_sub = df_lgl.copy()

                        if tm1 != 'All':
                            df_sub = df_sub[df_sub.MATCHUP.str.contains(tm1)]

                            if tm1_homestat == 'home only':
                                df_sub = df_sub[df_sub.MATCHUP.str.contains(f'@ {tm1}')]
                            elif tm1_homestat == 'away only':
                                df_sub = df_sub[df_sub.MATCHUP.str.contains(f'{tm1} @')]

                            opps = np.unique([x.replace(tm1, '').replace('@', '').strip() for x in df_sub.MATCHUP.values])
                            opps = np.concatenate((['All'], opps))

                            ui.update_selectize('team2', choices={x:x for x in opps})


                    @reactive.effect 
                    def _():
                            
                        input_season_str = input.season_str()
                        tm1 = input.team1()
                        tm1_homestat = input.team1_homestat()
                        tm2 = input.team2()

                        df_lgl = pd.read_csv(os.path.join(data_dir, f'lgls/df_lgl_T_{input_season_str}.csv'), 
                            dtype={'GAME_ID': str},
                            index_col=0)

                        df_lgl = df_lgl[df_lgl.MATCHUP.str.contains('@')]

                        df_sub = df_lgl.copy()
                        
                        if tm1 != 'All':
                            df_sub = df_sub[df_sub.MATCHUP.str.contains(tm1)]

                            if tm1_homestat == 'home only':
                                df_sub = df_sub[df_sub.MATCHUP.str.contains(f'@ {tm1}')]
                            elif tm1_homestat == 'away only':
                                df_sub = df_sub[df_sub.MATCHUP.str.contains(f'{tm1} @')]
                            
                            if tm2 != 'All':
                                df_sub = df_sub[(df_sub.MATCHUP.str.contains(tm1)) & \
                                                (df_sub.MATCHUP.str.replace(tm1, '').str.contains(tm2))]
                        
                        game_strs = (df_sub
                            .set_index('GAME_ID')
                            .apply(lambda x: x['GAME_DATE']+': '+x['MATCHUP'].replace('.', ''),axis=1)
                        )

                        ui.update_selectize("game_id", choices={str(game_strs.index[i]):str(game_strs.values[i]) for i in range(len(game_strs))},
                                            label='Select the game ({} choice{}):'.format(len(game_strs), '' if len(game_strs) == 1 else 's'))

                
                    
                with ui.accordion_panel('Plot Settings'):
                    ui.input_checkbox("checkbox_plottext", 
                                "Annotate with shift +/-", 
                                True)  
                    
                    ui.input_selectize("plot_cmap_name", 
                                "Colormap for shift +/-'s", 
                                ['RdBu_r', 'PiYG', 'bwr', 'PuOr'])  
                    
        with ui.card():  
            ui.card_header("Rotation Plot")

            @render.plot(width=1250, height=800, alt='rotation_plot')
            def plot(width='100%', height='100%', fill=False):
                
                g_id = input.game_id()               
                game_info = df_lgl_T_all[df_lgl_T_all['GAME_ID'] == g_id]
                
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

        
        #with ui.card():  
        #    ui.card_header("Data Availability")
        #    ui.markdown("Games for 2023-24 regular season up to Feb 13, 2024")
        
        
        with ui.layout_columns():  
            
            plot_cols = ['PLAYER_NAME', 'MIN', 
                         'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PF',
                             'FGM', 'FGA', 'FG_PCT', 
                             'FG3M', 'FG3A', 'FG3_PCT',
                             'FTM', 'FTA', 'FT_PCT',
                             'PLUS_MINUS']
            
            rename_col_d = {'PLUS_MINUS': '+/-',
                            'PLAYER_NAME': 'PLAYER',
                            'FG_PCT': 'FG%', 
                            'FG3_PCT': 'FG3%',
                            'FT_PCT': 'FT%',}
            with ui.card():       
                ui.card_header('Away Box Score')

                @render.data_frame 
                def box_away():
                    
                    g_id = input.game_id()       

                     

                    game_info = df_lgl_T_all[df_lgl_T_all['GAME_ID'] == g_id]
                    df_box_game = df_lgl_P_all[df_lgl_P_all['GAME_ID'] == g_id]
                    df_box_away = df_box_game[df_box_game.MATCHUP.str.contains('@')]
                    fintabl = df_box_away[plot_cols].sort_values('MIN', ascending=0)
                    fintabl = fintabl.rename(columns=rename_col_d)

                    return render.DataGrid(fintabl)
                
            
            with ui.card():  

                ui.card_header('Home Box Score')
                @render.data_frame 
                def box_home():
                    
                    g_id = input.game_id()         

                    game_info = df_lgl_T_all[df_lgl_T_all['GAME_ID'] == g_id]
                    df_box_game = df_lgl_P_all[df_lgl_P_all['GAME_ID'] == g_id]
                    df_box_home = df_box_game[df_box_game.MATCHUP.str.contains('vs.')]
                    fintabl = df_box_home[plot_cols].sort_values('MIN', ascending=0)
                    fintabl = fintabl.rename(columns = rename_col_d)

                    return render.DataGrid(fintabl)



with ui.nav_panel('Info'):

    with ui.card():       
        ui.card_header('About')
        ui.markdown('Individual player shifts and +/- in shifts are pulled from ' +\
                    'the GameRotations endpoint on nba.com/stats.\n\n' +\
                    'Accessed using the [nba_api](https://github.com/swar/nba_api) python API (endpoint info [here](https://github.com/swar/nba_api/blob/master/docs/nba_api/stats/endpoints/gamerotation.md)).'
        )


    with ui.card():       
        ui.card_header('Contact')
        ui.markdown('Feature requests? Feedback? Questions? '+\
                    'Happy to chat on [Twitter](https://twitter.com/d_lavrent) or by [email](mailto:moondogdata@gmail.com)'
        )

        
    with ui.card():
        ui.card_header('Releases')
        ui.markdown('- v0.0 (Feb 23, 2024)\n'+\
                    '   - 2022-23, 2023-24 seasons\n'+\
                    '   - optional text annotation, +/- colormap selection'
        )

    with ui.card():
        ui.card_header('Future Directions')
        ui.markdown('- add playoff games\n' +\
                    '- allow for plotting/highlighting subset of players\n' +\
                    '- add interactivity (hovering vertical bar that shows score, 5-man lineups)\n' +\
                    '- add support for ESPN box scores\n'
        )
            
with ui.nav_menu("Contact"):
    with ui.nav_control():
        ui.a("Twitter", href="https://twitter.com/d_lavrent/", target="_blank")
        ui.a("email", href="mailto:moondogdata@gmail.com", target="_blank")