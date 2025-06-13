import streamlit as st

if 'logged_in' not in st.session_state or not st.session_state['logged_in']:
    st.write("Redirecionando para login...")
    st.experimental_set_query_params(page="login")
    st.experimental_rerun()
else:
    st.write("Redirecionando para home...")
    st.experimental_set_query_params(page="home")
    st.experimental_rerun()