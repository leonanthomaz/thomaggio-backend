# app/functions/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from app.functions.cart.cart_jobs import expire_old_carts, delete_expired_carts
from app.functions.payment.payments_expired import cancel_expired_payments
from app.functions.product.discount import clear_expired_promotions
from app.functions.render.ping import keep_alive_ping

def start_scheduler():
    scheduler = BackgroundScheduler(timezone="UTC")

    # Roda a cada 10 minutos
    scheduler.add_job(expire_old_carts, "interval", minutes=10)

    # Roda 1x por dia, 4 da manhã UTC
    scheduler.add_job(delete_expired_carts, "cron", hour=3, minute=0)
    
    # Limpa promoções expiradas todo dia às 3 da manhã UTC
    scheduler.add_job(clear_expired_promotions, "cron", hour=3, minute=0)
    
    # Cancela pagamentos expirados a cada 5 minutos
    scheduler.add_job(cancel_expired_payments, "interval", minutes=1)
    
    # Ping de keep-alive a cada 5 minutos
    scheduler.add_job(keep_alive_ping, "interval", minutes=5)

    scheduler.start()
    