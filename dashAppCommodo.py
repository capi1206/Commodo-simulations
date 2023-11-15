import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import networkx as nx
from networkx import Graph
import numpy as np
import plotly.graph_objs as go
import copy 
import random
import plotly.colors as pc
import json


#color_scale = pc.qualitative.Viridis
#carga puntos precalculados
with open('assets/data.json', 'r') as json_file:
    puntos = json.load(json_file)
l_puntos = [k for k in puntos]

# Create a Dash app
app = dash.Dash(__name__)

# Initial values for widgets
n_usuarios = 200
monto_inicial = 50
n_iteraciones = 5
n_referidos = 4
monto_referir = 2.5
iteration=0

# Layout of the app
app.layout = html.Div([
    #html.Img(src=app.get_asset_url('C:\Users\difes\OneDrive\Documentos\Integrity\Graphs\commodo.png'), style={'height': '10%', 'width': '25%'}),
    html.Img(src='/assets/commodo.png', style={'height': '8%', 'width': '22%'}),
    
    #html.H1("Red de Commodo-visualización",style={'color': 'white'}),   
    html.Div(id='widget-container', children=[
        html.Label("Número de ususarios iniciales:"),
        dcc.Slider(id='n-usuarios-slider', min=0, max=800, step=50, value=n_usuarios, marks={i: str(i) for i in range(0, 801, 50)}),
        
        html.Label("Monto inicial:"),
        dcc.Slider(id='monto-inicial-input', min=1, max=100, value=monto_inicial),
    
        html.Label("Número de iteraciones:"),
        dcc.Slider(id='n-iteraciones-slider', min=0, max=12, step=1, value=n_iteraciones, marks={i: str(i) for i in range(12)}),
        
        html.Label("Número máxino de referidos:"),
        dcc.Slider(id='n-referidos-slider', min=0, max=5, step=1, value=n_referidos, marks={i: str(i) for i in range(6)}),
        
        html.Label("Monto por referir:"),
        dcc.Slider(id='monto-referir-input', min=1, max=20, value=monto_referir),
    
        html.Button('Calcular', id='compute-button', n_clicks=0),
    ]),
    html.Div(id='graph-container', style={'display': 'none'}, children=[
        html.Label("Número de iteración:"),
        dcc.Slider(id='iteration-slider', min=0, max=10, step=1, value=iteration, marks={i: str(i) for i in range(11)}),
        html.Div(style={'display': 'flex'}, children=[
        dcc.Graph(id='graph-output',style={'display': 'flex', 'justify-content': 'center'}, ),
        html.Div(id='table-container')])
    ])

])
#funcion que regresa el indice que mejor se aproxima a la cantidad de puntos, n
def best_match(n):
    min_l= min([abs(n-int(k)) for k in l_puntos])
    return [k for k in l_puntos if min_l==abs(n-int(k))][0]

def actualiza(graph, enlaces, n_referidos, monto_referir):
    c_graph=dict(graph)
    for k in c_graph:
        r=random.random()
        if graph[k]['profundidad']!=0 and graph[k]['referidos']<n_referidos and r>0.7:
            n_referir=max(1,int((n_referidos +1)*random.random())-graph[k]['referidos'])
            for _ in range(n_referir):
                graph, enlaces=refiere(graph, enlaces, k, monto_referir)
    return graph, enlaces
#se añade un nuevo nodo con n_monto y al nodo que refiere se le incrementa monto por n_monto
def refiere(graph, enlaces, de_nodo, n_monto):
    new_node_id = max(graph) + 1
    graph[new_node_id] = {
        'profundidad': graph[de_nodo]['profundidad'] + 1,'referidos':0, 'monto':n_monto
        }
    graph[de_nodo]['referidos'] += 1
    graph[de_nodo]['monto'] += n_monto
    enlaces.append((de_nodo,new_node_id))
    return graph, enlaces
