import pandas as pd
import streamlit as st

from askdb.pipeline import answer

st.set_page_config(page_title="AskDB", page_icon="🗄️")

st.title("AskDB")

with st.sidebar:
    use_retrieval = st.checkbox("Use schema retrieval", value=False)
    st.caption(
        "When enabled, only the top-6 most relevant tables are sent to the "
        "model instead of the full schema."
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.markdown(message["content"])
        else:
            sql, columns, rows, error, log = (
                message["sql"],
                message["columns"],
                message["rows"],
                message["error"],
                message["log"],
            )
            st.code(sql, language="sql")
            if error is None:
                if rows:
                    st.dataframe(pd.DataFrame(rows, columns=columns))
                else:
                    st.write("No rows returned")
            if error is not None:
                st.error(error)
            if len(log) > 1:
                with st.expander("Retry details"):
                    st.code(log[0]["sql"], language="sql")
                    st.text(log[0]["error"])

question = st.chat_input("Ask a question about the database")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    log = []
    sql, columns, rows, error = answer(question, use_retrieval=use_retrieval, log=log)

    with st.chat_message("assistant"):
        st.code(sql, language="sql")
        if error is None:
            if rows:
                st.dataframe(pd.DataFrame(rows, columns=columns))
            else:
                st.write("No rows returned")
        if error is not None:
            st.error(error)
        if len(log) > 1:
            with st.expander("Retry details"):
                st.code(log[0]["sql"], language="sql")
                st.text(log[0]["error"])

    st.session_state.messages.append(
        {
            "role": "assistant",
            "sql": sql,
            "columns": columns,
            "rows": rows,
            "error": error,
            "log": log,
        }
    )
