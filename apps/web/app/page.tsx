"use client";

import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

type DocType = "receipt" | "id";
type ExtractResponse = {
  doc_type: DocType;
  data: Record<string, unknown>;
  confidence: Record<string, number>;
  model: string;
};

const LOW_CONFIDENCE = 0.7;

function Confidence({ value }: { value?: number }) {
  if (value === undefined) return null;
  const level = value >= 0.9 ? "high" : value >= LOW_CONFIDENCE ? "mid" : "low";
  return (
    <span className={`badge ${level}`} title="Model-reported confidence">
      {Math.round(value * 100)}%
    </span>
  );
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [docType, setDocType] = useState<DocType>("receipt");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ExtractResponse | null>(null);

  useEffect(() => {
    if (!file) return setPreview(null);
    const url = URL.createObjectURL(file);
    setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  async function submit() {
    if (!file) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const body = new FormData();
      body.append("file", file);
      const res = await fetch(`${API_URL}/extract?doc_type=${docType}`, { method: "POST", body });
      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail.detail ?? `Request failed (${res.status})`);
      }
      setResult(await res.json());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <h1>Receipt Vision Extractor</h1>
      <p className="muted">Upload a receipt or ID and get structured JSON back.</p>
      <div className="grid">
        <section className="card">
          <div className="row">
            <select value={docType} onChange={(e) => setDocType(e.target.value as DocType)}>
              <option value="receipt">Receipt</option>
              <option value="id">ID document</option>
            </select>
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            />
          </div>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          {preview && <img className="preview" src={preview} alt="Selected upload" />}
          <div className="row" style={{ marginTop: 12 }}>
            <button className="primary" onClick={submit} disabled={!file || loading}>
              {loading ? "Extracting…" : "Extract"}
            </button>
          </div>
          {error && <p className="error">{error}</p>}
        </section>
        <section className="card">
          <h2 style={{ marginTop: 0 }}>Result</h2>
          {!result && <p className="muted">Nothing yet.</p>}
          {result && (
            <>
              <table>
                <tbody>
                  {Object.entries(result.data)
                    .filter(([, v]) => !Array.isArray(v))
                    .map(([k, v]) => (
                      <tr key={k} className={(result.confidence[k] ?? 1) < LOW_CONFIDENCE ? "review" : ""}>
                        <td>{k}</td>
                        <td>{v === null ? <em className="muted">not found</em> : String(v)}</td>
                        <td>
                          <Confidence value={result.confidence[k]} />
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
              {Object.values(result.confidence).some((c) => c < LOW_CONFIDENCE) && (
                <p className="error">Highlighted rows have low confidence. Please review them.</p>
              )}
              <h3>Raw JSON</h3>
              <pre>{JSON.stringify({ data: result.data, confidence: result.confidence }, null, 2)}</pre>
              <small className="muted">model: {result.model}</small>
            </>
          )}
        </section>
      </div>
    </main>
  );
}
