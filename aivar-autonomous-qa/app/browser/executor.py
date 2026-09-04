import json,time
from pathlib import Path
from playwright.sync_api import sync_playwright
from app.config import settings
from app.healing.healer import Healer
from app.models.schemas import *
class TestExecutor:
    def __init__(self): self.healer=Healer()
    def run_test(self,test,artifact_root="artifacts"):
        start=time.time(); td=Path(artifact_root)/test.id; td.mkdir(parents=True,exist_ok=True)
        with sync_playwright() as p:
            b=p.chromium.launch(headless=settings.HEADLESS); page=b.new_page()
            try:
                self._run(page,test.steps); return ExecutionResult(test_id=test.id,status="PASSED",duration_ms=int((time.time()-start)*1000),artifacts_dir=str(td))
            except Exception as e:
                try: page.screenshot(path=str(td/"failure.png"),full_page=True)
                except Exception: pass
                dom=page.content()
                try: (td/"dom.html").write_text(dom,encoding="utf-8")
                except Exception: pass
                evidence={"test_id":test.id,"url":page.url,"error":str(e),"dom":dom[:30000]}
                (td/"evidence.json").write_text(json.dumps(evidence,indent=2),encoding="utf-8")
                h=self.healer.heal(page,evidence)
                if h.status=="HEALED":
                    steps=[TestStep.model_validate(x.model_dump()) for x in test.steps]
                    for st in steps:
                        if st.action=="click" and st.target=={"strategy":"role","role":"button","name":"Login"}: st.target=h.diagnosis.healing_candidate
                    try:
                        page.goto(test.steps[0].value,wait_until="domcontentloaded",timeout=15000) if test.steps and test.steps[0].action=="navigate" else None
                        self._run(page,steps)
                        (td/"healing.json").write_text(h.model_dump_json(indent=2),encoding="utf-8")
                        return ExecutionResult(test_id=test.id,status="HEALED",duration_ms=int((time.time()-start)*1000),artifacts_dir=str(td),healing_action=h.action)
                    except Exception as re: return ExecutionResult(test_id=test.id,status="FAILED",duration_ms=int((time.time()-start)*1000),error=f"Full retest failed: {re}",artifacts_dir=str(td))
                if h.status=="ESCALATED":
                    (td/"healing.json").write_text(h.model_dump_json(indent=2),encoding="utf-8")
                    return ExecutionResult(test_id=test.id,status="ESCALATED",duration_ms=int((time.time()-start)*1000),error=str(e),artifacts_dir=str(td),healing_action=h.action)
                return ExecutionResult(test_id=test.id,status="FAILED",duration_ms=int((time.time()-start)*1000),error=str(e),artifacts_dir=str(td),healing_action=h.action)
            finally: b.close()
    def _run(self,page,steps):
        for st in steps:
            if st.action=="navigate":
                r=page.goto(st.value,wait_until="domcontentloaded",timeout=15000)
                if r is not None and r.status>=500: raise RuntimeError(f"HTTP {r.status} Internal Server Error")
            else:
                t=st.target; s=t.get("strategy")
                if s=="role": loc=page.get_by_role(t["role"],name=t["name"])
                elif s=="label": loc=page.get_by_label(t["value"])
                elif s=="text": loc=page.get_by_text(t["value"],exact=True)
                else: raise ValueError(f"Unsupported selector strategy: {s}")
                if st.action=="fill": loc.fill(st.value or "")
                elif st.action=="click": loc.click(timeout=5000)
                elif st.action=="assert_visible": loc.wait_for(state="visible",timeout=5000)
                elif st.action=="assert_text" and st.value not in loc.inner_text(): raise AssertionError(f"Expected text '{st.value}' not found")
