"""The named project variants: one list for the heavy tests and the fixtures.

Each name is a template and the answers that make it. The heavy tests run
every one through its own ``make ci``; ``make throwaway VARIANT=<name>``
generates one for a setup test.
"""

VARIANTS: dict[str, tuple[str, dict[str, str]]] = {
    "methodology-pytorch": ("methodology", {"ml_pytorch": "yes"}),
    "methodology-pytorch-cu126": (
        "methodology",
        {"ml_pytorch": "yes", "cuda_source": "cu126"},
    ),
    "methodology-plain": ("methodology", {"ml_pytorch": "no"}),
    "methodology-run-records": (
        "methodology",
        {"ml_pytorch": "yes", "run_records": "yes"},
    ),
    "methodology-lab-root": (
        "methodology",
        {"ml_pytorch": "no", "dataset_registry": "yes"},
    ),
    "methodology-pytorch-docs": (
        "methodology",
        {
            "ml_pytorch": "yes",
            "public_docs": "yes",
            "contact_email": "maintainers@example.org",
        },
    ),
    "methodology-plain-docs": (
        "methodology",
        {
            "ml_pytorch": "no",
            "public_docs": "yes",
            "contact_email": "maintainers@example.org",
        },
    ),
    "methodology-custom-docs-theme": (
        "methodology",
        {
            "ml_pytorch": "no",
            "public_docs": "yes",
            "docs_theme": "custom",
            "docs_domain": "docs.example.org",
            "contact_email": "maintainers@example.org",
        },
    ),
    "workspace": ("workspace", {}),
    "paper-article": ("paper", {"venue": "article"}),
    "paper-iclr": ("paper", {"venue": "iclr", "venue_year": "2027"}),
    "software-django": (
        "software",
        {"backend_django": "yes", "frontend_nextjs": "no"},
    ),
    "software-django-nextjs": (
        "software",
        {"backend_django": "yes", "frontend_nextjs": "yes"},
    ),
    "software-everything": (
        "software",
        {
            "backend_django": "yes",
            "frontend_nextjs": "yes",
            "proxy_caddy": "yes",
            "gateway_litellm": "yes",
        },
    ),
    "software-django-alone": (
        "software",
        {"frontend_nextjs": "no", "proxy_caddy": "no"},
    ),
    "software-ml": (
        "software",
        {"frontend_nextjs": "no", "proxy_caddy": "no", "ml_pytorch": "yes"},
    ),
    "methodology-long-name": (
        "methodology",
        {"project_name": "A Very Long Project Name To Test Line Wrapping"},
    ),
}
