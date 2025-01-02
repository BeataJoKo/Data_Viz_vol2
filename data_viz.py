# -*- coding: utf-8 -*-
"""
Created on Sun Nov 17 13:35:51 2024

@author: 
    Asger Møller Nielsen, 
    Beata Joanna Morawska, 
    Mathias Henssel Lund.
"""

#%%

import data_wrangling as data
import data_utils as util
import dash
from dash import Dash, dcc, html
# import dash_bootstrap_components as dbc
# import dash_core_components as dcc
# import plotly.express as px
from dash.dependencies import Output, Input, State
import plotly.graph_objects as go
# from collections import Counter
# import math
import pandas as pd
import numpy as np
#from dash_bootstrap_templates import load_figure_template

#%% create Dash app

app = dash.Dash()

#%% import data

mintime = min(data.df_visit['Year'])
maxtime = max(data.df_visit['Year'])

#%% define Dash app layout 

app.layout = html.Div([
    
    html.Div(id='title', children=[
        html.H1("Museums' Visitors"),
        html.H4(f"Total visitors on exhibitions: {round(data.df_visit['Visit_Exhibition'].sum()):,.0f}", 
                         id='total_exhibition'),
        html.H6(f"Total visitors on museum locations: {round(data.df_visit['Visit_Place'].sum()):,.0f}", 
                         id='total_place')
        ]),
    
    html.Div(id='nav', children=[
        html.Label('Choose map type:'),
        html.Label('Choose museum category:'),
        dcc.Dropdown(
            id='map_type',
            options=[
                     {'label': 'Visitors on Exhibition in Museum', 'value': 'exhibition'},
                     #{'label': 'Visitors of the Museum Location', 'value': 'location'},
                     #{'label': 'Visitors on Exhibition in Municipality', 'value': 'kommune_ex'},
                     {'label': 'Visitors of the Museum Location in Municipality', 'value': 'kommune_loc'}
                     ],
            value='exhibition',
            clearable= False
            ),
        dcc.Dropdown(
            id='map_category',
            options= data.map_cat,
            value='All museums',
            #multi=True,
            clearable= False
            ),
        html.Button("Reset", id = "reset_all", n_clicks=1),
        html.Div(id='museum', children=None)
        ]),
    
    html.Div(id='info_graphs', children=[
        
        # Top
        # Map
        html.Div(id='map_container', children=[
            dcc.Graph(id='map_chart')
            ]),
        # Iframe
        html.Div(id='myframe', children=None),
        
        # Middle
        # Corona
        html.Div(id='corona_container', children=[
            html.H4('Chose what to compare:'),
            html.Label('On the X-axis:'),
            html.Label('On the Y-axis:'),
            dcc.Dropdown(
                id='corona_map',
                options=[
                    {'label': 'Before Covid-19', 'value': 'Before Covid-19'},
                    {'label': 'After Covid-19', 'value': 'After Covid-19'},
                    {'label': 'During Covid-19', 'value': 'During Covid-19'}
                    ],
                value='Before Covid-19',
                clearable= False
                ),
            dcc.Dropdown(
                id='corona_map_2',
                options=[
                    {'label': 'Before Covid-19', 'value': 'Before Covid-19'},
                    {'label': 'After Covid-19', 'value': 'After Covid-19'},
                    {'label': 'During Covid-19', 'value': 'During Covid-19'}
                    ],
                value='After Covid-19',
                clearable= False
                ),
            dcc.Graph(id='scatterplot_corona')
            ]),
        # Bar
        html.Div(id='bar_container', children=[
            html.Button("Toggle Metric", id="toggle_metric", n_clicks=0),  # Add Toggle Button - Mathias
            dcc.Graph(id='bar_visit'),
            dcc.RangeSlider(
                id='time_slider',
                min=mintime,
                max=maxtime,
                step=1,
                value=[mintime, maxtime],
                marks={i: str(i) for i in range(mintime, maxtime+1, 1)}),
            dcc.Graph(id='distribution')
            ]),
        
        # Bottom
        # Sankey
        dcc.Graph(id='sanky_teaching'),
        # Distribution
        dcc.Graph(id='pop_graph')
        ]),
    
    html.Div(id='footer', children=[
        html.P('Created by:'),
        html.P('Asger Møller Nielsen, Beata Joanna Morawska & Mathias Henssel Lund'),
        html.P('Supervised by:'),
        html.P('Stefan Jänicke & Gareth Walsh'),
        html.P('for Data Visualization course at SDU - Syddansk Universitet'),
        ])

    ])


