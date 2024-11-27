import streamlit as st
import requests
from streamlit.components.v1 import html
from streamlit_pdf_viewer import pdf_viewer


st.title("Car Manual QA System")

# Add sidebar for manual selection
with st.sidebar:
    st.header("Upload Manual")
    uploaded_file = st.file_uploader("Upload Car Manual (PDF)", type=['pdf'])
    car_model = st.text_input("Enter Car Model:")
    
    if st.button("Upload") and uploaded_file and car_model:
        files = {"file": uploaded_file}
        data = {"id": car_model}
        
        response = requests.post(
            "http://backend:8000/index",
            files=files,
            data=data
        )
        
        if response.status_code == 200:
            st.success("Manual uploaded and indexed successfully!")
        else:
            st.error("Error uploading manual")

# Main content area for asking questions
question = st.text_input("Enter your question:")

if st.button("Ask"):
    if question:
        response = requests.post(
            "http://backend:8000/query",
            json={
                "question": question
            }
        )
        
        if response.status_code == 200:
            results = response.json()
            # Create tabs for each result
            if results:
                tabs = st.tabs([f"Answer {i+1}" for i in range(len(results))])
                
                for i, (result, tab) in enumerate(zip(results, tabs)):
                    with tab:
                        st.write(f"Answer: {result['answer']}")
                        
                        with st.expander("View Source Documents"):
                            for doc in result['retrieved_documents']:
                                st.write(doc)
                        
                        # Display PDF with highlights
                        if result['coordinates']:
                            st.write("Relevant sections highlighted in the PDF:")
                            
                            # Load PDF file
                            annotations = []
                            for coord, page_number in zip(result['coordinates'], result['page_numbers']):
                                # Convert coordinate to x, y, width, height
                                x0, y0, x1, y1 = coord['x0'], coord['y0'], coord['x1'], coord['y1']
                 
                                annotations.append({
                                    "page": page_number - 1, # Page numbers are 0-based in the viewer
                                    "x": str(x0),
                                    "y": str(y0), 
                                    "width": str(x1 - x0),
                                    "height": str(y1 - y0),
                                    "color": "#ff0000", # Solid red color
                                    "outline": True, # Add outline
                                    "border_width": "2px" # Make border more visible
                                })
                            
                            try:
                                # Add error handling and debug info
                                st.write(f"Number of annotations: {len(annotations)}")
                                st.write(f"Page numbers: {', '.join(map(str, result['page_numbers']))}")
                                
                                pdf_viewer(
                                    input=f"data/{result['filename']}",
                                    width=700,
                                    height=600,
                                    annotations=annotations,
                                    render_text=True, # Enable text rendering
                                    annotation_outline_size=2 # Increase outline size
                                )
                            except Exception as e:
                                st.error(f"Error displaying PDF: {str(e)}")
        else:
            st.error("Error getting response")
    else:
        st.warning("Please enter a question")