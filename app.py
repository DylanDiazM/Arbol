import plotly.graph_objs as go
import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output

# Create a Dash app
app = dash.Dash(__name__)

file_path = 'arbol_4.xlsx'
data = pd.read_excel(file_path)

def safe_int(value):
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None

# Processing data
data['Fecha y Hora de Programación'] = pd.to_datetime(data['Fecha y Hora de Programación'], errors='coerce')
data['Fecha y Hora de Programación_str'] = data['Fecha y Hora de Programación'].dt.strftime('%Y-%m-%d %H:%M:%S')
data['Fecha y Hora de Cierre'] = pd.to_datetime(data['Fecha y Hora de Cierre'], errors='coerce')
data['Fecha y Hora de Cierre_str'] = data['Fecha y Hora de Cierre'].dt.strftime('%Y-%m-%d %H:%M:%S')
data['Axis Y'] = pd.to_numeric(data['Axis Y'], errors='coerce')

data['Código Predecesor'] = data['Código Predecesor'].apply(lambda x: ','.join([str(safe_int(i)) for i in str(x).split(',') if safe_int(i) is not None]))
data['Código'] = data['Código'].apply(safe_int)
data['Código Sucesor'] = data['Código Sucesor'].apply(lambda x: ','.join([str(safe_int(i)) for i in str(x).split(',') if safe_int(i) is not None]))

# Find related predecessors and successors
def find_related_nodes_single(codigo):
    predecessors = []
    successors = []
    selected_row = data[data['Código'] == codigo]
    if not selected_row.empty:
        predecessors_str = selected_row.iloc[0]['Código Predecesor']
        successors_str = selected_row.iloc[0]['Código Sucesor']
        if pd.notna(predecessors_str):
            predecessors = [int(p) for p in predecessors_str.split(',') if p.strip()]
        if pd.notna(successors_str):
            successors = [int(s) for s in successors_str.split(',') if s.strip()]
    return predecessors, successors

# Set up Dash layout
app.layout = html.Div([
    html.H1('Árbol'),

    # Dropdown for Año selection
    dcc.Dropdown(
        id='filter-año',
        options=[{'label': str(year), 'value': year} for year in sorted(data['Año'].unique())],
        value=data['Año'].max(),  # Default to the most recent year
        multi=False,
        placeholder="Selecciona el Año"
    ),

    # Dropdown for Mes selection
    dcc.Dropdown(
        id='filter-mes',
        options=[{'label': str(month), 'value': month} for month in sorted(data['Mes'].unique())],
        value=data['Mes'].max(),  # Default to the most recent month
        multi=False,
        placeholder="Selecciona el Mes"
    ),

    # Dropdown for selecting between Programación and Cierre
    dcc.Dropdown(
        id='filter-fecha',
        options=[
            {'label': 'Fecha y Hora de Programación', 'value': 'Fecha y Hora de Programación_str'},
            {'label': 'Fecha y Hora de Cierre', 'value': 'Fecha y Hora de Cierre_str'}
        ],
        value='Fecha y Hora de Programación_str',  # Default to "Fecha y Hora de Programación"
        multi=False
    ),

    # Dropdown for Código selection (or any predefined list of codes)
    dcc.Dropdown(
        id='filter-codigo',
        options=[{'label': str(codigo), 'value': codigo} for codigo in sorted(data['Código'].unique())],
        value=[],  # Default is an empty list (no code selected)
        multi=True,
        placeholder="Selecciona los Códigos"
    ),

    # Graph for visualizing data
    dcc.Graph(id='graph')
])

