"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { readFile } from "fs/promises";
import { useEffect, useState } from "react";

export default function TermsOfServicePage() {
  const [content, setContent] = useState<string>("");

  useEffect(() => {
    // In a real app, fetch from API or use static import
    fetch("/api/legal/terms")
      .then((res) => res.text())
      .then((text) => setContent(text))
      .catch(() => {
        // Fallback to placeholder
        setContent("Terms of Service content will be loaded here.");
      });
  }, []);

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <Card>
        <CardHeader>
          <CardTitle className="text-3xl">Terms of Service</CardTitle>
          <p className="text-muted-foreground">Last Updated: January 2025</p>
        </CardHeader>
        <CardContent>
          <div
            className="prose prose-sm max-w-none dark:prose-invert"
            dangerouslySetInnerHTML={{
              __html: content
                .split("\n")
                .map((line) => {
                  if (line.startsWith("# ")) {
                    return `<h1>${line.substring(2)}</h1>`;
                  } else if (line.startsWith("## ")) {
                    return `<h2>${line.substring(3)}</h2>`;
                  } else if (line.startsWith("### ")) {
                    return `<h3>${line.substring(4)}</h3>`;
                  } else if (line.startsWith("**") && line.endsWith("**")) {
                    return `<p><strong>${line.substring(2, line.length - 2)}</strong></p>`;
                  } else if (line.trim() === "") {
                    return "<br/>";
                  } else {
                    return `<p>${line}</p>`;
                  }
                })
                .join("")
            }}
          />
        </CardContent>
      </Card>
    </div>
  );
}

