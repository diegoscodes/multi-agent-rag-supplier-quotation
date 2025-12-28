from app.services.query_parsing import extract_target_item

def test_extract_target_item_for_pattern():
    assert extract_target_item("best supplier for drill bits") == "drill bits"

def test_extract_target_item_need_pattern():
    assert extract_target_item("I need bolts 10mm") == "bolts 10mm"

def test_extract_target_item_fallback():
    assert extract_target_item("drill bits") == "drill bits"

def test_extract_target_item_returns_unknown_when_no_product():
    assert extract_target_item("best supplier please") == "unknown"