# Define callback to update graph based on filters
@app.callback(
    Output('graph', 'figure'),
    [Input('filter-fecha', 'value'),
     Input('filter-codigo', 'value'),
     Input('filter-año', 'value'),
     Input('filter-mes', 'value')]
)
def update_graph(selected_fecha, selected_codigos, selected_año, selected_mes):
    fig = go.Figure()

    # Filter data based on Año and Mes
    filtered_data_by_year_month = data[(data['Año'] == selected_año) & (data['Mes'] == selected_mes)]

    # If no codes are selected, exit early
    if not selected_codigos:
        return fig

    for selected_codigo in selected_codigos:
        predecessors, successors = find_related_nodes_single(selected_codigo)
        selected_data = filtered_data_by_year_month[filtered_data_by_year_month['Código'] == selected_codigo]

        if all(col in selected_data.columns for col in ['Responsable Principal', 'Duración', 'Duración Programada','Actividad']):
            selected_customdata = selected_data[['Responsable Principal', 'Duración', 'Duración Programada','Actividad']].fillna("N/A")
        else:
            selected_customdata = [["N/A", "N/A", "N/A", "N/A"]] * len(selected_data)

        if not selected_data.empty:
            fig.add_trace(go.Scatter(
                x=selected_data[selected_fecha],
                y=selected_data['Axis Y'],
                mode='markers+text',
                text=["<b>{}</b>".format(codigo) for codigo in selected_data['Código']],
                textposition='top center',
                marker=dict(size=10, color='blue'),
                customdata=selected_customdata,
                showlegend=False,
                hovertemplate=(
                    "%{text} - %{customdata[3]}<br>"
                    "<b>Fecha y Hora de Programación:</b> %{x}<br>"
                    "<b>Responsable principal:</b> %{customdata[0]}<br>"
                    "<b>Duración:</b> %{customdata[1]}<br>"
                    "<b>Duración Programada:</b> %{customdata[2]}<extra></extra>"
                )
            ))

        predecessor_data = filtered_data_by_year_month[filtered_data_by_year_month['Código'].isin(predecessors)]
        if all(col in predecessor_data.columns for col in ['Responsable Principal', 'Duración', 'Duración Programada','Actividad']):
            predecessor_customdata = predecessor_data[['Responsable Principal', 'Duración', 'Duración Programada','Actividad']].fillna("N/A")
        else:
            predecessor_customdata = [["N/A", "N/A", "N/A", "N/A"]] * len(predecessor_data)

        fig.add_trace(go.Scatter(
            x=predecessor_data[selected_fecha],
            y=predecessor_data['Axis Y'],
            mode='markers',
            text=predecessor_data['Código'],
            textposition='top center',
            marker=dict(size=8, color='green'),
            customdata=predecessor_customdata,
            showlegend=False,
            hovertemplate=(
                "%{text} - %{customdata[3]}<br>"
                "<b>Fecha y Hora de Programación:</b> %{x}<br>"
                "<b>Responsable principal:</b> %{customdata[0]}<br>"
                "<b>Duración:</b> %{customdata[1]}<br>"
                "<b>Duración Programada:</b> %{customdata[2]}<extra></extra>"
            )
        ))

        successor_data = filtered_data_by_year_month[filtered_data_by_year_month['Código'].isin(successors)]
        if all(col in successor_data.columns for col in ['Responsable Principal', 'Duración', 'Duración Programada','Actividad']):
            successor_customdata = successor_data[['Responsable Principal', 'Duración', 'Duración Programada','Actividad']].fillna("N/A")
        else:
            successor_customdata = [["N/A", "N/A", "N/A", "N/A"]] * len(successor_data)

        fig.add_trace(go.Scatter(
            x=successor_data[selected_fecha],
            y=successor_data['Axis Y'],
            mode='markers',
            text=successor_data['Código'],
            textposition='middle right',
            marker=dict(size=8, color='red'),
            textfont=dict(size=10),
            customdata=successor_customdata,
            showlegend=False,
            hovertemplate=(
                "%{text} - %{customdata[3]}<br>"
                "<b>Fecha y Hora de Programación:</b> %{x}<br>"
                "<b>Responsable principal:</b> %{customdata[0]}<br>"
                "<b>Duración:</b> %{customdata[1]}<br>"
                "<b>Duración Programada:</b> %{customdata[2]}<extra></extra>"
            )
        ))

        # Add lines for predecessors
        for pred in predecessors:
            pred_data = filtered_data_by_year_month[filtered_data_by_year_month['Código'] == pred]
            if not pred_data.empty and not selected_data.empty:
                fig.add_trace(go.Scatter(
                    x=[pred_data[selected_fecha].values[0], selected_data[selected_fecha].values[0]],
                    y=[pred_data['Axis Y'].values[0], selected_data['Axis Y'].values[0]],
                    mode='lines',
                    line=dict(color='green'),
                    showlegend=False
                ))

        # Add lines for successors
        for succ in successors:
            succ_data = filtered_data_by_year_month[filtered_data_by_year_month['Código'] == succ]
            if not succ_data.empty and not selected_data.empty:
                fig.add_trace(go.Scatter(
                    x=[selected_data[selected_fecha].values[0], succ_data[selected_fecha].values[0]],
                    y=[selected_data['Axis Y'].values[0], succ_data['Axis Y'].values[0]],
                    mode='lines',
                    line=dict(color='red'),
                    showlegend=False
                ))

    # Add legend
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode='markers',
        marker=dict(size=10, color='blue'),
        name="Actividad"
    ))
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode='markers',
        marker=dict(size=8, color='green'),
        name="Predecesor"
    ))
    fig.add_trace(go.Scatter(
        x=[None], y=[None],
        mode='markers',
        marker=dict(size=8, color='red'),
        name="Sucesor"
    ))

    # Layout settings
    fig.update_layout(
        title="Ánalisis",
        xaxis_title="Fecha y Hora",
        yaxis_title="",
        height=800,
        width=1050
    )

    return fig


