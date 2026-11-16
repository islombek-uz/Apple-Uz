import sys
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

BOT_DIR = Path(__file__).resolve().parent
if str(BOT_DIR) not in sys.path:
    sys.path.insert(0, str(BOT_DIR))

import telegram_bot


class TelegramBotTests(unittest.TestCase):
    def test_api_request_raises_telegram_api_errors(self):
        response = BytesIO(
            b'{"ok": false, "error_code": 409, "description": "Webhook is active"}'
        )
        with patch.object(telegram_bot.urllib.request, "urlopen", return_value=response):
            with self.assertRaisesRegex(RuntimeError, "409.*Webhook is active"):
                telegram_bot.api_request("getMe")

    def test_start_command_accepts_any_bot_username(self):
        with (
            patch.object(telegram_bot, "profile_has_telegram_fields", return_value=True),
            patch("store.models.Profile.objects.filter") as profile_filter,
            patch.object(telegram_bot, "send_message") as send,
        ):
            profile_filter.return_value.first.return_value = None
            telegram_bot.handle_message(
                {"chat": {"id": 17}, "text": "/start@different_bot"}
            )

        self.assertIn("Xush kelibsiz", send.call_args.args[1])

    def test_startup_rejects_an_active_webhook(self):
        with (
            patch.object(
                telegram_bot,
                "api_request",
                side_effect=[
                    {"ok": True, "result": {"id": 17, "username": "shop_bot"}},
                    {"ok": True, "result": {"url": "https://example.test/hook"}},
                ],
            ),
            patch.object(telegram_bot, "profile_has_telegram_fields", return_value=True),
        ):
            with self.assertRaisesRegex(RuntimeError, "webhook is active"):
                telegram_bot.validate_startup()

    def test_startup_returns_identity_when_polling_is_ready(self):
        with (
            patch.object(
                telegram_bot,
                "api_request",
                side_effect=[
                    {"ok": True, "result": {"id": 17, "username": "shop_bot"}},
                    {"ok": True, "result": {"url": ""}},
                ],
            ),
            patch.object(telegram_bot, "profile_has_telegram_fields", return_value=True),
        ):
            bot_info = telegram_bot.validate_startup()

        self.assertEqual(bot_info["username"], "shop_bot")


if __name__ == "__main__":
    unittest.main()