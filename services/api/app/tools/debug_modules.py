import json

from services.api.app.core import debug_modules

if __name__ == "__main__":
    print(json.dumps(debug_modules(), ensure_ascii=False, indent=2))
