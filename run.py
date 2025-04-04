from __future__ import annotations

import uvicorn

from embedez.main import app

if __name__ == "__main__":
    uvicorn.run(app, port=8069)
