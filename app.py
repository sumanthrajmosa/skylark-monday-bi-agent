import os
from dotenv import load_dotenv
load_dotenv()
import streamlit as st
from monday.client import MondayClient
from agent.agent import BIAGent

st.set_page_config(page_title='Skylark BI Agent', page_icon='📊', layout='wide')
st.title('📊 Skylark Drones — Monday.com BI Agent')
st.caption('Read-only business intelligence over Work Orders and Deals')

if not all(os.getenv(k) for k in ['MONDAY_API_TOKEN','MONDAY_WORK_ORDERS_BOARD_ID','MONDAY_DEALS_BOARD_ID']):
    st.warning('Configure MONDAY_API_TOKEN, MONDAY_WORK_ORDERS_BOARD_ID and MONDAY_DEALS_BOARD_ID in your environment. GEMINI_API_KEY is required for natural-language answers.')
    st.stop()

@st.cache_resource
def get_agent(): return BIAGent(MondayClient())
agent=get_agent()

examples=['How is our pipeline looking for the Energy sector this quarter?','What is our total open pipeline and weighted pipeline?','Which projects are operationally at risk?','Give me a leadership update for the business.','Which customers have both open deals and active work orders?']
with st.sidebar:
    st.header('Try a question')
    for q in examples:
        if st.button(q, use_container_width=True): st.session_state['q']=q

q=st.chat_input('Ask a founder-level business question...') or st.session_state.get('q')
if q:
    with st.chat_message('user'): st.write(q)
    with st.chat_message('assistant'):
        try:
            st.write(get_agent().answer(q))
        except Exception as e:
            error_text = str(e)

            if '503' in error_text or 'UNAVAILABLE' in error_text:
                st.error('Gemini is temporarily unavailable. Your Monday.com data was retrieved successfully. Please try again in a moment.')
            elif '429' in error_text:
                st.error('Gemini rate limit reached. Please wait a moment and try again.')
            elif '401' in error_text or '403' in error_text:
                st.error('Gemini authentication/permission error. Check your GEMINI_API_KEY.')
            else:
                st.error('The agent encountered an error while processing the request.')

            st.caption(f'Diagnostic: {e}')
