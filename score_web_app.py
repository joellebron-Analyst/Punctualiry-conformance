import pandas as pd
import streamlit as st
import math

@st.cache_data(ttl=86400)
def cargar_datos():
    return pd.read_csv('https://docs.google.com/spreadsheets/d/e/2PACX-1vSKlLRDJWe6p_AKZAVsUfGuEVANt9Dvn-1-vY1XnmzFox1MNOxxYZyg1c657bw6OFt7CV5xMKQhP0x8/pub?gid=1596580014&single=true&output=csv')


st.set_page_config(
    page_title="Scoring",
    layout="wide",
    initial_sidebar_state="expanded")


st.markdown('# ⌚📊 Platform under modifications')
st.markdown('## Thanks for being patient')


st.markdown('### Conformance - Punctuality Page')
data = cargar_datos()
data['datestamp'] = pd.to_datetime(data['datestamp'])

# Normalizar los estados (mayúsculas, espacios y errores de escritura del sheet)
data['Status'] = (data['Status'].fillna('').str.strip().str.lower()
                  .replace({
                      'late in': 'late',
                      'ealy out': 'early out',
                      'medical appoitment': 'medical appointment',
                      'maternity/paternity license': 'maternity/paternity leave',
                      'grief': 'duelo',
                  }))

# Horas vacías cuentan como 0
for columna in ['Total work time', 'Lunch', 'away']:
    data[columna] = pd.to_timedelta(data[columna], errors='coerce').fillna(pd.Timedelta(0))


# Reglas vigentes desde septiembre 2026
Base_data = data.loc[data['datestamp'] >= '2026-09-01'].drop_duplicates(['Full Name', 'datestamp'])


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
    '1001': {'lob': ['INBOUND & CHAT'],                 'lider': 'ELIMARDY NATHALY DIPRE DOMINGUEZ'},
    '1002': {'lob': ['RELATIONSHIP MANAGEMENT'],         'lider': 'JOHNANGEL RAMIREZ GUTIERREZ'},
    '1003': {'lob': ['SALES'],                           'lider': 'JUAN MIGUEL MENDEZ'},
    '1004': {'lob': ['ONBOARDING'],                      'lider': 'ELAINI ENCARNACION MAYNERD'},
    '1005': {'lob': ['PROCESS'],                         'lider': 'ABEL GOMEZ ORTIZ'},
    '1006': {'lob': ['MULTIFUNCTIONS'],                  'lider': 'YAEL JOHANNY CARO MARTINEZ'},
    '1007': {'lob': ['FRAUD/AML'],                       'lider': 'JHOAN ANDRES GOMEZ RODRIGUEZ'},
    '1008': {'lob': ['SUBMISSION AND OPERATIONS'],       'lider': 'MAYLIN TERESA SURIEL HERNANDEZ'},
    '1009': {'lob': ['QA'],                              'lider': 'ASHLIE GABRIELA VASQUEZ SANTIAGO'},
    '1010': {'lob': ['ANALYTICS', 'DATA SCIENCE'],     'lider': 'MARIO ALBERTO DE LA CRUZ FERRERAS'},
    '1011': {'lob': ['ACCOUNT MANAGEMENT'],                      'lider': 'ADRIAN PEÑA PAULINO'},
    '1012': {'lob': ['RISK & COMPLIANCE'],               'lider': 'JHOSWAL RAMIREZ SUAREZ'},
    '1013': {'lob': ['GO TO MARKET', 'CUSTOMER SATISFACTION'], 'lider': 'CINTHYA ROSSELYN BAEZ PAULINO'},
    '1014': {'lob': ['PORTFOLIO PERFORMANCE & RISK'],    'lider': 'ARGELIA NUÑEZ FERREIRA'},
    '1015': {'lob': ['HUMAN RESOURCES (HR)'],             'lider': 'DIANA COLLADO'},
    '1016': {'lob': ['OFAC'],                            'lider': 'DELYS DIPRE DOMINGUEZ'},
    '1017': {'lob': ['FINANCE'],                         'lider': 'YERITSA VICTORIA LANTIGUA VIZCAINO'},
    '1018': {'lob': ['INFORMATION TECHNOLOGY (IT)'],     'lider': 'THIARA SANCHEZ POLANCO'},
    '1019': {'lob': ['OPERATIONS'],                      'lider': 'LUIS MIGUEL POU RAMIREZ'},
    '1020': {'lob': ['REVENUE OPERATIONS'],              'lider': 'NYLEEN DASHILL PERDOMO MELO'},
    '9999': {'lob': ['ADMIN'],                           'lider': 'ADMINISTRADOR'},
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

