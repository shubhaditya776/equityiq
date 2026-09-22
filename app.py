import os, sqlite3
from io import BytesIO
import pandas as pd
import requests
import streamlit as st
import plotly.express as px
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None
from analysis_engine import rule_based_insights

st.set_page_config(page_title='EquityIQ', page_icon='📈', layout='wide')
DB='equityiq.db'; KEY=os.getenv('ALPHAVANTAGE_API_KEY','').strip()

def db():
    c=sqlite3.connect(DB); c.execute('CREATE TABLE IF NOT EXISTS holdings(ticker TEXT PRIMARY KEY, shares REAL, avg_price REAL)'); c.commit(); return c

def get_holdings():
    c=db(); x=pd.read_sql_query('SELECT * FROM holdings ORDER BY ticker',c); c.close(); return x

def save(t,s,p):
    c=db(); c.execute('INSERT INTO holdings VALUES(?,?,?) ON CONFLICT(ticker) DO UPDATE SET shares=excluded.shares, avg_price=excluded.avg_price',(t.upper(),s,p)); c.commit(); c.close()

def remove(t):
    c=db(); c.execute('DELETE FROM holdings WHERE ticker=?',(t,)); c.commit(); c.close()

@st.cache_data(ttl=900)
def av(fn,symbol):
    if not KEY:return {}
    try:return requests.get('https://www.alphavantage.co/query',params={'function':fn,'symbol':symbol,'apikey':KEY},timeout=20).json()
    except:return {}

def pct(x):
    try:return f'{float(x)*100:.1f}%'
    except:return '—'

def money(x):
    try:
        v=float(x); a=abs(v)
        if a>=1e12:return f'{v/1e12:.2f}T'
        if a>=1e9:return f'{v/1e9:.2f}B'
        if a>=1e7:return f'{v/1e7:.2f}Cr'
        return f'{v:,.0f}'
    except:return '—'

def research_prompt(o):
    fields=['Name','Sector','Industry','MarketCapitalization','PERatio','PriceToBookRatio','EVToEBITDA','ReturnOnEquityTTM','ProfitMargin','OperatingMarginTTM','RevenueTTM','EBITDA','EPS','QuarterlyRevenueGrowthYOY','QuarterlyEarningsGrowthYOY','DebtToEquity']
    data='\n'.join(f'{k}: {o.get(k)}' for k in fields)
    return f'Analyse {o.get("Name","the company")} using ONLY the supplied data. Produce business snapshot, financial performance, profitability/balance-sheet observations, valuation observations, growth drivers, risks and questions for further research. Separate facts from interpretation. Do not invent missing data.\n\n{data}'

st.sidebar.title('📈 EquityIQ'); page=st.sidebar.radio('Navigate',['Dashboard','Company Research','Portfolio','Valuation','Report Lab'])
if not KEY: st.sidebar.warning('Set ALPHAVANTAGE_API_KEY for live data.')

if page=='Dashboard':
    st.title('EquityIQ'); st.caption('AI-assisted equity research & portfolio intelligence')
    h=get_holdings(); invested=(h.shares*h.avg_price).sum() if not h.empty else 0
    a,b,c,d=st.columns(4); a.metric('Invested Capital',f'₹{invested:,.0f}'); b.metric('Holdings',len(h)); c.metric('Research Engine','Ready'); d.metric('Data','Alpha Vantage')
    if h.empty: st.info('Add holdings in Portfolio.')
    else: st.dataframe(h,hide_index=True,use_container_width=True)

