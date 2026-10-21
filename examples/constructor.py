"""Local constructor for a reliability network.

Usage:
    python -m examples.constructor
"""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import traceback

from reliability.display import bins, latex, layers, places
from reliability.estimate import path, scan, summarize
from reliability.laws import custom, exponential, normal, truncated_normal
from reliability.network import Network

ROOT = Path(__file__).resolve().parent
PAGE = ROOT / "constructor.html"
STATIC = ROOT / "static"


def figure():
    """Return the seven-element assignment graph with exponential laws."""
    return {
        "source": 1,
        "sink": 7,
        "nodes": [{"name": node, "law": "exponential", "rate": 0.02 * node} for node in range(1, 8)],
        "edges": [(1, 2), (1, 3), (1, 4), (2, 5), (3, 5), (4, 6), (5, 7), (6, 7)],
        "trials": 10000,
        "seed": 7,
        "level": 0.95,
        "bins": 24,
        "start": 20,
        "end": 10000,
        "stops": 16,
        "spacing": "geometric",
        "x-scale": "log",
        "grow-seed": 7,
        "grow-level": 0.95,
    }


def law(spec):
    """Build a vertex law from a constructor record."""
    kind = spec["law"]
    if kind == "exponential":
        return exponential(float(spec["rate"]))
    if kind == "normal":
        return normal(float(spec["center"]), float(spec["scale"]))
    if kind == "truncated_normal":
        return truncated_normal(float(spec["center"]), float(spec["scale"]), float(spec.get("low", 0.0)))
    if kind == "constant":
        value = float(spec["value"])
        return lambda rng: value
    if kind == "custom":
        return custom(spec["source"])
    raise ValueError(f"unknown law {kind!r}")


def assemble(spec):
    """Fold a constructor spec into a network and its drawing payload."""
    nodes = {item["name"]: law(item) for item in spec["nodes"]}
    edges = [tuple(edge) for edge in spec["edges"]]
    source = spec["source"]
    sink = spec["sink"]
    product = Network(source, sink, nodes, edges)
    names = [item["name"] for item in spec["nodes"]]
    return {
        "product": product,
        "layers": layers(source, names, edges),
        "places": {str(name): point for name, point in places(source, names, edges).items()},
        "latex": latex(product.formula),
        "edges": [[origin, destination] for origin, destination in edges],
    }


def layout(spec):
    """Return layers, places and LaTeX without running Monte Carlo."""
    built = assemble(spec)
    return {
        "layers": built["layers"],
        "places": built["places"],
        "latex": built["latex"],
        "edges": built["edges"],
    }


def rungs(start, end, count, spacing):
    """Return increasing sample sizes from start to end.

    Usage:
        rungs(2, 2000, 12, "geometric")
    """
    begin = max(2, int(start))
    finish = max(begin, int(end))
    size = max(1, int(count))
    if size == 1:
        return [finish]
    if spacing == "linear":
        raw = [begin + (finish - begin) * index / (size - 1) for index in range(size)]
    else:
        ratio = (finish / begin) ** (1 / (size - 1))
        raw = [begin * (ratio ** index) for index in range(size)]
    stops = []
    for value in raw:
        stop = min(finish, max(2, int(round(value))))
        if not stops or stop > stops[-1]:
            stops.append(stop)
    if stops[-1] != finish:
        if len(stops) < size:
            stops.append(finish)
        else:
            stops[-1] = finish
    return stops


def run(spec):
    """Return layout, estimate and histogram bins for a constructor spec."""
    return list(walk(spec))[-1]