@app.callback(
    [Output(component_id='reset_all', component_property='n_clicks'),
     Output(component_id='map_type', component_property='value'),
     Output(component_id='map_category', component_property='value'),
     Output(component_id='time_slider', component_property='value'),
     Output(component_id='toggle_metric', component_property='n_clicks'),
     Output(component_id='map_chart', component_property='clickData'),
     Output(component_id='corona_map', component_property='value'),
     Output(component_id='corona_map_2', component_property='value')
     ],
    [Input(component_id='reset_all', component_property='n_clicks')]
)
def reset_all_filters(reset_all):
    reset_all = 1
    selected_map = 'exhibition'
    map_category = 'All museums'
    time_slider = [2018, 2023]
    toggle_metric = 0
    map_chart = None
    corona_map = 'Before Covid-19'
    corona_map_2 = 'After Covid-19'
    return reset_all, selected_map, map_category, time_slider, toggle_metric, map_chart, corona_map, corona_map_2
                     

@app.callback(
    [Output(component_id="map_chart", component_property="figure")],
    [Input(component_id='map_type', component_property='value'),
     Input(component_id='map_category', component_property='value'),
     Input(component_id='reset_all', component_property='n_clicks'),
     Input(component_id='time_slider', component_property='value')],
    [State(component_id='map_chart', component_property='figure')]
)
def update_map(selected_map, map_category, reset_all,year_range, current_map_state):
    
    # Toggle reset
    if reset_all % 2 == 0:
        selected_map = 'exhibition'
        map_category = 'All museums'
    
    df = data.df_visit[
        (data.df_visit['Year'] >= year_range[0]) &
        (data.df_visit['Year'] <= year_range[1])
    ]
    if map_category != "All museums":
        df = df[df['Category'] == map_category]
    #df = data.df_visit
    df_agg_loc = util.kommune_agg(df, 'Visit_Place', data.dt_mun)

    initial_zoom = 5.6
    initial_center = {'lat': 56.30205043365613, 'lon': 11.153154691145753}

    # Preserve zoom and center if user interacts with the map
    if current_map_state:
        current_zoom = current_map_state['layout']['mapbox']['zoom']
        current_center = current_map_state['layout']['mapbox']['center']
    else:
        current_zoom = initial_zoom
        current_center = initial_center

    fig = go.Figure()

    if selected_map == 'exhibition':
        # Aggregate and categorize data
        df_agg_year = util.name_agg(df, 'Visit_Exhibition', year_range)
        limits = util.quantile_lim(df_agg_year, 'Visit_Exhibition')

        for lim in limits:
            df_agg_year.loc[
                (df_agg_year['Visit_Exhibition'] >= lim[0]) & 
                (df_agg_year['Visit_Exhibition'] <= lim[1]), 
                "type"
            ] = str(lim[0]) + ' - ' + str(lim[1])

        fig.add_trace(
            go.Scattermapbox(
                lat=df_agg_year['lat'],
                lon=df_agg_year['lon'],
                mode='markers',
                marker=go.scattermapbox.Marker(
                    size=df_agg_year['scale'],
                    #colorsrc=str(df_agg_year['type']),
                    opacity=0.7,
                    color='rgb(46,54,144)'
                ),
                customdata=df_agg_year[['Name', 'Category', 'Visit_Exhibition']].fillna(0).values,
                hovertemplate=(
                    "<b>Name: </b> %{customdata[0]}<br>"
                    "<b>Category: </b> %{customdata[1]}<br>"
                    "<b>Visit Exhibition: </b> %{customdata[2]:.3s}<br>"
                    "<extra></extra>"
               )
            )
        )

        fig.update_layout(
            title_text='Visitors on Exhibitions',
            mapbox=dict(
                style="carto-positron",
                center=current_center,
                zoom=current_zoom
            ),
            margin={"r": 0, "t": 50, "l": 0, "b": 0},
            plot_bgcolor='#efefef',
            paper_bgcolor='#efefef',
        )

    else:  # kommune_loc map
        # Add choropleth mapbox layer for location data
        fig.add_trace(
            go.Choroplethmapbox(
                geojson=data.kommune_geojson,
                locations=df_agg_loc['Location'],
                z=df_agg_loc['VisitCount'],
                featureidkey='properties.kode',
                colorscale=[[0, 'rgb(255, 255, 255)'], [1, 'rgba(89,0,43,1)']],  #'rgb(245, 28, 28)'
                zmin=0,
                zmax=df_agg_loc['VisitCount'].max(),
                marker=dict(opacity=.8),
                hovertext=df_agg_loc['Kommune'],
                name="Number of visitors in exibition",
                hovertemplate=(
                    "<b>%{hovertext}</b><br>"
                    "Visitors at Museum Location:  %{z:.3s}<br>"
                    "<extra></extra>"
               )
            )
        )

        fig.update_layout(
            title_text="Visitors at Museums' Location",
            mapbox=dict(
                style="carto-positron",
                center=current_center,
                zoom=current_zoom
            ),
            margin={"r": 0, "t": 50, "l": 0, "b": 0},
            plot_bgcolor='#efefef',
            paper_bgcolor='#efefef',
        )

    return [fig]


