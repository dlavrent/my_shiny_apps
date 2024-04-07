from shiny import App, Inputs, Outputs, Session, render, ui, reactive

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
from load_data_utils import get_gr, get_pbp
from plot_utils import make_final_fig

### SOMETHING BROKEN WITH 2024-02-25: SAS @ UTA
# (0022300825)
### SOMETHING BROKEN WITH 2024-02-27: UTA @ ATL
# (0022300835)

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

tm_choices = np.concatenate((['All'], tms_byalphabet))

app_ui = ui.page_navbar(
    ui.nav_panel('Main Application',
        ui.layout_sidebar(
            ui.sidebar(
                ui.accordion(
                    ui.accordion_panel('Data Availability',
                        ui.output_text('lastupdatetxt'),
                        ui.markdown('\n\nData updated nightly at 3am EST'),
                    ), 

                    ui.accordion_panel('Game Selection',
                        ui.input_selectize("season_str", 
                                        "Select a season:",
                                        {x: x for x in season_strs}),
                        ui.input_selectize('team1',
                                        'Filter for team:',
                                        {x: x for x in tm_choices}),
                        ui.input_radio_buttons('team1_homestat',
                                            'Filter team playing',
                                            ['either home or away', 'home only', 'away only']),
                        ui.input_selectize('team2',
                                        'Filter for opponent',
                                        {x: x for x in ['All']}),
                        ui.input_selectize('game_id',
                                        'Select the game:',
                                        {x: x for x in []}),
                    ),

                    ui.accordion_panel('Plot Settings',
                        ui.input_checkbox('checkbox_plottext',
                                        'Annotate with shift +/-', True),
                        ui.input_selectize('plot_cmap_name',
                                        "Colormap for shift +/-'s",
                                        ['RdBu_r', 'PiYG', 'bwr', 'PuOr'])
                    ),

                    open=['Game Selection', 'Plot Settings']
                ), 
                open='always'
            ),

            ui.card(
                ui.card_header('Rotation Plot'),
                ui.output_plot("plot", 
                               height='100%', 
                               width='1200px'
                               ),
            ),

            ui.layout_columns(
                ui.card(
                    ui.card_header('Away Box Score'),
                    ui.output_data_frame('away_box')
                ),
                ui.card(
                    ui.card_header('Home Box Score'),
                    ui.output_data_frame('home_box')
                )
            ),
        ),  
    ),

    ui.nav_panel('Info',
                 
        ui.card(
            ui.card_header('About'),
            ui.markdown('Individual player shifts and +/- in shifts are pulled from ' +\
                    'the GameRotation endpoint on nba.com/stats'+\
                    ', accessed using the [nba_api](https://github.com/swar/nba_api) python API (endpoint info [here](https://github.com/swar/nba_api/blob/master/docs/nba_api/stats/endpoints/gamerotation.md))'
            )
        ),
        ui.card(
            ui.card_header('Contact'),
            ui.markdown('Feature requests? Feedback? Questions? '+\
                        'Check out my website at [PlotandRoll.com](https://plotandroll.com).\n'+\
                        'Happy to chat on [Twitter](https://twitter.com/d_lavrent) or by [email](mailto:pnr@plotandroll.com)'
            )
        ),
        ui.card(
            ui.card_header('Releases'),
            ui.markdown('- v0.0 (Apr 3, 2024)\n'+\
                        '   - 2022-23, 2023-24 seasons\n'+\
                        '   - optional text annotation, +/- colormap selection'
            )
        ),
        ui.card(
            ui.card_header('Under development / future directions'),
            ui.markdown('- better support for mobile browsers\n' +\
                        '- add live game updates\n' +\
                        '- add playoff games\n' +\
                        '- filter games by player\n' +\
                        '- allow for plotting/highlighting subset of players\n' +\
                        '- color player shifts by other factors than team +/-, like player points\n' +\
                        '- add interactivity (hovering vertical bar that shows score, 5-man lineups)\n' +\
                        '- add support for ESPN box scores\n'
            ),
            style=".card-header { color:white; background:#2A2A2A !important; }"
        )
                 
    ),

    ui.nav_menu('Contact',
        ui.nav_control(
            ui.a("Website", href="https://plotandroll.com", target="_blank"),
            ui.a("Twitter", href="https://twitter.com/d_lavrent/", target="_blank"),
            ui.a("Email", href="mailto:pnr@plotandroll.com", target="_blank")
        )
    ),

    title='NBA Rotation Plots'
)


def server(input: Inputs, output: Outputs, session: Session):

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

        if tm1 == 'All':
            ui.update_selectize('team2', choices={x:x for x in ['All']})
        else:
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

        df_sub = df_lgl.copy().sort_values('GAME_DATE', ascending=0)
        
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


    @render.plot(width=1200, height=800, alt='rotation_plot')
    def plot():
        
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
    

    @render.data_frame 
    def away_box():
        
        g_id = input.game_id()       

        game_info = df_lgl_T_all[df_lgl_T_all['GAME_ID'] == g_id]
        df_box_game = df_lgl_P_all[df_lgl_P_all['GAME_ID'] == g_id]
        df_box_away = df_box_game[df_box_game.MATCHUP.str.contains('@')]
        fintabl = df_box_away[plot_cols].sort_values('MIN', ascending=0)
        fintabl = fintabl.rename(columns=rename_col_d)
        pct_cols = [c for c in fintabl.columns if '%' in c]
        for pct_col in pct_cols:
            fintabl[pct_col] = (fintabl[pct_col]*100).round(0)

        return render.DataGrid(fintabl)

    @render.data_frame 
    def home_box():
        
        g_id = input.game_id()         

        game_info = df_lgl_T_all[df_lgl_T_all['GAME_ID'] == g_id]
        df_box_game = df_lgl_P_all[df_lgl_P_all['GAME_ID'] == g_id]
        df_box_home = df_box_game[df_box_game.MATCHUP.str.contains('vs.')]
        fintabl = df_box_home[plot_cols].sort_values('MIN', ascending=0)
        fintabl = fintabl.rename(columns = rename_col_d)
        pct_cols = [c for c in fintabl.columns if '%' in c]
        for pct_col in pct_cols:
            fintabl[pct_col] = (fintabl[pct_col]*100).round(0)

        return render.DataGrid(fintabl)
        
    @render.text 
    def lastupdatetxt():
        last_date = df_lgl_T_all['GAME_DATE'].max()
        output_str = f'Games through: {last_date}'
        return output_str
  
app = App(app_ui, server)
