import json
import yaml


def convert_raw_context_to_dict(user_context) -> dict:
    if not user_context:
        return {}
    if isinstance(user_context, str):
        try:
            user_context = json.loads(user_context)
            if "ai_yml" in user_context:
                try:
                    ai_yml_json = yaml.safe_load(user_context["ai_yml"])
                    user_context.update({"ai_yml": ai_yml_json})
                except yaml.scanner.ScannerError:
                    pass
        except json.JSONDecodeError:
            pass
    if not isinstance(user_context, dict):
        # 避免抛异常阻塞用户，给到 dify 那边去查看
        user_context = {
            "PARSE_CONTEXT_FAILED": user_context
        }
    return user_context
