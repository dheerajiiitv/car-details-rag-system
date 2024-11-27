# Car Manual Question-Answering System

## Project Overview
Development of an interactive web application that allows users to query car owner's manuals and receive relevant answers with citations.

## Business Need
Car owners often need quick access to specific information from their vehicle's manual but find it cumbersome to search through lengthy PDF documents. A question-answering system would provide immediate, accurate responses to user queries about vehicle operation, maintenance, and specifications.

## Functional Requirements

### Core Features
1. Web Interface
   - Text input field for user questions
   - Display area for answers and citations
   - Clear visual feedback for system responses

2. Query Processing
   - Accept natural language questions about any car model
   - Process queries related to:
     - Vehicle operations (e.g., "How to turn on indicator in MG Astor?")
     - Maintenance requirements (e.g., "Which engine oil to use in Tiago?")
     - Technical specifications
     - Safety features
     - Troubleshooting guidance

3. Response System
   - Provide direct answers from available manuals
   - Include citations referencing specific sections of the manual
   - Return "Manual is not available" message for unsupported vehicles
   - Highlight relevant text passages from the source material

## Technical Requirements

### Data Management
1. Manual Storage
   - System to store and index car manuals
   - Support for PDF document processing
   - Structured storage of extracted manual content

2. Search and Retrieval
   - Natural language processing for query understanding
   - Semantic search capabilities
   - Citation tracking and reference system

### Implementation Suggestions
- Frontend: Streamlit for rapid development and deployment
- Backend: Text processing and search implementation
- Vector Database: Storage system for manual content and metadata

## Success Criteria
1. Accurate answer retrieval for queries about available manuals
2. Clear identification of cases where manuals are not available
3. Proper citation of sources in responses
4. User-friendly interface with clear input/output sections

## Constraints and Limitations
1. Limited to available car manuals in the system
2. Response quality dependent on extracted content quality


### File Structure
```
car-details-rag-system/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                # FastAPI application
│   │   ├── database.py            # ChromaDB setup and operations
│   │   ├── models.py              # Pydantic models
│   │   └── utils/logger.py        # Utility functions
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── data/
│   │   └── manuals/                # Store PDF manuals here
│   ├── app.py                    # Streamlit application
│   ├── requirements.txt
│   └── Dockerfile
│
│── README.md
│
└── docker-compose.yml            # Orchestration of services
```

## Running the project

### Docker Setup

#### Prerequisites
- Docker
- Docker Compose

#### Running the Application

1. Clone the repository
2. Navigate to the project root directory
3. Set the OpenAI API key as an environment variable:
   ```bash
   export OPENAI_API_KEY=<your-openai-api-key>
   ```
4. Build and start the containers:
   ```bash
   docker-compose up --build
   ```
5. Access the application:
   - Frontend: http://localhost:8501
   - Backend API: http://localhost:8000

#### Sample Output demo video


#### Stopping the Application

To stop the application, run:
```bash
docker-compose down
```


## Future Improvements
1. Multicolumn pdfs might mix up and contain mix text from different columns. Need to use Document vision to detect columns and extract text from each column.
2. Improving Retrieval
   - Using reranker to improve retrieval.
   - Adding metadata about chunk while indexing to help with retrieval. (like using vehicle section names)
3. Improving the prompt for better answer quality.




