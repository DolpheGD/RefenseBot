import topgg

from bot.config import WEBHOOK_SECRET

async def setup_webhook(bot, TOPGG_WEBHOOK_PORT = 5000):
    webhook_manager = topgg.WebhookManager(bot).dbl_webhook(
        route="/dblwebhook",
        auth_key=WEBHOOK_SECRET
    )

    await webhook_manager.run(TOPGG_WEBHOOK_PORT)
    bot.topgg_webhook_manager = webhook_manager
    print(f"top.gg webhook listening on port {TOPGG_WEBHOOK_PORT}")