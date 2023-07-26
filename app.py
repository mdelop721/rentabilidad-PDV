import pandas as pd
import plotly.express as px
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from flask import Flask, render_template, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt

import os

# basedir = os.path.abspath(os.path.dirname(__file__))
#
# 'sqlite:///' + os.path.join(basedir, 'database.db')





ruta_archivo = r'C:/Users/MDELGADILLO/OneDrive - Primewireless Holdings, S. de R.L. de C.V/Documentos/Rentabilidad Tiendas/Scripts/Rentabilidad/Rentabilidad 2023_Valores.xlsx'


# ruta_archivo = r'Rentabilidad 2023_Valores.xlsx'

# Usamos "r" antes de la ruta del archivo para evitar problemas con caracteres especiales en la ruta.

DATA = pd.read_excel(ruta_archivo,sheet_name="Info para Graficar")

ACTIVOS = DATA.query("ESTATUS == 1 and MAP != 0")

app_flask = Flask(__name__,root_path='C:\\Users\\MDELGADILLO\\OneDrive - Primewireless Holdings, S. de R.L. de C.V\\Documentos\\Rentabilidad Tiendas\\Scripts\\Rentabilidad')

basedir = os.path.abspath(os.path.dirname(__file__))
app_flask.config['SQLALCHEMY_DATABASE_URI'] ='sqlite:///' + os.path.join(basedir, 'database.db')
app_flask.config['SECRET_KEY'] = 'thisisasecretkey'

login_manager = LoginManager()
login_manager.init_app(app_flask)
login_manager.login_view = "index"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

db = SQLAlchemy(app_flask)
bcrypt = Bcrypt(app_flask)

app_flask.app_context().push()


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)


class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Usuario"}, label="Usuario")

    password = PasswordField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Contraseña"})

    submit = SubmitField("Crear Usuario", render_kw={"class": "btn"})

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(
            username=username.data).first()

        if existing_user_username:
            print("That username already exists. Please choose a different one.")
            # flash('El usuario ingresado ya existe. Favor de intentar con uno diferente')



class LoginForm(FlaskForm):
    username = StringField(label="Usuario", validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Ingresa tu usuario"})

    password = PasswordField(label="Contraseña", validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Introduce tu contraseña"})

    submit = SubmitField("Iniciar sesión", render_kw={"class": "btn"})


fig = px.scatter(ACTIVOS, x="DELTA", y="Sueldos y comisiones (%)",
                 color="CLUSTER", size="Renta Promedio",
                 hover_data=["PDV"])

valores_clasificacion = ACTIVOS["CLASIFICACION"].unique()
# opciones_clasificacion = [{'label': 'Seleccionar todo', 'value': 'Select all'}] + [{'label': c, 'value': c} for c in valores_clasificacion]

colors = ["red", "orange", "#DDE200", "#92D050", "#00B050"]
cluster = ['REVISAR RENTA/HC', 'PRESIONAR', 'SUFICIENTE', 'MANTENER', 'SOBRESALIENTE']

map_colors = zip(colors, cluster)

map_colors = {clus: col for col, clus in map_colors}

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP], server=app_flask, url_base_pathname='/dashboard/')
# server = app.server


