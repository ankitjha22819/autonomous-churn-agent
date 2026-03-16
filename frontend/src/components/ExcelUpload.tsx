"use client";

import { useState, useCallback, useRef } from "react";
import * as XLSX from "xlsx";

type JsonRow = Record<string, string | number | boolean | null>;

interface ExcelUploadProps {
  onSubmit: (rows: JsonRow[], file: File) => void;
  onReset: () => void;
  isLoading: boolean;
}

function UploadIcon() {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" className="text-slate-400">
      <path d="M12 4v12M12 4L8 8M12 4l4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

export default function ExcelUpload({ onSubmit, onReset, isLoading }: ExcelUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [rows, setRows] = useState<JsonRow[]>([]);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const processFile = useCallback((f: File) => {
    setError(null);
    if (!f.name.match(/\.(xlsx|xls|csv)$/i)) {
      setError("Only .xlsx, .xls, and .csv files are supported.");
      return;
    }
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = new Uint8Array(e.target?.result as ArrayBuffer);
        const wb = XLSX.read(data, { type: "array" });
        const ws = wb.Sheets[wb.SheetNames[0]];
        const parsed = XLSX.utils.sheet_to_json<JsonRow>(ws, { defval: null, raw: false });
        if (parsed.length === 0) { setError("The sheet appears to be empty."); return; }
        setRows(parsed);
        setFile(f);
      } catch {
        setError("Failed to parse file.");
      }
    };
    reader.readAsArrayBuffer(f);
  }, []);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) processFile(f);
  }, [processFile]);

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) processFile(f);
    e.target.value = "";
  };

  const handleReset = () => {
    setFile(null);
    setRows([]);
    setError(null);
    onReset();
  };

  const columns = Object.keys(rows[0] ?? {});

  return (
    <div className="bg-[#fffffa] shadow-2xl min-h-[400px] rounded-xl border-2 border-slate-500 p-5 flex flex-col">
      <div className="flex items-center gap-2 mb-4">
        <span className="w-5 h-5 rounded-full bg-slate-900 text-white text-xs flex items-center justify-center font-medium">
          1
        </span>
        <h2 className="text-lg font-semibold text-slate-700">Upload data</h2>
      </div>

      {!file ? (
        <>
          <div
            onDrop={onDrop}
            onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onClick={() => fileRef.current?.click()}
            className={`flex flex-col h-[300px] items-center justify-center gap-3 rounded-lg border-2 border-dashed cursor-pointer py-10 transition-colors ${
              dragging
                ? "border-slate-500 bg-slate-50"
                : "border-slate-500 hover:border-slate-300 hover:bg-slate-50"
            }`}
          >
            <UploadIcon />
            <div className="text-center">
              <p className="text-sm text-slate-600">Drop your Excel file here</p>
              <p className="text-xs text-slate-400 mt-0.5">
                or{" "}
                <span className="text-slate-600 underline underline-offset-2">browse</span>
                {" "}· .xlsx .xls .csv
              </p>
            </div>
            <input
              ref={fileRef}
              type="file"
              accept=".xlsx,.xls,.csv"
              onChange={onFileChange}
              className="hidden"
            />
          </div>

          {error && (
            <p className="mt-3 text-xs text-red-500 flex items-center gap-1.5">
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <circle cx="6" cy="6" r="5" stroke="currentColor" strokeWidth="1.2" />
                <path d="M6 3.5V6.5M6 8v.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
              </svg>
              {error}
            </p>
          )}
        </>
      ) : (
        <div className="flex flex-col gap-3 flex-1">

          {/* File info */}
          <div className="flex items-center gap-3 p-3 rounded-lg bg-slate-50 border border-slate-200">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="text-emerald-500 flex-shrink-0">
              <rect x="2" y="1" width="12" height="14" rx="2" stroke="currentColor" strokeWidth="1.2" />
              <path d="M5 5H11M5 8H11M5 11H8" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
            </svg>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-700 truncate">{file.name}</p>
              <p className="text-xs text-slate-400">
                {rows.length} row{rows.length !== 1 ? "s" : ""} · {columns.length} columns
              </p>
            </div>
            <button onClick={handleReset} className="text-slate-400 hover:text-slate-600 transition-colors">
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M2 2l10 10M12 2L2 12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
              </svg>
            </button>
          </div>

          {/* Parsed data table */}
          <div className="flex-1 overflow-auto rounded-lg border border-slate-200 max-h-64">
            <table className="text-xs w-full border-collapse">
              <thead className="sticky top-0 z-10">
                <tr>
                  {columns.map((col) => (
                    <th
                      key={col}
                      className="whitespace-nowrap px-3 py-2 text-left font-medium text-slate-500 bg-slate-100 border-b border-slate-200 border-r last:border-r-0"
                    >
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((row, i) => (
                  <tr key={i} className={i % 2 === 0 ? "bg-white" : "bg-slate-50"}>
                    {columns.map((col) => (
                      <td
                        key={col}
                        className="whitespace-nowrap px-3 py-1.5 text-slate-600 border-b border-slate-100 border-r last:border-r-0"
                      >
                        {row[col] === null || row[col] === "" ? (
                          <span className="text-slate-300">—</span>
                        ) : (
                          String(row[col])
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Submit */}
          <button
            onClick={() => onSubmit(rows, file)}
            disabled={isLoading}
            className="w-full py-2.5 rounded-lg bg-slate-900 text-white text-sm font-medium
                       hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed
                       transition-colors"
          >
            {isLoading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" strokeOpacity="0.25" />
                  <path d="M12 2a10 10 0 0110 10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
                </svg>
                Analysing…
              </span>
            ) : (
              "Run churn analysis"
            )}
          </button>
        </div>
      )}
    </div>
  );
}