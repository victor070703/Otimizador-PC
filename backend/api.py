import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend import system, processes, services, cleanup, history, optimizer


class Api:
    """Exposed to JavaScript via window.pywebview.api"""

    # ── Métricas ────────────────────────────────────────────────────────────
    def get_metrics(self):
        return system.get_all()

    # ── Processos ───────────────────────────────────────────────────────────
    def get_processes(self, limit=25):
        return processes.get_processes(int(limit))

    def kill_process(self, pid):
        return processes.kill_process(int(pid))

    # ── Serviços ────────────────────────────────────────────────────────────
    def get_services(self):
        return services.get_services()

    def stop_service(self, service_id):
        return services.stop_service(str(service_id))

    # ── Limpeza ─────────────────────────────────────────────────────────────
    def get_cleanup_items(self):
        return cleanup.get_cleanable_items()

    def clean_item(self, item_id):
        return cleanup.clean_item(str(item_id))

    # ── Histórico ───────────────────────────────────────────────────────────
    def get_history(self):
        return history.load()

    # ── Otimizador ──────────────────────────────────────────────────────────
    def get_optimization_preview(self, mode='gaming'):
        return optimizer.get_preview(str(mode))

    def run_optimization(self, plan):
        return optimizer.run(plan)
