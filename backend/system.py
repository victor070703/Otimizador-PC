import psutil
import platform
import subprocess
import threading
import copy
import time

_system = platform.system()  # 'Darwin', 'Windows', 'Linux'

_metrics = {
    'cpu': {'percent': 0, 'model': 'Carregando...', 'cores': 0, 'threads': 0},
    'ram': {'used_gb': 0.0, 'total_gb': 0.0, 'percent': 0},
    'gpu': {'name': 'N/A', 'percent': 0, 'temp': 0, 'available': False},
    'disk': {'read_mb': 0.0, 'write_mb': 0.0, 'free_gb': 0.0, 'total_gb': 0.0, 'percent': 0},
    'platform': _system,
}
_lock = threading.Lock()


def _get_cpu_model():
    try:
        if _system == 'Darwin':
            result = subprocess.run(
                ['sysctl', '-n', 'machdep.cpu.brand_string'],
                capture_output=True, text=True, timeout=3
            )
            name = result.stdout.strip()
            if name:
                return name
            # Apple Silicon
            result2 = subprocess.run(
                ['sysctl', '-n', 'hw.model'],
                capture_output=True, text=True, timeout=3
            )
            return result2.stdout.strip() or 'Apple Silicon'

        elif _system == 'Windows':
            result = subprocess.run(
                ['wmic', 'cpu', 'get', 'name', '/value'],
                capture_output=True, text=True, shell=True, timeout=5
            )
            for line in result.stdout.splitlines():
                if line.startswith('Name='):
                    return line.split('=', 1)[1].strip()
    except Exception:
        pass
    return platform.processor() or 'CPU Desconhecida'


def _get_gpu_name():
    try:
        if _system == 'Darwin':
            result = subprocess.run(
                ['system_profiler', 'SPDisplaysDataType'],
                capture_output=True, text=True, timeout=8
            )
            for line in result.stdout.splitlines():
                stripped = line.strip()
                if stripped.startswith('Chipset Model:'):
                    return stripped.split(':', 1)[1].strip()
            return 'Apple GPU'

        elif _system == 'Windows':
            result = subprocess.run(
                ['wmic', 'path', 'win32_VideoController', 'get', 'name', '/value'],
                capture_output=True, text=True, shell=True, timeout=5
            )
            for line in result.stdout.splitlines():
                if line.startswith('Name='):
                    return line.split('=', 1)[1].strip()
    except Exception:
        pass
    return 'GPU'


def _try_nvidia_gpu():
    """Returns (percent, temp) for NVIDIA GPU on Windows, or (0, 0) otherwise."""
    try:
        import pynvml
        pynvml.nvmlInit()
        handle = pynvml.nvmlDeviceGetHandleByIndex(0)
        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
        return util.gpu, temp
    except Exception:
        return 0, 0


# Initialise static info once at import time (runs in background to avoid blocking)
_cpu_model = 'Carregando...'
_gpu_name = 'Carregando...'
_gpu_available = False


def _load_static_info():
    global _cpu_model, _gpu_name, _gpu_available
    _cpu_model = _get_cpu_model()
    _gpu_name = _get_gpu_name()
    _gpu_available = _system == 'Windows'
    with _lock:
        _metrics['cpu']['model'] = _cpu_model
        _metrics['gpu']['name'] = _gpu_name
        _metrics['gpu']['available'] = _gpu_available


# Warm up cpu_percent (first call always returns 0.0)
psutil.cpu_percent(interval=None)


def _update_loop():
    prev_disk_io = None
    try:
        prev_disk_io = psutil.disk_io_counters()
    except Exception:
        pass

    while True:
        try:
            cpu_pct = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory()

            # Disk I/O delta
            read_mb = write_mb = 0.0
            try:
                curr_disk_io = psutil.disk_io_counters()
                if prev_disk_io and curr_disk_io:
                    read_mb = max(0.0, (curr_disk_io.read_bytes - prev_disk_io.read_bytes) / (1024 ** 2))
                    write_mb = max(0.0, (curr_disk_io.write_bytes - prev_disk_io.write_bytes) / (1024 ** 2))
                prev_disk_io = curr_disk_io
            except Exception:
                pass

            disk_path = 'C:\\' if _system == 'Windows' else '/'
            disk_usage = psutil.disk_usage(disk_path)

            gpu_pct, gpu_temp = (0, 0)
            if _system == 'Windows':
                gpu_pct, gpu_temp = _try_nvidia_gpu()

            with _lock:
                _metrics['cpu'].update({
                    'percent': round(cpu_pct, 1),
                    'model': _cpu_model,
                    'cores': psutil.cpu_count(logical=False) or psutil.cpu_count(),
                    'threads': psutil.cpu_count(logical=True),
                })
                _metrics['ram'].update({
                    'used_gb': round(mem.used / (1024 ** 3), 1),
                    'total_gb': round(mem.total / (1024 ** 3), 0),
                    'percent': round(mem.percent, 1),
                })
                _metrics['gpu'].update({
                    'name': _gpu_name,
                    'percent': gpu_pct,
                    'temp': gpu_temp,
                    'available': _gpu_available,
                })
                _metrics['disk'].update({
                    'read_mb': round(read_mb, 1),
                    'write_mb': round(write_mb, 1),
                    'free_gb': round(disk_usage.free / (1024 ** 3), 0),
                    'total_gb': round(disk_usage.total / (1024 ** 3), 0),
                    'percent': round(disk_usage.percent, 1),
                })
        except Exception:
            pass

        time.sleep(1)


_static_thread = threading.Thread(target=_load_static_info, daemon=True)
_static_thread.start()

_monitor_thread = threading.Thread(target=_update_loop, daemon=True)
_monitor_thread.start()


def get_all():
    with _lock:
        return copy.deepcopy(_metrics)
