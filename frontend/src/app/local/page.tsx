import { LocalAccess } from "@/components/local-access";
import Link from "next/link";
import "../globals.css";

export default function LocalMonitor() {
  return <><Link href="/" style={{ display: "block", padding: "12px 24px", background: "#d9eeea", color: "#163438" }}>← Back to the connection helper · Advanced local monitor</Link><LocalAccess /></>;
}