@app.callback(
    [Output('myframe', 'children'),
     Output('museum', 'children'),
     ],
    [Input(component_id='map_chart', component_property='clickData'),
     Input(component_id='map_category', component_property='value'),
     Input(component_id='map_type', component_property='value'),
     Input(component_id='reset_all', component_property='n_clicks')]
)
def update_url(clickData, map_cat, map_type, reset_all):
    
    # Toggle reset
    if reset_all % 2 == 0:
        map_cat = 'All museums'
        map_type = 'exhibition'
        select_museum = None  
        selected_kommune = None
        clickData = None
    
    if (map_cat != 'All museums') & (map_cat != 'Other'):
        map_cat = map_cat + 's'
    elif map_cat == 'Other':
        map_cat = 'Other Categories of Museums'
    mus = [
        html.H3(f"{map_cat}")
        ]
    child = [
        html.H5(""),
        html.Iframe(src="")
        ]
    
    select_museum = None  
    selected_kommune = None
    
    if map_type != 'exhibition':
        if clickData and 'points' in clickData:
            selected_kommune = clickData['points'][0]['hovertext']
            mus = [
                html.H3(f"{map_cat}")
                ]
            child = [
                html.H5(f"In {selected_kommune} Municipality"),
                html.Iframe(src="")
                ]
    else:
        if clickData and 'points' in clickData:
            select_museum = clickData['points'][0]['customdata'][0]
            
            df = pd.DataFrame(data.df_visit[['Name', 'Kommune', 'Url', 'Category']].value_counts().reset_index(name='Counts'))
            df_filtered = df[df['Name'] == select_museum]
            mus = [
                html.H3(f"{select_museum}")
                ]
            child = [
                html.H5(f"{df_filtered['Category'].values[0]} in {df_filtered['Kommune'].values[0]} Municipality"),
                html.Iframe(src=df_filtered['Url'].values[0])
                ]

    return child, mus


