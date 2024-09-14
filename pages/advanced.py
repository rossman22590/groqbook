import streamlit as st
from groq import Groq
import json
from infinite_bookshelf.agents import (
    generate_section,
    generate_book_structure,
    generate_book_title,
)
from infinite_bookshelf.inference import GenerationStatistics
from infinite_bookshelf.tools import create_markdown_file, create_pdf_file
from infinite_bookshelf.ui.components import (
    render_groq_form,
    render_advanced_groq_form,
    display_statistics,
    render_download_buttons,
)
from infinite_bookshelf.ui import Book, load_return_env, ensure_states

# Include custom CSS
st.markdown("""
    <style>
        body {
            font-family: 'Arial', sans-serif;
            background-color: #f5f5f5;
            color: #333;
        }
        .main {
            max-width: 800px;
            margin: auto;
            padding: 2rem;
            background-color: #fff;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .btn-primary {
            background-color: #007bff;
            color: #fff;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }
        .btn-primary:hover {
            background-color: #0056b3;
        }
        .btn-secondary {
            background-color: #6c757d;
            color: #fff;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }
        .btn-secondary:hover {
            background-color: #5a6268;
        }
        .card {
            background-color: #fff;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
        }
        .header {
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 20px;
        }
        .subheader {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 10px;
        }
        .input, .textarea, .select, .file-upload {
            width: 100%;
            padding: 10px;
            margin-bottom: 20px;
            border: 1px solid #ccc;
            border-radius: 4px;
        }
    </style>
""", unsafe_allow_html=True)

# Initialize env variables and session states
GROQ_API_KEY = load_return_env(["GROQ_API_KEY"])["GROQ_API_KEY"]

states = {
    "api_key": GROQ_API_KEY,
    "button_disabled": False,
    "button_text": "Generate",
    "statistics_text": "",
    "book_title": "",
}

if GROQ_API_KEY:
    states["groq"] = Groq()  # Define Groq provider if API key provided. Otherwise defined later after API key is provided.

ensure_states(states)

# Define Streamlit page structure and functionality
st.markdown("""
    <div class="main">
        <h1 class="header">Bookify Advanced: Write full books using the power of AI Tutor - in advanced mode</h1>
""", unsafe_allow_html=True)

def disable():
    st.session_state.button_disabled = True

def enable():
    st.session_state.button_disabled = False

def empty_st():
    st.empty()

try:
    if st.button("End Generation and Download Book", key="end_download", disabled=st.session_state.button_disabled, on_click=enable):
        if "book" in st.session_state:
            render_download_buttons(st.session_state.get("book"))

    (
        submitted,
        groq_input_key,
        topic_text,
        additional_instructions,
        writing_style,
        complexity_level,
        seed_content,
        uploaded_file,
        title_agent_model,
        structure_agent_model,
        section_agent_model,
    ) = render_advanced_groq_form(
        on_submit=disable,
        button_disabled=st.session_state.button_disabled,
        button_text=st.session_state.button_text,
    )

    # New content for advanced mode
    additional_section_writer_prompt = "The book chapters should be comprehensive. The writing should be: \nEngaging and tailored to the specified writing style, tone, and complexity level. \nWell-structured with clear subheadings, paragraphs, and transitions. \nRich in relevant examples, analogies, and explanations. \nConsistent with provided seed content and additional instructions. \nFocused on delivering value through insightful analysis and information. \nFactually accurate based on the latest available information. \nCreative, offering unique perspectives or thought-provoking ideas. \nEnsure each section flows logically, maintaining coherence throughout the chapter."
    advanced_settings_prompt = f"Use the following parameters:\nWriting Style: {writing_style}\nComplexity Level: {complexity_level}"
    total_seed_content = ""

    # Fill total_seed_content
    if seed_content:
        total_seed_content += seed_content
    if uploaded_file:
        total_seed_content += uploaded_file.read().decode("utf-8")
    if total_seed_content != "":
        total_seed_content = f"The user has provided seed content for context. Develop the structure and content around the provided seed: <seed>{total_seed_content}</seed>"

    if submitted:
        if len(topic_text) < 10:
            raise ValueError("Book topic must be at least 10 characters long")

        st.session_state.button_disabled = True
        st.session_state.statistics_text = (
            "Generating book title and structure in background...."
        )

        placeholder = st.empty()
        display_statistics(
            placeholder=placeholder, statistics_text=st.session_state.statistics_text
        )

        if not GROQ_API_KEY:
            st.session_state.groq = Groq(api_key=groq_input_key)

        # Step 1: Generate book structure using structure_writer agent
        additional_instructions_prompt = (
            additional_instructions + advanced_settings_prompt
        )
        if total_seed_content != "":
            additional_instructions_prompt += "\n" + total_seed_content

        large_model_generation_statistics, book_structure = generate_book_structure(
            prompt=topic_text,
            additional_instructions=additional_instructions_prompt,
            model=structure_agent_model,
            groq_provider=st.session_state.groq,
            long=True # Use longer version in advanced
        )

        # Step 2: Generate book title using title_writer agent
        st.session_state.book_title = generate_book_title(
            prompt=topic_text,
            model=title_agent_model,
            groq_provider=st.session_state.groq,
        )

        st.markdown(f"<h2 class='subheader'>{st.session_state.book_title}</h2>", unsafe_allow_html=True)

        total_generation_statistics = GenerationStatistics(
            model_name=section_agent_model
        )

        # Step 3: Generate book section content using section_writer agent
        try:
            book_structure_json = json.loads(book_structure)
            book = Book(st.session_state.book_title, book_structure_json)

            if "book" not in st.session_state:
                st.session_state.book = book

            # Print the book structure to the terminal to show structure
            print(json.dumps(book_structure_json, indent=2))

            st.session_state.book.display_structure()

            def stream_section_content(sections):
                for title, content in sections.items():
                    if isinstance(content, str):
                        additional_instructions_prompt = f"{additional_section_writer_prompt}\n{additional_instructions}\n{advanced_settings_prompt}"
                        if total_seed_content != "":
                            additional_instructions_prompt += "\n" + total_seed_content

                        content_stream = generate_section(
                            prompt=(title + ": " + content),
                            additional_instructions=additional_instructions_prompt,
                            model=section_agent_model,
                            groq_provider=st.session_state.groq,
                        )
                        for chunk in content_stream:
                            # Check if GenerationStatistics data is returned instead of str tokens
                            chunk_data = chunk
                            if type(chunk_data) == GenerationStatistics:
                                total_generation_statistics.add(chunk_data)

                                st.session_state.statistics_text = str(
                                    total_generation_statistics
                                )
                                display_statistics(
                                    placeholder=placeholder,
                                    statistics_text=st.session_state.statistics_text,
                                )

                            elif chunk != None:
                                st.session_state.book.update_content(title, chunk)
                    elif isinstance(content, dict):
                        stream_section_content(content)

            stream_section_content(book_structure_json)

        except json.JSONDecodeError:
            st.error("Failed to decode the book structure. Please try again.")

