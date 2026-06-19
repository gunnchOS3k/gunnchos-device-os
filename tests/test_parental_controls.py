from gunnchos_device_os.parental_controls import school_restrictions, parental_override, content_report

def test_school_restrictions():
    r = school_restrictions("School")
    assert r["content_filter"] is True

def test_parental_override():
    assert parental_override("parent_guardian", "extend_screen_time")["approved"] is True

def test_content_report():
    assert content_report("student", "bullying")["received"] is True
