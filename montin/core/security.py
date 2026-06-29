"""
montin.core.security
======================
Opt-in security / privacy hardening for a generated report, grouped into one
:class:`Security` object passed as ``Deck(security=...)``.

Montin's whole point is a report that transfers **no data** and works fully
offline. These switches let you turn that into an enforced, verifiable property
instead of just a default. Every field is documented in plain language because
the underlying web terms (CSP, SRI, Permissions-Policy) are easy to misjudge —
see each attribute below and ``docs/sections/security.md``.
"""

from __future__ import annotations

from dataclasses import dataclass

# Strict Content-Security-Policy used by ``block_external``. ``default-src
# 'none'`` forbids every network destination (scripts, styles, images, fonts,
# XHR/fetch/websockets, frames...) unless re-allowed below. We re-allow only
# *inline* code and ``data:`` URIs — never an external origin — because Montin
# inlines its own JS/CSS and embeds images as data URIs. The net effect: the
# page cannot make a single outbound request, so it cannot leak data or phone
# home, even when double-clicked from disk.
STRICT_CSP = (
    "default-src 'none'; "
    "script-src 'unsafe-inline'; "
    "style-src 'unsafe-inline'; "
    "img-src data: blob:; "
    "font-src data:; "
    "media-src data: blob:; "
    "connect-src 'none'; "
    "base-uri 'none'; "
    "form-action 'none'"
)

# Sensible default for ``permissions_policy=True``: declare that the report needs
# none of these device features.
DEFAULT_PERMISSIONS_POLICY = (
    "camera=(), microphone=(), geolocation=(), "
    "usb=(), payment=(), interest-cohort=()"
)


@dataclass
class Security:
    """Security / privacy options for a report.

    The default ``Security()`` applies light, always-safe hardening (a
    no-referrer hint, a Permissions-Policy declaration, and integrity hashes on
    any CDN-loaded library). The strong guarantee — a report that provably makes
    no external request — is the opt-in ``block_external``.

    Attributes:
        block_external: **Hard offline guarantee.** Embeds every library in the
            file, tells the browser (via a strict Content-Security-Policy) to
            refuse *any* external request, and then re-reads the finished HTML to
            prove not a single external URL remains — raising instead of writing
            if one does. Use for air-gapped / regulated environments where the
            report must provably phone home to nobody. Forces all plugins to
            ``bundled`` (and errors if a plugin was explicitly set to ``"cdn"``).
        sri: **Tamper-check for CDN libraries.** When a library loads from a CDN,
            the browser compares the downloaded file against a fingerprint baked
            into the page; if a hacked or man-in-the-middled CDN serves altered
            code, the fingerprint won't match and the browser refuses to run it.
            No effect on bundled plugins.
        no_referrer: **Don't leak where the report came from.** When the report
            is hosted and someone clicks a link in it, the browser won't tell the
            destination site which report URL they came from — avoiding leaks of
            possibly-sensitive internal paths. (Opening from disk has no referrer
            anyway, so this only matters when the report is served.)
        noindex: **Keep it out of search engines.** If the report is hosted on
            the web, asks crawlers not to list it, so an internal report doesn't
            surface on Google. No effect for a file opened from disk.
        permissions_policy: **Declare no camera / microphone / location use.**
            ``True`` emits a sensible "all sensors off" policy, a string sets a
            custom one, ``False`` omits it. **Caveat:** browsers only *enforce*
            this when a server sends it as an HTTP header; opened straight from
            disk (``file://``) the ``<meta>`` form is ignored, so here it is a
            documented statement of intent that becomes a real control only when
            the report is served behind a header-setting host.
        csp: **Advanced.** Supply your own Content-Security-Policy string to take
            full control of what the page may load. Overrides the policy Montin
            would generate.
    """

    block_external:     bool = False
    sri:                bool = True
    no_referrer:        bool = True
    noindex:            bool = False
    permissions_policy: bool | str = True
    csp:                str | None = None

    def csp_content(self) -> str | None:
        """The Content-Security-Policy to emit, or ``None`` for no CSP meta tag.

        An explicit ``csp`` wins; otherwise ``block_external`` emits the strict
        no-egress policy; otherwise no CSP is set.
        """
        if self.csp is not None:
            return self.csp
        if self.block_external:
            return STRICT_CSP
        return None

    def permissions_policy_content(self) -> str | None:
        """The Permissions-Policy string to emit, or ``None`` to omit it."""
        if self.permissions_policy is True:
            return DEFAULT_PERMISSIONS_POLICY
        if isinstance(self.permissions_policy, str):
            return self.permissions_policy
        return None
