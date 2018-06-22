from celery import Celery

# 创建celery对象
celery_app = Celery('meiduo')

# 导入任务
celery_app.autodiscover_tasks(['celery_tasks.sms'])