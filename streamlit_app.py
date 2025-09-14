import streamlit as st
import requests

st.title("🧠 GenAI Markdown Viewer")

prompt = st.text_area("Enter your prompt")

if st.button("Generate"):
    with st.spinner("Calling FastAPI..."):
        response = requests.post(
            "http://localhost:8000/generate-vlog",
            params={"llm_message": prompt}
        )
        print(response)
        if response.status_code == 200:
            #markdown = response.json()["content"]
            #st.markdown(markdown, unsafe_allow_html=True)
            data = response.json()
            st.subheader("message:")
            st.write(data.get("message"))
        else:
            st.error(f"Error: {response.status_code}")

elif st.button("Initialize LLM GROQ AI"):
    with st.spinner("Initializing LLM..."):
        response = requests.post(
            "http://localhost:8000/init-llm",
            params={"llm_name": "groq"}
        )
        #print(response.json())
        if response.json()["message"] == "LLM initialized":
            st.success("LLM Initialized")
        else:
            st.error(f"Error: {response}")