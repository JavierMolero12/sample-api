"""Punto de entrada: `python -m app`.

Se arranca uvicorn desde Python (y no desde la CLI) porque la imagen distroless no
tiene shell: así PORT y LOG_LEVEL se leen del entorno sin necesidad de `sh -c`.
"""

import os

import uvicorn


def main() -> None:
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",  # escucha en todas las interfaces del pod
        port=int(os.getenv("PORT", "8080")),
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )


if __name__ == "__main__":
    main()