@app.callback(
    [Output(component_id="bar_visit", component_property="figure")],
    [Input(component_id='time_slider', component_property='value'),
     Input(component_id='map_category', component_property='value'),
     Input(component_id='map_type', component_property='value'),  
     Input(component_id='toggle_metric', component_property='n_clicks'),
     Input(component_id='map_chart', component_property='clickData'),
     Input(component_id='reset_all', component_property='n_clicks')]
)
def update_bar(year_range, map_category, map_type,n_clicks, clickData,reset_all):
    # Toggle reset
    if reset_all % 2 == 0:
        year_range = [2018, 2023]
        map_category = 'All museums'
        map_type = 'exhibition'
        selected_name = None  
        selected_kommune = None
        clickData = None


    selected_kommune = None
    selected_name = None
    title = "All museums"
    
    if clickData and 'points' in clickData:
        if map_type == 'kommune_loc':  # Choroplethmapbox case
            selected_kommune = clickData['points'][0]['hovertext']
        elif map_type == 'exhibition':  # Scattermapbox case
            selected_name = clickData['points'][0]['customdata'][0]
            print(f"Selected Name: {selected_name}")

    # Filter based on year, map_category and Municipality
    #df_filtered = data.df_visit[
    #    (data.df_visit['Year'] >= year_range[0]) &
    #    (data.df_visit['Year'] <= year_range[1])
    #]
    df_filtered = data.df_visit
    
    if map_category != "All museums":
        df_filtered = df_filtered[df_filtered['Category'] == map_category]
        title = map_category
    if selected_kommune:  # Filter further if a kommune is clicked
        df_filtered = df_filtered[df_filtered['Kommune'] == selected_kommune]
        title = selected_kommune
    if selected_name:  # Filter further if a museum is clicked
        df_filtered = df_filtered[df_filtered['Name'] == selected_name]
        title = selected_name

    # Toggle between two metrics by checking if it has been clicked an even number of times
    y_column = 'Visit_Exhibition' if n_clicks % 2 == 0 else 'Visitors_Exhibition_per_opening_hour'
    y_title = 'Visitors on Exhibition' if n_clicks % 2 == 0 else 'Visitors per Opening Hour'
    # df_agg = df_filtered.groupby('Year', as_index=False)[y_column].sum()
    df_agg, colors = util.year_agg(df_filtered, year_range, y_column)
    # Create the barplot
    fig = go.Figure(
        data=[go.Bar(
            x=df_agg['Year'], 
            y=df_agg[y_column],
            hovertext=df_agg[y_column],
            marker={'opacity': colors},
            hovertemplate=(
            #"<b>Name:</b> %{hovertext}<br>" +  
             "In <b> %{x}</b><br>"       
            f"<b>{y_title}</b> "+ " %{y:.3s}<br>"     
             "<extra></extra>"                
            )
        )]
    )
    
    fig.update_traces(marker_color='rgb(89,0,43)', 
                      #marker_line_color='rgb(8,48,107)',
                      marker_line_width=1.5) 
    
    fig.update_layout(
        title_text=f'Yearly {y_title} for {title}',
        margin={"r": 0, "t": 50, "l": 0, "b": 0},
        plot_bgcolor='#efefef',
        paper_bgcolor='#efefef',
    )
    
    return [fig]


