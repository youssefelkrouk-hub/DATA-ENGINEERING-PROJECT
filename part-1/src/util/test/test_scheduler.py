import pytest
from unittest.mock import patch, MagicMock, call

from util.scheduler import Scheduler
from util.exceptions import ProjectBaseException, ApiRequestException


@pytest.fixture
def scheduler():
    """Scheduler avec ApiHandler et FileHandler mockés (pas de vraie config/API)."""
    with patch("util.scheduler.ApiHandler") as MockApiHandler, \
         patch("util.scheduler.FileHandler") as MockFileHandler:
        instance = Scheduler()
        instance._mock_api_handler = MockApiHandler.return_value
        instance._mock_file_handler = MockFileHandler.return_value
        yield instance


class TestSafeRun:

    def test_job_success_runs_without_error(self, scheduler):
        job_func = MagicMock()

        scheduler._safe_run(job_func, "test_job")

        job_func.assert_called_once()

    def test_project_base_exception_is_caught_and_logged(self, scheduler, capsys):
        job_func = MagicMock(side_effect=ApiRequestException("erreur API"))

        scheduler._safe_run(job_func, "fetch_data_to_csv")  # ne doit pas lever

        captured = capsys.readouterr()
        assert "[ERROR]" in captured.out
        assert "fetch_data_to_csv" in captured.out
        assert "erreur API" in captured.out

    def test_unexpected_exception_is_caught_and_logged(self, scheduler, capsys):
        job_func = MagicMock(side_effect=ValueError("boom"))

        scheduler._safe_run(job_func, "track_new_files")  # ne doit pas lever

        captured = capsys.readouterr()
        assert "[ERROR] Erreur inattendue" in captured.out
        assert "track_new_files" in captured.out
        assert "boom" in captured.out

    def test_does_not_propagate_any_exception(self, scheduler):
        """Garantit que _safe_run ne laisse fuir aucune exception, peu importe le type."""
        job_func = MagicMock(side_effect=RuntimeError("erreur imprévue"))

        try:
            scheduler._safe_run(job_func, "any_job")
        except Exception:
            pytest.fail("_safe_run ne doit jamais laisser une exception se propager")


class TestScheduleJobs:

    @patch("util.scheduler.time.sleep")
    @patch("util.scheduler.schedule")
    def test_registers_both_jobs_with_correct_intervals(self, mock_schedule, mock_sleep, scheduler):
        # On force l'arrêt de la boucle "while True" après 1 itération
        mock_sleep.side_effect = KeyboardInterrupt()

        mock_schedule.every.return_value.seconds.do = MagicMock()
        mock_schedule.every.return_value.minutes.do = MagicMock()

        with pytest.raises(KeyboardInterrupt):
            scheduler.schedule_jobs()

        # Vérifie que les deux jobs sont bien programmés avec les bons intervalles
        assert call(40) in mock_schedule.every.call_args_list
        assert call(10) in mock_schedule.every.call_args_list

    @patch("util.scheduler.time.sleep")
    @patch("util.scheduler.schedule")
    def test_run_pending_is_called_in_loop(self, mock_schedule, mock_sleep, scheduler):
        mock_sleep.side_effect = KeyboardInterrupt()  # sort de la boucle après 1 tour

        with pytest.raises(KeyboardInterrupt):
            scheduler.schedule_jobs()

        mock_schedule.run_pending.assert_called_once()

    @patch("util.scheduler.time.sleep")
    @patch("util.scheduler.schedule")
    def test_unexpected_error_in_run_pending_does_not_crash_loop(self, mock_schedule, mock_sleep, scheduler, capsys):
        """
        Le filet de sécurité doit logger l'erreur de run_pending() et continuer
        (donc arriver jusqu'au time.sleep, qu'on utilise ensuite pour sortir de la boucle).
        """
        mock_schedule.run_pending.side_effect = RuntimeError("erreur schedule")
        mock_sleep.side_effect = KeyboardInterrupt()

        with pytest.raises(KeyboardInterrupt):
            scheduler.schedule_jobs()

        captured = capsys.readouterr()
        assert "[ERROR] Erreur inattendue dans la boucle du scheduler" in captured.out
        assert "erreur schedule" in captured.out