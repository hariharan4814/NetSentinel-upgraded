"""Build a reviewed source installer ZIP; no credentials, data, envs or drivers."""
import hashlib
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parent.parent
VERSION = "0.2.0"
PYTHON_FILES = ["__init__.py","__main__.py","identity.py","attribution.py","store.py","collector.py","http_boundary.py","broker.py","service.py","firewall.py","windows_security.py","reports.py"]
SENSOR_FILES = ["__init__.py","models.py","normalize.py","capture.py","flows.py","interfaces.py","counters.py","features.py"]


def build():
    files = {"companion/"+name:ROOT/"companion"/name for name in PYTHON_FILES}
    files.update({"companion/web/"+name:ROOT/"companion/web"/name for name in ["index.html","app.js","style.css"]})
    files.update({"sensor/"+name:ROOT/"sensor"/name for name in SENSOR_FILES})
    for name in ["Install.ps1","Start.ps1","Stop.ps1","Start-Broker.ps1","Recover.ps1","Uninstall.ps1","Show-Access-Key.ps1"]:
        files[name] = ROOT/"companion/packaging"/name
    files.update({"requirements-companion.txt":ROOT/"requirements-companion.txt", "requirements-companion.lock":ROOT/"requirements-companion.lock",
                  "README.md":ROOT/"docs/COMPANION_SETUP.md", "UPGRADE.md":ROOT/"docs/COMPANION_UPGRADE.md",
                  "THIRD_PARTY_NOTICES.txt":ROOT/"companion/THIRD_PARTY_NOTICES.txt"})
    for name, path in files.items():
        if not path.is_file() or path.is_symlink():
            raise RuntimeError("Missing or indirect package input: "+name)
        if path.suffix in {".token",".sqlite3",".pcap",".zip"} or ".env" in path.name:
            raise RuntimeError("Forbidden package input")
    output = ROOT/"output/releases"
    output.mkdir(parents=True,exist_ok=True)
    archive=output/f"NetSentinel-Companion-{VERSION}.zip"
    with zipfile.ZipFile(archive,"w",compression=zipfile.ZIP_DEFLATED,compresslevel=9) as bundle:
        for name,path in sorted(files.items()):
            info=zipfile.ZipInfo(name,date_time=(2026,10,2,0,0,0))
            info.compress_type=zipfile.ZIP_DEFLATED
            bundle.writestr(info,path.read_bytes())
        bundle.writestr(zipfile.ZipInfo("VERSION",date_time=(2026,10,2,0,0,0)),VERSION+"\n")
    digest=hashlib.sha256(archive.read_bytes()).hexdigest()
    archive.with_suffix(".zip.sha256").write_text(digest+"  "+archive.name+"\n",encoding="ascii")
    print(f"{archive.name}: {archive.stat().st_size} bytes; {len(files)+1} allowlisted files; SHA-256 {digest}")


if __name__=="__main__":
    build()
