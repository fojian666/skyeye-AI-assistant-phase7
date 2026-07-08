"""gtus URL Configuration

注意：WebSocket 路由不在此文件注册，而是在 gtus/asgi.py 中通过
ProtocolTypeRouter 的 "websocket" 分支配置（apps/drone_track/routing.py）。
urls.py 只处理普通 HTTP 请求。
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include, re_path

urlpatterns = [
                  path('admin/', admin.site.urls),
                  path('api/panorama/', include('apps.panorama.urls')),
                  path('api/system/', include('apps.system.urls')),
                  path('api/model/', include('apps.model.urls')),
                  path('api/report/', include('apps.report.urls')),
                  path('api/route/', include('apps.route.urls')),
                  path('api/resource/', include('apps.resource.urls')),

              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
