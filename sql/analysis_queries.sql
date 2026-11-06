-- Each query starts with "-- name: <key>" so analyze.py can run it by name.

-- name: kpis
SELECT COUNT(*)                                             AS applications,
       SUM(offered)                                         AS offers,
       SUM(enrolled)                                        AS enrolled,
       ROUND(100.0 * SUM(offered)  / COUNT(*), 1)           AS offer_rate_pct,
       ROUND(100.0 * SUM(enrolled) / SUM(offered), 1)       AS yield_pct,
       ROUND(100.0 * SUM(enrolled) / COUNT(*), 1)           AS conversion_pct,
       ROUND(100.0 * AVG(retained_next_term), 1)            AS retention_pct
FROM applications;

-- name: funnel
SELECT 'Applied'  AS stage, COUNT(*)                     AS students FROM applications
UNION ALL SELECT 'Offered',  SUM(offered)                FROM applications
UNION ALL SELECT 'Accepted', SUM(accepted)               FROM applications
UNION ALL SELECT 'Enrolled', SUM(enrolled)               FROM applications
UNION ALL SELECT 'Retained', SUM(retained_next_term = 1) FROM applications;

-- name: by_program
SELECT p.program_name,
       COUNT(*)                                             AS applications,
       ROUND(100.0 * SUM(a.offered)  / COUNT(*), 1)         AS offer_rate_pct,
       ROUND(100.0 * SUM(a.enrolled) / SUM(a.offered), 1)   AS yield_pct,
       SUM(a.enrolled)                                      AS enrolled,
       ROUND(100.0 * AVG(a.retained_next_term), 1)          AS retention_pct,
       ROUND(AVG(a.first_term_gpa), 2)                      AS avg_gpa
FROM applications a JOIN programs p USING (program_code)
GROUP BY p.program_name
ORDER BY enrolled DESC;

-- name: by_channel
SELECT student_type, channel,
       COUNT(*)                                             AS applications,
       ROUND(100.0 * SUM(enrolled) / COUNT(*), 1)           AS conversion_pct
FROM applications
WHERE channel <> 'Unknown'
GROUP BY student_type, channel
HAVING COUNT(*) >= 100
ORDER BY student_type, conversion_pct DESC;

-- name: by_term
WITH t AS (
    SELECT a.term, MIN(tm.start_date) AS start_date,
           SUM(a.student_type = 'Domestic')                          AS domestic_apps,
           SUM(a.student_type = 'International')                     AS international_apps,
           SUM(a.enrolled)                                           AS enrolled,
           SUM(CASE WHEN a.enrolled = 1 THEN CASE a.student_type
                    WHEN 'Domestic' THEN p.tuition_domestic
                    ELSE p.tuition_international END END)            AS tuition_revenue
    FROM applications a
    JOIN terms tm USING (term)
    JOIN programs p USING (program_code)
    GROUP BY a.term
)
SELECT term, domestic_apps, international_apps, enrolled, ROUND(tuition_revenue) AS tuition_revenue,
       ROUND(100.0 * (international_apps - LAG(international_apps, 2) OVER (ORDER BY start_date))
             / LAG(international_apps, 2) OVER (ORDER BY start_date), 1) AS intl_change_vs_same_intake_pct
FROM t
ORDER BY start_date;

-- name: retention_by_gpa
SELECT CASE WHEN first_term_gpa < 2.0 THEN '1: Below 2.0'
            WHEN first_term_gpa < 2.5 THEN '2: 2.0-2.49'
            WHEN first_term_gpa < 3.0 THEN '3: 2.5-2.99'
            WHEN first_term_gpa < 3.5 THEN '4: 3.0-3.49'
            ELSE '5: 3.5+' END                              AS gpa_band,
       COUNT(*)                                             AS students,
       ROUND(100.0 * AVG(retained_next_term), 1)            AS retention_pct
FROM applications
WHERE enrolled = 1 AND first_term_gpa IS NOT NULL AND retained_next_term IS NOT NULL
GROUP BY gpa_band
ORDER BY gpa_band;

-- name: retention_by_intake
SELECT tm.intake,
       COUNT(*)                                             AS students,
       ROUND(100.0 * AVG(a.retained_next_term), 1)          AS retention_pct
FROM applications a JOIN terms tm USING (term)
WHERE a.enrolled = 1 AND a.retained_next_term IS NOT NULL
GROUP BY tm.intake;

-- name: yield_by_type
SELECT student_type,
       SUM(offered)                                         AS offers,
       ROUND(100.0 * SUM(accepted) / SUM(offered), 1)       AS acceptance_pct,
       ROUND(100.0 * SUM(enrolled) / SUM(accepted), 1)      AS show_up_pct,
       ROUND(100.0 * SUM(enrolled) / SUM(offered), 1)       AS yield_pct
FROM applications
GROUP BY student_type;
