import os


def _setup_django():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gtus.settings')
    import django
    django.setup()


def run_filter_job(job_id):
    _setup_django()
    from apps.route.views import _run_filter_job
    _run_filter_job(job_id)


def run_route_plan_job(job_id):
    _setup_django()
    from apps.route.views import _run_route_plan_job
    _run_route_plan_job(job_id)
