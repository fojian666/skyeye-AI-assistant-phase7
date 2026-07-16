/**
 * 处理统一认证登录后返回的认证信息
 * 将token、刷新token存储在本地
 */
(() => {
    const url = location.href;
    // 获取url中的st, rst, expires参数
    const params = getUrlParams(url);
    if (params['portal-url']) {
        sessionStorage.setItem('portal-url', decodeURIComponent(params['portal-url']));
    }
    if (params.st && params.rst && params.expires) {
        sessionStorage.setItem('token', params.st);
        sessionStorage.setItem('refreshToken', params.rst);
        sessionStorage.setItem('expires', params.expires);
        // 删除url中的st, rst, expires参数
        const newUrl = removeURLParameters(url, ['st', 'rst', 'expires', 'portal-url']);
        // window.history.replaceState({}, document.title, newUrl);
        window.location.href = newUrl;
    }
})();

/**
 * 获取URL参数的函数
 * @param url - 需要解析的URL
 * @returns 包含所有参数的对象
 */
function getUrlParams(url) {
    if (!url) return {};
    // 创建一个 URL 对象
    const urlObj = new URL(url);
    // 获取标准查询参数部分
    const urlParams = new URLSearchParams(urlObj.search);
    const params = {};
    // 遍历查询参数并添加到对象中
    for (const [key, value] of urlParams.entries()) {
        params[key] = value;
    }

    // 获取 hash 部分并解析其中的查询参数（如果有）
    if (urlObj.hash.includes('?')) {
        const hashQueryString = urlObj.hash.split('?')[1];
        const hashParams = new URLSearchParams(hashQueryString);
        for (const [key, value] of hashParams.entries()) {
            params[key] = value;
        }
    }
    return params;
}

/**
 * 移除URL中的参数
 * @param url
 * @param parameters
 * @returns
 */
function removeURLParameters(url, parameters) {
    const urlParts = url.split('?'); // 通过问号将 URL 分割成两部分
    if (urlParts.length >= 2) {
        const baseUrl = urlParts[0]; // 获取基本 URL 部分
        const queryString = urlParts[1]; // 获取参数部分
        // 将参数部分拆分成数组
        const parameterPairs = queryString.split('&');
        // 过滤掉要删除的参数
        const filteredPairs = parameterPairs.filter((pair) => {
            const paramName = pair.split('=')[0];
            return !parameters.includes(paramName);
        });
        // 重新构建 URL
        url = baseUrl + '?' + filteredPairs.join('&');
        // 处理 # 符号
        if (urlParts.length >= 3) {
            url += '?' + urlParts.slice(2).join('?');
        }
    }
    return url;
}