app.layout = dbc.Container(
    fluid=True,
    children=[
        html.Img(src="https://ii.ct-stc.com/2/logos/empresas/2019/08/20/844522c9b76e41698c76011050410thumbnail.jpg",
                 style={'position': 'absolute', 'top': '10px', 'right': '10px', 'width': '150px', 'height': '40px'}),
        html.A('Cerrar sesión', href='/logout'),
        html.H1('Rentabilidad PDV YTD 2023', style={'text-align': 'left'}),
        dbc.Button(
            "Mostrar/Ocultar Filtros",
            id="toggle-filtros",
            color="primary",
            style={'margin-bottom': '10px', 'width': '3rem'}
        ),
        dbc.Row(
            [
                dbc.Col(
                    id="filtros-col",
                    children=[
                        dbc.Collapse(
                            children=[
                                html.Details([
                                    html.Summary('Seleccione la Región', style={'font-weight': 'bold'}),
                                    html.Br(),
                                    dcc.Checklist(
                                        id='filtro-region',
                                        options=[{'label': r, 'value': r} for r in ACTIVOS['REGION'].unique()],
                                        value=[],
                                        labelStyle={'display': 'inline-block', 'margin-right': '10px'}
                                    )
                                ]),
                                # html.Br(),
                                html.Details([
                                    html.Summary('Seleccione la Clasificación de la Tienda',
                                                 style={'font-weight': 'bold'}),
                                    html.Br(),
                                    dcc.Checklist(id='filtro-clasificacion',
                                                  options=valores_clasificacion,
                                                  value=valores_clasificacion,
                                                  labelStyle={'display': 'block'}
                                                  )
                                ]),
                                # html.Br(),
                                html.Details([
                                    html.Summary('Filtro Delta', style={'font-weight': 'bold'}),
                                    html.Br(),
                                    html.Label('Delta:'),
                                    dcc.Input(
                                        id='filtro-delta-igualdad',
                                        type='number',
                                        value=None,
                                        placeholder='',
                                        style={'width': '100%'}
                                    ),
                                    html.Label('Modo:', id='modo-delta'),
                                    dcc.Dropdown(
                                        id='filtro-delta-desigualdad',
                                        options=[
                                            {'label': '=', 'value': 'igual'},
                                            {'label': '>', 'value': 'mayor'},
                                            {'label': '<', 'value': 'menor'},
                                            {'label': '>=', 'value': 'mayor_igual'},
                                            {'label': '<=', 'value': 'menor_igual'},
                                            {'label': 'Entre', 'value': 'entre'}  # Nueva opción "Entre"
                                        ],
                                        value='mayor_igual',
                                        clearable=False,
                                        searchable=False
                                    ),
                                    html.Div(id='entre-limits-delta',
                                             # Contenedor para los inputs de límites inferiores y superiores
                                             children=[
                                                 html.Label('Límite Inferior:'),
                                                 dcc.Input(id='filtro-delta-limite-inferior',
                                                           type='number',
                                                           value=None,
                                                           placeholder='',
                                                           style={'width': '100%'}
                                                           ),
                                                 html.Label('Límite Superior:'),
                                                 dcc.Input(id='filtro-delta-limite-superior',
                                                           type='number',
                                                           value=None,
                                                           placeholder='',
                                                           style={'width': '100%'}
                                                           )],
                                             style={'display': 'none'}
                                             # Inicialmente oculto hasta que se seleccione "Entre"
                                             )
                                ]),
                                html.Details([
                                    html.Summary('Productividad Por HC', style={'font-weight': 'bold'}),
                                    html.Br(),
                                    html.Label('MAP X HC:'),
                                    dcc.Input(
                                        id='filtro-HC-igualdad',
                                        type='number',
                                        value=None,
                                        placeholder='',
                                        style={'width': '100%'}
                                    ),
                                    html.Label('Modo:', id="label_modo"),
                                    dcc.Dropdown(
                                        id='filtro-HC-desigualdad',
                                        options=[
                                            {'label': '=', 'value': 'igual'},
                                            {'label': '>', 'value': 'mayor'},
                                            {'label': '<', 'value': 'menor'},
                                            {'label': '>=', 'value': 'mayor_igual'},
                                            {'label': '<=', 'value': 'menor_igual'},
                                            {'label': 'Entre', 'value': 'entre'}  # Nueva opción "Entre"
                                        ],
                                        value='mayor_igual',
                                        clearable=False,
                                        searchable=False
                                    ),
                                    html.Div(id='entre-limits',
                                             # Contenedor para los inputs de límites inferiores y superiores
                                             children=[
                                                 html.Label('Límite Inferior:'),
                                                 dcc.Input(id='filtro-HC-limite-inferior',
                                                           type='number',
                                                           value=None,
                                                           placeholder='',
                                                           style={'width': '100%'}
                                                           ),
                                                 html.Label('Límite Superior:'),
                                                 dcc.Input(id='filtro-HC-limite-superior',
                                                           type='number',
                                                           value=None,
                                                           placeholder='',
                                                           style={'width': '100%'}
                                                           )],
                                             style={'display': 'none'}
                                             # Inicialmente oculto hasta que se seleccione "Entre"
                                             )
                                ]),
                                html.Details([
                                    html.Summary('Filtro ARPU', style={'font-weight': 'bold'}),
                                    html.Br(),
                                    html.Label('ARPU:'),
                                    dcc.Input(
                                        id='filtro-ARPU-igualdad',
                                        type='number',
                                        value=None,
                                        placeholder='',
                                        style={'width': '100%'}
                                    ),
                                    html.Label('Modo:', id="label_modo_ARPU"),
                                    dcc.Dropdown(
                                        id='filtro-ARPU-desigualdad',
                                        options=[
                                            {'label': '=', 'value': 'igual'},
                                            {'label': '>', 'value': 'mayor'},
                                            {'label': '<', 'value': 'menor'},
                                            {'label': '>=', 'value': 'mayor_igual'},
                                            {'label': '<=', 'value': 'menor_igual'},
                                            {'label': 'Entre', 'value': 'entre'}  # Nueva opción "Entre"
                                        ],
                                        value='mayor_igual',
                                        clearable=False,
                                        searchable=False
                                    ),
                                    html.Div(id='entre-limits-ARPU',
                                             # Contenedor para los inputs de límites inferiores y superiores
                                             children=[
                                                 html.Label('Límite Inferior:'),
                                                 dcc.Input(id='filtro-ARPU-limite-inferior',
                                                           type='number',
                                                           value=None,
                                                           placeholder='',
                                                           style={'width': '100%'}
                                                           ),
                                                 html.Label('Límite Superior:'),
                                                 dcc.Input(id='filtro-ARPU-limite-superior',
                                                           type='number',
                                                           value=None,
                                                           placeholder='',
                                                           style={'width': '100%'}
                                                           )],
                                             style={'display': 'none'}
                                             # Inicialmente oculto hasta que se seleccione "Entre"
                                             )
                                ]),
                                html.Br(),
                                html.Div([
                                    html.Label('Filtro PDV:'),
                                    dcc.Dropdown(
                                        id='filtro-pdv',
                                        options=[{'label': str(pdv), 'value': pdv} for pdv in
                                                 sorted(ACTIVOS['PDV'].unique())],
                                        value=None,
                                        placeholder='Seleccione un valor'
                                    )
                                ], style={'width': '100%', 'margin-bottom': '10px'}),
                                dbc.Button('Mostrar Por Origen/Total', id='toggle-facet-col', n_clicks=0,
                                           style={'margin-bottom': '10px'}),
                                html.Br(),
                                dbc.Button('Cambiar Campos', id='cambiar-campos', n_clicks=0,
                                           style={'margin-bottom': '10px'}),
                                html.Br(),
                                dbc.Button('Borrar Filtros', id='borrar-filtros', n_clicks=0,
                                           style={'margin-bottom': '10px'}),
                            ],
                            id="collapse-filtros",
                            is_open=False
                        )
                    ],
                    width={'size': 0, 'order': 1},  # Ajusta el ancho de la columna de filtros según tus necesidades
                    style={'display': 'none'}
                ),
                dbc.Col(
                    id="scatter-col",
                    children=[
                        html.Div(id='conteo-etiqueta',
                                 style={'text-align': 'center', 'margin-top': '10px', 'font-weight': 'bold',
                                        'font-size': '20px', 'white-space': 'pre-wrap'}),
                        dcc.Graph(id='scatter-plot', figure=fig, style={'height': '85vh'})
                    ],
                    width={'size': 12, 'order': 2}
                )
            ]
        )
    ]
)


