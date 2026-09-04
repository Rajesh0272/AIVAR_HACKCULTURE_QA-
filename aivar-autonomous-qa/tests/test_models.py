from app.models.schemas import TestPlan,TestScenario,CoverageAnalysis
def test_models():
 p=TestPlan(application_url="http://example.com",application_summary="demo",scenarios=[TestScenario(id="S001",name="Login",flow="login",category="happy_path",expected_outcome="dashboard")]); assert p.scenarios[0].category=="happy_path"
def test_coverage(): assert CoverageAnalysis(score=.75,should_replan=False,reasoning="ok").score==.75
