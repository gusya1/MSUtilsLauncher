import time
import unittest
from unittest.mock import MagicMock, patch

from . import client as client_module
from .client import MoySkladClient, RATE_LIMIT_MAX_RETRIES, retry_delay_seconds
from .exceptions import MoySkladError, MoySkladRateLimitError


def make_response(status_code: int = 200, headers=None):
    response = MagicMock()
    response.status_code = status_code
    response.headers = headers or {}
    return response


class Client429RetryTests(unittest.TestCase):

    """Повтор запроса при HTTP 429 в MoySkladClient (mock'нутая session, без сети)."""

    def setUp(self):
        self.session = MagicMock()
        with patch.object(client_module, "_create_session", return_value=self.session):
            self.client = MoySkladClient(token="test-token")

    def _call_get(self):
        """Выполнить GET с заглушками sleep и джиттера; вернуть (response, mock_sleep)."""
        mock_sleep = MagicMock()
        fake_time = MagicMock(sleep=mock_sleep)
        fake_random = MagicMock(uniform=MagicMock(return_value=0.0))
        with patch.object(client_module, "time", fake_time), \
                patch.object(client_module, "random", fake_random):
            response = self.client.get_by_href("https://api.moysklad.ru/api/remap/1.2/entity/product")
        return response, mock_sleep

    def test_429_then_success_retries_with_header_delay(self):
        """429 с X-Lognex-Retry-After → повтор по заголовку (мс → с)."""
        self.session.request.side_effect = [
            make_response(429, {"X-Lognex-Retry-After": "2000"}),
            make_response(200),
        ]
        response, mock_sleep = self._call_get()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.session.request.call_count, 2)
        self.assertEqual(mock_sleep.call_count, 1)
        self.assertEqual(mock_sleep.call_args_list[0].args[0], 2.0)

    def test_429_retry_uses_x_lognex_reset_header(self):
        """429 с X-Lognex-Reset → повтор по заголовку."""
        self.session.request.side_effect = [
            make_response(429, {"X-Lognex-Reset": "3000"}),
            make_response(200),
        ]
        response, mock_sleep = self._call_get()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.session.request.call_count, 2)
        self.assertEqual(mock_sleep.call_args_list[0].args[0], 3.0)

    def test_429_reset_zero_falls_back_to_exponential_backoff(self):
        """X-Lognex-Reset == 0 (ограничение не установлено) → только backoff."""
        self.session.request.side_effect = [
            make_response(429, {"X-Lognex-Reset": "0"}),
            make_response(200),
        ]
        response, mock_sleep = self._call_get()

        self.assertEqual(response.status_code, 200)
        # backoff первого повтора: RETRY_BASE_BACKOFF_SECONDS * 2**0 + джиттер (0.0)
        self.assertEqual(mock_sleep.call_args_list[0].args[0], 1.0)

    def test_429_retry_on_put(self):
        """Повтор при 429 работает и для put."""
        self.session.request.side_effect = [
            make_response(429, {"X-Lognex-Retry-After": "2000"}),
            make_response(200),
        ]
        mock_sleep = MagicMock()
        fake_time = MagicMock(sleep=mock_sleep)
        fake_random = MagicMock(uniform=MagicMock(return_value=0.0))
        with patch.object(client_module, "time", fake_time), \
                patch.object(client_module, "random", fake_random):
            response = self.client.put("entity/product", "{}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.session.request.call_count, 2)
        self.assertEqual(mock_sleep.call_args_list[0].args[0], 2.0)

    def test_429_without_headers_retries_with_backoff(self):
        """429 без заголовков → повтор по backoff (1с, 2с), затем успех."""
        self.session.request.side_effect = [
            make_response(429),
            make_response(429),
            make_response(200),
        ]
        mock_sleep = MagicMock()
        fake_time = MagicMock(sleep=mock_sleep)
        fake_random = MagicMock(uniform=MagicMock(return_value=0.0))
        with patch.object(client_module, "time", fake_time), \
                patch.object(client_module, "random", fake_random):
            response = self.client.get_by_href("https://api.moysklad.ru/api/remap/1.2/entity/product")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.session.request.call_count, 3)
        # backoff: RETRY_BASE_BACKOFF_SECONDS * 2**0 и * 2**1
        self.assertEqual(mock_sleep.call_args_list[0].args[0], 1.0)
        self.assertEqual(mock_sleep.call_args_list[1].args[0], 2.0)

    def test_retry_logs_warning_with_headers(self):
        """Ретрай логируется WARNING с методом, заголовками и остатком лимита."""
        self.session.request.side_effect = [
            make_response(429, {
                "X-RateLimit-Remaining": "8",
                "X-Lognex-Retry-After": "2000",
            }),
            make_response(200),
        ]
        mock_sleep = MagicMock()
        fake_time = MagicMock(sleep=mock_sleep)
        fake_random = MagicMock(uniform=MagicMock(return_value=0.0))
        with patch.object(client_module, "time", fake_time), \
                patch.object(client_module, "random", fake_random), \
                self.assertLogs("moysklad_sync", level="WARNING") as cm:
            response = self.client.get_by_href("https://api.moysklad.ru/api/remap/1.2/entity/product")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(cm.records), 1)
        record = cm.records[0]
        self.assertEqual(record.levelname, "WARNING")
        message = record.getMessage()
        self.assertIn("GET", message)
        self.assertIn("entity/product", message)
        self.assertIn("повтор 1/5", message)
        self.assertIn("X-RateLimit-Remaining=8", message)
        self.assertIn("X-Lognex-Retry-After=2000", message)
        self.assertIn("X-Lognex-Reset=-", message)

    def test_exhausted_retries_logs_error(self):
        """Исчерпание повторов логируется ERROR (5 warnings + 1 error)."""
        self.session.request.side_effect = [
            make_response(429, {"X-Lognex-Retry-After": "1"})
        ] * (RATE_LIMIT_MAX_RETRIES + 1)
        mock_sleep = MagicMock()
        fake_time = MagicMock(sleep=mock_sleep)
        fake_random = MagicMock(uniform=MagicMock(return_value=0.0))
        with patch.object(client_module, "time", fake_time), \
                patch.object(client_module, "random", fake_random), \
                self.assertLogs("moysklad_sync", level="WARNING") as cm:
            with self.assertRaises(MoySkladRateLimitError):
                self.client.post("entity/product", "{}")

        # 5 warnings (повторы) + 1 error (исчерпание)
        self.assertEqual(len(cm.records), RATE_LIMIT_MAX_RETRIES + 1)
        self.assertEqual(cm.records[-1].levelname, "ERROR")
        self.assertIn(str(RATE_LIMIT_MAX_RETRIES), cm.records[-1].getMessage())
        self.assertIn("entity/product", cm.records[-1].getMessage())

    def test_429_exhausted_retries_raise_rate_limit_error(self):
        """После исчерпания повторов → MoySkladRateLimitError."""
        self.session.request.side_effect = [
            make_response(429, {"X-Lognex-Retry-After": "1"})
        ] * (RATE_LIMIT_MAX_RETRIES + 1)

        mock_sleep = MagicMock()
        fake_time = MagicMock(sleep=mock_sleep)
        fake_random = MagicMock(uniform=MagicMock(return_value=0.0))
        with patch.object(client_module, "time", fake_time), \
                patch.object(client_module, "random", fake_random):
            with self.assertRaises(MoySkladRateLimitError) as ctx:
                self.client.post("entity/product", "{}")

        # начальный запрос + RATE_LIMIT_MAX_RETRIES повторов
        self.assertEqual(self.session.request.call_count, RATE_LIMIT_MAX_RETRIES + 1)
        # сон перед каждым повтором, после последнего неудачного — нет
        self.assertEqual(mock_sleep.call_count, RATE_LIMIT_MAX_RETRIES)
        self.assertIn(str(RATE_LIMIT_MAX_RETRIES), str(ctx.exception))
        self.assertIn("entity/product", str(ctx.exception))

    def test_no_retry_on_200(self):
        """При 200 повтор не происходит; заголовки авторизации/gzip сохраняются."""
        self.session.request.return_value = make_response(200)
        response, mock_sleep = self._call_get()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.session.request.call_count, 1)
        mock_sleep.assert_not_called()
        headers = self.session.request.call_args.kwargs["headers"]
        self.assertEqual(headers["Authorization"], "Bearer test-token")
        self.assertEqual(headers["Accept-Encoding"], "gzip")

    def test_no_retry_on_5xx(self):
        """При 5xx повтор в клиенте не происходит (ретраи 500/503 — за urllib3 Retry)."""
        self.session.request.return_value = make_response(503)
        response, mock_sleep = self._call_get()

        self.assertEqual(response.status_code, 503)
        self.assertEqual(self.session.request.call_count, 1)
        mock_sleep.assert_not_called()


