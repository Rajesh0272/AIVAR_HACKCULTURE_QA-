from app.models.schemas import ValidationResult
class LocatorValidator:
    def validate(self,page,candidate):
        try:
            s=candidate.get("strategy")
            if s=="role": loc=page.get_by_role(candidate["role"],name=candidate["name"])
            elif s=="label": loc=page.get_by_label(candidate["value"])
            elif s=="text": loc=page.get_by_text(candidate["value"],exact=True)
            else: raise ValueError("Only role, label and text strategies are allowed")
            count=loc.count()
            if count!=1: return ValidationResult(valid=False,reason=f"Expected exactly one match, got {count}",matched_count=count)
            vis=loc.is_visible(); en=loc.is_enabled()
            if not vis: return ValidationResult(valid=False,reason="Candidate is not visible",matched_count=count,visible=False,enabled=en)
            if not en: return ValidationResult(valid=False,reason="Candidate is disabled",matched_count=count,visible=True,enabled=False)
            return ValidationResult(valid=True,reason="Unique, visible and enabled",matched_count=1,visible=True,enabled=True)
        except Exception as e: return ValidationResult(valid=False,reason=str(e))
