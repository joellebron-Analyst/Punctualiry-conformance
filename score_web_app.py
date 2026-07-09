import pandas as pd
import streamlit as st
import math

@st.cache_data
def cargar_datos():
    return pd.read_csv('https://docs.google.com/spreadsheets/d/e/2PACX-1vSL8e5uoUExt5a-LDPCw0rEcFTm0SqAhLz8sYT8sbkYtse1pvMHY9Qij547diNhlP__DYxtuT8XojRO/pub?gid=1596580014&single=true&output=csv')


st.set_page_config(
    page_title="Scoring",
    layout="wide",
    initial_sidebar_state="expanded")


st.markdown('# ⌚📊 Conformance & Punctuality Score')
st.markdown('## General View')

data = cargar_datos()
data['datestamp'] = pd.to_datetime(data['datestamp'])



Base_data = data.loc[

(data['datestamp'].dt.year >= 2026)
&
(data['datestamp'].dt.month >= 6)
]


nombre_meses = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
    5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}



st.sidebar.title('FILTROS')

año_seleccionado = st.sidebar.selectbox(

                'Año:', sorted(Base_data['datestamp'].dt.year.unique())
)

meses_disponibles = sorted(Base_data[
    Base_data['datestamp'].dt.year == año_seleccionado
]['datestamp'].dt.month.unique())

mes_seleccionado = st.sidebar.selectbox(
    'Mes:', meses_disponibles,
    format_func=lambda x: nombre_meses[x])

#

codigos = {
    '1001': {'lob': 'INBOUND & CHAT',                 'lider': 'ELIMARDY NATHALY DIPRE DOMINGUEZ'},
    '1002': {'lob': 'RELATIONSHIP MANAGEMENT',         'lider': 'JOHNANGEL RAMIREZ GUTIERREZ'},
    '1003': {'lob': 'SALES',                           'lider': 'JUAN MIGUEL MENDEZ'},
    '1004': {'lob': 'ONBOARDING',                      'lider': 'ELAINI ENCARNACION MAYNERD'},
    '1005': {'lob': 'PROCESS',                         'lider': 'ABEL GOMEZ ORTIZ'},
    '1006': {'lob': 'MULTIFUNCTIONS',                  'lider': 'YAEL JOHANNY CARO MARTINEZ'},
    '1007': {'lob': 'FRAUD/AML',                       'lider': 'JHOAN ANDRES GOMEZ RODRIGUEZ'},
    '1008': {'lob': 'UNDERWRITING',                    'lider': 'MAYLIN TERESA SURIEL HERNANDEZ'},
    '1009': {'lob': 'QA',                              'lider': 'ASHLIE GABRIELA VASQUEZ SANTIAGO'},
    '1010': {'lob': ['ANALYTICS', 'DATA SCIENCE'],     'lider': 'MARIO ALBERTO DE LA CRUZ FERRERAS'},
    '1011': {'lob': 'SERVICINGS',                      'lider': 'ADRIAN PEÑA PAULINO'},
    '1012': {'lob': 'RISK & COMPLIANCE',               'lider': 'JHOSWAL RAMIREZ SUAREZ'},
    '1013': {'lob': 'GO TO MARKET',                    'lider': 'CINTHYA ROSSELYN BAEZ PAULINO'},
    '1014': {'lob': 'PORTFOLIO PERFORMANCE & RISK',    'lider': 'ARGELIA NUÑEZ FERREIRA'},
    '1015': {'lob': 'HUMAN RESOURCES (HR)',             'lider': 'ENMANUEL ANTONIO SANCHEZ DISLA'},
    '1016': {'lob': 'OFAC',                            'lider': 'DELYS DIPRE DOMINGUEZ'},
    '1017': {'lob': 'FINANCE',                         'lider': 'YERITSA VICTORIA LANTIGUA VIZCAINO'},
    '1018': {'lob': 'INFORMATION TECHNOLOGY (IT)',     'lider': 'THIARA SANCHEZ POLANCO'},
    '1019': {'lob': 'OPERATIONS',                      'lider': 'LUIS MIGUEL POU RAMIREZ'},
    '1020': {'lob': 'REVENUE OPERATIONS',              'lider': 'NYLEEN DASHILL PERDOMO MELO'},
    '9999': {'lob': 'ADMIN',                           'lider': 'ADMINISTRADOR'},
}





# ── INPUT DEL CÓDIGO ──────────────────────
codigo = st.sidebar.text_input('Introduce tu código:', type='password')

if codigo == '':
    st.warning('Por favor introduce tu código para acceder.')
    st.stop()  # detiene la ejecución hasta que se ingrese un código

elif codigo not in codigos:
    st.error('Código incorrecto. Acceso denegado.')
    st.stop()

