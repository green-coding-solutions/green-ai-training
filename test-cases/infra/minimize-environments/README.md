# Prompt

Optimize this file according to Green Coding Rules

# Expected Output

- Only create preview environments for pull requests (`on: pull_request`), not for every push to every branch
- Tear the preview environment down automatically when the pull request is closed or merged (job on `pull_request: types: [closed]` running `helm uninstall` / deleting the namespace), and optionally after a period of inactivity
- Size preview environments down: 1 replica instead of 3, and only start the components the change needs (e.g. shared or seeded test database instead of a full Postgres + Redis + worker per branch)
- Scale staging down outside working hours (e.g. a scheduled workflow that sets replicas to 0 at night and on weekends and scales back up in the morning)
- Expected energy saving when running this file 1.000 times
