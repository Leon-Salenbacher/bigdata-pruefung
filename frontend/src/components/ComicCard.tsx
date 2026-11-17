
import type { Comic } from "../types/Comic";

interface ComicCardProps {
  comic: Comic;
}

export default function ComicCard({
  comic,
}: ComicCardProps) {
  const date =
    comic.year && comic.month && comic.day
      ? `${String(comic.day).padStart(2, "0")}.${String(comic.month).padStart(2, "0")}.${comic.year}`
      : "Unknown date";

  return (
    <article className="comic-card">
      <div className="comic-image-container">
        <img
          src={comic.image_url}
          alt={comic.title}
          loading="lazy"
        />
      </div>

      <div className="comic-content">
        <div className="comic-meta">
          <span>#{comic.num}</span>
          <span>{date}</span>
        </div>

        <h3>{comic.title}</h3>

        <p className="comic-description">
          {comic.alt || "No description available."}
        </p>

        <a
          href={comic.comic_url}
          target="_blank"
          rel="noopener noreferrer"
          className="comic-link"
        >
          View original comic ↗
        </a>
      </div>
    </article>
  );
}
