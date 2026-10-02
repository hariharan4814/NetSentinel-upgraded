from datetime import datetime, timezone
from io import BytesIO
import unittest

from companion.reports import create_report
from companion.store import Store
from sensor.models import PacketMetadata


def fixture():
    now = datetime(2026,10,2,12,tzinfo=timezone.utc).timestamp()
    store = Store(":memory:", lambda: now)
    for i in range(45):
        app = store.discover(r"C:\PrivateFixture\An intentionally long demonstration executable name with spaces " + str(i) + ".exe")
        packet = PacketMetadata(now-60, "SIMULATION-fixture", "192.0.2.1", "198.51.100.10",1200,443,"TCP",(i+1)*1024,"outbound")
        store.record([(app,packet)],"SIMULATION")
    result = store.snapshot("SIMULATION")
    result["capture"] = {"state":"SIMULATION fixture","last_packet_at":now-60}
    result["security"] = None
    store.close()
    return result


class ReportTests(unittest.TestCase):
    def test_pdf_is_semantic_paginated_and_sensitive_by_explicit_choice(self):
        try:
            from pypdf import PdfReader
        except ImportError:
            self.skipTest("pypdf is a QA-only dependency; install separately to inspect semantic output")
        data=fixture()
        for private in (False,True):
            output=create_report(data,["usage","connections","security","actions"],private)
            self.assertTrue(output.startswith(b"%PDF-"))
            reader=PdfReader(BytesIO(output))
            self.assertGreater(len(reader.pages),2)
            text="\n".join(page.extract_text() for page in reader.pages)
            for expected in ("SIMULATION", "LABELLED TEST DATA", "No Defender or firewall claim", "Rule application is not verified"):
                self.assertIn(expected,text)
            self.assertEqual("198.51.100.10" in text,private)
            self.assertEqual("privatefixture" in text.lower(),private)
            self.assertIn("Page 1",reader.pages[0].extract_text())

    def test_unknown_provenance_rejected(self):
        with self.assertRaises(ValueError):
            create_report({"mode":"DEMO"},["usage"])


if __name__ == "__main__":
    unittest.main()
