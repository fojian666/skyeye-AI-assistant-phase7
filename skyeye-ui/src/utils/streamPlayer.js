import flvjs from 'flv.js';
import { playWhipStream, stopWhipStream, normalizeWhipPlayUrl, applyStreamProxy } from './whipPlayer';

/**
 * 解析 webrtc://host:port/app/stream?token=xxx
 */
export function parseWebrtcSchemeUrl(url) {
    const match = url.match(/^webrtc:\/\/([^/]+)\/([^/]+)\/([^?]+)(\?(.*))?$/i);
    if (!match) {
        return null;
    }
    return {
        host: match[1],
        app: match[2],
        stream: match[3],
        query: match[5] || ''
    };
}

/**
 * 解析 rtmp://host/app/stream?token=xxx
 */
export function parseRtmpUrl(url) {
    const match = url.match(/^rtmp:\/\/([^/]+)\/([^/]+)\/([^?]+)(\?(.*))?$/i);
    if (!match) {
        return null;
    }
    return {
        host: match[1],
        app: match[2],
        stream: match[3],
        query: match[5] || ''
    };
}

/**
 * 清洗后端/配置里误拼接的流地址
 */
export function normalizeRawStreamUrl(url) {
    if (!url || typeof url !== 'string') return '';
    let normalized = url.trim();

    // 修复 https://host:portwebrtc://host:port/... 这类错误拼接
    const stuckIdx = normalized.toLowerCase().indexOf('webrtc://');
    if (stuckIdx > 0) {
        normalized = normalized.slice(stuckIdx);
    }

    // 从混合字符串中提取 webrtc 地址
    const embedded = normalized.match(/webrtc:\/\/[^/]+\/[^/]+\/[^?\s]+(?:\?[^\s]*)?/i);
    if (embedded) {
        normalized = embedded[0];
    }

    return normalized;
}

function getWebrtcPlayPath() {
    const cfg = window.config?.liveStreamPlay || {};
    let playPath = cfg.webrtcPlayPath || '/rtc/v1/whip-play/';
    // 防止把完整 webrtc:// 地址误填到 webrtcPlayPath
    if (typeof playPath !== 'string' || playPath.includes('://')) {
        playPath = '/rtc/v1/whep/';
    }
    if (!playPath.startsWith('/')) {
        playPath = `/${playPath}`;
    }
    if (!playPath.endsWith('/')) {
        playPath = `${playPath}/`;
    }
    return playPath;
}

/**
 * webrtc:// 转 WHEP/WHIP-Play HTTP 地址（浏览器可播放）
 */
export function convertWebrtcToPlayUrl(webrtcUrl) {
    const parsed = parseWebrtcSchemeUrl(normalizeRawStreamUrl(webrtcUrl));
    if (!parsed) {
        throw new Error('webrtc 地址格式无效');
    }
    const cfg = window.config?.liveStreamPlay || {};
    const playPath = getWebrtcPlayPath();
    const protocol = cfg.useHttps === false ? 'http' : 'https';
    const querySuffix = parsed.query ? `&${parsed.query}` : '';
    const directUrl = `${protocol}://${parsed.host}${playPath}?app=${encodeURIComponent(parsed.app)}&stream=${encodeURIComponent(
        parsed.stream
    )}${querySuffix}`;
    return applyStreamProxy(directUrl);
}

/**
 * rtmp:// 转 HTTP-FLV（需流媒体服务开启 FLV 拉流，flv.js 播放）
 */
export function convertRtmpToFlvUrl(rtmpUrl) {
    const parsed = parseRtmpUrl(rtmpUrl);
    if (!parsed) {
        throw new Error('rtmp 地址格式无效');
    }
    const cfg = window.config?.liveStreamPlay || {};
    const protocol = cfg.useHttps === false ? 'http' : 'https';
    let host = parsed.host;
    if (!host.includes(':') && cfg.rtmpFlvPort) {
        host = `${host}:${cfg.rtmpFlvPort}`;
    }
    const querySuffix = parsed.query ? `?${parsed.query}` : '';
    return `${protocol}://${host}/${parsed.app}/${parsed.stream}.flv${querySuffix}`;
}