elif page=='Company Research':
    st.title('🔎 Company Research'); symbol=st.text_input('Ticker / Alpha Vantage symbol','RELIANCE.BSE').strip().upper()
    if st.button('Load Company',type='primary'):
        o=av('OVERVIEW',symbol)
        if 'Symbol' not in o: st.error('No company data returned. Check symbol or API quota.')
        else: st.session_state.o=o
    if 'o' in st.session_state:
        o=st.session_state.o; st.header(o.get('Name',symbol)); st.caption(f'{o.get("Sector","—")} • {o.get("Industry","—")}')
        cols=st.columns(6); vals=[('Market Cap',money(o.get('MarketCapitalization'))),('P/E',o.get('PERatio','—')),('P/B',o.get('PriceToBookRatio','—')),('EV/EBITDA',o.get('EVToEBITDA','—')),('ROE',pct(o.get('ReturnOnEquityTTM'))),('Margin',pct(o.get('ProfitMargin')))]
        for col,(lab,val) in zip(cols,vals): col.metric(lab,val)
        rows=[('Revenue TTM',money(o.get('RevenueTTM'))),('EBITDA',money(o.get('EBITDA'))),('EPS',o.get('EPS','—')),('Revenue Growth',pct(o.get('QuarterlyRevenueGrowthYOY'))),('Earnings Growth',pct(o.get('QuarterlyEarningsGrowthYOY'))),('Operating Margin',pct(o.get('OperatingMarginTTM'))),('Debt/Equity',o.get('DebtToEquity','—')),('Dividend Yield',pct(o.get('DividendYield')))]
        st.subheader('Financial snapshot'); st.dataframe(pd.DataFrame(rows,columns=['Metric','Value']),hide_index=True,use_container_width=True)
        st.subheader('Business description'); st.write(o.get('Description','No description returned.'))
        st.subheader('Rule-based research insights')
        insights,flags=rule_based_insights(o)
        for x in insights: st.write('• '+x)
        if flags:
            st.subheader('Items to investigate');
            for x in flags: st.warning(x)
        st.subheader('AI Research Brief'); st.code(research_prompt(o),language='text')

elif page=='Portfolio':
    st.title('💼 Portfolio Tracker')
    with st.form('holding'):
        a,b,c=st.columns(3); t=a.text_input('Ticker','RELIANCE.BSE'); s=b.number_input('Shares',0.0,1000000.0,10.0); p=c.number_input('Average price (₹)',0.0,10000000.0,1000.0)
        if st.form_submit_button('Save Holding',type='primary'): save(t,s,p); st.success('Saved'); st.rerun()
    h=get_holdings()
    if not h.empty:
        st.dataframe(h,hide_index=True,use_container_width=True); x=st.selectbox('Remove',['']+h.ticker.tolist())
        if st.button('Remove') and x: remove(x); st.rerun()

elif page=='Valuation':
    st.title('🧮 Relative Valuation'); st.caption('Peer-multiple framework for research.')
    n=st.number_input('Companies',2,10,5); rows=[]
    for i in range(int(n)):
        a,b,c,d=st.columns(4); name=a.text_input(f'Company {i+1}',f'Company {i+1}',key=f'n{i}'); pe=b.number_input('P/E',0.0,1000.0,20.0,key=f'p{i}'); ev=c.number_input('EV/EBITDA',0.0,1000.0,15.0,key=f'e{i}'); gr=d.number_input('Growth %',-100.0,500.0,10.0,key=f'g{i}'); rows.append([name,pe,ev,gr])
    df=pd.DataFrame(rows,columns=['Company','P/E','EV/EBITDA','Growth %']); st.dataframe(df,hide_index=True,use_container_width=True)
    a,b,c=st.columns(3); a.metric('Median P/E',f'{df["P/E"].median():.2f}x'); b.metric('Median EV/EBITDA',f'{df["EV/EBITDA"].median():.2f}x'); c.metric('Median Growth',f'{df["Growth %"].median():.1f}%')
    st.plotly_chart(px.scatter(df,x='Growth %',y='P/E',text='Company',title='Growth vs P/E'),use_container_width=True)

else:
    st.title('📄 Report Lab'); st.caption('Upload an annual report PDF and extract text locally for AI-assisted research.')
    f=st.file_uploader('Upload PDF',type=['pdf'])
    if f:
        if PdfReader is None: st.error('Install pypdf.')
        else:
            text='\n'.join((p.extract_text() or '') for p in PdfReader(BytesIO(f.getvalue())).pages)
            st.success(f'Extracted {len(text):,} characters.'); st.text_area('Preview',text[:12000],height=350)
            st.download_button('Download text',text,file_name=f'{f.name}.txt')
            st.subheader('AI research prompt'); st.code('Analyse the supplied annual report. Extract only supported facts. Produce business model, segment performance, revenue/profitability trends, cash flow/capital allocation, debt/liquidity, management priorities, risks, accounting/governance items and five analyst questions. Do not invent data.\n\nREPORT TEXT:\n'+text[:30000],language='text')
