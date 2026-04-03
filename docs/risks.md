## Structural Issues / Risks

- Early return statements can abort an entire library scan on a single bad item. In the show and music loops, missing ratingKey, failed metadata
  fetches, or missing XML nodes return from the whole handler instead of skipping one item; see plex_poster_downloader/library_handlers.py:49 and
  plex_poster_downloader/library_handlers.py:131.
- Error handling around network/XML parsing is thin. Most requests.get(...) calls have no timeout and XML parsing assumes valid responses; malformed
  Plex responses or transient failures can crash the run rather than degrade cleanly, especially in plex_poster_downloader/plex_api.py:20.
- The code uses module-level env state loaded at import time. That makes config less explicit and harder to test or override cleanly in-process; see
  plex_poster_downloader/config.py:18.
- The show/music path resolution strategy is heuristic. Deriving a show path from the first episode and an artist path from the first album works
  only if library organization is consistent; mixed or irregular folders will produce skips or misplacement.
- Music album matching uses fuzzy matching plus optional rename, which is convenient but carries correctness risk. A weak difflib match can target
  the wrong folder in ambiguous artist directories; see plex_poster_downloader/file_utils.py:97.
- There is no abstraction boundary between Plex API, business rules, and filesystem writes. The code is small enough to manage now, but it will get
  harder to test and extend safely if more media types or behaviors are added.
- No test suite is present in the repo, so regressions around naming/path resolution are likely to surface only against real media libraries.

Net: the architecture is simple and workable for a CLI utility, but it is tightly coupled to Plex XML responses and local folder conventions, with
the biggest immediate risk being whole-run aborts from item-level failures.

## Where it feels weak:

- Error reporting was too compressed. You saw that firsthand.
- The code is tightly coupled to Plex XML responses and folder naming conventions, so it’s brittle around edge cases.
- A few control-flow choices are risky, especially item-level failures returning from whole handlers instead of continuing.
- Config-at-import and limited testability make maintenance harder than it needs to be.

## Things to focus on improving:

1. better diagnostics
2. safer continue-on-error behavior
3. a small test suite around path resolution and output naming
4. optional dry-run mode
