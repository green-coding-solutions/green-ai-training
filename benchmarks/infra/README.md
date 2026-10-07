# Infrastructure Benchmarks

| Folder | Variants | What to compare |
|---|---|---|
| `container-image/` | `original` (test-case Dockerfile as is), `optimized` (`Dockerfile.optimized`: slim base, runtime deps only, dependency layer first, no pip cache) | The **[INSTALLATION]** phase holds the image build (GMT builds with kaniko). Run without `--dev-cache-build`, otherwise cached images skip the build. The runtime flow reports `image_size_mb` (container root filesystem via `du -x`) and serves 2000 health requests as a control, since the app is identical. |
| `minimize-environments/` | `full` (3 app replicas, Postgres, Redis, polling worker, as the test-case workflow deploys per branch), `minimal` (1 app replica, Postgres) | Energy per `environment_minutes` while the environment idles. Multiply by the hours an environment exists. Environments torn down on merge or scaled to zero at night cost nothing for the hours they don't exist, which is the larger part of the saving and not something a run can measure. |

Both use the Flask app from `test-cases/infra/container-image`. The optimized Dockerfile avoids BuildKit-only syntax
(`RUN --mount`) because kaniko doesn't support it.
