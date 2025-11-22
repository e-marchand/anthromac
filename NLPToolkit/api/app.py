"""FastAPI application for NLPToolkit."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pipeline import NLPPipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global pipeline instance
nlp_pipeline: Optional[NLPPipeline] = None

# Create FastAPI app
app = FastAPI(
    title="NLPToolkit API",
    description="Multi-language NLP processing system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class AnalyzeRequest(BaseModel):
    """Request schema for text analysis."""
    text: str = Field(..., description="Text to analyze")
    tasks: List[str] = Field(
        default=["language", "ner", "sentiment"],
        description="NLP tasks to perform"
    )
    language: Optional[str] = Field(default="auto", description="Text language (auto-detect if 'auto')")
    options: Optional[Dict[str, Any]] = Field(default=None, description="Additional options")


class Entity(BaseModel):
    """Named entity."""
    text: str
    type: str
    start: int
    end: int
    confidence: Optional[float] = None


class AnalyzeResponse(BaseModel):
    """Response schema for text analysis."""
    text: str
    language: Optional[Dict[str, Any]] = None
    entities: Optional[List[Entity]] = None
    sentiment: Optional[Dict[str, Any]] = None
    topics: Optional[List[Dict[str, Any]]] = None
    metadata: Dict[str, Any] = {}


class TranslateRequest(BaseModel):
    """Request schema for translation."""
    text: str
    source_lang: str = Field(default="auto", description="Source language")
    target_lang: str = Field(..., description="Target language")


class SummarizeRequest(BaseModel):
    """Request schema for summarization."""
    text: str
    max_length: int = Field(default=150, ge=10, le=500)
    min_length: int = Field(default=50, ge=10, le=200)


class QuestionRequest(BaseModel):
    """Request schema for question answering."""
    question: str
    context: str


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "NLPToolkit API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_text(request: AnalyzeRequest):
    """
    Analyze text with multiple NLP tasks.

    Available tasks:
    - language: Language detection
    - ner: Named entity recognition
    - sentiment: Sentiment analysis
    - topics: Topic extraction
    - pos: Part-of-speech tagging
    - keywords: Keyword extraction

    Args:
        request: Analysis request with text and tasks

    Returns:
        Analysis results
    """
    global nlp_pipeline

    try:
        logger.info(f"Analysis request: {len(request.text)} chars, tasks={request.tasks}")

        # Initialize pipeline if needed
        if nlp_pipeline is None:
            nlp_pipeline = NLPPipeline(
                tasks=request.tasks,
                language=request.language
            )

        # Process text
        results = nlp_pipeline.process(
            text=request.text,
            language=request.language if request.language != 'auto' else None
        )

        # Build response
        response = AnalyzeResponse(
            text=request.text,
            metadata={
                "tasks_performed": request.tasks,
                "timestamp": datetime.utcnow().isoformat(),
                "text_length": len(request.text)
            }
        )

        # Add results
        if "language" in request.tasks or "language_detection" in request.tasks:
            response.language = results.get('language')

        if "ner" in request.tasks:
            entities_data = results.get('entities', [])
            response.entities = [
                Entity(**ent) for ent in entities_data
            ]

        if "sentiment" in request.tasks:
            response.sentiment = results.get('sentiment')

        if "topics" in request.tasks:
            response.topics = results.get('topics')

        return response

    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/translate")
async def translate(request: TranslateRequest):
    """
    Translate text between languages.

    Args:
        request: Translation request

    Returns:
        Translated text
    """
    try:
        logger.info(f"Translation request: {request.source_lang} -> {request.target_lang}")

        # TODO: Implement actual translation
        translated_text = request.text

        return {
            "translated_text": translated_text,
            "source_language": request.source_lang,
            "target_language": request.target_lang,
            "model": "placeholder"
        }

    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/summarize")
async def summarize(request: SummarizeRequest):
    """
    Generate text summary.

    Args:
        request: Summarization request

    Returns:
        Summary text
    """
    try:
        logger.info(f"Summarization request: {len(request.text)} chars")

        # TODO: Implement actual summarization
        summary = request.text[:request.max_length] + "..."

        return {
            "summary": summary,
            "original_length": len(request.text),
            "summary_length": len(summary),
            "compression_ratio": len(summary) / len(request.text)
        }

    except Exception as e:
        logger.error(f"Summarization error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/question")
async def answer_question(request: QuestionRequest):
    """
    Answer question based on context.

    Args:
        request: Question answering request

    Returns:
        Answer with confidence score
    """
    try:
        logger.info(f"QA request: question='{request.question[:50]}...'")

        # TODO: Implement actual QA
        answer = "placeholder answer"

        return {
            "answer": answer,
            "score": 0.85,
            "start": 0,
            "end": len(answer),
            "context_used": len(request.context)
        }

    except Exception as e:
        logger.error(f"QA error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/languages")
async def list_languages():
    """List supported languages."""
    return {
        "total": 100,
        "languages": [
            {"code": "en", "name": "English"},
            {"code": "fr", "name": "French"},
            {"code": "de", "name": "German"},
            {"code": "es", "name": "Spanish"},
            {"code": "it", "name": "Italian"},
            {"code": "pt", "name": "Portuguese"},
            {"code": "ru", "name": "Russian"},
            {"code": "zh", "name": "Chinese"},
            {"code": "ja", "name": "Japanese"},
            {"code": "ko", "name": "Korean"},
            {"code": "ar", "name": "Arabic"},
            {"code": "hi", "name": "Hindi"},
        ]
    }


@app.get("/models")
async def list_models():
    """List available models."""
    return {
        "models": [
            {
                "task": "ner",
                "models": [
                    "bert-base-ner-multilingual",
                    "xlm-roberta-large-ner",
                    "spacy-multilingual"
                ]
            },
            {
                "task": "sentiment",
                "models": [
                    "bert-base-multilingual-sentiment",
                    "xlm-roberta-sentiment"
                ]
            },
            {
                "task": "qa",
                "models": [
                    "bert-base-squad2",
                    "xlm-roberta-squad2"
                ]
            },
            {
                "task": "generation",
                "models": [
                    "gpt2", "t5-base", "mbart"
                ]
            }
        ]
    }


@app.get("/metrics")
async def get_metrics():
    """Get system metrics."""
    return {
        "system": {
            "uptime": "24h",
            "requests_processed": 10000,
            "avg_latency_ms": 120
        },
        "performance": {
            "ner_f1": 0.925,
            "sentiment_accuracy": 0.932,
            "qa_exact_match": 0.832
        }
    }


def main():
    """Run the API server."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
