from django.db import migrations


TRIGGER_SQL = """
CREATE OR REPLACE FUNCTION mobile_dailymob_status_audit() RETURNS trigger AS $$
BEGIN
    IF (TG_OP = 'INSERT') THEN
        INSERT INTO mobile_dailymobstatusaudit
            ("dailymob_id", "old_status", "new_status", "operation", "changed_at",
             "db_user", "session_user", "app_user", "txid")
        VALUES (NEW.id, NULL, NEW."Status", TG_OP, clock_timestamp(),
                current_user, session_user,
                nullif(current_setting('app.current_user', true), ''),
                txid_current());
    ELSIF (TG_OP = 'UPDATE') THEN
        IF NEW."Status" IS DISTINCT FROM OLD."Status" THEN
            INSERT INTO mobile_dailymobstatusaudit
                ("dailymob_id", "old_status", "new_status", "operation", "changed_at",
                 "db_user", "session_user", "app_user", "txid")
            VALUES (NEW.id, OLD."Status", NEW."Status", TG_OP, clock_timestamp(),
                    current_user, session_user,
                    nullif(current_setting('app.current_user', true), ''),
                    txid_current());
        END IF;
    ELSIF (TG_OP = 'DELETE') THEN
        INSERT INTO mobile_dailymobstatusaudit
            ("dailymob_id", "old_status", "new_status", "operation", "changed_at",
             "db_user", "session_user", "app_user", "txid")
        VALUES (OLD.id, OLD."Status", NULL, TG_OP, clock_timestamp(),
                current_user, session_user,
                nullif(current_setting('app.current_user', true), ''),
                txid_current());
    END IF;
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_dailymob_status_audit
AFTER INSERT OR UPDATE OF "Status" OR DELETE ON mobile_dailymob
FOR EACH ROW EXECUTE FUNCTION mobile_dailymob_status_audit();
"""

DROP_SQL = """
DROP TRIGGER IF EXISTS trg_dailymob_status_audit ON mobile_dailymob;
DROP FUNCTION IF EXISTS mobile_dailymob_status_audit();
"""


class Migration(migrations.Migration):

    dependencies = [
        ('mobile', '0019_dailymobstatusaudit'),
    ]

    operations = [
        migrations.RunSQL(sql=TRIGGER_SQL, reverse_sql=DROP_SQL),
    ]
