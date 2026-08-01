"""
load_data.py

Initializes the SQLite database (cell_counts.db) with a normalized schema
and loads all rows from cell-count.csv into it.

Run directly:
    python load_data.py

Produces:
    cell_counts.db  (SQLite database in the repository root)
"""

import csv
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cell_counts.db")
CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cell-count.csv")

POPULATIONS = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]

SCHEMA = """
DROP TABLE IF EXISTS cell_counts;
DROP TABLE IF EXISTS samples;
DROP TABLE IF EXISTS subjects;
DROP TABLE IF EXISTS projects;

CREATE TABLE projects (
    project_id      TEXT PRIMARY KEY
);

CREATE TABLE subjects (
    subject_id      TEXT PRIMARY KEY,
    project_id      TEXT NOT NULL,
    condition       TEXT NOT NULL,
    age             INTEGER,
    sex             TEXT,
    treatment       TEXT,
    response        TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);

CREATE TABLE samples (
    sample_id                  TEXT PRIMARY KEY,
    subject_id                 TEXT NOT NULL,
    sample_type                TEXT NOT NULL,
    time_from_treatment_start  INTEGER,
    FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
);

CREATE TABLE cell_counts (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sample_id   TEXT NOT NULL,
    population  TEXT NOT NULL,
    count       INTEGER NOT NULL,
    FOREIGN KEY (sample_id) REFERENCES samples(sample_id)
);

CREATE INDEX idx_subjects_project ON subjects(project_id);
CREATE INDEX idx_samples_subject ON samples(subject_id);
CREATE INDEX idx_cellcounts_sample ON cell_counts(sample_id);
CREATE INDEX idx_cellcounts_population ON cell_counts(population);
"""


def init_db(conn):
    conn.executescript(SCHEMA)
    conn.commit()


def load_csv(conn, csv_path):
    cur = conn.cursor()
    seen_projects = set()
    seen_subjects = set()

    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            project_id = row["project"]
            subject_id = row["subject"]
            sample_id = row["sample"]

            if project_id not in seen_projects:
                cur.execute(
                    "INSERT OR IGNORE INTO projects (project_id) VALUES (?)",
                    (project_id,),
                )
                seen_projects.add(project_id)

            if subject_id not in seen_subjects:
                cur.execute(
                    """INSERT OR IGNORE INTO subjects
                       (subject_id, project_id, condition, age, sex, treatment, response)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        subject_id,
                        project_id,
                        row["condition"],
                        int(row["age"]),
                        row["sex"],
                        row["treatment"],
                        row["response"] if row["response"] != "" else None,
                    ),
                )
                seen_subjects.add(subject_id)

            cur.execute(
                """INSERT INTO samples
                   (sample_id, subject_id, sample_type, time_from_treatment_start)
                   VALUES (?, ?, ?, ?)""",
                (
                    sample_id,
                    subject_id,
                    row["sample_type"],
                    int(row["time_from_treatment_start"]),
                ),
            )

            for population in POPULATIONS:
                cur.execute(
                    """INSERT INTO cell_counts (sample_id, population, count)
                       VALUES (?, ?, ?)""",
                    (sample_id, population, int(row[population])),
                )

    conn.commit()


def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    try:
        init_db(conn)
        load_csv(conn, CSV_PATH)

        cur = conn.cursor()
        n_projects = cur.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        n_subjects = cur.execute("SELECT COUNT(*) FROM subjects").fetchone()[0]
        n_samples = cur.execute("SELECT COUNT(*) FROM samples").fetchone()[0]
        n_counts = cur.execute("SELECT COUNT(*) FROM cell_counts").fetchone()[0]

        print(f"Database created at: {DB_PATH}")
        print(f"  projects:    {n_projects}")
        print(f"  subjects:    {n_subjects}")
        print(f"  samples:     {n_samples}")
        print(f"  cell_counts: {n_counts}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
