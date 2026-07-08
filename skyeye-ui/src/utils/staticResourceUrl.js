const STATIC_PROXY_PREFIX = '/panoramaUrl';

/**
 * 将后端返回的绝对静态资源 URL 转为同源代理路径，避免 CORS。
 * 与 vue.config.js 中 /panoramaUrl -> baseUrl 代理及全景图资源加载方式一致。
 * @param {string} url
 * @returns {string}
 */
export function normalizeStaticResourceUrl(url) {
  if (!url || typeof url !== 'string') return url;

  const trimmed = url.trim();
  if (
    trimmed.startsWith(`${STATIC_PROXY_PREFIX}/`) ||
    trimmed === STATIC_PROXY_PREFIX
  ) {
    return trimmed;
  }

  if (trimmed.startsWith('/static/')) {
    return `${STATIC_PROXY_PREFIX}${trimmed}`;
  }

  const config = typeof window !== 'undefined' ? window.config : null;
  const bases = [config && config.baseUrl, config && config.panoramaUrl].filter(Boolean);

  for (const base of bases) {
    try {
      const baseOrigin = new URL(base.endsWith('/') ? base : `${base}/`).origin;
      if (trimmed.startsWith(baseOrigin)) {
        const pathname = trimmed.slice(baseOrigin.length);
        return `${STATIC_PROXY_PREFIX}${pathname.startsWith('/') ? pathname : `/${pathname}`}`;
      }
    } catch (e) {
      // ignore invalid base
    }
  }

  return trimmed;
}