# ── REGLAS DE NEGOCIO ──────────────────────

# Días que no cuentan (la persona no estaba trabajando)
AUSENCIAS = ['vacation', 'maternity/paternity leave', 'medical license', 'sick leave', 'de viaje',
             'holiday at home', 'leave of absence', 'duelo', 'medical appointment']

# Estados que cuentan como falta de puntualidad ('late in' ya se normalizó a 'late')
TARDANZAS = ['late', 'called out', 'no show']

HORAS_DIA     = pd.Timedelta(hours=8)
HORAS_SABADO  = pd.Timedelta(hours=4)
LUNCH_DIA     = pd.Timedelta(hours=1)      # Los sábados no hay lunch
AWAY_DIA      = pd.Timedelta(minutes=15)   # Aplica también los sábados


def escala(ratio, menos_es_mejor=False):
    """Convierte realizado / esperado a la escala de 1 a 5."""
    if menos_es_mejor:   # Lunch y away: hasta lo esperado = 5, cada exceso resta proporcionalmente
        score = 5 if ratio <= 1 else 5 - (ratio - 1) * 5
    else:                # Horas: sin bono por horas extra
        score = min(ratio, 1) * 5
    return round(max(score, 1), 2)


es_sabado = working_data['datestamp'].dt.dayofweek == 5


# Dataset for conformance calculation (horas)
conformance_data = working_data.loc[~working_data['Status'].isin(AUSENCIAS)].copy()
conformance_data['horas_esperadas'] = es_sabado[conformance_data.index].map({True: HORAS_SABADO, False: HORAS_DIA})

# Dataset for away calculation (No Show no vino, no tiene away)
away_base_data = conformance_data.loc[conformance_data['Status'] != 'no show']

# Dataset for lunch calculation (igual que away, sin sábados)
Lunch_Data = away_base_data.loc[~es_sabado[away_base_data.index]]


# Funcion para calculo de puntualidad

def punctuality(name):
    punct_data = working_data.loc[
        (working_data['Full Name'] == name)
        &
        (~working_data['Status'].isin(AUSENCIAS))
    ]

    total_records = len(punct_data)
    if total_records == 0:
        return None

    not_allowed = punct_data['Status'].isin(TARDANZAS).sum()
    return escala(1 - not_allowed / total_records)


# Funciones para el calculo del conformance

def score_horas(name):
    d = conformance_data.loc[conformance_data['Full Name'] == name]
    if d.empty:
        return None
    return escala(d['Total work time'].sum() / d['horas_esperadas'].sum())


def score_lunch(name):
    d = Lunch_Data.loc[Lunch_Data['Full Name'] == name]
    if d.empty:
        return None
    return escala(d['Lunch'].sum() / (len(d) * LUNCH_DIA), menos_es_mejor=True)


def score_away(name):
    d = away_base_data.loc[away_base_data['Full Name'] == name]
    if d.empty:
        return None
    return escala(d['away'].sum() / (len(d) * AWAY_DIA), menos_es_mejor=True)


def conformance(row):
    scores = [s for s in (row['Horas_score'], row['Lunch_score'], row['Away_score']) if pd.notna(s)]
    return round(sum(scores) / len(scores), 2) if scores else None



#Grouping the data for calculation
grouped_data = pd.DataFrame({'Full Name': sorted(working_data['Full Name'].dropna().unique())})

#Adding columns using functions
grouped_data['Punctuality_score'] = grouped_data['Full Name'].apply(punctuality)
grouped_data['Horas_score']       = grouped_data['Full Name'].apply(score_horas)
grouped_data['Lunch_score']       = grouped_data['Full Name'].apply(score_lunch)
grouped_data['Away_score']        = grouped_data['Full Name'].apply(score_away)
grouped_data['Conformance']       = grouped_data.apply(conformance, axis=1)

grouped_data = grouped_data[['Full Name', 'Punctuality_score', 'Conformance']]
grouped_data = grouped_data.sort_values(by='Punctuality_score', ascending=False)


st.dataframe(grouped_data, hide_index=True)