@app.callback(
    [Output(component_id="pop_graph", component_property="figure")],
    [Input(component_id='time_slider', component_property='value'),
    Input(component_id='map_category', component_property='value'),
    Input(component_id='map_type', component_property='value'),
    Input(component_id='reset_all', component_property='n_clicks')]
)
def update_pop(year_range, map_category, map_type, reset_all):  
    
    # Toggle reset
    if reset_all % 2 == 0:
        year_range = [2018, 2023]
        map_category = "All museums"
        
    if year_range[0] == year_range[1]:
        years = str(year_range[0])
    else:
        years = str(year_range[0]) + ' - ' + str(year_range[1])
    
    selected_cat = None
    if map_category != "All museums":
        selected_cat = map_category

    man, woman = util.gender_data(data.df_cat, year_range, selected_cat)
    colors = 1.0
    
    fig = go.Figure()
    for col in man.columns[1:]:
        fig.add_trace(
            go.Bar(x=-man[col],
                   y =man['Age'],
                   orientation='h',
                   name= 'Male',
                   marker={
                       'opacity': colors,
                       'color': 'rgb(41,134,204)'
                           },
                   legendgroup="Male",
                   showlegend = (col == man.columns[1]),
                   customdata=man[col],
                   hovertemplate = 
                       "%{y}: %{customdata:.1f}%"
                       f"<extra><b>Male: </b> {col}<br></extra>"))
       # colors = colors - 0.2
        
    colors = 1.0
    for col in woman.columns[1:]:
        fig.add_trace(
            go.Bar(x= woman[col].values,
                   y=woman['Age'],
                   orientation='h',
                   name='Female',
                   marker={
                       'opacity': colors,
                       'color': 'rgb(202,71,117)'
                           },
                   legendgroup="Female",
                   #hovertext=woman[col],
                   showlegend = (col == woman.columns[1]),
                   customdata=woman[col],
                   hovertemplate = 
                       "%{y}: %{customdata:.1f}%"
                       f"<extra><b>Female: </b> {col}<br></extra>"))
        #colors = colors - 0.2
    title_text = 'Population Graph' if selected_cat is None else f'Population Graph for {selected_cat}'
    title_text = title_text if year_range == [2018, 2023] else title_text + f' in {years}'

    fig.update_layout(barmode='relative', 
                  yaxis_autorange='reversed',
                  legend_orientation ='h',
                  bargap=0.01,
                  legend_x=-0.05, 
                  legend_y=1.11,
                  title_text= title_text,
                  margin={"r": 0, "t": 80, "l": 0, "b": 0},
                  plot_bgcolor='#efefef',
                  paper_bgcolor = '#efefef'
                 )
    
    return [fig]
        

@app.callback(
    [Output(component_id="scatterplot_corona", component_property="figure")],  
    [Input(component_id='corona_map', component_property='value'),
     Input(component_id='corona_map_2', component_property='value'),
     Input(component_id='reset_all', component_property='n_clicks'),
     Input(component_id='map_chart', component_property='clickData'),
     Input(component_id='map_type', component_property='value'),
     Input(component_id='map_category', component_property='value'),]
)
def update_corona(x_axis, y_axis, reset_all, clickData, map_type, map_category):
    
    # Toggle reset
    if reset_all % 2 == 0:
        x_axis = 'Before'
        y_axis = 'After'
        selected_kommune = None
        selected_name = None
        clickData = None
    
    selected_kommune = None
    selected_name = None
    title = f"Attendance: {x_axis} vs {y_axis}"
    
    if clickData and 'points' in clickData:
        if map_type == 'kommune_loc':  
            selected_kommune = clickData['points'][0]['hovertext']
        elif map_type == 'exhibition':  
            selected_name = clickData['points'][0]['customdata'][0]
            
    
    df_filtered = data.df_visit
    
    if map_category != "All museums":
        df_filtered = df_filtered[df_filtered['Category'] == map_category]
        title = f"Attendance: {x_axis} vs {y_axis} for {map_category}"
    if selected_kommune:  
        df_filtered = df_filtered[df_filtered['Kommune'] == selected_kommune]
        title = f"Attendance: {x_axis} vs {y_axis} in {selected_kommune}"
    
    
    df = util.corona_data2(df_filtered)
    max_limit = max(df[x_axis].max(), df[y_axis].max())

    if selected_name:
        selected_df = df[df['Name'] == selected_name]
        rest_df = df[df['Name'] != selected_name]
    else:
        selected_df = pd.DataFrame()  
        rest_df = df

    
    fig = go.Figure(
        
    )

    fig.add_trace(
        go.Scatter(
            x=rest_df[x_axis],
            y=rest_df[y_axis],
            mode='markers',
            hovertext=rest_df['Name'],
            marker=dict(
                color='rgb(46,54,144)',
                size=rest_df['scale'],
                showscale=False
            ),
            name='museums',
            hovertemplate=(
                "<b>Name: </b>%{hovertext}<br>"
                f'<b>{x_axis}: </b>'+' %{x:.3s}<br>'
                f'<b>{y_axis}: </b>'+' %{y:.3s}<br>'
                "<extra></extra>"
            )
        )
    )

    # Add highlighted point
    if not selected_df.empty:
        fig.add_trace(
            go.Scatter(
                x=selected_df[x_axis],
                y=selected_df[y_axis],
                mode='markers',
                hovertext=selected_df['Name'],
                marker=dict(
                    color='rgba(250,175,67,1)',  
                    size=selected_df['scale'], # *1.5, 
                    line=dict(color='rgb(255,255,255)', width=1.5)  
                ),
                name=selected_name,
                hovertemplate=(
                    "<b>Name: </b> %{hovertext}<br>"
                    f'<b>{x_axis}: </b>'+' %{x:.3s}<br>'
                    f'<b>{y_axis}: </b>'+' %{y:.3s}<br>'
                    "<extra></extra>"
                )
            )
        )
    
    fig.update_layout(
        title_text=f'{title}',
        #showlegend=False,
        shapes = [
    {
        'type': 'line',      
        'yref': 'paper',    
        'xref': 'paper',    
        'y0': 0,             
        'y1': 1,             
        'x0': 0,             
        'x1': 1,            
        'layer': 'below',    
        'opacity': 0.2       
    }
],
        xaxis=dict(
            title=x_axis,
            range=[0, max_limit * 1.1],  
            constrain="domain"           
        ),
        yaxis=dict(
            title=y_axis,
            range=[0, max_limit * 1.1],  
            constrain="domain"           
        ),
        margin={"r": 10, "t": 50, "l": 30, "b": 10},
        plot_bgcolor='#efefef',
        paper_bgcolor='#efefef'
    )
    
    return [fig]


