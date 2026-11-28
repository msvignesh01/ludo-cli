"use client";

import { useEffect } from "react";

export default function ErrorPage({ error, reset }: { error: Error; reset: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <main className="errorPage">
      <p className="eyebrow">Table interrupted</p>
      <h1>The match screen could not be opened.</h1>
      <p>Your saved match is still in this browser. Reload the table to try again.</p>
      <button className="button buttonPrimary" type="button" onClick={reset}>
        Reload the table
      </button>
    </main>
  );
}