#################CALLBACK PARA FILTRO DELTA#########################
@app.callback(
    dash.dependencies.Output('entre-limits-delta', 'style'),
    dash.dependencies.Output('filtro-delta-igualdad', 'style'),
    # Mostrar u ocultar los inputs según la opción seleccionada
    dash.dependencies.Output('modo-delta', 'style'),
    dash.dependencies.Output('filtro-delta-igualdad', 'value', allow_duplicate=True),
    dash.dependencies.Output('filtro-delta-limite-inferior', 'value', allow_duplicate=True),
    # Nuevo input para límite inferior
    dash.dependencies.Output('filtro-delta-limite-superior', 'value', allow_duplicate=True),
    # Nuevo input para límite superior
    [dash.dependencies.Input('filtro-delta-desigualdad', 'value'),
     dash.dependencies.Input('filtro-delta-igualdad', 'value')],
    prevent_initial_call=True
)
def show_hide_inputs_delta(desigualdad, valor):
    if desigualdad == 'entre':
        return {'display': 'block'}, {'display': 'none'}, {'display': 'none'}, None, ACTIVOS["DELTA"].min(), ACTIVOS[
            "DELTA"].max()
    else:
        return {'display': 'none'}, {'display': 'block'}, {'display': 'block'}, valor, None, None