#callback para actualizar slider
@app.callback(
    Output('iteration-slider', 'marks'),
    Output('iteration-slider', 'max'),
    Output('iteration-slider', 'value'),
    Input('n-iteraciones-slider', 'value')
)

def update_iteration_slider(n_iteraciones_value):
    iteration_marks = {i: str(i) for i in range(n_iteraciones_value + 1)}
    return iteration_marks, n_iteraciones_value, min(n_iteraciones_value, iteration)
# callback para generar graficas
@app.callback(
    Output('graph-container', 'style'),
    Output('widget-container', 'style'),    
    Output('graph-output', 'figure'),
    Output('table-container', 'children'),
    Input('compute-button', 'n_clicks'),
    Input('n-usuarios-slider', 'value'),
    Input('monto-inicial-input', 'value'),
    Input('n-iteraciones-slider', 'value'),
    Input('n-referidos-slider', 'value'),
    Input('monto-referir-input', 'value'),
    Input('iteration-slider', 'value')
)
#actualiza grafica
def update_graph(n_clicks, n_usuarios, monto_inicial, n_iteraciones, n_referidos, monto_referir, selected_iteration):
    if n_clicks > 0:
        sel_iter=selected_iteration #min(selected_iteration, n_iteraciones-1)
        graph = {1: {'profundidad': 0, 'referidos':0, 'monto':0}}
        enlaces=[]
        for _ in range(n_usuarios):
            n_id = max(graph) + 1
            graph[n_id] = {'profundidad': 1,'referidos':0, 'monto':monto_inicial}
            enlaces.append((1,n_id))
        for _ in range(sel_iter):  
            graph, enlaces=actualiza(graph, enlaces, n_referidos, monto_referir)
        ind_l=best_match(len(graph))
        prof_values = [graph[k]['profundidad'] for k in graph]
        normalized_prof = np.interp(prof_values, (min(prof_values), max(prof_values)), (0, 1))
        #normalized_prof[1:] = np.interp(normalized_prof[1:], (0, 1), (0.9, 0.95))
        if selected_iteration == 0:
            color_scale = [[0.0, 'red'],[1.0, 'lightcoral'] ]
            normalized_prof[1:] = np.interp(normalized_prof[1:], (0, 1), (0.9, 0.95))  # Fade other points
        else:
            color_scale = [[0.0, 'red'],  [1.0, 'white']   ]
        x_nodes = puntos[ind_l]['x']
        y_nodes = puntos[ind_l]['y']
        z_nodes = puntos[ind_l]['z']
        trace_nodes = go.Scatter3d(
            x=x_nodes, y=y_nodes, z=z_nodes,
            mode='markers', marker=dict(
        symbol='circle',
        size=5,
        color=normalized_prof,  
        colorscale=color_scale,
        line=dict(color='black', width=1),  
    ),
        hoverinfo='none'
    )
        layout = go.Layout(
            width=800, height=800,
            scene=dict(
                xaxis=dict(showbackground=False, showline=False, zeroline=False, showgrid=False, showticklabels=False),
                yaxis=dict(showbackground=False, showline=False, zeroline=False, showgrid=False, showticklabels=False),
                zaxis=dict(showbackground=False, showline=False, zeroline=False, showgrid=False, showticklabels=False),
            ),
            margin=dict(l=0, r=0, t=0, b=0)
        )

        data = [trace_nodes]
        fig = go.Figure(data=data, layout=layout)
        
        
        total_nodes = len(graph)-1
        total_monto = sum(graph[k]['monto'] for k in graph)
        table_content = html.Table([
            html.Tr([html.Th('Usuarios totales'), html.Td(total_nodes)]),
            
            
            html.Tr([html.Th('Monto total (x 1000$)'), html.Td(total_monto)])
        ])
        print(graph)
        widget_style = {'display': 'none'}
        graph_style={'display': 'block'}
    
        return graph_style, widget_style, fig, table_content
    else:
        widget_style = {'display': 'block'}
        graph_style = {'display': 'none'} 

        return graph_style, widget_style, {}, {}
# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)

