
import { useState } from "react";
import type { FormEvent } from "react";

interface SearchBarProps {
  onSearch: (query: string) => void;
  loading: boolean;
}

export default function SearchBar({
  onSearch,
  loading,
}: SearchBarProps) {
  const [query, setQuery] = useState("");

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmedQuery = query.trim();

    if (!trimmedQuery) {
      return;
    }

    onSearch(trimmedQuery);
  }

  return (
    <form className="search-bar" onSubmit={handleSubmit}>
      <input
        type="search"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="Search comics by title or description..."
        aria-label="Search comics"
      />

      <button
        type="submit"
        disabled={loading || !query.trim()}
      >
        {loading ? "Searching..." : "Search"}
      </button>
    </form>
  );
}