#################CALLBACK PARA FILTRO PROD POR HC#########################
@app.callback(
    dash.dependencies.Output('entre-limits', 'style'),
    dash.dependencies.Output('filtro-HC-igualdad', 'style'),
    # Mostrar u ocultar los inputs según la opción seleccionada
    dash.dependencies.Output('label_modo', 'style'),
    dash.dependencies.Output('filtro-HC-igualdad', 'value', allow_duplicate=True),
    dash.dependencies.Output('filtro-HC-limite-inferior', 'value', allow_duplicate=True),
    # Nuevo input para límite inferior
    dash.dependencies.Output('filtro-HC-limite-superior', 'value', allow_duplicate=True),
    # Nuevo input para límite superior
    [dash.dependencies.Input('filtro-HC-desigualdad', 'value'),
     dash.dependencies.Input('filtro-HC-igualdad', 'value')],
    prevent_initial_call=True
)
def show_hide_inputs(desigualdad, valor):
    if desigualdad == 'entre':
        return {'display': 'block'}, {'display': 'none'}, {'display': 'none'}, None, ACTIVOS["MAP X HC"].min(), ACTIVOS[
            "MAP X HC"].max()
    else:
        return {'display': 'none'}, {'display': 'block'}, {'display': 'block'}, valor, None, None


#################CALLBACK PARA FILTRO ARPU#########################
@app.callback(
    dash.dependencies.Output('entre-limits-ARPU', 'style'),
    dash.dependencies.Output('filtro-ARPU-igualdad', 'style'),
    # Mostrar u ocultar los inputs según la opción seleccionada
    dash.dependencies.Output('label_modo_ARPU', 'style'),
    dash.dependencies.Output('filtro-ARPU-igualdad', 'value', allow_duplicate=True),
    dash.dependencies.Output('filtro-ARPU-limite-inferior', 'value', allow_duplicate=True),
    # Nuevo input para límite inferior
    dash.dependencies.Output('filtro-ARPU-limite-superior', 'value', allow_duplicate=True),
    # Nuevo input para límite superior
    [dash.dependencies.Input('filtro-ARPU-desigualdad', 'value'),
     dash.dependencies.Input('filtro-ARPU-igualdad', 'value')],
    prevent_initial_call=True
)
def show_hide_inputs_ARPU(desigualdad, valor):
    if desigualdad == 'entre':
        return {'display': 'block'}, {'display': 'none'}, {'display': 'none'}, None, ACTIVOS["ARPU"].min(), ACTIVOS[
            "ARPU"].max()
    else:
        return {'display': 'none'}, {'display': 'block'}, {'display': 'block'}, valor, None, None


#################CALLBACK PARA MOSTRAR/OCULTAR PANEL DE FILTROS#########################
@app.callback(
    dash.dependencies.Output("scatter-col", "width"),
    dash.dependencies.Output("toggle-filtros", "children"),
    dash.dependencies.Output("toggle-filtros", "color"),
    dash.dependencies.Output("filtros-col", "style"),
    dash.dependencies.Output("collapse-filtros", "is_open"),
    [dash.dependencies.Input("toggle-filtros", "n_clicks")],
    [dash.dependencies.State("scatter-col", "width")]
)
def toggle_filters(n_clicks, scatter_col_width):
    if n_clicks and n_clicks % 2 == 1:
        # return {'size': 12, 'order': 2}, "☰", "primary", {'display': 'none'}
        return {'size': 9, 'order': 2}, "☰", "danger", {'size': 3, 'order': 1}, True
    else:
        return {'size': 12, 'order': 2}, "☰", "primary", {'display': 'none'}, False
        # return {'size': 9, 'order': 2}, "☰", "danger", {'size': 3, 'order': 1}


