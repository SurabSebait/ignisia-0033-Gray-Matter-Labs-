"use client";

import React, { useState } from "react";

interface FileUploadProps {
  task: "webcrawler" | "disposition";
  llm: "gemini" | "gpt-oss";
  userEmail: string;
  accept?: string;
  onValidate: (file: File) => Promise<boolean>;
}

export default function FileUpload({
  task,
  llm,
  userEmail,
  accept = ".xlsx",
  onValidate
}: FileUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleUpload = async () => {
    if (!file) return; // ✅ first check

    if (onValidate) {
        const isValid = await onValidate(file);
        if (!isValid) return;
        }

    setUploading(true);
    setSuccess(false);

    try {
      const contentType = file.type || "application/octet-stream";

      const fileName = `input/${file.name}`;

      const res = await fetch("/api/gcs/get-signed-url", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          fileName,
          contentType
        })
      });

      const { url } = await res.json();

      const uploadRes = await fetch(url, {
        method: "PUT",
        body: file,
        headers: {
          "Content-Type": contentType
        }
});

      console.log("UPLOAD STATUS:", uploadRes.status);
      console.log("UPLOAD TEXT:", await uploadRes.text());

      if (!uploadRes.ok) throw new Error("Upload failed");

      setSuccess(true);
      setFile(null);

    } catch (err) {
      console.error("Upload error:", err);
      alert("Upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-4">
      <input
        type="file"
        accept={accept}
        onChange={(e) => {
          setFile(e.target.files?.[0] || null);
          setSuccess(false);
        }}
        className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
      />

      <button
        onClick={handleUpload}
        disabled={!file || uploading}
        className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-400"
      >
        {uploading ? "Uploading..." : "Upload & Process"}
      </button>

      {success && (
        <div className="p-4 bg-green-50 text-green-700 rounded-lg text-sm">
          ✅ Uploaded successfully!
        </div>
      )}
    </div>
  );
}