except Exception as e:
    st.session_state.button_disabled = False
    st.error(e)

    if st.button("Clear"):
        st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

# Update render_advanced_groq_form to use custom CSS classes
def render_advanced_groq_form(on_submit, button_disabled, button_text):
    with st.form(key='advanced_groq_form'):
        groq_input_key = st.text_input("GROQ API Key", type="password", placeholder="Enter your GROQ API Key", help="Your GROQ API Key for accessing the API", key="groq_input_key", disabled=button_disabled, css_classes="input")
        topic_text = st.text_area("Book Topic", placeholder="Enter the topic of the book", help="The main topic of the book", key="topic_text", disabled=button_disabled, css_classes="textarea")
        additional_instructions = st.text_area("Additional Instructions", placeholder="Enter any additional instructions", help="Any additional instructions for the book generation", key="additional_instructions", disabled=button_disabled, css_classes="textarea")
        writing_style = st.selectbox("Writing Style", ["Formal", "Informal", "Technical", "Narrative"], help="Choose a writing style", key="writing_style", disabled=button_disabled, css_classes="select")
        complexity_level = st.selectbox("Complexity Level", ["Beginner", "Intermediate", "Advanced"], help="Choose the complexity level", key="complexity_level", disabled=button_disabled, css_classes="select")
        seed_content = st.text_area("Seed Content", placeholder="Enter any seed content", help="Any seed content to guide the book generation", key="seed_content", disabled=button_disabled, css_classes="textarea")
        uploaded_file = st.file_uploader("Upload Seed Content File", type=["txt"], help="Upload a text file with seed content", key="uploaded_file", disabled=button_disabled, css_classes="file-upload")
        title_agent_model = st.selectbox("Title Agent Model", ["default", "advanced"], help="Choose the model for generating the book title", key="title_agent_model", disabled=button_disabled, css_classes="select")
        structure_agent_model = st.selectbox("Structure Agent Model", ["default", "advanced"], help="Choose the model for generating the book structure", key="structure_agent_model", disabled=button_disabled, css_classes="select")
        section_agent_model = st.selectbox("Section Agent Model", ["default", "advanced"], help="Choose the model for generating the book sections", key="section_agent_model", disabled=button_disabled, css_classes="select")

        submitted = st.form_submit_button(label=button_text, on_click=on_submit, disabled=button_disabled, css_classes="btn-primary")

    return submitted, groq_input_key, topic_text, additional_instructions, writing_style, complexity_level, seed_content, uploaded_file, title_agent_model, structure_agent_model, section_agent_model

# Update display_statistics to use custom CSS classes
def display_statistics(placeholder, statistics_text):
    with placeholder.container():
        st.markdown(f"<div class='card'><p>{statistics_text}</p></div>", unsafe_allow_html=True)

# Update render_download_buttons to use custom CSS classes
def render_download_buttons(book):
    st.markdown("""
        <div style="display: flex; gap: 10px;">
            <button class="btn-primary" onclick="create_markdown_file(book)">Download Markdown</button>
            <button class="btn-secondary" onclick="create_pdf_file(book)">Download PDF</button>
        </div>
    """, unsafe_allow_html=True)