"""
assessor — AI Vendor Risk Assessor for Nimbu Mart (production-oriented package).

Architecture (ports & adapters + DI)
  ports/        Protocol interfaces (LLM, policy, research, router, …)
  services/     Use-case services with constructor injection
  container.py  Composition root — wires adapters to ports
  graph.py      Backward-compatible Pipeline façade

Prefer:
  from assessor.container import AppContainer
  pipe = AppContainer.create().pipeline()
"""

__version__ = "0.6.0"
