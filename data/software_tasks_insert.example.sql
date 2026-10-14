-- This is an example SQL for to insert new softwares for benchmarks
-- into softwares and software_tasks tables
-- Please use the LLM query in software_tasks_insert.query.md to generate a current file.
-- Do not use this example directly

BEGIN;

INSERT INTO softwares (name, category_ids)
SELECT v.name, v.category_ids::integer[]
FROM (VALUES
    ('Bash', '{2,5,33}'),
    ('Container Image', '{2,22}'),
) AS v(name, category_ids)
WHERE NOT EXISTS (SELECT 1 FROM softwares s WHERE s.name = v.name);

INSERT INTO software_tasks (software_id, name, uri, branch, filename, machine_id, phase)
SELECT s.id, v.task_name, 'https://github.com/green-coding-solutions/green-ai-training', 'main', v.filename, v.machine_id, v.phase
FROM (VALUES
    -- Bash Log Summary
    ('Bash Log Summary', 'Single awk Pass', 'benchmarks/bash/builtins/usage_scenario-awk.yml', 6, 'Summarize 20k lines'),
    ('Bash Log Summary', 'Shell Builtins', 'benchmarks/bash/builtins/usage_scenario-builtins.yml', 6, 'Summarize 20k lines'),
    ('Bash Log Summary', 'Subprocess per Field', 'benchmarks/bash/builtins/usage_scenario-subprocess.yml', 6, 'Summarize 20k lines'),

    -- Container Image: build happens in [INSTALLATION], serving requests is the control
    ('Container Image', 'Optimized Dockerfile - Build', 'benchmarks/infra/container-image/usage_scenario-optimized.yml', 6, '[INSTALLATION]'),
    ('Container Image', 'Optimized Dockerfile - Serve 2000 requests', 'benchmarks/infra/container-image/usage_scenario-optimized.yml', 6, 'Serve 2000 requests'),
    ('Container Image', 'Original Dockerfile - Build', 'benchmarks/infra/container-image/usage_scenario-original.yml', 6, '[INSTALLATION]'),
    ('Container Image', 'Original Dockerfile - Serve 2000 requests', 'benchmarks/infra/container-image/usage_scenario-original.yml', 6, 'Serve 2000 requests'),

) AS v(software_name, task_name, filename, machine_id, phase)
JOIN softwares s ON s.name = v.software_name
ON CONFLICT DO NOTHING;

COMMIT;
