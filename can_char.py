import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Literal


class Canada_Processed(object):
    def __init__(self, df: pd.DataFrame, grain: Literal['Wheat', 'Barley', 'Corn', 'Oat', 'Rye','Canola', 'Soybeans','Amber Durum'], item: Literal['Domestic', 'Producer Deliveries', 'Exports', 'Producer Shipments']):
        self.grain = grain
        self.item = item
        self.df = df.loc[(df['grain']==grain) & (df['item']==item)]
        self.last_year = self.df['crop_year'].max()
        self.preprocessing()

    def preprocessing(self):
        last_week = self.df[self.df['crop_year']==self.last_year]['grain_week'].max()
        self.current_week_value = self.df.loc[(self.df['grain_week']>=last_week-1) & (self.df['crop_year']==self.last_year)]['value'].diff().dropna().values[0]
        self.last_week_value = self.df.loc[(self.df['grain_week']>=last_week-2)&(self.df['grain_week']<last_week) & (self.df['crop_year']==self.last_year)]['value'].diff().dropna().values[0]
        self.to_date_value = self.df.loc[(self.df['grain_week']==last_week) & (self.df['crop_year']==self.last_year)]['value'].values[0]
        self.last_year_value = self.df.loc[(self.df['grain_week']==last_week) & (self.df['crop_year']==self.last_year-1)]['value'].values[0]
        self.wow_value = self.current_week_value/self.last_week_value-1
        self.yoy_value = self.to_date_value/self.last_year_value-1

        subdf_pivot = self.df.pivot(index='grain_week', columns='crop_year', values='value')
        subdf_pivot = subdf_pivot.interpolate(limit_direction='backward')
        subdf_pivot['date'] = pd.Timestamp(f"{self.last_year}-08-01")+ pd.to_timedelta(7*subdf_pivot.index, unit='d')
        self.df_weekly_pivot = subdf_pivot.copy()
        self.df_weekly_pivot.index = self.df_weekly_pivot['date']
        self.df_weekly_pivot = self.df_weekly_pivot.drop('date', axis=1)
        self.df_weekly_pivot = self.df_weekly_pivot.diff()
        self.df_weekly_pivot = self.df_weekly_pivot.dropna(how='all')
        self.df_weekly_pivot[self.df_weekly_pivot < 0] = 0
        
        df_monthly = pd.DataFrame(index=pd.date_range(start=f"{self.last_year}-08-08", end=f"{self.last_year+1}-07-31"))
        df_monthly = df_monthly.merge(subdf_pivot, left_index=True, right_on='date', how='left')
        df_monthly.index = df_monthly['date']
        df_monthly = df_monthly.drop('date', axis=1)
        df_monthly = df_monthly.interpolate(limit_direction='backward')
        df_monthly['month'] = df_monthly.index.month
        df_monthly['month'] = df_monthly['month'].replace(dict(zip(list(range(8, 13))+list(range(1, 8)), range(1, 13))))
        year_cols = list(df_monthly.columns)[:-1]
        df_monthly[year_cols] = df_monthly[year_cols].diff()
        df_monthly = df_monthly.melt(id_vars='month', var_name='year')
        df_monthly = df_monthly.groupby(['year', 'month'], as_index=False).sum()
        self.df_monthly_pivot = df_monthly.pivot(index='month', columns='year', values='value')

    def plot_weekly_item(self):
        fig = go.Figure()
        for year in self.df_weekly_pivot.columns:
            if year == self.last_year:
                color = 'indianred'
            elif year == self.last_year-1:
                color = 'black'
            else:
                color = '#B2BEB5'
            fig.add_trace(go.Bar(x=self.df_weekly_pivot.index, y=self.df_weekly_pivot[year], name=str(year), marker_color=color))

        fig.update_layout(title=f'Canada - {self.grain} {self.item}, Weekly', hovermode="x unified", font=dict(color='rgb(82, 82, 82)', family='Arial'),width=1000,height=500,
                            xaxis=dict(gridcolor='#FFFFFF',tickformat="%b %d", linecolor='rgb(204, 204, 204)', linewidth=1, ticks='outside', tickfont=dict(size=12)),
                            yaxis=dict(gridcolor='#F8F8F8', tickfont=dict(size=12)),
                            plot_bgcolor='white')
        return fig

    def plot_monthly_item(self):
        fig = go.Figure()
        for year in self.df_monthly_pivot.columns:
            if year == self.last_year:
                color = 'indianred'
            elif year == self.last_year-1:
                color = 'black'
            else:
                color = '#B2BEB5'
            fig.add_trace(go.Bar(x=self.df_monthly_pivot.index, y=self.df_monthly_pivot[year], name=str(year), marker_color=color))

        fig.update_layout(title=f'Canada - {self.grain} {self.item}, Monthly', hovermode="x unified", font=dict(color='rgb(82, 82, 82)', family='Arial'),width=1000,height=500,
                            xaxis=dict(ticktext=['Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'], tickvals=list(range(1, 13)), gridcolor='#FFFFFF', tickformat="%b %d", linecolor='rgb(204, 204, 204)', linewidth=1, ticks='outside', tickfont=dict(size=12)),
                            yaxis=dict(gridcolor='#F8F8F8', tickfont=dict(size=12)),
                            plot_bgcolor='white')
        return fig

    def plot_grain_item(self):
        fig = px.line(self.df.loc[self.df['crop_year']<self.last_year-1], color_discrete_sequence=px.colors.qualitative.G10, 
        x="grain_week", y="value", color='crop_year', labels={'crop_year':'', 'grain_week':"Week"})
        fig.update_traces(line=dict(width=1))

        fig.add_trace(go.Scatter(x=self.df.loc[self.df['crop_year']==self.last_year-1]['grain_week'],y=self.df.loc[self.df['crop_year']==self.last_year-1]['value'],
                                            fill=None, name=str(self.last_year-1),
                                            line=dict(width=2, color='#000000')))

        fig.add_trace(go.Scatter(x=self.df.loc[self.df['crop_year']==self.last_year]['grain_week'],y=self.df.loc[self.df['crop_year']==self.last_year]['value'],
                                            fill=None, name=str(self.last_year),
                                            line=dict(width=2, color='#d62728')))
                                            
        fig.update_layout(title=f'Canada - {self.item}, {self.grain}', hovermode="x unified", font=dict(color='rgb(82, 82, 82)', family='Arial'),width=1000,height=500,
                            xaxis=dict(gridcolor='#FFFFFF',tickformat="%b %d", linecolor='rgb(204, 204, 204)', linewidth=1, ticks='outside', tickfont=dict(size=12)),
                            yaxis=dict(gridcolor='#F8F8F8', tickfont=dict(size=12)),
                            plot_bgcolor='white')
        return fig