@app.callback(
    dash.dependencies.Output('scatter-plot', 'figure'),
    dash.dependencies.Output('conteo-etiqueta', 'children'),
    dash.dependencies.Output('toggle-facet-col', 'children'),
    dash.dependencies.Output('cambiar-campos', 'children'),
    [dash.dependencies.Input('filtro-region', 'value'),
     dash.dependencies.Input('toggle-facet-col', 'n_clicks'),
     dash.dependencies.Input('filtro-delta-igualdad', 'value'),
     dash.dependencies.Input('filtro-delta-desigualdad', 'value'),
     dash.dependencies.Input('filtro-HC-igualdad', 'value'),
     dash.dependencies.Input('filtro-HC-desigualdad', 'value'),
     dash.dependencies.Input('filtro-ARPU-igualdad', 'value'),
     dash.dependencies.Input('filtro-ARPU-desigualdad', 'value'),
     dash.dependencies.Input('filtro-pdv', 'value'),
     dash.dependencies.Input('filtro-clasificacion', 'value'),
     dash.dependencies.Input('cambiar-campos', 'n_clicks'),
     dash.dependencies.Input('filtro-HC-limite-inferior', 'value'),  # Nuevo input para límite inferior
     dash.dependencies.Input('filtro-HC-limite-superior', 'value'),  # Nuevo input para límite superior
     dash.dependencies.Input('filtro-delta-limite-inferior', 'value'),  # Nuevo input para límite inferior
     dash.dependencies.Input('filtro-delta-limite-superior', 'value'),  # Nuevo input para límite superior
     dash.dependencies.Input('filtro-ARPU-limite-inferior', 'value'),  # Nuevo input para límite inferior
     dash.dependencies.Input('filtro-ARPU-limite-superior', 'value'),  # Nuevo input para límite superior
     ]
)
def update_scatter_plot(region, n_clicks, delta_igualdad, delta_desigualdad, hc_igualdad, hc_desigualdad,
                        ARPU_igualdad, ARPU_desigualdad, pdv, clasificacion, cambiar_campos, limite_inferior,
                        limite_superior, LI_DELTA, LS_DELTA, LI_ARPU, LS_ARPU):
    filtered_df = ACTIVOS.copy()

    if cambiar_campos % 2 == 1:
        filtered_df = filtered_df[['CVE_UNICA_PDV', 'PDV', 'Sueldos y comisiones ($)', 'Renta ($)',
                                   'SyC Promedio', 'Renta Promedio', 'Sueldos y comisiones (%)',
                                   'Renta (%)', 'SC NEGATIVO', 'SC NEGATIVO ACUMULADO',
                                   'BE AJ', 'DELTA AJ', 'CLUSTER AJ', 'ESTATUS', 'ORIGEN', 'REGION', 'HC',
                                   'ARPU', 'MAP', 'CLASIFICACION', 'INGRESOS', 'SC AJUSTADO', 'SC AJUSTADO PROMEDIO',
                                   'INGRESOS PROMEDIO',
                                   'MAP X HC']]

        filtered_df.rename(columns={
            "BE AJ": "BREAK EVEN",
            "DELTA AJ": "DELTA",
            "CLUSTER AJ": "CLUSTER",
            "SC AJUSTADO": "SC",
            "SC AJUSTADO PROMEDIO": "SC PROMEDIO"
        }, inplace=True)

    if hc_igualdad is not None:
        if hc_desigualdad == 'igual':
            filtered_df = filtered_df[filtered_df['MAP X HC'] == hc_igualdad]
        elif hc_desigualdad == 'mayor':
            filtered_df = filtered_df[filtered_df['MAP X HC'] > hc_igualdad]
        elif hc_desigualdad == 'menor':
            filtered_df = filtered_df[filtered_df['MAP X HC'] < hc_igualdad]
        elif hc_desigualdad == 'mayor_igual':
            filtered_df = filtered_df[filtered_df['MAP X HC'] >= hc_igualdad]
        elif hc_desigualdad == 'menor_igual':
            filtered_df = filtered_df[filtered_df['MAP X HC'] <= hc_igualdad]
    else:
        if hc_desigualdad == 'entre':  # Aplicar filtro "Entre"
            if limite_inferior is not None and limite_superior is not None:
                filtered_df = filtered_df.query('`MAP X HC`.between(@limite_inferior, @limite_superior)')

    if region:
        filtered_df = filtered_df[filtered_df['REGION'].isin(region)]

    facet_col = "ORIGEN" if n_clicks % 2 == 1 else None

    if delta_igualdad is not None:
        if delta_desigualdad == 'igual':
            filtered_df = filtered_df[filtered_df['DELTA'] == delta_igualdad]
        elif delta_desigualdad == 'mayor':
            filtered_df = filtered_df[filtered_df['DELTA'] > delta_igualdad]
        elif delta_desigualdad == 'menor':
            filtered_df = filtered_df[filtered_df['DELTA'] < delta_igualdad]
        elif delta_desigualdad == 'mayor_igual':
            filtered_df = filtered_df[filtered_df['DELTA'] >= delta_igualdad]
        elif delta_desigualdad == 'menor_igual':
            filtered_df = filtered_df[filtered_df['DELTA'] <= delta_igualdad]
    else:
        if delta_desigualdad == 'entre':  # Aplicar filtro "Entre"
            if LI_DELTA is not None and LS_DELTA is not None:
                filtered_df = filtered_df.query('DELTA.between(@LI_DELTA, @LS_DELTA)')

    if ARPU_igualdad is not None:
        if ARPU_desigualdad == 'igual':
            filtered_df = filtered_df[filtered_df['ARPU'] == ARPU_igualdad]
        elif ARPU_desigualdad == 'mayor':
            filtered_df = filtered_df[filtered_df['ARPU'] > ARPU_igualdad]
        elif ARPU_desigualdad == 'menor':
            filtered_df = filtered_df[filtered_df['ARPU'] < ARPU_igualdad]
        elif ARPU_desigualdad == 'mayor_igual':
            filtered_df = filtered_df[filtered_df['ARPU'] >= ARPU_igualdad]
        elif ARPU_desigualdad == 'menor_igual':
            filtered_df = filtered_df[filtered_df['ARPU'] <= ARPU_igualdad]
    else:
        if ARPU_desigualdad == 'entre':  # Aplicar filtro "Entre"
            if LI_ARPU is not None and LS_ARPU is not None:
                filtered_df = filtered_df.query('ARPU.between(@LI_ARPU, @LS_ARPU)')

    if pdv is not None:
        filtered_df = filtered_df[filtered_df['PDV'] == pdv]

    if clasificacion:
        filtered_df = filtered_df[filtered_df['CLASIFICACION'].isin(clasificacion)]

    conteo = len(filtered_df['CVE_UNICA_PDV'])
    etiqueta = f"Total de PDV: {conteo}"

    label_toggle = "Mostrar por origen de tienda" if facet_col is None else "Mostrar por total de tiendas"

    estado_cambio_campos = cambiar_campos % 2

    supervision = "NO" if estado_cambio_campos == 1 else None

    label_supervision = "Sin Costos de Supervisión" if supervision is None else "Con Costos de Supervisión"

    etiqueta = f"{etiqueta}" if supervision is None else f"{etiqueta} (Sin Costo Supervisión)"

    updated_fig = px.scatter(filtered_df, x="DELTA", y="Sueldos y comisiones (%)",
                             facet_col=facet_col,
                             color="CLUSTER",
                             color_discrete_map=map_colors,
                             size="Renta Promedio",
                             hover_name="PDV",
                             hover_data={
                                 "SC PROMEDIO": ':$,.0f',
                                 "INGRESOS PROMEDIO": ':$,.0f',
                                 "SyC Promedio": ':$,.0f',
                                 "REGION": True,
                                 "ORIGEN": True,
                                 "CLASIFICACION": True,
                                 "HC": ":,.0f",
                                 'ARPU': ':$.0f',
                                 "MAP": ":,.0f",
                                 "BREAK EVEN": ":,.0f",
                                 "Renta Promedio": ":$,.0f",
                                 "Sueldos y comisiones (%)": False
                             })

    return updated_fig, etiqueta, label_toggle, label_supervision


