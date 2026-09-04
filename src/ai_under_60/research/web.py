"""Live web research provider implementing web search, page fetching, and evidence extraction."""

from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
import re
from typing import Any, Callable, Dict, List, Optional, Set
import urllib.parse
import urllib.request

from ai_under_60.logger import setup_logger
from ai_under_60.research.models import (
    Claim,
    Evidence,
    ResearchPackage,
    Source,
    VALID_SOURCE_QUALITIES,
)
from ai_under_60.research.request import ResearchRequest

logger = setup_logger("ai_under_60.research.web")

# Standard user-agent to ensure search engine and web pages return standard HTML
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

# Basic English stop words for keyword extraction
STOP_WORDS: Set[str] = frozenset({
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't",
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
    "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i",
    "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's",
    "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
    "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
    "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
    "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
    "they've", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
    "weren't", "what", "what's", "when", "when's", "where", "where's", "which",
    "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
    "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours",
    "yourself", "yourselves", "vs", "versus", "meet", "dead",
})

# ---------------------------------------------------------------------------
# Deterministic domain lists for source quality classification.
# Conservative: only well-known domains are listed; everything else defaults to
# general_secondary. This list MUST NOT be expanded to include unknown domains.
# ---------------------------------------------------------------------------

_REPUTABLE_SECONDARY_DOMAINS: Set[str] = frozenset({
    # Major news / media
    "time.com", "bbc.com", "bbc.co.uk", "nytimes.com", "washingtonpost.com",
    "theguardian.com", "reuters.com", "apnews.com", "bloomberg.com",
    "wsj.com", "ft.com", "forbes.com", "fortune.com", "economist.com",
    "wired.com", "techcrunch.com", "theverge.com", "arstechnica.com",
    "zdnet.com", "cnet.com", "engadget.com", "venturebeat.com",
    "mit.edu", "stanford.edu", "harvard.edu", "nature.com", "sciencemag.org",
    "scientificamerican.com", "newscientist.com",
    # Official/government-adjacent
    "nist.gov", "nasa.gov", "nih.gov", "cdc.gov", "who.int", "un.org",
    "europa.eu", "gov.uk",
})

_USER_GENERATED_DOMAINS: Set[str] = frozenset({
    "linkedin.com", "twitter.com", "x.com", "facebook.com", "instagram.com",
    "reddit.com", "quora.com", "medium.com", "substack.com", "tumblr.com",
    "youtube.com", "tiktok.com", "pinterest.com",
})


def classify_source_quality(url: str) -> str:
    """Classify a source URL into a quality tier deterministically.

    Classification is conservative and based solely on domain pattern matching.
    No external calls, no LLM, no semantic analysis.

    Categories (values are members of VALID_SOURCE_QUALITIES):
        primary            – Official docs, specification bodies, primary datasets
                             (currently unused; reserved for future explicit tagging).
        reputable_secondary – Well-known established news, academic, or government domains.
        general_secondary   – Other retrievable web pages from unknown/unlisted domains.
        user_generated      – Social networks, forums, personal posts, aggregated feeds.
        unknown             – URL could not be parsed or domain could not be determined.

    Args:
        url: Any URL string (normalized or raw).

    Returns:
        One of the VALID_SOURCE_QUALITIES strings.
    """
    if not url or not isinstance(url, str):
        return "unknown"

    try:
        parsed = urllib.parse.urlparse(url)
        host = parsed.netloc.lower()
        if not host:
            return "unknown"
        # Strip leading www.
        if host.startswith("www."):
            host = host[4:]
    except Exception:
        return "unknown"

    if host in _USER_GENERATED_DOMAINS:
        return "user_generated"

    # Check reputable list by exact domain or subdomain suffix
    # e.g. "blog.mit.edu" matches "mit.edu"
    for reputable in _REPUTABLE_SECONDARY_DOMAINS:
        if host == reputable or host.endswith("." + reputable):
            return "reputable_secondary"

    return "general_secondary"




