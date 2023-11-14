# -*- coding: utf-8 -*-
"""
Created on Thu Jul 13 02:14:12 2023

@author: aleex
"""

import soccerdata as sd
import pandas as pd
import socceraction as sa
import matplotsoccer
import numpy as np
import plotly.graph_objs as go
import plotly.offline as ply
from mplsoccer import Standardizer
import json
#ws = sd.WhoScored(leagues=league, seasons=season)

standard = Standardizer(pitch_from='opta', pitch_to='custom',
                        length_to=105, width_to=68)

def sd_match_events_spadl(league, season, game_id, g,ws):
    # Dado un id de opta, su competición y su temporada, devuelve los eventos de un encuentro
    # + los jugadores y equipos involucrados, respectivamente, en tres dfs
    with open('C:\\Users\\aleex\\soccerdata\\config\\teamname_replacements.json') as user_file:
        json_file = json.load(user_file)
    hteam= g[g.game_id==game_id]['home_team'].values[0]
    for i in json_file:
        hteam = hteam.replace(i,json_file[i])
    loader = ws.read_events(match_id=game_id, output_fmt='loader')
    df_teams = loader.teams(game_id=game_id)
   
    hteam_id = df_teams[df_teams.team_name==hteam].team_id.values[0]
    df_players = loader.players(game_id=game_id)
    evraw = loader.events(game_id= game_id)
    evraw['time_seconds'] = (evraw.minute - ((evraw.period_id - 1) * 45)) * 60 + evraw.second
    df_events = sa.spadl.opta.convert_to_actions(evraw, hteam_id)
    evraw.rename({'event_id':'original_event_id',
                  'outcome':'result_id'},axis=1,inplace=True)
    df_events = pd.merge(df_events,evraw[['original_event_id','qualifiers']],
                         how='left',on='original_event_id')
    
    df_events = sa.spadl.play_left_to_right(df_events, hteam_id)
    df_events = sa.spadl.add_names(df_events)
    cols = []
    for i in evraw.columns:
        if i in df_events.columns:
            cols.append(i)
            
    evraw = evraw[cols]
    evraw['result_id'] = np.where(evraw['result_id'] == True, 1, 0)
    evraw['result_name'] = np.where(evraw['result_id'] == 1, 'success', 'fail')
    evraw_non = evraw[~evraw.original_event_id.isin(df_events.original_event_id.unique())]
    evraw_non['start_x'], evraw_non['start_y'] = standard.transform(evraw_non.start_x, 
                                                                    evraw_non.start_y)
    evraw_non['end_x'], evraw_non['end_y'] = standard.transform(evraw_non.end_x, 
                                                                    evraw_non.end_y)
    evraw_non['time_seconds'] = evraw_non['time_seconds'] - .25
    df_events = pd.concat([df_events,evraw_non])
    df_events = df_events.sort_values(by=['period_id','time_seconds'])
    df_events = pd.merge(df_events,df_players[['player_name','player_id']],how='left',on='player_id')
    df_events = pd.merge(df_events,df_teams[['team_name','team_id']],how='left',on='team_id')
    

    return df_events, df_teams, df_players

def sd_match_events(league, season, game_id, g, ws):
    # Dado un id de opta, su competición y su temporada, devuelve los eventos de un encuentro
    # + los jugadores y equipos involucrados, respectivamente, en tres dfs
    
    with open('C:\\Users\\aleex\\soccerdata\\config\\teamname_replacements.json') as user_file:
        json_file = json.load(user_file)
    hteam= g[g.game_id==game_id]['home_team'].values[0]
    for i in json_file:
        hteam = hteam.replace(i,json_file[i])
    loader = ws.read_events(match_id=game_id, output_fmt='loader')
    df_teams = loader.teams(game_id=game_id)
    hteam = df_teams[df_teams.team_name==hteam].team_id.values[0]
    df_players = loader.players(game_id=game_id)
    df_events = loader.events(game_id= game_id)
    
    
    
    #df_events = sa.spadl.opta.convert_to_actions(df_events, hteam)
    df_events['start_x'], df_events['start_y'] = standard.transform(df_events.start_x, 
                                                                    df_events.start_y)
    df_events['end_x'], df_events['end_y'] = standard.transform(df_events.end_x, 
                                                                    df_events.end_y)
    #df_events = sa.spadl.play_left_to_right(df_events, hteam)
    #df_events = sa.spadl.add_names(df_events)
    df_events = pd.merge(df_events,df_players[['player_name','player_id']],how='left',on='player_id')
    df_events = pd.merge(df_events,df_teams[['team_name','team_id']],how='left',on='team_id')
    

    return df_events, df_teams, df_players

