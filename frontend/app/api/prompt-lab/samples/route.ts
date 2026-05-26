import type { PromptLabSampleInput } from "@/lib/types";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

function getBackendUrl(): string {
  const backendUrl = process.env.ADK_BACKEND_URL?.trim();

  if (!backendUrl) {
    throw new Error("ADK_BACKEND_URL is not configured.");
  }

  return backendUrl.replace(/\/$/, "");
}

export async function GET(): Promise<Response> {
  let upstreamResponse: Response;

  try {
    upstreamResponse = await fetch(`${getBackendUrl()}/prompt-lab/samples`, {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
      cache: "no-store",
    });
  } catch (error) {
    return Response.json(
      {
        error:
          error instanceof Error
            ? error.message
            : "The backend prompt-lab samples endpoint could not be reached.",
      },
      { status: 502 },
    );
  }

  if (!upstreamResponse.ok) {
    const errorBody = await upstreamResponse.text();
    return Response.json(
      {
        error:
          errorBody ||
          "The backend prompt-lab samples endpoint returned an error.",
      },
      { status: upstreamResponse.status || 502 },
    );
  }

  const payload = (await upstreamResponse.json()) as PromptLabSampleInput[];
  return Response.json(payload, { status: upstreamResponse.status });
}