def walk(spec):
    """Yield progress rows and then the finished Monte Carlo payload.

    Usage:
        list(walk(figure()))[-1]["mean"]
    """
    built = assemble(spec)
    trials = int(spec["trials"])
    samples = []
    step = max(1, trials // 40)
    for sample in scan(built["product"], trials, int(spec["seed"])):
        samples.append(sample)
        if len(samples) % step == 0 and len(samples) < trials:
            yield {"done": len(samples), "total": trials}
    estimate = summarize(samples, float(spec.get("level", 0.95)))
    yield {
        "layers": built["layers"],
        "places": built["places"],
        "latex": built["latex"],
        "edges": built["edges"],
        "mean": estimate.mean,
        "se": estimate.error,
        "low": estimate.low,
        "high": estimate.high,
        "bins": bins(samples, int(spec.get("bins", 24))),
        "done": trials,
        "total": trials,
    }


def grow(spec):
    """Yield prefix-estimate progress, then the convergence payload.

    Usage:
        list(grow(spec))[-1]["points"]
    """
    built = assemble(spec)
    stops = rungs(spec.get("start", 2), spec.get("end", spec.get("trials", 2000)), spec.get("stops", 12), spec.get("spacing", "geometric"))
    trials = stops[-1]
    samples = []
    marks = set(stops)
    seed = spec.get("grow-seed", spec.get("seed"))
    level = spec.get("grow-level", spec.get("level", 0.95))
    for sample in scan(built["product"], trials, int(seed)):
        samples.append(sample)
        if len(samples) in marks:
            yield {"done": len(samples), "total": trials}
    yield {
        "layers": built["layers"],
        "places": built["places"],
        "latex": built["latex"],
        "edges": built["edges"],
        "points": path(samples, stops, float(level)),
        "done": trials,
        "total": trials,
    }


class Page(BaseHTTPRequestHandler):
    """Serve the constructor page and JSON fold/run endpoints.

    Usage:
        ThreadingHTTPServer(("127.0.0.1", 8000), Page)
    """

    def log_message(self, format, *args):
        """Keep the constructor quiet during tests."""
        return

    def do_GET(self):
        """Serve the page, the default figure, or a static KaTeX file."""
        if self.path in {"/", "/constructor.html"}:
            self._send(200, "text/html; charset=utf-8", PAGE.read_bytes())
            return
        if self.path == "/figure":
            self._json(200, figure())
            return
        if self.path == "/report":
            page = (ROOT.parent / "project_report.html").read_text(encoding="utf-8")
            self._send(200, "text/html; charset=utf-8", page.replace("examples/static/katex", "/static/katex").encode("utf-8"))
            return
        if self.path.startswith("/static/"):
            target = (ROOT / self.path.lstrip("/")).resolve()
            if STATIC not in target.parents and target != STATIC:
                self._send(404, "text/plain; charset=utf-8", b"missing static file")
                return
            if not target.is_file():
                self._send(404, "text/plain; charset=utf-8", b"missing static file")
                return
            types = {".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".woff2": "font/woff2", ".woff": "font/woff", ".ttf": "font/ttf"}
            self._send(200, types.get(target.suffix, "application/octet-stream"), target.read_bytes())
            return
        self._send(404, "text/plain; charset=utf-8", b"missing page")

    def do_POST(self):
        """Fold a spec or run Monte Carlo."""
        payload = self.rfile.read(int(self.headers.get("Content-Length", "0")))
        try:
            spec = json.loads(payload.decode("utf-8"))
            if self.path == "/layout":
                self._json(200, layout(spec))
                return
            if self.path == "/run":
                self._stream(walk(spec))
                return
            if self.path == "/grow":
                self._stream(grow(spec))
                return
            self._send(404, "text/plain; charset=utf-8", b"missing endpoint")
        except Exception as error:
            self._json(400, {"error": str(error), "trace": traceback.format_exc()})

    def _send(self, status, mime, body):
        """Write a raw HTTP response."""
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status, payload):
        """Write a JSON HTTP response."""
        self._send(status, "application/json; charset=utf-8", json.dumps(payload).encode("utf-8"))

    def _stream(self, rows):
        """Write one JSON object per line as the Monte Carlo run advances."""
        first = next(rows)
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write((json.dumps(first) + "\n").encode("utf-8"))
        self.wfile.flush()
        for row in rows:
            self.wfile.write((json.dumps(row) + "\n").encode("utf-8"))
            self.wfile.flush()


def main():
    """Listen on 127.0.0.1:8000 and serve the constructor."""
    server = ThreadingHTTPServer(("127.0.0.1", 8000), Page)
    print("constructor on http://127.0.0.1:8000")
    server.serve_forever()


if __name__ == "__main__":
    main()
