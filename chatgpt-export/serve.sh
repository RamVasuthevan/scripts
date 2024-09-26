#!/bin/bash

# Serve the export.db with metadata and settings using key-value pairs
datasette serve export.db --metadata metadata.yml \
    --setting default_page_size 100 \
    --setting max_returned_rows 100 \
    --setting max_insert_rows 1000 \
    --setting num_sql_threads 3 \
    --setting sql_time_limit_ms 100000 \
    --setting default_facet_size 10 \
    --setting facet_time_limit_ms 2000000 \
    --setting facet_suggest_time_limit_ms 50000 \
    --setting allow_facet true \
    --setting allow_download true \
    --setting allow_signed_tokens true \
    --setting default_allow_sql true \
    --setting max_signed_tokens_ttl 0 \
    --setting suggest_facets true \
    --setting default_cache_ttl 5 \
    --setting cache_size_kb 0 \
    --setting allow_csv_stream true \
    --setting max_csv_mb 100 \
    --setting truncate_cells_html 2048 \
    --setting force_https_urls false \
    --setting template_debug false \
    --setting trace_debug false \
    --setting base_url "/"
