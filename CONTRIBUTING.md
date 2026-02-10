# Contributing

## Development Flow

1. Update API surface in backend.
2. Sync OpenAPI snapshot via `npm run sync:openapi`.
3. Regenerate SDK baselines via `npm run generate`.
4. Implement/adjust handwritten DX layers.
5. Run `npm run check`.

## Versioning

Use `scripts/bump-version.ps1 -Version X.Y.Z`.

## Commit Guidance

- Keep generated changes in a dedicated commit when possible.
- Include spec updates and codegen updates together.
- Do not hand-edit generated sources.