/**
 * 识别流类型并解析为可播放地址
 */
export function resolveStreamPlayInfo(rawUrl) {
    if (!rawUrl || typeof rawUrl !== 'string') {
        return { type: 'unknown', rawUrl: '', playUrl: '' };
    }
    const url = normalizeRawStreamUrl(rawUrl);

    if (/^https?:\/\//i.test(url) && /whep|whip-play/i.test(url)) {
        return {
            type: 'whep',
            rawUrl: url,
            playUrl: applyStreamProxy(normalizeWhipPlayUrl(url))
        };
    }

    if (/^webrtc:\/\//i.test(url)) {
        return {
            type: 'webrtc',
            rawUrl: url,
            playUrl: convertWebrtcToPlayUrl(url)
        };
    }
    if (/^rtmp:\/\//i.test(url)) {
        return {
            type: 'rtmp',
            rawUrl: url,
            playUrl: convertRtmpToFlvUrl(url)
        };
    }
    if (/\.m3u8(\?|$)/i.test(url)) {
        return { type: 'hls', rawUrl: url, playUrl: url };
    }
    if (/\.flv(\?|$)/i.test(url)) {
        return { type: 'flv', rawUrl: url, playUrl: url };
    }
    if (/whip-play|\/whep\//i.test(url)) {
        return {
            type: 'whep',
            rawUrl: url,
            playUrl: applyStreamProxy(normalizeWhipPlayUrl(url))
        };
    }
    return { type: 'whep', rawUrl: url, playUrl: applyStreamProxy(normalizeWhipPlayUrl(url)) };
}

function playFlvStream(videoEl, url) {
    if (!flvjs.isSupported()) {
        return Promise.reject(new Error('当前浏览器不支持 FLV 播放'));
    }
    const player = flvjs.createPlayer(
        {
            type: 'flv',
            url,
            isLive: true,
            hasAudio: true
        },
        {
            enableWorker: false,
            enableStashBuffer: false,
            lazyLoad: false,
            autoCleanupSourceBuffer: true
        }
    );
    player.attachMediaElement(videoEl);
    player.load();
    return player.play().then(() => player);
}

/**
 * 统一拉流播放
 * @returns {Promise<{ type: string, whepPc?: RTCPeerConnection, flvPlayer?: object, playUrl: string, rawUrl: string }>}
 */
export async function playLiveStream(videoEl, rawUrl) {
    const info = resolveStreamPlayInfo(rawUrl);

    if (info.type === 'hls') {
        if (videoEl.canPlayType('application/vnd.apple.mpegurl')) {
            videoEl.src = info.playUrl;
            await videoEl.play().catch(() => {});
            return { ...info, hlsNative: true };
        }
        throw new Error('HLS 播放需要服务端提供 FLV/WebRTC 地址，或引入 hls.js');
    }

    if (info.type === 'flv' || info.type === 'rtmp') {
        videoEl.srcObject = null;
        const flvPlayer = await playFlvStream(videoEl, info.playUrl);
        return { ...info, flvPlayer };
    }

    const whepPc = await playWhipStream(videoEl, info.playUrl);
    return { ...info, whepPc };
}

export function stopLiveStream(playerState, videoEl) {
    if (!playerState) return;
    if (playerState.flvPlayer) {
        try {
            playerState.flvPlayer.pause();
            playerState.flvPlayer.unload();
            playerState.flvPlayer.detachMediaElement();
            playerState.flvPlayer.destroy();
        } catch (e) {
            // ignore
        }
    }
    if (playerState.whepPc) {
        stopWhipStream(playerState.whepPc, videoEl);
        return;
    }
    if (videoEl) {
        videoEl.pause();
        videoEl.removeAttribute('src');
        videoEl.srcObject = null;
        videoEl.load();
    }
}

/**
 * 从飞控平台接口 data 中取最佳播放地址
 */
export function pickStreamUrlFromResponse(data) {
    if (!data) return '';
    const httpUrl = data.httpUrl;
    if (httpUrl && /whep|whip-play/i.test(httpUrl)) {
        return httpUrl;
    }
    return data.webrtcUrl || httpUrl || data.liveStreamUrl || data.playUrl || data.play_flv || '';
}
