from . import multiprocess as multiprocess
from . import values as values
from .exposition import start_http_server as start_http_server
from .metrics import Counter as Counter
from .metrics import Gauge as Gauge
from .metrics import Histogram as Histogram
from .metrics import Info as Info
from .metrics import Summary as Summary
from .registry import CollectorRegistry as CollectorRegistry

def disable_created_metrics() -> None: ...
def enable_created_metrics() -> None: ...
def generate_latest(registry: CollectorRegistry = ...) -> bytes: ...