class RateLimitWindowTests(unittest.TestCase):

    """Лимитер rate_limited: фиксированное окно 11 вызовов / 3 секунды."""

    def setUp(self):
        self.session = MagicMock()
        with patch.object(client_module, "_create_session", return_value=self.session):
            self.client = MoySkladClient(token="test-token")
        self.session.request.return_value = make_response(200)

    def _reset_shared_limiter(self):
        """Сброс состояния общего лимитера клиента (тестовый seam)."""
        limiter = client_module._client_limiter
        with limiter.lock:
            limiter.num_calls = 0
            limiter.last_reset = time.monotonic()

    def test_post_and_put_share_single_limiter(self):
        """Post и put идут через общий лимитер — одна «корзинка» на клиент."""
        self._reset_shared_limiter()
        self.client.post("entity/product", "{}")
        self.client.put("entity/product", "{}")
        self.assertEqual(client_module._client_limiter.num_calls, 2)

    def test_rate_limited_defaults_to_11_calls_per_3_seconds(self):
        """rate_limited() по умолчанию: 12-й вызов в пределах 3-секундного окна ждёт сброса (sleep_and_retry)."""
        @client_module.rate_limited()
        def dummy():
            return None

        start = time.monotonic()
        for _ in range(12):
            dummy()
        elapsed = time.monotonic() - start

        # 11 вызовов проходят сразу, 12-й ждёт ~3 с до сброса окна
        self.assertGreaterEqual(elapsed, 2.5)
        self.assertLess(elapsed, 6.0)


