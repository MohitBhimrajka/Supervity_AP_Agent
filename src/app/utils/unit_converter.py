# src/app/utils/unit_converter.py
from typing import Dict, Any

# Define our standard base units
BASE_WEIGHT_UNIT = "kg"
BASE_COUNT_UNIT = "pcs"

# Conversion factors to our base weight unit (kg)
WEIGHT_CONVERSION_FACTORS = {
    'kg': 1.0,
    'kilogram': 1.0,
    'kilograms': 1.0,
    'ton': 1000.0,
    'tons': 1000.0,
    'tonne': 1000.0,
    'tonnes': 1000.0,
    'lb': 0.453592,
    'lbs': 0.453592,
    'pound': 0.453592,
    'pounds': 0.453592,
    'oz': 0.0283495,
    'ounce': 0.0283495,
    'ounces': 0.0283495,
}

# Words that should all be treated as our base count unit (pcs)
COUNT_SYNONYMS = {
    'pcs', 'piece', 'pieces', 'each', 'ea', 'unit', 'units', 
    'set', 'sets', 'pair', 'pairs', 'pack', 'packs'
}

def normalize_item(line_item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes a line item's quantity and unit, adding normalized fields.
    This function will add:
    - 'normalized_qty'
    - 'normalized_unit'
    - 'normalized_unit_price' (if unit price is present)
    """
    if not isinstance(line_item, dict):
        return line_item

    original_unit = (line_item.get('unit') or '').lower()
    
    # Determine original quantity from possible keys
    qty_keys = ['quantity', 'ordered_qty', 'received_qty']
    original_qty = None
    for key in qty_keys:
        if key in line_item and line_item[key] is not None:
            original_qty = float(line_item[key])
            break

    if original_qty is None:
        return line_item # Cannot normalize without a quantity

    # Default to original values
    normalized_qty = original_qty
    normalized_unit = original_unit
    
    # Check for weight conversion
    if original_unit in WEIGHT_CONVERSION_FACTORS:
        normalized_qty = original_qty * WEIGHT_CONVERSION_FACTORS[original_unit]
        normalized_unit = BASE_WEIGHT_UNIT
    # Check for count conversion
    elif original_unit in COUNT_SYNONYMS:
        normalized_unit = BASE_COUNT_UNIT
        # Quantity remains the same for counts

    line_item['normalized_qty'] = normalized_qty
    line_item['normalized_unit'] = normalized_unit
    
    # Normalize unit price if available
    original_price = line_item.get('unit_price')
    if original_price is not None and original_qty > 0:
        original_price = float(original_price)
        # Calculate price per normalized quantity
        # Total price = original_qty * original_price
        # Normalized unit price = Total price / normalized_qty
        total_price = original_qty * original_price
        if normalized_qty > 0:
            line_item['normalized_unit_price'] = total_price / normalized_qty
        else:
            line_item['normalized_unit_price'] = 0
            
    return line_item 