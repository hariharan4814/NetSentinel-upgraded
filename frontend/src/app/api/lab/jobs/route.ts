import { labRelay } from "@/lib/lab-gateway";
export const dynamic = "force-dynamic";
export const runtime = "nodejs";
export const GET = (request: Request) => labRelay(request);
export const POST = (request: Request) => labRelay(request);
