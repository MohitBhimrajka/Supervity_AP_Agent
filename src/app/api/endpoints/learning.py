# src/app/api/endpoints/learning.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api.dependencies import get_db
from app.db import models, schemas

router = APIRouter()

@router.get("/heuristics", response_model=List[schemas.LearnedHeuristic], summary="Get All Learned Heuristics")
def get_all_learned_heuristics(
    vendor_name: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    """
    Retrieves a list of all patterns the agent has learned from user actions.
    This can be displayed on a 'Learnings' tab in the frontend to provide
    transparency into the agent's evolving knowledge base.
    """
    query = db.query(models.LearnedHeuristic)
    if vendor_name:
        query = query.filter(models.LearnedHeuristic.vendor_name.ilike(f"%{vendor_name}%"))
    
    return query.order_by(models.LearnedHeuristic.confidence_score.desc()).all() 