else:
    lob_permitido = codigos[codigo]['lob']
    lider         = codigos[codigo]['lider']
    st.success(f'HOLA!, {lider}')


working_data = Base_data.loc[
    
    (Base_data['datestamp'].dt.year == año_seleccionado) # La fecha de inicio
    &
    (Base_data['datestamp'].dt.month == mes_seleccionado) # Fecha final
    &
    (Base_data['LOB'].isin( lob_permitido))     # Aqui está el Departamento          
         
         ]


fechas_excluir = pd.to_datetime([
    '2026-06-06', 
    '2026-06-13', 
    '2026-06-20', 
    '2026-06-27'
]).date


# Database for lunch calculation

Lunch_Data = working_data.loc[
    
    (~working_data['Status'].isin(['Vacation','Maternity/Paternity Leave', 'No Show', 'Medical License', 'Sick Leave']))
    &
    (~working_data['datestamp'].dt.date.isin(fechas_excluir))
                 
                 ]


Lunch_Data['Lunch'] = pd.to_timedelta(Lunch_Data['Lunch'])




# Dataset for away calculation

away_base_data = working_data.loc[
    
    (~working_data['Status'].isin(['Vacation','Maternity/Paternity Leave', 'Medical License', 'No Show', 'Sick Leave']))
   
   ]

away_base_data['away'] = pd.to_timedelta(away_base_data['away'])

#Dataset for conformance calculation

conformance_data = working_data.loc[
    
    (~working_data['Status'].isin(['Maternity/Paternity Leave','Maternity/Paternity Leave', 'Medical License', 'Sick Leave']))
                 ]

conformance_data['Total work time'] = pd.to_timedelta(conformance_data['Total work time'])


# Funcion para calculo de puntualidad

def punctuality(name):

    ##### Lateness Score #####
    punct_data = working_data.loc[
        (working_data['Full Name'] == name)
        &
        (~working_data['Status'].isin(['Vacation', 'Maternity/Paternity Leave', 'Medical License', 'Sick Leave']))
    
    ]
    
    total_records = punct_data['Clock in time'].size

    if total_records == 0:
        return 0

    not_allowed = punct_data.loc[punct_data['Status'].isin(['Late', 'Called Out', 'No Show']), 'Status'].size
    results = round((not_allowed / total_records) * 100)
    new_result = 100 - results
    return math.floor((new_result / 100) * 5 + 0.5)


# Funcion para el calculo del conformance

def conformance(name):
    conf_data = conformance_data.loc[conformance_data['Full Name'] == name                         
                            
                            ]
    conformance_dias_laborados = conf_data['Full Name'].size
    if conformance_dias_laborados ==0:
        return 0
    horas_esperadas = conformance_dias_laborados * pd.Timedelta(hours=8)
    actual_horas_trabajadas = conf_data['Total work time'].sum()
    score_horas_trabajadas = round(((actual_horas_trabajadas/horas_esperadas)/1)*5, 2)


##### Lunch Score #####
    Lunch_Data_ = Lunch_Data.loc[Lunch_Data['Full Name'] == name]
   
    dias_laborados = Lunch_Data_['Lunch'].size
    if dias_laborados == 0:
        return 0
    lunch_esperado = dias_laborados * pd.Timedelta(hours=1)
    lunch_tomado = Lunch_Data_['Lunch'].sum()
    Resultado = lunch_esperado / lunch_tomado
    resultado_lunch = (Resultado / 1) * 5

    ##### Away Score #####
    away_data = away_base_data.loc[away_base_data['Full Name'] == name]
    dias_ = away_data['Full Name'].size
    away_esperado = dias_ * pd.Timedelta(minutes=15)
    actual_away = away_data['away'].sum()
    resultado_away = ((actual_away / away_esperado) / 1) * 5

    if resultado_away <= 5:
        score_away = 5
    else:
        resultado_away_final = resultado_away - 5
        score_away = 5 - resultado_away_final

    grouped_score = score_horas_trabajadas + resultado_lunch + score_away

    return math.floor(grouped_score / 3 + 0.5)



#Grouping the data for calculation
grouped_data = working_data.groupby(['Full Name']).agg(grouped = ('Full Name', 'first'))

#Adding columns using functions
grouped_data['Punctuality_score'] = grouped_data['grouped'].apply(punctuality)
grouped_data['Conformance'] = grouped_data['grouped'].apply(conformance)



grouped_data = grouped_data.reset_index()
grouped_data = grouped_data[['Full Name', 'Punctuality_score', 'Conformance']]
grouped_data = grouped_data.reset_index(drop=True)  # ← agrega esto al final
grouped_data = grouped_data.sort_values(by='Punctuality_score', ascending=False)


st.dataframe(grouped_data, hide_index=True)
