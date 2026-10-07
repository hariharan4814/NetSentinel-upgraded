"""Explicit local lifecycle; no driver installation, automatic elevation or scans."""
import argparse
import json
import os
from pathlib import Path
import secrets
import subprocess
import threading
import urllib.request

from . import __version__
from .windows_security import PowerShellRunner, system_directory


def default_data():
    base = os.environ.get("LOCALAPPDATA")
    if not base:
        raise RuntimeError("LOCALAPPDATA is unavailable; supply --data-dir explicitly")
    return Path(base)/"NetSentinel"/"state"


def initialize(folder):
    folder.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        # A private per-user directory protects credentials and network metadata.
        answer = PowerShellRunner().run("@{sid=[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value} | ConvertTo-Json -Compress")
        sid = answer.get("sid", "")
        import re
        if not re.fullmatch(r"S-1-5-[0-9-]+", sid):
            raise RuntimeError("Cannot establish the local data directory owner")
        process = subprocess.run([str(system_directory()/"icacls.exe"), str(folder), "/inheritance:r", "/grant:r",
                                  "*"+sid+":(OI)(CI)F", "*S-1-5-18:(OI)(CI)F", "*S-1-5-32-544:(OI)(CI)F"],
                                 capture_output=True, timeout=15, creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        if process.returncode:
            raise RuntimeError("Cannot secure the private state directory")
    else:
        folder.chmod(0o700)
    for name in ("access.token", "broker.token"):
        path=folder/name
        if not path.exists():
            with path.open("x",encoding="ascii") as file:
                file.write(secrets.token_hex(32))
            if os.name != "nt":
                path.chmod(0o600)


def key(folder, name):
    value=(folder/name).read_text(encoding="ascii").strip()
    if len(value)!=64 or any(c not in "0123456789abcdef" for c in value):
        raise RuntimeError("Invalid local credential; restore a valid private state directory")
    return value


def main():
    parser=argparse.ArgumentParser(description="NetSentinel Windows companion; explicit local actions only")
    parser.add_argument("command",choices=["init","serve","broker","recover","stop","version","check"])
    parser.add_argument("--data-dir",type=Path)
    parser.add_argument("--port",type=int,default=8765)
    parser.add_argument("--broker-port",type=int,default=8766)
    args=parser.parse_args()
    if not 1024 <= args.port <= 65535 or not 1024 <= args.broker_port <= 65535 or args.port == args.broker_port:
        parser.error("Choose distinct local ports from 1024 to 65535")
    if args.command == "version":
        print("NetSentinel companion "+__version__+" (unsigned source distribution)")
        return
    folder=(args.data_dir or default_data()).resolve()
    if args.command == "init":
        initialize(folder)
        print("Private state initialized. Existing credentials were preserved.")
        return
    if args.command == "check":
        from .windows_security import SecurityProvider
        value=SecurityProvider().status()
        print(json.dumps({"defender":value["defender"].get("state"),"firewall_profiles":value["firewall"]["profiles"],
                          "npcap_standard_path_present":(system_directory()/"Npcap/wpcap.dll").exists()},indent=2))
        return
    if args.command == "recover":
        from .firewall import FirewallController
        result=FirewallController().cleanup()
        print(json.dumps({"success":result["success"],"state":result["state"],"removed_count":len(result["removed"]),"error":result.get("error")},indent=2))
        if not result["success"]:
            raise SystemExit(1)
        return
    if args.command == "broker":
        from .broker import serve_broker
        print("Starting narrow broker on loopback. Only explicitly authorized controls are accepted. Ctrl+C stops and cleans owned rules.")
        serve_broker(key(folder,"broker.token"),args.broker_port)
        return
    if args.command == "stop":
        from .broker import BrokerClient
        from .http_boundary import APIError
        request=urllib.request.Request(f"http://127.0.0.1:{args.port}/api/shutdown",data=b"{}",
                                       headers={"Authorization":"Bearer "+key(folder,"access.token"),"Content-Type":"application/json","Origin":f"http://127.0.0.1:{args.port}"})
        try:
            opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
            with opener.open(request,timeout=30) as response:
                if response.status != 200:
                    raise RuntimeError("Stop request failed")
            print("Companion shutdown requested.")
        except OSError:
            print("Companion is not reachable. Run recover if enforcement was previously enabled.")
        try:
            BrokerClient(key(folder,"broker.token"),args.broker_port).call("shutdown")
        except APIError:
            print("Broker stop unconfirmed. Close its console or run recover to inspect owned rules.")
        return
    from .service import Companion, make_server
    from .store import Store
    from .broker import BrokerClient
    access=key(folder,"access.token")
    broker=key(folder,"broker.token")
    if access == broker:
        raise RuntimeError("Local and broker keys must be distinct")
    store=Store(folder/"companion.sqlite3")
    app=Companion(store,BrokerClient(broker,args.broker_port))
    server=make_server(app,access,args.port)
    worker=threading.Thread(target=app.worker,name="netsentinel-quota-monitor",daemon=True)
    print(f"NetSentinel {__version__} at http://127.0.0.1:{args.port}. Use the private access.token to connect.")
    print("No capture or scan starts automatically. Ctrl+C requests shutdown and owned-rule cleanup.")
    worker.start()
    try:
        server.serve_forever(poll_interval=.3)
    finally:
        app.closed.set()
        worker.join(timeout=30)
        app.stop()
        server.server_close()
        store.close()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("NetSentinel stopped. Check recovery instructions if shutdown was interrupted.")
