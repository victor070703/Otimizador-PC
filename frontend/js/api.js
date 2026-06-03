/**
 * api.js — Wrapper para chamadas ao backend Python via pywebview.
 * Todos os métodos retornam Promises.
 */

function _call(method, ...args) {
  return new Promise((resolve, reject) => {
    if (!window.pywebview || !window.pywebview.api) {
      reject(new Error('pywebview API não disponível'));
      return;
    }
    window.pywebview.api[method](...args).then(resolve).catch(reject);
  });
}

const API = {
  getMetrics()                    { return _call('get_metrics'); },
  getProcesses(limit = 25)        { return _call('get_processes', limit); },
  killProcess(pid)                 { return _call('kill_process', pid); },
  getServices()                   { return _call('get_services'); },
  stopService(id)                  { return _call('stop_service', id); },
  getCleanupItems()               { return _call('get_cleanup_items'); },
  cleanItem(id)                    { return _call('clean_item', id); },
  getHistory()                    { return _call('get_history'); },
  getOptimizationPreview(mode)    { return _call('get_optimization_preview', mode); },
  runOptimization(plan)            { return _call('run_optimization', plan); },
};
