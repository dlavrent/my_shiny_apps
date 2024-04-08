# -*- coding: utf-8 -*-
"""
Created on Tue Feb  6 18:28:26 2024

@author: dolavrent@gmail.com
"""
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.ticker import MultipleLocator

# plotting parameters that are not 
# really meant to be modified by a user

cmap_VMIN = -20                  # lower limit of colormap
cmap_VMAX = +20                  # upper limit of colormap
min_shift_len_min = 1            # if annotating text, min stint to annotate
shift_rectangle_height = 0.3     # height of stint rectangle (players spaced by 1)


def set_font_sizes(SMALL_SIZE=12, MEDIUM_SIZE=14, LARGE_SIZE=16):
    '''
    Sets font size for matplotlib
    From: https://stackoverflow.com/a/39566040
    '''
    font = {'family':'monospace',
             'size': SMALL_SIZE}

    plt.rcParams.update({'text.latex.preamble': r"""\usepackage{bm}"""})
    
    
    plt.rc('font', **font)                   # controls default text sizes
    plt.rc('axes', titlesize=MEDIUM_SIZE)    # fontsize of the axes title
    plt.rc('axes', labelsize=SMALL_SIZE)     # fontsize of the x and y labels
    plt.rc('xtick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
    plt.rc('ytick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
    plt.rc('legend', fontsize=SMALL_SIZE)    # legend fontsize
    plt.rc('figure', titlesize=LARGE_SIZE)   # fontsize of the figure title
    
    
set_font_sizes()


def get_player_summary(df_gr0):
    
    df_gr = df_gr0.copy()

    df_gr['nameI'] = df_gr.apply(lambda x: x['PLAYER_FIRST'][0] + '. ' + x['PLAYER_LAST'], axis=1)
    df_gr['in_min'] = df_gr['IN_TIME_REAL']/60/10
    df_gr['out_min'] = df_gr['OUT_TIME_REAL']/60/10
    df_gr['min'] = df_gr['out_min'] - df_gr['in_min']
    
    player_summary = (df_gr
                          [['PERSON_ID', 'nameI',
                            'min', 'PT_DIFF']]
                          .groupby(['PERSON_ID', 'nameI'])
                          .sum()
                          .sort_values('min', ascending=0)
                          .reset_index()
                          )
    
    player_IDs_sorted = player_summary['PERSON_ID'].values
    player_nms = player_summary['nameI'].values
    player_mins = np.round(player_summary['min'].values).astype(int)
    player_pms = player_summary['PT_DIFF'].values.astype(int)
    player_signs = ['+' if x >= 0 else '-' for x in player_pms]
    n_players = len(player_summary)
    
    d_ID_to_pos = {player_IDs_sorted[i]:n_players-i for i in range(n_players)}
    
    plyr_strings = ['{} ({:>2} min, {}{:>2})'.format(player_nms[i], 
                                               player_mins[i],
                                               player_signs[i],
                                               np.abs(player_pms[i]).astype(int)) for i in range(n_players)]
    
    return df_gr, player_summary, plyr_strings, d_ID_to_pos



def plot_stints(plyr_strings, d_ID_to_pos, df_gr, ax, cmap, show_text=False):
    '''
    Plots player stints as rectangles, colored by +/- in stint
    Inputs: 
     - game rotations dataframe (df_gr),
     - player labels (i. e. L. James (32 min, +23)), 
       in the order desired along the Y axis (plyr_strings)
     - a dictionary mapping player IDs to position on Y axis 
       (d_ID_to_pos)
     - the axis to plot on (ax)
     - the colormap for +/-'s (cmap)
    '''
          
    n_players = len(plyr_strings)
    n_rows = len(df_gr)

    # go row by row to add rectangles with width given by in/out times
    for i in range(n_rows):
        cur_row = df_gr.iloc[i]
        
        # get the in and out times along with where to plot along y
        cur_person_ID, cur_in_min, cur_out_min, cur_pm = \
            cur_row[['PERSON_ID', 'in_min', 'out_min', 'PT_DIFF']]
        cur_ypos = d_ID_to_pos[cur_person_ID]
        
        # plot the rectangle
        ax.fill_between(x=[cur_in_min, cur_out_min], 
                        y1=cur_ypos-shift_rectangle_height, 
                        y2=cur_ypos+shift_rectangle_height,
                        lw=0.2, edgecolor='0.5',
                        facecolor=cmap.to_rgba(cur_pm))
        
        # optional: annotate stint rectangle with text
        if show_text:
            lenshift = cur_out_min - cur_in_min
            if lenshift > min_shift_len_min:
                textpos = cur_in_min + lenshift/2
                texttag = '{}{:.0f}'.format('+' if cur_pm >= 0 else '-', abs(cur_pm))
                ax.text(textpos, cur_ypos, texttag, size=10,
                        c='k', 
                        path_effects=[pe.withStroke(linewidth=6, foreground="w")],
                        ha='center', va='center')
    
    # format y ticks and labels
    ax.set_yticks(1+np.arange(n_players))
    ax.set_yticklabels(plyr_strings[::-1])

def convert_to_time(pbp_row):
    '''
    Utility function for processing time info in play by play dataframe,
    converting clock_min and clock_sec to elapsed minutes in game
    '''
    qtr = pbp_row['PERIOD']
    clock_min = pbp_row['clock_min']
    clock_sec = pbp_row['clock_sec']
    
    # quarters 1, 2, 3, 4 are regular time, no OTs needed to process
    if qtr <= 4:
        tt_sec = 12*(qtr-1)*60 + (12*60 - 60*clock_min - clock_sec)
    # process OT
    else:
        tt_sec = 48*60 + 60*5*(qtr-5) + (5*60 - 60*clock_min - clock_sec)
    
    # return minutes
    return tt_sec/60
 
def get_home_away_diff(df_pbp):
    '''
    Utility function for getting home - away score margin
    through game time, by processing play by play df
    '''
    
    df_pbp_slim = df_pbp.copy()[['EVENTNUM', 'PERIOD', 'PCTIMESTRING', 'SCOREMARGIN']]
    df_pbp_slim[['clock_min', 'clock_sec']] = df_pbp_slim['PCTIMESTRING'].str.split(':', expand=True).astype(int)
    df_pbp_slim['time'] = df_pbp_slim.apply(lambda x: convert_to_time(x), axis=1)
    
    df_pbp_slim.loc[((df_pbp_slim['EVENTNUM'] == 2) & \
                     (df_pbp_slim['PERIOD'] == 1)),
                     'SCOREMARGIN'] = 0    
    df_fin = df_pbp_slim.dropna(subset='SCOREMARGIN')

    return df_fin['time'].values, df_fin['SCOREMARGIN'].values
    

    
def plot_diff(game_times, away_home_diff, 
              home_info, away_info,
              ax):
    '''
    Plots away - home margin through time,
    using the away/home colors to color the line
    and shade between the line and a margin of 0
    '''
    
    # get colors + abbreviations for both teams
    home_color, home_color2 = home_info['COLOR1'], home_info['COLOR2']
    away_color, away_color2 = away_info['COLOR1'], away_info['COLOR2']
    home_abbrev = home_info['TEAM_ABBREVIATION']; away_abbrev = away_info['TEAM_ABBREVIATION']
    
    # shade each side of the away - home margin with appropriate colors
    ax.fill_between(game_times,  0, away_home_diff,
                    where=away_home_diff <= 0, color=home_color, interpolate=True, alpha=0.9)
    ax.fill_between(game_times, 0, away_home_diff,
                    where=away_home_diff >= 0, color=away_color, interpolate=True, alpha=0.9)
    
    # now plot the away - home margin as a line
    # using the secondary colors for each team,
    # coloring the line appropriately if away/home is winning
    game_times_fine = np.arange(0, game_times[-1]+1e-4, 0.01)
    margin_fine = np.interp(game_times_fine, game_times, away_home_diff)
    
    ax.plot(game_times_fine, 
            np.ma.masked_where(margin_fine <= 0, margin_fine), c=away_color2)
    ax.plot(game_times_fine, 
            np.ma.masked_where(margin_fine >  0, margin_fine), c=home_color2)
    
    # adjust y limits and add team abbreviation text labels
    max_diff = max(np.abs(away_home_diff))
    ax.set_ylim(-1.05*max_diff, 1.05*max_diff)
    ax.text(0.2, +0.95*max_diff, away_abbrev, 
                 path_effects=[pe.withStroke(linewidth=3, foreground="w")],
                 color=away_color, ha='left', va='top')
    ax.text(0.2, -1*max_diff, home_abbrev, 
                 path_effects=[pe.withStroke(linewidth=3, foreground="w")],
                 color=home_color, ha='left', va='bottom')
    ax.set_ylabel('point diff\n(away - home)', ha='right', va='center', rotation=0)
    
    
def make_final_score_tag(home_info, away_info, df_pbp, num_OTs):
    '''
    Makes suptitle for final plot, 
    with the score, and bolding the winner
    '''
    # get team names
    away_team = away_info['TEAM_FULL_NAME']; home_team = home_info['TEAM_FULL_NAME']
    final_away_score, final_home_score = [int(x.strip()) for x in df_pbp.iloc[-1]['SCORE'].split('-')]
    
    # determine who won --> who to bold
    home_win = int(final_home_score > final_away_score)
    
    away_score_tag = r'$\bf{'*(1-home_win) + \
         away_team + ' - ' + str(int(final_away_score)) + \
         '}$'*(1-home_win)
    home_score_tag = r'$\bf{'*home_win + \
         str(int(final_home_score)) + ' - ' + home_team + \
         '}$'*home_win
    if home_win:
        home_score_tag = home_score_tag.replace(' ', '~')
        away_score_tag = away_score_tag.replace(' - ', '$~-~$')
    else:
        away_score_tag = away_score_tag.replace(' ', '~')
        home_score_tag = home_score_tag.replace(' - ', '$~-~$')

    final_score_tag = away_score_tag + ' @ ' + home_score_tag

    # add number of OTs to the end if there was one
    if num_OTs == 1:
        final_score_tag += ' (OT)'
    elif num_OTs > 1:
        final_score_tag += ' ({} OT)'.format(num_OTs)
        
    return final_score_tag


def make_final_fig(df_gr, df_pbp, df_team_info, game_info,
                   show_text=False, show_plot=False,
                   season_type='Regular Season',
                   cmap_name = 'RdBu_r'):
    '''
    Puts it all together
    '''


    game_id = df_gr['GAME_ID'].iloc[0]
    

    norm = mpl.colors.Normalize(vmin=-20, vmax=20)
    cmap = mpl.cm.ScalarMappable(norm=norm, cmap=cmap_name)

    num_OTs = df_pbp.iloc[-1]['PERIOD'] - 4
    
    game_times, home_away_diff = get_home_away_diff(df_pbp)
    
    
    game_start = pd.to_datetime(game_info['GAME_DATE'])

    game_start_date = '{}, {} {}, {}'.format(game_start.day_name(), 
                                             game_start.month_name(), 
                                             game_start.day, 
                                             game_start.year)
    
    gr_home0 = df_gr[df_gr['h_a'] == 'home']
    gr_away0 = df_gr[df_gr['h_a'] == 'away']
    
    n_home_players = len(gr_home0['PERSON_ID'].unique())
    n_away_players = len(gr_away0['PERSON_ID'].unique())
    n_tot_players = n_home_players + n_away_players 
    
    home_id = gr_home0.iloc[0]['TEAM_ID']
    away_id = gr_away0.iloc[0]['TEAM_ID']
    
    home_info = df_team_info[df_team_info.TEAM_ID == home_id].iloc[0]
    away_info = df_team_info[df_team_info.TEAM_ID == away_id].iloc[0]
    

    gr_home, home_player_summary, home_plyr_strings, home_d_ID_to_pos = get_player_summary(gr_home0)
    gr_away, away_player_summary, away_plyr_strings, away_d_ID_to_pos = get_player_summary(gr_away0)
    
    max_string_len = max([max([len(x) for x in home_plyr_strings]),
                          max([len(x) for x in away_plyr_strings])]) - 14
    
    
    rot_plot_rats = 10*n_away_players/n_tot_players, 10*n_home_players/n_tot_players
    
    
    
    
        
    fig_width = 13+0.1167*max_string_len
    fig, axs = plt.subplots(3, 2, figsize=(fig_width,8), 
                            sharex=True,
                            height_ratios=(*rot_plot_rats,2), 
                            width_ratios=(40, 1) ,
                            facecolor='w',
                            layout='tight',
                            )
    
    ax_home = axs[1, 0]; ax_away = axs[0, 0]; ax_diff = axs[2, 0]
    
    for ax in axs[:, 1]:
        ax.axis('off')
    
    fig.colorbar(cmap, 
                 ax=axs[1, 1],
                 fraction=1,
                 pad=0.05,
                 shrink=1,
                 label='point diff in stint')
        
    # main plots
    plot_stints(away_plyr_strings, away_d_ID_to_pos, gr_away, ax_away, cmap, show_text)
    plot_stints(home_plyr_strings, home_d_ID_to_pos, gr_home, ax_home, cmap, show_text)
    plot_diff(game_times, -home_away_diff, home_info, away_info, ax_diff)
    
    # x axis ticks
    my_xticks = np.concatenate((np.arange(0, 48.1, 12), 48 + 5*np.arange(1, num_OTs+1)))
    ax_diff.xaxis.set_minor_locator(MultipleLocator(1))
    ax_diff.set_xticks(my_xticks)
    ax_diff.set_xlim(0, 48+5*num_OTs)
    ax_diff.set_xlabel('minute in game')
    
    # make suptitle
    final_score_tag = make_final_score_tag(home_info, away_info, df_pbp, num_OTs)
    suptitl_suffix = ''
    if season_type == 'Playoffs':
        suptitl_suffix = ' (playoffs)'
    elif season_type == 'PlayIn':
        suptitl_suffix = ' (play-in tournament)'
    # to-do: annotate round in playoffs
    plt.suptitle(final_score_tag + f'\n{game_start_date}')
    
    # add gridlines for each quarter/OT
    for ax in axs[:, 0]:
        ax.xaxis.grid()
    
    # add author information
    axs[-1, 0].text(1, -0.53, 
                'by: plotandroll.com\n'+\
                'data accessed with: swar/nba_api\n'+\
                'nba.com/stats game ID: {}'.format(game_id),
                ha='right',
                va='top',
                transform=axs[-1,0].transAxes, 
                c='0.5',
                )
    
    # if not in use in shiny app, optional flag to show plot
    if show_plot:
        plt.show()

    return fig


if __name__ == '__main__':
    
    season_str = '2023-24'
    
    game_id = '0022300650'
    game_id = '0022301230'
    #game_id = '0022300572'
    game_id = '0022300040'
    game_id = '0022300452'
    game_id = '0022300336'
    game_id = '0022300063'
    
    #import os
    from load_data_utils import get_gr, get_pbp
    
    read_data = False 
    
    if read_data:
        from nba_api.stats.endpoints import gamerotation, playbyplayv2
        gr_res = gamerotation.GameRotation(game_id=game_id).get_data_frames()
        df_pbp = playbyplayv2.PlayByPlayV2(game_id=game_id).get_data_frames()[0]
    
    
    

    df_pbp = get_pbp(season_str, game_id)
    df_gr = get_gr(season_str, game_id)
    
    df_team_info = pd.read_csv('data/df_team_info.csv')
    
    df_lgl = pd.read_csv('data/lgls/df_lgl_2023-24.csv', index_col=0)
    game_info = df_lgl[df_lgl['GAME_ID'] == int(game_id)].iloc[0] 

    
    
    fig = make_final_fig(df_gr, df_pbp, df_team_info, game_info,
                         show_plot=True, show_text=True)
    #fig.show()