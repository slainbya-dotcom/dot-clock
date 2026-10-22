"""Inlines CSS/JS into single-file HTML previews (with a fake Tauri bridge and
sample settings) so the UI can be checked in any browser without building."""
import json, os, re, sys
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "preview")
os.makedirs(OUT, exist_ok=True)

SAMPLE = {
  "clocks": [
    {"id": "h", "label": "London, UK", "tz": "Europe/London", "lat": 51.51, "lng": -0.13, "home": True},
    {"id": "a", "label": "New York, USA", "tz": "America/New_York", "lat": 40.71, "lng": -74.01},
    {"id": "b", "label": "Tokyo, Japan", "tz": "Asia/Tokyo", "lat": 35.68, "lng": 139.69, "color": "#5ad1ff"},
    {"id": "c", "label": "Sydney, Australia", "tz": "Australia/Sydney", "lat": -33.87, "lng": 151.21},
    {"id": "d", "label": "Kathmandu, Nepal", "tz": "Asia/Kathmandu", "lat": 27.72, "lng": 85.32},
  ],
  "use24h": True, "dotColor": "#ffb000", "dotSize": 3, "bgColor": "#101010", "bgOpacity": 0.85,
}

def shim(state):
    return """<script>
window.__TAURI__ = {
  core: { invoke: async (cmd, args) => {
    if (cmd === 'load_state') return %s;
    if (cmd === 'save_state') { console.log('save_state', args.json.length, 'bytes'); return; }
    console.log('invoke', cmd, args);
  } },
  event: { listen: async () => () => {} },
  window: { getCurrentWindow: () => ({ setSize: async () => {}, setAlwaysOnTop: async () => {}, startDragging: async () => {} }) },
  dpi: { LogicalSize: function (w, h) { this.width = w; this.height = h; } },
};
</script>""" % json.dumps(json.dumps(state))

def inline(name, extra_head="", state=SAMPLE):
    html = open(os.path.join(ROOT, "src", name), encoding="utf-8").read()
    html = re.sub(r'<link rel="stylesheet" href="([^"]+)">',
                  lambda m: "<style>" + open(os.path.join(ROOT, "src", m.group(1)), encoding="utf-8").read() + "</style>", html)
    html = re.sub(r'<script src="([^"]+)"></script>',
                  lambda m: "<script>" + open(os.path.join(ROOT, "src", m.group(1)), encoding="utf-8").read().replace("</script", "<\\/script") + "</script>", html)
    html = html.replace("</head>", extra_head + shim(state) + "</head>", 1)
    return html

desk = "<style>body{min-height:100vh;padding:24px;background:linear-gradient(135deg,#3a6186,#89253e)!important}</style>"
open(os.path.join(OUT, "widget-preview.html"), "w", encoding="utf-8").write(inline("index.html", desk))
light = dict(SAMPLE, use24h=False, showSeconds=True, dotColor="#39ff7a", bgOpacity=0.0, dotSize=2, dotShape="square")
open(os.path.join(OUT, "widget-preview-12h.html"), "w", encoding="utf-8").write(inline("index.html", desk, light))
open(os.path.join(OUT, "settings-preview.html"), "w", encoding="utf-8").write(inline("settings.html"))
open(os.path.join(OUT, "settings-preview-firstrun.html"), "w", encoding="utf-8").write(inline("settings.html", "", {"clocks": [{"id": "h", "label": "London, UK", "tz": "Europe/London", "lat": 51.51, "lng": -0.13, "home": True, "auto": True}]}))
print("previews written to", os.path.abspath(OUT))
