-- This query is to export the data from a running GMT instance
-- GMT is the tool used to measure this data - https://github.com/green-coding-solutions/green-metrics-tool
-- ⚙️ Detailed machine specs and configuration like CPU Cores, Memory, TurboBoost etc. are always up to date on the (ℹ︎) icon in the [Cluster Machine Listing](https://metrics.green-coding.io/cluster-status.html)

WITH task_runs AS (
    SELECT
        sw.id          AS software_id,
        sw.name        AS software_name,
        st.id          AS task_id,
        st.name        AS task_name,
        st.uri,
        st.branch,
        st.filename,
        st.phase,
        st.machine_id,
        m.description  AS machine_name,
        st.created_at,
        r.run_id,
        r.run_created_at
    FROM software_tasks st
    JOIN softwares sw ON sw.id = st.software_id
    JOIN machines m ON m.id = st.machine_id
    LEFT JOIN LATERAL (
        SELECT r.id AS run_id, r.created_at AS run_created_at
        FROM runs r
        WHERE r.uri = st.uri
            AND r.branch = st.branch
            AND r.filename = st.filename
            AND r.machine_id = st.machine_id
            AND r.failed = FALSE
            AND r.archived = FALSE
            AND r.end_measurement IS NOT NULL
        ORDER BY r.created_at DESC
        LIMIT 1
    ) r ON TRUE
    WHERE sw.name = ANY(ARRAY[
        'Browser Animation Rendering Cost (CSS vs JS)',
        'brotli',
        'bzip2',
        'gzip',
        'zstd',
        'Image Format Encoding Cost',
        'Image Format Rendering Cost (Headful Browser)',
        'Python'
    ])
)
SELECT
    tr.software_id, tr.software_name,
    tr.task_id, tr.task_name, tr.uri, tr.branch, tr.filename,
    tr.phase, tr.machine_id, tr.machine_name, tr.created_at,
    tr.run_id, tr.run_created_at,
    p.metric, SUM(p.value)::bigint AS value, p.unit, p.type
FROM task_runs tr
LEFT JOIN phase_stats p ON p.run_id = tr.run_id
    AND regexp_replace(p.phase, '^[0-9]+_', '') = tr.phase
    AND p.hidden = false
    AND (
        (p.metric LIKE 'psu_energy_%' AND p.metric LIKE '%_machine')      -- Machine energy
        OR (p.metric LIKE 'cpu_energy_%' AND p.metric LIKE '%_component') -- CPU energy
        OR p.metric = 'phase_time_syscall_system'                        -- CPU duration
    )
GROUP BY
    tr.software_id, tr.software_name,
    tr.task_id, tr.task_name, tr.uri, tr.branch, tr.filename,
    tr.phase, tr.machine_id, tr.machine_name, tr.created_at,
    tr.run_id, tr.run_created_at, p.metric, p.unit, p.type
ORDER BY tr.software_name, tr.task_id, p.metric;