def plot_actions(df_actions_to_plot,local_team,display_cols=['nice_time', 'type_name', 'short_name', 'short_team_name']):
    if len(list(df_actions_to_plot.team_id.unique()))>1:
        df_actions_to_plot['start_x'] = np.where(df_actions_to_plot.team_id!=local_team,
                                                 105-df_actions_to_plot['start_x'],
                                                 df_actions_to_plot['start_x'])
        df_actions_to_plot['end_x'] = np.where(df_actions_to_plot.team_id!=local_team,
                                                 105-df_actions_to_plot['end_x'],
                                                 df_actions_to_plot['end_x'])
        
    matplotsoccer.actions(
        location=df_actions_to_plot[['start_x', 'start_y', 'end_x', 'end_y']],
        action_type=df_actions_to_plot['type_name'],
        team=df_actions_to_plot['team_name'],
        result=df_actions_to_plot['result_name'] == 'success',
        label=df_actions_to_plot[display_cols],
        labeltitle=['time', 'actiontype', 'player', 'team'],
        zoom=False,
        figsize=8)

def plot_actions_from_action_name(df_actions, action_name):
    if 'short_team_name' not in df_actions.columns:
        df_actions['short_team_name'] = df_actions['team_name']
    if 'short_name' not in df_actions.columns:
        df_actions['short_name'] = df_actions['player_name']    
    action_id = int(action_name.split(':')[0])
    df_actions_to_plot = df_actions[action_id-3: action_id+3]
    plot_actions(df_actions_to_plot)
#events, teams, players = sd_match_events("ENG-Premier League", 2017, 1190471)

def nice_time(row):
    minute = int((row['period_id']>=2) * 45 + (row['period_id']>=3) * 15 + 
                 (row['period_id']==4) * 15 + row['time_seconds'] // 60)
    second = int(row['time_seconds'] % 60)
    return f'{minute}m{second}s'

def action_name(row):
    return f"{row['action_id']}: {row['nice_time']} - {row['short_name']} {row['type_name']}"



def compare_player_ovtime(df_events, plA,plB, titulo):
    tA = go.Line(
        x = df_events[df_events.player_name == plA.value]['date'],
        y = df_events[df_events.player_name == plA.value]['vaep_value'],
        name = plA.value
    )
    tB = go.Line(
        x = df_events[df_events.player_name == plB.value]['date'],
        y = df_events[df_events.player_name == plB.value]['vaep_value'],
        name = plB.value
    )
    traces = [tA,tB]
    figure = go.Figure(
        data = traces,
        layout = go.Layout(
            title = titulo,
            xaxis = dict(title = 'date', zeroline = True, showgrid = False, zerolinewidth = 2),
            yaxis = dict(title = 'Evolución',zeroline = True, showgrid = False),
            showlegend = True
        )
    )
    
    ply.iplot(figure)
    
def compare_player_ovtime_acum(df_events, plA,plB, titulo):
    df_events_ot = df_events.groupby(by=['player_id','date'],as_index=False)['vaep_value'].sum()
    mplayers = df_events_ot.sort_values(by='date').drop_duplicates(subset='player_id',keep='last')[['player_id','player_name']]
    df_events_ot['cumsum'] = df_events_ot.groupby(['player_id'])['vaep_value'].cumsum()
    df_events_ot = pd.merge(df_events_ot,mplayers[['player_id','player_name']],on='player_id',how='left')
    tA = go.Line(
        x = df_events_ot[df_events_ot.player_name == plA.value]['date'],
        y = df_events_ot[df_events_ot.player_name == plA.value]['cumsum'],
        name = plA.value
    )
    tB = go.Line(
        x = df_events_ot[df_events_ot.player_name == plB.value]['date'],
        y = df_events_ot[df_events_ot.player_name == plB.value]['cumsum'],
        name = plB.value
    )
    traces = [tA,tB]
    figure = go.Figure(
        data = traces,
        layout = go.Layout(
            title = '{} Comparison Cumulative'.format(titulo),
            xaxis = dict(title = 'date', zeroline = True, showgrid = False, zerolinewidth = 2),
            yaxis = dict(title = 'Evolución',zeroline = True, showgrid = False),
            showlegend = True
        )
    )
    
    ply.iplot(figure)