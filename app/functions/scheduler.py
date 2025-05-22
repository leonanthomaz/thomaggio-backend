# # app/scheduler.py
# from apscheduler.schedulers.background import BackgroundScheduler
# from app.functions.cart import expire_old_carts, delete_expired_carts

# def start_scheduler():
#     scheduler = BackgroundScheduler(timezone="UTC")

#     # Roda a cada 10 minutos
#     scheduler.add_job(expire_old_carts, "interval", minutes=10)

#     # Roda 1x por dia, 4 da manhã UTC
#     scheduler.add_job(delete_expired_carts, "cron", hour=4, minute=0)

#     scheduler.start()


# pip install apscheduler

