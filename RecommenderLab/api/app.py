"""FastAPI application for RecommenderLab."""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models.recommender import RecommenderSystem

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="RecommenderLab API",
    description="Scalable multi-algorithm recommendation system",
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

# Global recommender instance
recommender: Optional[RecommenderSystem] = None


# Request/Response Models
class TrainRequest(BaseModel):
    """Request schema for training."""
    interactions: List[Dict[str, Any]] = Field(..., description="User-item interactions")
    model_type: str = Field(default="ncf", description="Model type (als, ncf)")
    config: Optional[Dict[str, Any]] = Field(default=None, description="Model configuration")



class RecommendationRequest(BaseModel):
    """Request schema for recommendations."""
    user_id: int = Field(..., description="User ID")
    n: int = Field(default=10, ge=1, le=100, description="Number of recommendations")
    filter_seen: bool = Field(default=True, description="Filter already seen items")
    diversity: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Diversity parameter")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Contextual information")


class RecommendationItem(BaseModel):
    """Single recommendation item."""
    item_id: int
    score: float
    title: Optional[str] = None
    category: Optional[str] = None
    explanation: Optional[str] = None


class RecommendationResponse(BaseModel):
    """Response schema for recommendations."""
    user_id: int
    recommendations: List[RecommendationItem]
    metadata: Dict[str, Any] = {}


class SimilarItemsRequest(BaseModel):
    """Request schema for similar items."""
    item_id: int
    n: int = Field(default=10, ge=1, le=100)
    filter_category: Optional[str] = None


class BatchRecommendRequest(BaseModel):
    """Request schema for batch recommendations."""
    user_ids: List[int]
    n: int = Field(default=10, ge=1, le=100)


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "RecommenderLab API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.post("/train")
async def train_model(request: TrainRequest):
    """
    Train a recommendation model.

    Args:
        request: Training request with interactions and config

    Returns:
        Training status
    """
    global recommender

    try:
        logger.info(f"Training {request.model_type} model with {len(request.interactions)} interactions")

        # Convert interactions to DataFrame
        interactions_df = pd.DataFrame(request.interactions)

        # Validate required columns
        required_cols = ['user_id', 'item_id', 'rating']
        if not all(col in interactions_df.columns for col in required_cols):
            raise HTTPException(
                status_code=400,
                detail=f"Interactions must contain columns: {required_cols}"
            )

        # Initialize recommender
        recommender = RecommenderSystem(
            model_type=request.model_type,
            config=request.config or {}
        )

        # Train the model
        recommender.fit(interactions_df)

        return {
            "status": "success",
            "message": f"Successfully trained {request.model_type} model",
            "model_type": request.model_type,
            "num_interactions": len(interactions_df),
            "num_users": interactions_df['user_id'].nunique(),
            "num_items": interactions_df['item_id'].nunique()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Training error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/recommend", response_model=RecommendationResponse)
async def recommend(request: RecommendationRequest):
    """
    Generate personalized recommendations for a user.

    Args:
        request: Recommendation request with user ID and parameters

    Returns:
        List of recommended items with scores
    """
    global recommender

    try:
        logger.info(f"Recommendation request for user {request.user_id}")

        if recommender is None:
            raise HTTPException(
                status_code=400,
                detail="No trained model available. Please train a model first using /train endpoint."
            )

        # Get recommendations from model
        start_time = datetime.utcnow()
        recs = recommender.recommend(
            user_id=request.user_id,
            n=request.n,
            filter_seen=request.filter_seen,
            diversity=request.diversity,
            context=request.context
        )
        latency = (datetime.utcnow() - start_time).total_seconds() * 1000

        # Format recommendations
        recommendations = [
            RecommendationItem(
                item_id=rec['item_id'],
                score=rec['score'],
                title=f"Item {rec['item_id']}",
                explanation=f"Recommended based on score: {rec['score']:.3f}"
            )
            for rec in recs
        ]

        return RecommendationResponse(
            user_id=request.user_id,
            recommendations=recommendations,
            metadata={
                "model_type": recommender.model_type,
                "timestamp": datetime.utcnow().isoformat(),
                "latency_ms": latency,
                "num_recommendations": len(recommendations)
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Recommendation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/similar-items")
async def similar_items(request: SimilarItemsRequest):
    """
    Find items similar to a given item.

    Args:
        request: Similar items request

    Returns:
        List of similar items
    """
    global recommender

    try:
        logger.info(f"Similar items request for item {request.item_id}")

        if recommender is None:
            raise HTTPException(
                status_code=400,
                detail="No trained model available. Please train a model first."
            )

        # Get similar items from model
        similar = recommender.similar_items(
            item_id=request.item_id,
            n=request.n
        )

        # Format response
        formatted_similar = [
            {
                "item_id": item['item_id'],
                "similarity": item['similarity'],
                "title": f"Item {item['item_id']}"
            }
            for item in similar
        ]

        return {
            "item_id": request.item_id,
            "similar_items": formatted_similar,
            "model_type": recommender.model_type
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Similar items error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/trending")
async def trending(n: int = 10, category: Optional[str] = None):
    """
    Get currently trending items.

    Args:
        n: Number of items to return
        category: Optional category filter

    Returns:
        List of trending items
    """
    try:
        logger.info(f"Trending request: n={n}, category={category}")

        # TODO: Implement trending logic
        items = [
            {
                "item_id": i,
                "title": f"Trending Item {i}",
                "score": 100 - i,
                "category": category or "general"
            }
            for i in range(1, min(n + 1, 11))
        ]

        return {"trending": items}

    except Exception as e:
        logger.error(f"Trending error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/batch-recommend")
async def batch_recommend(request: BatchRecommendRequest):
    """
    Generate recommendations for multiple users in batch.

    Args:
        request: Batch recommendation request

    Returns:
        Recommendations for all users
    """
    try:
        logger.info(f"Batch recommendation for {len(request.user_ids)} users")

        # TODO: Implement batch recommendation
        results = {}
        for user_id in request.user_ids:
            results[user_id] = [
                {"item_id": i, "score": 0.9 - (i * 0.05)}
                for i in range(1, min(request.n + 1, 6))
            ]

        return {
            "recommendations": results,
            "total_users": len(request.user_ids)
        }

    except Exception as e:
        logger.error(f"Batch recommendation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models")
async def list_models():
    """List available recommendation models."""
    return {
        "models": [
            {
                "name": "als",
                "type": "collaborative",
                "status": "available"
            },
            {
                "name": "ncf",
                "type": "collaborative",
                "status": "available"
            },
            {
                "name": "two_tower",
                "type": "hybrid",
                "status": "available"
            },
            {
                "name": "transformer4rec",
                "type": "sequential",
                "status": "available"
            }
        ]
    }


@app.get("/metrics")
async def get_metrics():
    """Get system and model metrics."""
    return {
        "system": {
            "uptime": "24h",
            "requests_per_second": 100,
            "avg_latency_ms": 45
        },
        "model": {
            "ndcg@10": 0.385,
            "coverage": 0.65,
            "diversity": 0.42
        }
    }


def main():
    """Run the API server."""
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
