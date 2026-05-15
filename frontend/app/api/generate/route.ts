import type { NextRequest } from "next/server";

import type { GenerateRequest } from "@/lib/types";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

const SSE_HEADERS = {
  "Cache-Control": "no-cache, no-transform",
  Connection: "keep-alive",
  "Content-Type": "text/event-stream; charset=utf-8",
} as const;

function buildSseEvent(eventName: string, payload: unknown): string {
  return `event: ${eventName}\ndata: ${JSON.stringify(payload)}\n\n`;
}

function getBackendUrl(): string {
  const backendUrl = process.env.ADK_BACKEND_URL?.trim();

  if (!backendUrl) {
    throw new Error("ADK_BACKEND_URL is not configured.");
  }

  return backendUrl.replace(/\/$/, "");
}

export async function POST(request: NextRequest): Promise<Response> {
  let payload: GenerateRequest;

  try {
    payload = (await request.json()) as GenerateRequest;
  } catch {
    return new Response(
      buildSseEvent("error", {
        error: "The request body must be valid JSON.",
      }),
      {
        status: 400,
        headers: SSE_HEADERS,
      },
    );
  }

  const abortController = new AbortController();
  request.signal.addEventListener("abort", () => abortController.abort());

  let upstreamResponse: Response;

  try {
    upstreamResponse = await fetch(`${getBackendUrl()}/generate`, {
      method: "POST",
      headers: {
        Accept: "text/event-stream",
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
      cache: "no-store",
      signal: abortController.signal,
    });
  } catch (error) {
    return new Response(
      buildSseEvent("error", {
        error:
          error instanceof Error
            ? error.message
            : "The backend generate endpoint could not be reached.",
      }),
      {
        status: 502,
        headers: SSE_HEADERS,
      },
    );
  }

  if (!upstreamResponse.ok || !upstreamResponse.body) {
    const contentType = upstreamResponse.headers.get("content-type") ?? "";

    if (contentType.includes("text/event-stream") && upstreamResponse.body) {
      return new Response(upstreamResponse.body, {
        status: upstreamResponse.status,
        headers: SSE_HEADERS,
      });
    }

    const errorBody = await upstreamResponse.text();

    return new Response(
      buildSseEvent("error", {
        error: errorBody || "The backend generate endpoint returned an error.",
      }),
      {
        status: upstreamResponse.status || 502,
        headers: SSE_HEADERS,
      },
    );
  }

  return new Response(upstreamResponse.body, {
    status: upstreamResponse.status,
    headers: SSE_HEADERS,
  });
}
