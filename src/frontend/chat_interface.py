import streamlit as st
from api_utils import get_api_response



import json


def render_summary_card(file_id, summary_text_or_json):
    with st.container(border=True):
        st.markdown(f"### 📄 Document ID: `{file_id}`")

        parsed = None
        if isinstance(summary_text_or_json, str):
            try:
                parsed = json.loads(summary_text_or_json)
            except:
                parsed = None
        elif isinstance(summary_text_or_json, dict):
            parsed = summary_text_or_json

        if parsed:
            st.markdown(f"**Type:** `{parsed.get('document_type', 'Not Found')}`")
            st.markdown(f"**One-line:** {parsed.get('one_line_summary', '')}")

            st.markdown("**Short Summary:**")
            st.write(parsed.get("short_summary", ""))

            key_fields = parsed.get("key_fields", [])
            if key_fields:
                st.markdown("**Key Fields**")
                st.dataframe(key_fields, use_container_width=True)

            entities = parsed.get("important_entities", {})
            if entities:
                with st.expander("Entities"):
                    st.json(entities)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Missing / Unclear**")
                st.write(parsed.get("missing_or_unclear_fields", []))
            with col2:
                st.markdown("**Red Flags**")
                st.write(parsed.get("red_flags", []))

            with st.expander("Raw Summary JSON"):
                st.json(parsed)

        else:
            st.write(summary_text_or_json)
import json
import streamlit as st

def render_insights_card(insights_text_or_json):
    with st.container(border=True):
        st.markdown("## 📊 Holistic Insights")

        parsed = None
        if isinstance(insights_text_or_json, str):
            try:
                parsed = json.loads(insights_text_or_json)
            except:
                parsed = None
        elif isinstance(insights_text_or_json, dict):
            parsed = insights_text_or_json

        if parsed:
            st.markdown("### ✅ Answer")
            st.write(parsed.get("answer", "Not Found"))

            per_doc = parsed.get("per_document", [])
            if per_doc:
                st.markdown("### 📄 Per Document Findings")
                st.dataframe(per_doc, use_container_width=True)

            stats = parsed.get("stats", {})
            if stats:
                st.markdown("### 📈 Stats")
                st.json(stats)

            recs = parsed.get("recommendations", [])
            if recs:
                st.markdown("### 💡 Recommendations")
                for r in recs:
                    st.write(f"- {r}")

            with st.expander("Raw Insights JSON"):
                st.json(parsed)
        else:
            st.write(insights_text_or_json)

def display_chat_interface():
    # Chat interface
    summary_data = st.session_state.get("summary_results")
    if summary_data and "summaries" in summary_data:
        with st.chat_message("assistant"):
            st.markdown("## 📌 Document Summaries")
            for item in summary_data["summaries"]:
                render_summary_card(item["file_id"], item["summary"])
                st.divider()
                
    insights_data = st.session_state.get("insights_result")
    if insights_data and "result" in insights_data:
        with st.chat_message("assistant"):
            render_insights_card(insights_data["result"])
            st.divider()


    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Ask anything related to Form:"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.spinner("Generating response..."):
            response = get_api_response(prompt, st.session_state.session_id, model='gpt-4o-mini')
            
            
            if response:
                st.session_state.session_id = response.get('session_id')
                st.session_state.messages.append({"role": "assistant", "content": response['answer']})
                
                with st.chat_message("assistant"):
                    st.markdown(response['answer'])
                    
                    with st.expander("Details"):
                        st.subheader("Sources Used")
                        st.code(response['sources'])
                        st.subheader("Model Used")
                        st.code(response['model'])
                        st.subheader("Session ID")
                        st.code(response['session_id'])
            else:
                st.error("Failed to get a response from the API. Please try again.")