def normalize_url(raw_url: str) -> str:
    """Normalize and validate a URL by stripping fragments and standardizing components.

    Args:
        raw_url: Candidate URL string.

    Returns:
        Clean normalized URL string, or empty string if invalid.
    """
    if not raw_url or not isinstance(raw_url, str):
        return ""

    url = raw_url.strip()
    # Decode DuckDuckGo redirect wrapper if present
    if "uddg=" in url:
        match = re.search(r"uddg=([^&]+)", url)
        if match:
            url = urllib.parse.unquote(match.group(1))

    try:
        parsed = urllib.parse.urlparse(url)
    except Exception:
        return ""

    if parsed.scheme.lower() not in ("http", "https") or not parsed.netloc:
        return ""

    # Normalize: lowercase scheme and host, drop fragment
    clean_scheme = parsed.scheme.lower()
    clean_netloc = parsed.netloc.lower()
    clean_path = parsed.path.rstrip("/") if parsed.path != "/" else "/"
    clean_query = parsed.query

    normalized = urllib.parse.urlunparse((
        clean_scheme,
        clean_netloc,
        clean_path,
        "",  # params
        clean_query,
        "",  # fragment dropped
    ))
    return normalized


def extract_publisher(url: str) -> str:
    """Derive publisher or domain name from a URL.

    Args:
        url: Valid URL string.

    Returns:
        Clean publisher string.
    """
    try:
        parsed = urllib.parse.urlparse(url)
        host = parsed.netloc.lower()
        # Remove common 'www.' prefix
        if host.startswith("www."):
            host = host[4:]
        return host or "Web Source"
    except Exception:
        return "Web Source"


def generate_search_queries(request: ResearchRequest, max_queries: int = 4) -> List[str]:
    """Generate 3-5 focused search queries from a research request.

    Args:
        request: The validated research request.
        max_queries: Maximum number of queries to generate (default: 4).

    Returns:
        List of distinct search queries.
    """
    queries: List[str] = []

    # 1. Topic query
    if request.topic.strip():
        queries.append(request.topic.strip())

    # 2. Title query cleaned of punctuation/clickbait
    clean_title = re.sub(r"[^\w\s-]", "", request.title).strip()
    if clean_title and clean_title.lower() != request.topic.lower():
        queries.append(clean_title)

    # 3. Key point queries (concise keyword phrases)
    for point in request.key_points:
        words = [
            w for w in re.findall(r"\b[A-Za-z]{3,}\b", point)
            if w.lower() not in STOP_WORDS
        ]
        if words:
            # Combine topic context with key words from point
            query_phrase = " ".join(words[:5])
            if query_phrase and query_phrase not in queries:
                queries.append(query_phrase)
        if len(queries) >= max_queries:
            break

    # Deduplicate preserving order
    seen: Set[str] = set()
    deduped: List[str] = []
    for q in queries:
        low = q.lower()
        if low not in seen:
            seen.add(low)
            deduped.append(q)

    return deduped[:max_queries]