@app.callback(
    dash.dependencies.Output('filtro-region', 'value'),
    dash.dependencies.Output('toggle-facet-col', 'n_clicks'),
    dash.dependencies.Output('filtro-delta-igualdad', 'value'),
    dash.dependencies.Output('filtro-delta-desigualdad', 'value'),
    dash.dependencies.Output('filtro-HC-igualdad', 'value'),
    dash.dependencies.Output('filtro-HC-desigualdad', 'value', allow_duplicate=True),
    dash.dependencies.Output('filtro-ARPU-igualdad', 'value'),
    dash.dependencies.Output('filtro-ARPU-desigualdad', 'value', allow_duplicate=True),
    dash.dependencies.Output('filtro-pdv', 'value'),
    dash.dependencies.Output('filtro-clasificacion', 'value'),
    dash.dependencies.Output('borrar-filtros', 'n_clicks'),
    dash.dependencies.Output('cambiar-campos', 'n_clicks'),
    dash.dependencies.Output('filtro-HC-limite-inferior', 'value', allow_duplicate=True),
    # Nuevo input para límite inferior
    dash.dependencies.Output('filtro-HC-limite-superior', 'value', allow_duplicate=True),
    # Nuevo input para límite superior
    dash.dependencies.Output('filtro-delta-limite-inferior', 'value', allow_duplicate=True),
    # Nuevo input para límite inferior
    dash.dependencies.Output('filtro-delta-limite-superior', 'value', allow_duplicate=True),
    # Nuevo input para límite superior
    dash.dependencies.Output('filtro-ARPU-limite-inferior', 'value', allow_duplicate=True),
    # Nuevo input para límite inferior
    dash.dependencies.Output('filtro-ARPU-limite-superior', 'value', allow_duplicate=True),
    # Nuevo input para límite superior
    [dash.dependencies.Input('borrar-filtros', 'n_clicks')],
    prevent_initial_call=True
)
def borrar_filtros(n_clicks):
    return [], 0, None, 'mayor_igual', 0, 'mayor_igual', 0, 'mayor_igual', None, valores_clasificacion, n_clicks + 1, 0, None, None, None, None, None, None


