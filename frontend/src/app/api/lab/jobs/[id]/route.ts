import { labRelay } from "@/lib/lab-gateway";
export const dynamic = "force-dynamic";
export const runtime = "nodejs";
export async function GET(request: Request, context: { params: Promise<{ id: string }> }) { return labRelay(request, (await context.params).id); }
