# -*- coding: utf-8 -*-
"""
Created on Sun Nov 17 13:43:55 2024

@author: BeButton
"""

#%%
# import os 
import geojson
import pandas as pd
# from datetime import datetime

#%%
with open('data/municipalities.geojson') as file:
    kommune_geojson = geojson.load(file)
#with open('data/municipalities_codes.geojson') as file:
#    kommune_geojson = geojson.load(file)
#with open('data/postal_codes.geojson') as file:
#    zipcode_geojson = geojson.load(file)
    
#%%
df_base = pd.read_csv('data/base_data_2018_2023.csv')
df_cat = pd.read_csv('data/museum_category_2018_2023.csv')
#df_art = pd.read_csv('data/graphic_art_2018_2023.csv')
#df_area = pd.read_csv('data/visit_area_2018_2023.csv')
#df_purp = pd.read_csv('data/visit_reason_2018_2023.csv')
df_geo = pd.read_csv('data/mus_address.csv')
dt_mun = pd.read_csv('data/data_mun.csv')
#df_code = pd.read_excel('data/municipality_code.xlsx')
#df_web = pd.read_excel('data/museum_websites.xlsx', sheet_name='cleaned')
#dt_cod = pd.read_csv('data/data_post.csv')

#%%
map_cat = ['All museums'] + list(df_base['Category'].unique())
map_cat = [{'label': i, 'value': i} for i in map_cat]

#%%
df_base = df_base[['Name', 'Category', 'Visit_Exhibition', 'Visit_Place', 'Opening_Time', 'Under_18_Teaching', 'Under_18_NO_teaching', 'Region', 'Year','Visitors_Exhibition_per_opening_hour']]
df_geo.drop(['Counts', 'address', 'country', 'new_name'], axis=1,  inplace=True)

#%%
for i, row in dt_mun.iterrows():
    df_geo.loc[df_geo["Kommune"] == row['label_dk'], "GeoCode"] = row['lau_1']
    #df_geo.loc[df_geo["Kommune"] == row['label_dk'], "Iso"] = row['iso_3166_2']

#%%
df_visit = df_base[['Name', 'Category', 'Visit_Exhibition', 'Visit_Place', 'Opening_Time', 'Year','Visitors_Exhibition_per_opening_hour']]

#%%
df_visit = pd.merge(df_visit, df_geo, on='Name')

#%%
df_visit = df_visit[df_visit['Name'] != 'Muserum']
df_visit['Visit_Exhibition'] = [round(num) for num in df_visit['Visit_Exhibition']]
df_visit['Visit_Place'] = [round(num) for num in df_visit['Visit_Place']]

#%%
#df_cat = pd.melt(df_cat, id_vars=['Age','Sex', 'Category'], var_name='Year', value_name='Pop_Percent', ignore_index=True)

#%%
df_teaching = df_base[['Name', 'Category', 'Under_18_Teaching', 'Under_18_NO_teaching', 'Visitors_Exhibition_per_opening_hour', 'Year']]
df_teaching = pd.merge(df_teaching, df_geo, on='Name')

#%%
df_teaching = pd.melt(df_teaching, id_vars=['Name', 'Category', 'Kommune', 'Year'], value_vars=['Under_18_NO_teaching', 'Under_18_Teaching'], var_name='Teaching', value_name='Amount', ignore_index=True)

#%%
df_teaching.loc[df_teaching["Teaching"] == "Under_18_Teaching", "Teaching"] = 'Teaching'
df_teaching.loc[df_teaching["Teaching"] == "Under_18_NO_teaching", "Teaching"] = 'No Teaching'

#%%
#df_cat.to_csv('museum_category_2018_2023.csv', index=False)

#%%

#%%
print(round(df_visit['Visit_Exhibition'].sum()))

#%%
print(df_visit['Category'].unique())
#print(df_purp['Category'].nunique())
#print(df_cat['Category'].isna().sum())

#%%