@app.callback(
    [Output(component_id="sanky_teaching", component_property="figure")],
    [Input(component_id='time_slider', component_property='value'),
     Input(component_id='map_category', component_property='value'),
     Input(component_id='map_chart', component_property='clickData'),
     Input(component_id='map_type', component_property='value'),
     Input(component_id='reset_all', component_property='n_clicks')]
)
def update_sankey(time_slider, map_cat, clickData, map_type, reset_all):
    
    # Toggle reset
    if reset_all % 2 == 0:
        time_slider = [2018, 2023]
        map_cat = 'All museums'
        map_type = 'exhibition'
        selected_kommune = None
        select_museum = None
        clickData = None
    
    selected_kommune = None
    select_museum = None
    if clickData and 'points' in clickData:
        if map_type == 'kommune_loc':  # Choroplethmapbox case
            selected_kommune = clickData['points'][0]['hovertext']
        elif map_type == 'exhibition':  # Scattermapbox case
            select_museum = clickData['points'][0]['customdata'][0]
            print(f"Selected Name: {select_museum}")

    # Filter based on year, map_category and Municipality
    df_filtered = data.df_teaching[
        (data.df_teaching['Year'] >= time_slider[0]) &
        (data.df_teaching['Year'] <= time_slider[1])
    ]
    
    if time_slider[0] == time_slider[1]:
        years = str(time_slider[0])
    else:
        years = str(time_slider[0]) + ' - ' + str(time_slider[1])
    
    title = 'all museums'
    if map_cat != "All museums":
        df_filtered = df_filtered[df_filtered['Category'] == map_cat]
        title = map_cat
    if selected_kommune:  # Filter further if a kommune is clicked
        df_filtered = df_filtered[df_filtered['Kommune'] == selected_kommune]
        title = selected_kommune
    # Dont make sense since it works with highlight
    #if select_museum:  # Filter further if a museum is clicked
    #    df_filtered = df_filtered[df_filtered['Name'] == select_museum]
        
    df = util.teaching_data(df_filtered, ['Teaching', 'Category'], 'Amount')
    
    if select_museum:  # Filter further if a museum is clicked
        df = util.teaching_data(df_filtered, ['Teaching', 'Category'], 'Amount', select_museum)
        #df_filtered = df_filtered[df_filtered['Name'] == select_museum]
        #title = select_museum
    
    fig = go.Figure(
        data=[
            go.Sankey(
                node = dict(
                    pad = 15,
                    thickness = 20,
                    line = dict(color = "black", width = 0.5),
                    label = df[0],
                    color = df[4], 
                    hovertemplate='%{label} has groups of total size %{value:.3s}<extra></extra>'
                    ),
                link = dict(
                    source = df[2], # indices correspond to labels, eg A1, A2, A1, B1, ...
                    target = df[1],
                    value = df[3],
                    color = df[5], 
                    #hovercolor = df[6],
                    customdata = df[7],
                    hovertemplate=
                        '%{customdata}<br>'
                        'has %{target.label} groups of total size %{value:.3s}' 
                        '<extra></extra>'
        ))])
    
    #fig.update_traces(link_hovercolor=df[6], selector=dict(type='sankey'))
    
    fig.update_layout(
                  title_text=f'Groups undrer 18 years in {title} for {years}',
                  margin={"r": 0, "t": 50, "l": 0, "b": 20},
                  #font_size=10,
                  plot_bgcolor='#efefef',
                  paper_bgcolor = '#efefef'
                 )

    return [fig]


