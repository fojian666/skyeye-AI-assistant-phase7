function waitIceGatheringComplete(pc, timeout = 5000) {
    if (pc.iceGatheringState === 'complete') {
        return Promise.resolve();
    }
    return new Promise((resolve) => {
        const timer = setTimeout(resolve, timeout);
        const checkState = () => {
            if (pc.iceGatheringState === 'complete') {
                clearTimeout(timer);
                pc.removeEventListener('icegatheringstatechange', checkState);
                resolve();
            }
        };
        pc.addEventListener('icegatheringstatechange', checkState);
    });
}

/**
 * 修正后端 URL 中 stream 参数误用 ?token= 的情况
 */
export function normalizeWhipPlayUrl(url) {
    if (!url || typeof url !== 'string') return url;
    return url.replace(/([?&]stream=[^&?#]+)\?token=/i, '$1&token=');
}

export function applyStreamProxy(playUrl) {
    const cfg = window.config?.liveStreamPlay || {};
    const prefix = cfg.proxyPrefix;
    const whepPath = cfg.proxyWhepPath;
    if ((!prefix && !whepPath) || !playUrl) return playUrl;

    const normalizedPath = whepPath ? (whepPath.startsWith('/') ? whepPath : `/${whepPath}`) : '';

    if (prefix && (playUrl.startsWith(`${prefix}/`) || playUrl === prefix)) {
        return playUrl;
    }
    if (normalizedPath && playUrl.startsWith(normalizedPath)) {
        return prefix ? `${prefix}${normalizedPath}${playUrl.slice(normalizedPath.length)}` : playUrl;
    }

    try {
        const u = new URL(playUrl, window.location.origin);
        if (!/^https?:$/i.test(u.protocol)) {
            return playUrl;
        }
        const hosts = cfg.proxyHosts;
        if (Array.isArray(hosts) && hosts.length && !hosts.includes(u.host)) {
            return playUrl;
        }
        if (normalizedPath) {
            const base = prefix || '';
            return `${base}${normalizedPath}${u.search}`;
        }
        return `${prefix}${u.pathname}${u.search}`;
    } catch (e) {
        return playUrl;
    }
}

export function buildWhepPlayCandidates(playUrl) {
    const cfg = window.config?.liveStreamPlay || {};
    const forceProxy = !!(cfg.proxyPrefix || cfg.proxyWhepPath);
    const normalized = applyStreamProxy(normalizeWhipPlayUrl(playUrl));
    const variants = [normalized];

    if (!cfg.proxyWhepPath) {
        if (normalized.includes('/whep/')) {
            variants.push(normalized.replace('/whep/', '/whip-play/'));
        } else if (normalized.includes('/whip-play/')) {
            variants.push(normalized.replace('/whip-play/', '/whep/'));
        }
    }

    const result = [];
    variants.forEach((url) => {
        const finalUrl = forceProxy ? url : applyStreamProxy(url);
        if (!result.includes(finalUrl)) result.push(finalUrl);
        if (!forceProxy && finalUrl !== url && !result.includes(url)) {
            result.push(url);
        }
    });
    return result;
}

function extractToken(url) {
    try {
        const u = new URL(url, window.location.origin);
        return u.searchParams.get('token');
    } catch (e) {
        return null;
    }
}

function buildFetchError(error, url) {
    const msg = (error && error.message) || '';
    const isProxy = url.startsWith('/live-stream-proxy');
    if (msg === 'Failed to fetch' || (error && error.name === 'TypeError')) {
        if (isProxy) {
            return new Error(
                `WHEP 代理请求失败：${url}。请确认已重启 npm run serve，且 vue.config.js / nginx 已配置 /live-stream-proxy 转发到流媒体服务`
            );
        }
        return new Error(`WHEP 请求失败（跨域 CORS）：${url}。请配置 liveStreamPlay.proxyPrefix: '/live-stream-proxy'`);
    }
    return error;
}

async function playWhipStreamOnce(videoEl, streamUrl) {
    const url = normalizeWhipPlayUrl(streamUrl);
    const pc = new RTCPeerConnection({
        iceServers: [{ urls: 'stun:stun.l.google.com:19302' }]
    });

    pc.addTransceiver('video', { direction: 'recvonly' });
    pc.addTransceiver('audio', { direction: 'recvonly' });

    pc.ontrack = (event) => {
        if (event.streams && event.streams[0] && videoEl) {
            videoEl.srcObject = event.streams[0];
        }
    };

    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);
    await waitIceGatheringComplete(pc);

    const token = extractToken(url);
    const headers = {
        'Content-Type': 'application/sdp',
        Accept: 'application/sdp'
    };
    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }

    let response;
    try {
        response = await fetch(url, {
            method: 'POST',
            headers,
            body: pc.localDescription.sdp
        });
    } catch (error) {
        pc.close();
        throw buildFetchError(error, url);
    }

    if (!response.ok) {
        pc.close();
        const errText = await response.text().catch(() => '');
        throw new Error(errText || `拉流失败(${response.status})：${url}`);
    }

    const answerSdp = await response.text();
    await pc.setRemoteDescription({ type: 'answer', sdp: answerSdp });

    if (videoEl) {
        videoEl.muted = true;
        await videoEl.play().catch(() => {});
    }

    return { pc, playUrl: url };
}

/**
 * 使用 WebRTC 播放 WHEP/WHIP-Play 流
 */
export async function playWhipStream(videoEl, streamUrl) {
    const candidates = buildWhepPlayCandidates(streamUrl);
    let lastError = null;

    for (const url of candidates) {
        try {
            const { pc } = await playWhipStreamOnce(videoEl, url);
            return pc;
        } catch (error) {
            lastError = error;
            console.warn('WHEP 尝试失败:', url, error);
        }
    }

    const tried = candidates.join(' | ');
    const err = lastError || new Error('所有 WHEP 播放地址均失败');
    err.message = `${err.message}。已尝试：${tried}`;
    throw err;
}

export function stopWhipStream(pc, videoEl) {
    if (pc) {
        pc.getSenders().forEach((sender) => sender.track && sender.track.stop());
        pc.close();
    }
    if (videoEl) {
        videoEl.pause();
        videoEl.srcObject = null;
    }
}
