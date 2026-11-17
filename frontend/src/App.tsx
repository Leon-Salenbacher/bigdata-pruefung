
import { useEffect, useState } from "react";

import SearchBar from "./components/SearchBar";
import ComicCard from "./components/ComicCard";

import { searchComics } from "./services/comicService";
import type { ComicSearchResponse } from "./types/Comic";

import "./App.css";

const PAGE_SIZE = 20;

export default function App() {
    const [query, setQuery] = useState("")
    const [page, setPage] = useState(1);

    const [data, setData] = useState<ComicSearchResponse | null>(null);

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);


    useEffect(() => {
        if (!query) return;

        const controller = new AbortController();

        setLoading(true);
        setError(null);
        setData(null);

        searchComics(
            query,
            page,
            PAGE_SIZE,
            controller.signal
        )
            .then((result) => {
                if (!controller.signal.aborted) {
                    setData(result);
                }
            })
            .catch((err) => {
                if (!controller.signal.aborted) {
                    setError(
                        err instanceof Error
                            ? err.message
                            : "Search failed."
                    )
                }
            })
            .finally(() => {
                if (!controller.signal.aborted) {
                    setLoading(false);
                }
            })

        return () => controller.abort();
    }, [query, page]);

    function handleSearch(value: string) {
        const nextQuery = value.trim();

        if (nextQuery == query && page === 1) {
            return;
        }

        setPage(1);
        setQuery(nextQuery);
    }

    const totalPages = data
        ? Math.ceil(data.total / PAGE_SIZE)
        : 0;

    return (
        <div className="app">
            <header className="header">
                <div className="container header-content">
                    <div className="brand">
                        <span className="brand-icon">X</span>
                        <span>XKCD Explorer</span>
                    </div>
                    <span className="header-label">Big Data Project</span>
                </div>
            </header>

            <main className="container">
                <section className="hero">
                    <span className="eyebrow">
                        COMIC DATABASE
                    </span>

                    <h1>Explore the XKCD universe.</h1>

                    <p>
                        Search through XKCD comics and discover ideas about science, technology, mathematics and more.
                    </p>

                    <SearchBar
                        onSearch={handleSearch}
                        loading={loading}
                    />
                </section>
                <section className="results-section">
                    <div className="results-header">
                        <div>
                            <h2>Search Results</h2>

                            {query && (
                                <p>
                                    Results for <strong>"{query}"</strong>
                                </p>
                            )}
                        </div>

                        {data && (
                            <span className="result-count">{data.total} results</span>
                        )}
                    </div>

                    {loading && (
                        <div className="state-message" role="status">
                            Searching comics...
                        </div>
                    )}

                    {error && (
                        <div className="state-message error" role="alert">
                            {error}
                        </div>
                    )}


                    {!query && (
                        <div className="state-message">
                            Enter a search term to discover comics.
                        </div>
                    )}

                    {!loading && !error &&
                        data?.results.length === 0 && (
                            <div className="state-message">
                                No comics found.
                            </div>
                        )}

                    {!loading && !error && data && (
                        <>
                            <div className="comic-grid">
                                {data.results.map((comic) => (
                                    <ComicCard
                                        key={comic.num}
                                        comic={comic}
                                    />
                                ))}
                            </div>

                            {totalPages > 1 && (
                                <nav
                                    className="pagination"
                                    aria-label="Search result pages"
                                >
                                    <button
                                        disabled={page === 1}
                                        onClick={() => setPage(page - 1)}
                                    >Previous</button>
                                    <span>Page {page} of {totalPages}</span>

                                    <button
                                        disabled={page >= totalPages}
                                        onClick={() => setPage(page + 1)}
                                    >
                                        Next
                                    </button>
                                </nav>
                            )}
                        </>
                    )}
                </section>
            </main>
            <footer className="footer">
                XKCD Explorer · Big Data Practical Exam
            </footer>
        </div>
    )
}