@app.callback(
    [Output(component_id="distribution", component_property="figure")],
    [Input(component_id='time_slider', component_property='value'),
     Input(component_id='map_category', component_property='value'),
     Input(component_id='map_chart', component_property='clickData'),
     Input(component_id='map_type', component_property='value'),
     Input(component_id='reset_all', component_property='n_clicks')]
)
def update_dist(time_slider, map_cat, clickData, map_type, reset_all):
    
    # Toggle reset
    if reset_all % 2 == 0:
        time_slider = [2018, 2023]
        map_cat = 'All museums'
        map_type = 'exhibition'
        selected_kommune = None
        clickData = None
    
    selected_kommune = None 
    title = 'all museums'
    if time_slider[0] == time_slider[1]:
        years = str(time_slider[0])
    else:
        years = str(time_slider[0]) + ' - ' + str(time_slider[1])
        
    if map_type != 'exhibition':
        if clickData and 'points' in clickData:
            selected_kommune = clickData['points'][0]['hovertext']
      
    df_filtered = data.df_visit
    
    if map_cat != "All museums":
        df_filtered = df_filtered[df_filtered['Category'] == map_cat]
        title = map_cat
    if selected_kommune:  # Filter further if a kommune is clicked
        df_filtered = df_filtered[df_filtered['Kommune'] == selected_kommune]
        title = selected_kommune
    
    df = util.name_agg(df_filtered, 'Visit_Exhibition', time_slider)

# produce histogram data wiht numpy
    count, index = np.histogram(df['Visit_Exhibition'], bins=100)
    fig = go.Figure(
        data=[
            go.Scatter(
                x=index, 
                y=count,
                line=dict(
                    width = 2, 
                    shape='hvh', 
                    color='rgb(89,0,43)'),
                #hovertext=df['Name'],
                hovertemplate=(
                    #"<b>Name:</b> %{hovertext}<br>" +  
                    "<b>Visitors: </b> %{x:.3s}<br>"       
                    "<b>Count: </b> %{y}<br>"       
                    "<extra></extra>"                
                )
                )])
    
    fig.add_vline(x=df['Visit_Exhibition'].median(), 
                  line_width=1.5, 
                  line_dash="dash", 
                  line_color="rgba(56,62,66,1)",
                  annotation_text="median: " + f"{df['Visit_Exhibition'].median():,.0f}", 
                  annotation_position="top right",
                  annotation_font_size=12,
                  annotation_font_color="rgba(56,62,66,1)")
        
    fig.update_layout(
        title_text=f'Distribution of visitors in {title} for {years}',
        showlegend=False,
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
        plot_bgcolor='#efefef',
        paper_bgcolor = '#efefef')

    return [fig]

if __name__ == '__main__':
    app.run_server(debug=False, port=8080)
