# src/app/api/endpoints/learning.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.api.dependencies import get_db
from app.db import models, schemas

router = APIRouter()

# New schema for aggregated results
class AggregatedHeuristic(schemas.LearnedHeuristicBase):
    id: str
    confidence_score: float
    trigger_count: int
    potential_impact: int # e.g., number of invoices this would affect per month
    
@router.get("/heuristics", response_model=List[AggregatedHeuristic], summary="Get Aggregated Learned Heuristics")
def get_aggregated_heuristics(
    vendor_name: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    """
    Retrieves and aggregates learned heuristics to provide clear, actionable
    suggestions for automation.
    """
    query = db.query(models.LearnedHeuristic)
    if vendor_name:
        query = query.filter(models.LearnedHeuristic.vendor_name.ilike(f"%{vendor_name}%"))
    
    all_heuristics = query.all()
    
    # Aggregate in Python
    aggregated: Dict[str, Dict[str, Any]] = {}
    
    for h in all_heuristics:
        key = f"{h.vendor_name}-{h.exception_type}"
        if key not in aggregated:
            aggregated[key] = {
                "id": key,
                "vendor_name": h.vendor_name,
                "exception_type": h.exception_type,
                "learned_condition": h.learned_condition,
                "resolution_action": h.resolution_action,
                "confidence_score": h.confidence_score,
                "trigger_count": h.trigger_count,
                "potential_impact": 1,
            }
        else:
            # Update with the highest confidence and trigger count, sum impact
            agg = aggregated[key]
            agg["trigger_count"] += h.trigger_count
            agg["confidence_score"] = max(agg["confidence_score"], h.confidence_score)
            agg["potential_impact"] += 1
            # For conditions like variance, take the max value
            if 'max_variance_percent' in h.learned_condition:
                current_max = agg["learned_condition"].get('max_variance_percent', 0)
                new_val = h.learned_condition.get('max_variance_percent', 0)
                agg["learned_condition"]['max_variance_percent'] = max(current_max, new_val)

    return sorted(list(aggregated.values()), key=lambda x: x['confidence_score'], reverse=True) 