"""Regression checks for data integrity and the failure fallback contract."""
import contextlib
import io
import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch
import refresh_data as refresh


def calendar():
    start = date(2024,1,1)
    return [{'date':(start+timedelta(days=i)).isoformat(),'count':i%4} for i in range(366)]


class DataIntegrity(unittest.TestCase):
    def test_calendar_rejects_missing_duplicate_and_negative_days(self):
        days = calendar()
        refresh.validate_days(days)
        for invalid in [days[:100], days[:100]+days[101:], days[:-1]+[days[0]], [dict(d,count=-1) for d in days]]:
            with self.subTest(case=len(invalid)), self.assertRaises(ValueError):
                refresh.validate_days(invalid)

    def test_public_html_preserves_zero_and_exact_counts(self):
        parser = refresh.CalendarParser()
        for i,day in enumerate(calendar()):
            count = 'No' if day['count']==0 else str(day['count'])
            parser.feed(f'<td id="day-{i}" data-date="{day["date"]}"></td><tool-tip for="day-{i}">{count} contributions on a day.</tool-tip>')
        self.assertEqual(parser.days(),calendar())

    def test_changed_tooltip_is_rejected_instead_of_guessed(self):
        parser = refresh.CalendarParser()
        with self.assertRaises(ValueError):
            parser.feed('<td id="d" data-date="2024-01-01"></td><tool-tip for="d">activity unavailable</tool-tip>')

    def test_graphql_mismatched_total_is_rejected(self):
        result = {'data':{'user':{'contributionsCollection':{'contributionCalendar':{
            'totalContributions':999999,
            'weeks':[{'contributionDays':[{'date':d['date'],'contributionCount':d['count']} for d in calendar()]}]
        }}}}}
        with patch.dict('os.environ',{'GH_TOKEN':'fake-test-token'}), patch.object(refresh,'get',return_value=json.dumps(result)):
            with self.assertRaises(ValueError):
                refresh.fetch_contributions()

    def test_partial_failure_preserves_old_source_and_timestamp(self):
        original = {'schema':1,'repositories':{'updated_at':'old','items':[]},'contributions':{'updated_at':'old','days':calendar()}}
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'snapshot.json';path.write_text(json.dumps(original))
            with patch.object(refresh,'SNAPSHOT',path), patch.object(refresh,'fetch_repositories',side_effect=OSError), patch.object(refresh,'fetch_contributions',return_value={'updated_at':'new','days':calendar()}), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                refresh.main()
            saved=json.loads(path.read_text())
            self.assertEqual(saved['repositories'],original['repositories'])
            self.assertEqual(saved['contributions']['updated_at'],'new')

    def test_total_failure_leaves_snapshot_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'snapshot.json';original='{"schema":1,"repositories":{},"contributions":{}}\n';path.write_text(original)
            with patch.object(refresh,'SNAPSHOT',path), patch.object(refresh,'fetch_repositories',side_effect=OSError), patch.object(refresh,'fetch_contributions',side_effect=OSError), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    refresh.main()
            self.assertEqual(path.read_text(),original)


if __name__ == '__main__':
    unittest.main()