def extract_text_from_html(html_content: str) -> str:
    """Extract readable plaintext from HTML by stripping markup, scripts, and navigation.

    Args:
        html_content: Raw HTML document string.

    Returns:
        Normalized clean plaintext.
    """
    if not html_content or not isinstance(html_content, str):
        return ""

    # Remove HTML comments
    text = re.sub(r"<!--.*?-->", "", html_content, flags=re.DOTALL)

    # Remove script, style, nav, header, footer, noscript tags and contents
    text = re.sub(
        r"<(script|style|nav|header|footer|noscript|svg|aside)[^>]*>.*?</\1>",
        " ",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    # Replace block elements with newlines to preserve sentence separation
    text = re.sub(r"<(p|div|h\d|li|br|tr)[^>]*>", "\n", text, flags=re.IGNORECASE)

    # Remove all remaining HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Unescape HTML entities (e.g. &amp;, &quot;, &#39;)
    text = unescape(text)

    # Collapse multiple whitespace characters to single spaces, preserving clean text
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    clean_text = " ".join(line for line in lines if line)
    return clean_text.strip()


def search_duckduckgo(
    query: str,
    timeout: int = 10,
    user_agent: str = DEFAULT_USER_AGENT,
) -> List[Dict[str, str]]:
    """Execute a web search via DuckDuckGo HTML search and parse result snippets.

    Args:
        query: Search query string.
        timeout: HTTP timeout in seconds.
        user_agent: User agent header for request.

    Returns:
        List of dicts with 'title', 'url', 'snippet', 'publisher'.
    """
    encoded_query = urllib.parse.quote(query.strip())
    search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

    req = urllib.request.Request(
        search_url,
        headers={"User-Agent": user_agent},
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception as err:
        logger.warning("Search request failed for query '%s': %s", query, err)
        return []

    results: List[Dict[str, str]] = []

    # Pattern for DuckDuckGo HTML results:
    # <h2 class="result__title"><a class="result__a" href="[HREF]">[TITLE]</a></h2>
    # followed by optional snippet in <a class="result__snippet" ...>[SNIPPET]</a>
    pattern = re.compile(
        r'<h2[^>]*class="[^"]*result__title[^"]*"[^>]*>\s*'
        r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>.*?'
        r'(?:<a[^>]+class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</a>)?',
        re.DOTALL | re.IGNORECASE,
    )

    for match in pattern.finditer(html):
        raw_href = match.group(1) or ""
        raw_title = match.group(2) or ""
        raw_snippet = match.group(3) or ""

        url = normalize_url(raw_href)
        if not url:
            continue

        clean_title = re.sub(r"<[^>]+>", "", raw_title).strip()
        clean_title = unescape(clean_title) or "Web Source"
        clean_snippet = re.sub(r"<[^>]+>", "", raw_snippet).strip()
        clean_snippet = unescape(clean_snippet)

        results.append({
            "title": clean_title,
            "url": url,
            "snippet": clean_snippet,
            "publisher": extract_publisher(url),
        })

    return results


def fetch_source_text(
    url: str,
    timeout: int = 8,
    user_agent: str = DEFAULT_USER_AGENT,
) -> Optional[str]:
    """Fetch an external web page and extract clean plaintext.

    Args:
        url: Absolute HTTP/HTTPS URL.
        timeout: Request timeout in seconds.
        user_agent: User-Agent string.

    Returns:
        Clean plaintext content or None if fetch fails.
    """
    req = urllib.request.Request(
        url,
        headers={"User-Agent": user_agent},
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content_type = resp.headers.get("Content-Type", "").lower()
            # Only process HTML/text responses
            if content_type and "text" not in content_type and "html" not in content_type:
                logger.debug("Skipping non-text content-type '%s' for '%s'", content_type, url)
                return None

            raw_bytes = resp.read(500_000)  # Read at most 500KB to stay bounded
            html = raw_bytes.decode("utf-8", errors="ignore")
            text = extract_text_from_html(html)
            return text if len(text) >= 50 else None
    except Exception as err:
        logger.debug("Failed to fetch source page '%s': %s", url, err)
        return None


def _looks_like_noise(sentence: str) -> bool:
    """Return True if a sentence appears to be navigation, feed, or sidebar noise.

    This is a conservative heuristic — when in doubt, return False so that
    genuine evidence is not discarded. Only flag text that strongly resembles
    structured UI noise rather than prose.

    Noise patterns detected:
    1. High proportion of numeric/short-code tokens with low real-word density
       (e.g. menus, item lists, counters).
    2. Sentence begins with a social-media-style time abbreviation (e.g. "1y", "2h",
       "3d", "4w") — strongly characteristic of feed/notification artifacts such as
       LinkedIn post previews: "1y 9 AI Tools I Use to Run a Growth System in 2026".

    Args:
        sentence: A candidate plaintext excerpt.

    Returns:
        True only if the sentence is confidently noise; False otherwise.
    """
    tokens = sentence.split()
    if not tokens:
        return True

    total = len(tokens)

    # Pattern 2: sentences starting with a social-media time-ago token (e.g. "1y", "2h", "3d")
    # This is a very strong signal of feed/notification content, not article prose.
    if re.fullmatch(r"\d+[ymwdh]", tokens[0], re.IGNORECASE):
        return True

    # Pattern 1: high numeric/short-code token density with low real-word ratio
    # Count tokens that are purely numeric or a digit+letter abbreviation like "1y", "2h"
    short_or_numeric = sum(
        1 for t in tokens
        if re.fullmatch(r"\d+[a-z]?", t, re.IGNORECASE)
    )
    # Fraction of tokens that are meaningful alpha words (3+ letters)
    alpha_tokens = sum(1 for t in tokens if re.fullmatch(r"[A-Za-z]{3,}.*", t))
    alpha_ratio = alpha_tokens / total

    # If more than 30% of tokens are numeric/short-code AND fewer than 50% are real words,
    # treat as noise. This catches dense numeric lists without affecting normal prose.
    if short_or_numeric / total > 0.30 and alpha_ratio < 0.50:
        return True

    return False



def find_evidence_in_text(
    text: str,
    source_url: str,
    statement: str,
    min_keyword_matches: int = 2,
    max_excerpts: int = 2,
) -> List[Evidence]:
    """Search extracted text for factual excerpts relevant to a statement.

    Args:
        text: Plaintext content of a retrieved source.
        source_url: Exact URL where text originated.
        statement: The factual statement or key point to verify.
        min_keyword_matches: Minimum distinctive keyword hits to consider an excerpt relevant.
        max_excerpts: Maximum number of evidence excerpts to extract per source.

    Returns:
        List of verified Evidence objects originating from the source text.
        Sentences identified as navigation/feed noise are silently excluded.
    """
    if not text or not statement:
        return []

    # Extract distinctive alphanumeric keywords from statement
    keywords = [
        w.lower()
        for w in re.findall(r"\b[A-Za-z]{3,}\b", statement)
        if w.lower() not in STOP_WORDS
    ]
    if not keywords:
        return []

    # Split text into sentences (delimiters: . ! ? followed by space)
    raw_sentences = re.split(r"(?<=[.!?])\s+", text)
    matches: List[Evidence] = []

    for sentence in raw_sentences:
        clean_sentence = sentence.strip()
        if len(clean_sentence) < 30 or len(clean_sentence) > 500:
            continue

        # Reject obvious navigation/feed noise before keyword matching
        if _looks_like_noise(clean_sentence):
            logger.debug("Evidence noise filter rejected: %r", clean_sentence[:80])
            continue

        sentence_lower = clean_sentence.lower()
        matched_words = [kw for kw in keywords if kw in sentence_lower]

        if len(matched_words) >= min_keyword_matches:
            relevance = (
                f"Excerpt contains key terms [{', '.join(matched_words[:4])}] "
                f"relevant to '{statement[:50]}...'"
            )
            matches.append(
                Evidence(
                    source_url=source_url,
                    excerpt=clean_sentence[:300],
                    relevance=relevance,
                )
            )
            if len(matches) >= max_excerpts:
                break

    return matches




class WebResearchProvider:
    """Real web research provider gathering live evidence and assessing claims.

    Adheres strictly to the project integrity rule:
    - Never fabricates URLs, publishers, excerpts, or citations.
    - Every Source and Evidence object originates from actual retrieved web content.
    - Claims without factual evidence are marked 'unsupported' with empty evidence.
    """

    def __init__(
        self,
        search_fn: Optional[Callable[[str, int], List[Dict[str, str]]]] = None,
        page_fetcher: Optional[Callable[[str, int], Optional[str]]] = None,
        max_queries: int = 4,
        max_sources: int = 5,
        request_timeout: int = 8,
    ) -> None:
        """Initialize WebResearchProvider with optional dependency injection for testing.

        Args:
            search_fn: Search function (query, timeout) -> list of result dicts.
            page_fetcher: Page fetcher function (url, timeout) -> plaintext or None.
            max_queries: Maximum number of search queries generated per request.
            max_sources: Maximum number of distinct source pages fetched.
            request_timeout: HTTP timeout in seconds for search and page fetches.
        """
        self._search_fn = search_fn if search_fn is not None else search_duckduckgo
        self._page_fetcher = page_fetcher if page_fetcher is not None else fetch_source_text
        self._max_queries = max_queries
        self._max_sources = max_sources
        self._timeout = request_timeout

    def research(self, request: ResearchRequest) -> ResearchPackage:
        """Conduct live web research for the given ResearchRequest.

        Pipeline:
        1. Generate 3-5 focused search queries from topic, title, and key points.
        2. Perform web search and collect candidate URLs.
        3. Deduplicate URLs across queries.
        4. Fetch top source pages (bounded, timeout handled, no infinite retries).
        5. Extract clean plaintext from pages.
        6. Search extracted text for real evidence matching request key points.
        7. Evaluate claims conservatively (supported, uncertain, unsupported).
        8. Return validated ResearchPackage.

        Args:
            request: Validated ResearchRequest.

        Returns:
            Validated ResearchPackage containing real sources and verified claims.

        Raises:
            TypeError: If request is not an instance of ResearchRequest.
        """
        if not isinstance(request, ResearchRequest):
            raise TypeError(f"Expected ResearchRequest instance, got {type(request).__name__}.")

        logger.info("Starting live web research for topic: '%s'.", request.topic)

        # Step A: Generate search queries
        queries = generate_search_queries(request, max_queries=self._max_queries)
        logger.debug("Generated %d search queries: %s", len(queries), queries)

        # Step B & C: Search & Deduplicate candidate results
        candidate_sources: Dict[str, Dict[str, str]] = {}
        for q in queries:
            try:
                results = self._search_fn(q, self._timeout)
                for item in results:
                    url = normalize_url(item.get("url", ""))
                    if url and url not in candidate_sources:
                        candidate_sources[url] = {
                            "title": item.get("title", "Web Source"),
                            "url": url,
                            "publisher": item.get("publisher") or extract_publisher(url),
                            "snippet": item.get("snippet", ""),
                        }
                    if len(candidate_sources) >= self._max_sources * 2:
                        break
            except Exception as err:
                logger.warning("Search query '%s' encountered an error: %s", q, err)

            if len(candidate_sources) >= self._max_sources * 2:
                break

        # Step D & E: Fetch top bounded source pages and extract text
        sources: List[Source] = []
        source_texts: Dict[str, str] = {}
        retrieved_timestamp = datetime.now(timezone.utc).isoformat()

        for url, meta in list(candidate_sources.items())[:self._max_sources]:
            logger.debug("Fetching source page: '%s'", url)
            page_text = None
            try:
                page_text = self._page_fetcher(url, self._timeout)
            except Exception as err:
                logger.debug("Could not fetch page '%s': %s", url, err)

            # If page text was fetched successfully, register Source and text
            if page_text and len(page_text) >= 50:
                source = Source(
                    title=meta["title"],
                    url=url,
                    publisher=meta["publisher"],
                    retrieved_at=retrieved_timestamp,
                    source_quality=classify_source_quality(url),
                )
                sources.append(source)
                source_texts[url] = page_text
            elif meta.get("snippet") and len(meta["snippet"]) >= 40:
                # Fallback: use actual search snippet if page body was blocked/inaccessible
                source = Source(
                    title=meta["title"],
                    url=url,
                    publisher=meta["publisher"],
                    retrieved_at=retrieved_timestamp,
                    source_quality=classify_source_quality(url),
                )
                sources.append(source)
                source_texts[url] = meta["snippet"]

        logger.info("Successfully retrieved and extracted text from %d web sources.", len(sources))

        # Step F: Evaluate claims against real extracted evidence
        claims: List[Claim] = []
        for point in request.key_points:
            point_evidence: List[Evidence] = []

            for source in sources:
                text = source_texts.get(source.url, "")
                if text:
                    found = find_evidence_in_text(
                        text=text,
                        source_url=source.url,
                        statement=point,
                        min_keyword_matches=2,
                        max_excerpts=2,
                    )
                    point_evidence.extend(found)

            # Assess claim status conservatively
            if len(point_evidence) >= 2:
                status = "supported"
            elif len(point_evidence) == 1:
                status = "uncertain"
            else:
                status = "unsupported"
                point_evidence = []

            claims.append(
                Claim(
                    statement=point,
                    status=status,
                    evidence=point_evidence,
                )
            )

        # Step G: Build honest ResearchPackage summary
        supported_count = sum(1 for c in claims if c.status == "supported")
        uncertain_count = sum(1 for c in claims if c.status == "uncertain")
        unsupported_count = sum(1 for c in claims if c.status == "unsupported")

        if sources:
            summary = (
                f"Live web research for '{request.title}'. "
                f"Retrieved {len(sources)} web sources across {len(queries)} search queries. "
                f"Evaluated {len(claims)} claim(s): {supported_count} supported, "
                f"{uncertain_count} uncertain, {unsupported_count} unsupported."
            )
        else:
            summary = (
                f"Live web research for '{request.title}' yielded no accessible web sources. "
                f"All {len(claims)} claim(s) remain unsupported."
            )

        return ResearchPackage(
            topic=request.topic,
            sources=sources,
            claims=claims,
            summary=summary,
        )
