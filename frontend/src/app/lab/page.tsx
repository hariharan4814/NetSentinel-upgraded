import type { Metadata } from "next";
import { LabAccess } from "@/components/lab/workbench";
import "./lab.css";

export const metadata: Metadata = { title: "NetSentinel AI Lab · Explainable traffic experiments", description: "A private simulation workbench for reproducible network machine-learning experiments.", robots: { index: false, follow: false } };
export default function LabPage() { return <div className="lab-root"><LabAccess /></div>; }