class RetryDelayTests(unittest.TestCase):

    """Формула времени сна перед повтором: max(заголовок (мс → с), backoff + джиттер)."""

    def _delay(self, response, attempt, jitter=0.0):
        fake_random = MagicMock(uniform=MagicMock(return_value=jitter))
        with patch.object(client_module, "random", fake_random):
            return retry_delay_seconds(response, attempt)

    def test_exponential_backoff_without_headers(self):
        response = make_response(429)
        self.assertEqual(self._delay(response, 0), 1.0)
        self.assertEqual(self._delay(response, 1), 2.0)
        self.assertEqual(self._delay(response, 2), 4.0)

    def test_header_value_dominates_backoff(self):
        response = make_response(429, {"X-Lognex-Retry-After": "5000"})
        self.assertEqual(self._delay(response, 0), 5.0)

    def test_max_of_both_headers(self):
        response = make_response(429, {"X-Lognex-Retry-After": "1000", "X-Lognex-Reset": "3000"})
        self.assertEqual(self._delay(response, 0), 3.0)

    def test_invalid_header_value_ignored(self):
        response = make_response(429, {"X-Lognex-Retry-After": "not-a-number"})
        self.assertEqual(self._delay(response, 0), 1.0)

    def test_nan_inf_header_values_ignored(self):
        """'nan'/'inf' в заголовках игнорируются → только backoff."""
        response = make_response(429, {"X-Lognex-Retry-After": "nan", "X-Lognex-Reset": "inf"})
        self.assertEqual(self._delay(response, 0), 1.0)

    def test_jitter_added_to_backoff(self):
        response = make_response(429)
        self.assertEqual(self._delay(response, 0, jitter=0.25), 1.25)


class RateLimitErrorContractTests(unittest.TestCase):

    """Контракт наследования: обработчики вызывающего кода ловят MoySkladError."""

    def test_rate_limit_error_is_moy_sklad_error(self):
        self.assertTrue(issubclass(MoySkladRateLimitError, MoySkladError))
