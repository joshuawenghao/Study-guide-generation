"use client";

import { useState } from "react";

import type { DownloadButtonProps } from "@/lib/types";

function sanitizeFilename(filename: string): string {
  const trimmed = filename.trim();

  if (trimmed.length === 0) {
    return "study-guide.pdf";
  }

  const normalized = trimmed.replace(/[^a-zA-Z0-9._-]+/g, "-");
  const withExtension = normalized.toLowerCase().endsWith(".pdf")
    ? normalized
    : `${normalized}.pdf`;

  return withExtension.replace(/-+/g, "-");
}

function decodePdfBase64(pdfBase64: string): Uint8Array {
  const binary = window.atob(pdfBase64);
  const bytes = new Uint8Array(binary.length);

  for (let index = 0; index < binary.length; index += 1) {
    bytes[index] = binary.charCodeAt(index);
  }

  return bytes;
}

export default function DownloadButton({
  pdfBase64,
  filename,
}: DownloadButtonProps) {
  const [downloadError, setDownloadError] = useState<string | null>(null);

  function handleDownload() {
    if (!pdfBase64.trim()) {
      setDownloadError("The generated PDF is not available yet.");
      return;
    }

    try {
      const bytes = decodePdfBase64(pdfBase64);
      const pdfBuffer = new ArrayBuffer(bytes.byteLength);
      new Uint8Array(pdfBuffer).set(bytes);
      const blob = new Blob([pdfBuffer], { type: "application/pdf" });
      const objectUrl = URL.createObjectURL(blob);
      const link = document.createElement("a");

      link.href = objectUrl;
      link.download = sanitizeFilename(filename);
      link.rel = "noopener";
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(objectUrl);
      setDownloadError(null);
    } catch {
      setDownloadError(
        "The PDF could not be prepared for download. Try generating it again.",
      );
    }
  }

  return (
    <div className="space-y-3">
      <button
        type="button"
        onClick={handleDownload}
        className="inline-flex w-full items-center justify-center rounded-full bg-slate-950 px-5 py-3 text-sm font-semibold text-white transition hover:bg-cyan-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-cyan-700 sm:w-auto"
      >
        Download PDF
      </button>

      {downloadError ? (
        <p className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm leading-6 text-rose-700">
          {downloadError}
        </p>
      ) : (
        <p className="text-sm leading-6 text-slate-600">
          Downloads the generated guide as a PDF file.
        </p>
      )}
    </div>
  );
}