@app_flask.route('/', methods=['GET', 'POST'])
def index():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('render_dashboard'))
            else:
                # Contraseña incorrecta, mostrar mensaje flash
                flash('Usuario o contraseña incorrecto')
        else:
            # Usuario no encontrado, mostrar mensaje flash
            flash('Usuario o contraseña incorrecto')
    return render_template('login_page.html', form=form)



@app_flask.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        # Verificar si el usuario ya existe en la base de datos
        existing_user = User.query.filter_by(username=form.username.data).first()

        if existing_user:
            flash('El usuario ingresado ya existe. Favor de intentar con uno diferente')
            return render_template('register.html', form=form)

        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('¡Registro exitoso! Ahora puedes iniciar sesión con tu nuevo usuario.', 'success')
        return redirect(url_for('index'))
        # return render_template('register.html', form=form)

    return render_template('register.html', form=form)


@app_flask.route('/pathname',methods=['GET','POST'])
@login_required
def render_dashboard():
    return flask.redirect('/dashboard/')

@app_flask.route('/logout', methods = ['GET','POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


for view_func in app_flask.view_functions:
    if view_func.startswith(app.config['url_base_pathname']):
        app_flask.view_functions[view_func] = login_required(app_flask.view_functions[view_func])

if __name__ == '__main__':
    app_flask.run(debug=False)