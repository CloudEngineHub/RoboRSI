FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# The project depends on the vendored LeRobot tree, so copy the complete source
# before installation. Installing from a metadata-only layer would leave the
# local path dependency unresolved in a clean Docker build.
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY roborsi/ roborsi/
COPY third_party/ third_party/
RUN uv pip install --system --no-cache ".[web,libero]"

# Create config directory
RUN mkdir -p /root/.roborsi

# Evolution dashboard.
EXPOSE 8787

ENTRYPOINT ["roborsi"]
CMD ["status"]
