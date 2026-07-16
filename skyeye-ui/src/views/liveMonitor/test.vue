<template>
    <div class="whip-container">
        <div class="control-bar">
            <el-button type="primary" @click="startPlay" :loading="connecting" :disabled="playing"> ▶ 开始播放 </el-button>
            <el-button type="danger" @click="stopPlay" :disabled="!playing && !connecting"> ⏹ 停止播放 </el-button>
            <el-button @click="clearLogs">🗑 清空日志</el-button>
        </div>

        <div class="video-area">
            <video ref="videoPlayer" autoplay muted playsinline class="video-player" :class="{ 'has-stream': playing }"></video>
            <div class="status-overlay" :class="statusClass">
                <span>{{ statusText }}</span>
            </div>
        </div>

        <div class="info-panel">
            <div class="stats" v-if="playing">
                <div class="stat">
                    <span class="label">连接状态：</span>
                    <span class="value">{{ connectionState }}</span>
                </div>
                <div class="stat">
                    <span class="label">ICE 状态：</span>
                    <span class="value">{{ iceState }}</span>
                </div>
                <div class="stat">
                    <span class="label">视频状态：</span>
                    <span class="value">{{ videoState }}</span>
                </div>
            </div>
        </div>

        <div class="log-area">
            <div v-for="(log, index) in logs" :key="index" :class="['log-item', `log-${log.type}`]">
                <span class="log-time">{{ log.time }}</span>
                <span class="log-message">{{ log.message }}</span>
            </div>
        </div>
    </div>
</template>

<script>
import { applyStreamProxy, normalizeWhipPlayUrl } from '@/utils/whipPlayer';

export default {
    name: 'WHIPVideoPlayer',
    data() {
        return {
            whipUrl: 'http://127.0.0.1:8088/drone-whep',
            // WebRTC 配置
            peerConnection: null,
            connecting: false,
            playing: false,

            // 状态显示
            statusText: '未连接',
            statusClass: '',
            connectionState: '-',
            iceState: '-',
            videoState: '-',

            // 日志
            logs: [],

            // 定时器
            statsTimer: null,

            // 重连计数
            reconnectCount: 0
        };
    },

    mounted() {
        //this.whipUrl = this.resolveWhipUrl();
        this.addLog('组件初始化完成', 'info');
        this.addLog('WHIP 端点: ' + (this.whipUrl || '未配置'), 'info');
        this.checkBrowserSupport();
    },

    beforeDestroy() {
        this.cleanup();
    },

    methods: {
        resolveWhipUrl() {
            const queryUrl = this.$route.query.httpUrl || this.$route.query.whipUrl;
            if (queryUrl) {
                return applyStreamProxy(normalizeWhipPlayUrl(decodeURIComponent(queryUrl)));
            }

            const cfg = window.config?.liveStreamPlay || {};
            const prefix = cfg.proxyPrefix || '/live-stream-proxy';
            const whepPath = cfg.proxyWhepPath || '/drone-whep';
            const app = this.$route.query.app || 'live';
            const stream = this.$route.query.stream || '';
            const token = this.$route.query.token || '';

            if (!stream || !token) {
                return '';
            }

            const params = new URLSearchParams({ app, stream, token });
            return `${prefix}${whepPath}?${params.toString()}`;
        },

        extractToken(url) {
            try {
                const u = new URL(url, window.location.origin);
                return u.searchParams.get('token');
            } catch (e) {
                return null;
            }
        },

        // 添加日志
        addLog(message, type = 'info') {
            const now = new Date();
            const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now
                .getSeconds()
                .toString()
                .padStart(2, '0')}`;

            this.logs.unshift({
                time: time,
                message: message,
                type: type
            });

            // 限制日志数量
            if (this.logs.length > 200) {
                this.logs.pop();
            }

            console.log(`[${type.toUpperCase()}]`, message);
        },

        // 清空日志
        clearLogs() {
            this.logs = [];
            this.addLog('日志已清空', 'info');
        },

        // 检查浏览器支持
        checkBrowserSupport() {
            if (!window.RTCPeerConnection) {
                this.addLog('当前浏览器不支持 WebRTC，请使用 Chrome/Edge/Firefox', 'error');
                this.statusText = '浏览器不支持';
                this.statusClass = 'error';
                return false;
            }
            this.addLog('浏览器支持 WebRTC', 'success');
            return true;
        },

        // 更新状态显示
        updateStatus(text, isError = false) {
            this.statusText = text;
            this.statusClass = isError ? 'error' : this.playing ? 'connected' : '';
        },

        // 清理资源
        cleanup() {
            if (this.statsTimer) {
                clearInterval(this.statsTimer);
                this.statsTimer = null;
            }

            if (this.peerConnection) {
                this.peerConnection.close();
                this.peerConnection = null;
            }

            const video = this.$refs.videoPlayer;
            if (video && video.srcObject) {
                const tracks = video.srcObject.getTracks();
                tracks.forEach((track) => track.stop());
                video.srcObject = null;
            }
        },

        // 停止播放
        stopPlay() {
            this.cleanup();
            this.connecting = false;
            this.playing = false;
            this.connectionState = '-';
            this.iceState = '-';
            this.videoState = '-';
            this.updateStatus('已停止');
            this.addLog('播放已停止', 'warning');
        },

        // 等待 ICE 收集完成
        waitForIceGathering() {
            return new Promise((resolve) => {
                if (this.peerConnection.iceGatheringState === 'complete') {
                    resolve();
                } else {
                    const timeout = setTimeout(() => {
                        this.addLog('ICE 收集超时，使用当前候选', 'warning');
                        resolve();
                    }, 3000);

                    const checkState = () => {
                        if (this.peerConnection.iceGatheringState === 'complete') {
                            clearTimeout(timeout);
                            this.peerConnection.removeEventListener('icegatheringstatechange', checkState);
                            resolve();
                        }
                    };
                    this.peerConnection.addEventListener('icegatheringstatechange', checkState);
                }
            });
        },

        // 开始播放
        async startPlay() {
            if (this.connecting) {
                this.addLog('正在连接中，请稍后', 'warning');
                return;
            }

            if (!this.checkBrowserSupport()) {
                return;
            }

            if (!this.whipUrl) {
                this.addLog('缺少 stream/token 参数，请通过 URL 传入 httpUrl 或 stream+token', 'error');
                this.updateStatus('未配置拉流地址', true);
                return;
            }

            // 清理旧连接
            this.stopPlay();

            this.connecting = true;
            this.updateStatus('连接中...');
            this.addLog('========== 开始建立 WHIP 连接 ==========', 'info');

            // 创建 RTCPeerConnection
            const config = {
                iceServers: [
                    { urls: 'stun:stun.l.google.com:19302' },
                    { urls: 'stun:stun1.l.google.com:19302' },
                    { urls: 'stun:stun2.l.google.com:19302' },
                    { urls: 'stun:stun3.l.google.com:19302' },
                    { urls: 'stun:stun4.l.google.com:19302' }
                ],
                iceCandidatePoolSize: 10
            };

            this.peerConnection = new RTCPeerConnection(config);
            this.addLog('RTCPeerConnection 创建成功', 'success');

            // 接收视频流
            this.peerConnection.ontrack = (event) => {
                this.addLog(`收到 ${event.track.kind} 轨道`, 'success');

                if (event.track.kind === 'video') {
                    const video = this.$refs.videoPlayer;
                    if (video && event.streams[0]) {
                        video.srcObject = event.streams[0];
                        this.playing = true;
                        this.connecting = false;
                        this.updateStatus('已连接');
                        this.addLog('✅ 视频流加载成功！', 'success');

                        // 监听视频轨道状态
                        event.track.onunmute = () => {
                            this.videoState = '播放中';
                            this.addLog('视频轨道已启用', 'success');
                        };
                        event.track.onmute = () => {
                            this.videoState = '暂停';
                            this.addLog('视频轨道已静音', 'warning');
                        };
                    }
                }
            };

            // ICE 候选（只记录，不主动发送，等待服务器响应）
            this.peerConnection.onicecandidate = (event) => {
                if (event.candidate) {
                    const candidateType = event.candidate.type;
                    const address = event.candidate.address || event.candidate.ip;
                    this.addLog(`ICE 候选 [${candidateType}]: ${address}`, 'info');
                } else {
                    this.addLog('ICE 候选收集完成', 'success');
                }
            };

            // 连接状态
            this.peerConnection.onconnectionstatechange = () => {
                const state = this.peerConnection.connectionState;
                this.connectionState = state;
                this.addLog(`连接状态: ${state}`, 'info');

                if (state === 'connected') {
                    this.addLog('🎉 WebRTC 连接已建立', 'success');
                    // 启动状态监控
                    this.startStatsMonitor();
                } else if (state === 'failed') {
                    this.addLog('❌ 连接失败，可能是网络问题', 'error');
                    this.updateStatus('连接失败', true);
                    this.connecting = false;
                } else if (state === 'disconnected') {
                    this.addLog('连接断开，尝试重连...', 'warning');
                }
            };

            // ICE 连接状态
            this.peerConnection.oniceconnectionstatechange = () => {
                const state = this.peerConnection.iceConnectionState;
                this.iceState = state;
                this.addLog(`ICE 状态: ${state}`, 'info');

                if (state === 'failed') {
                    this.addLog('ICE 连接失败，可能需要 TURN 服务器', 'error');
                } else if (state === 'connected') {
                    this.addLog('ICE 连接成功', 'success');
                }
            };

            // 创建 Offer
            this.addLog('创建 SDP Offer...', 'info');
            const offer = await this.peerConnection.createOffer({
                offerToReceiveVideo: true,
                offerToReceiveAudio: false
            });

            this.addLog('Offer 创建成功', 'success');
            await this.peerConnection.setLocalDescription(offer);
            this.addLog('本地 SDP 设置完成', 'success');

            // 等待 ICE 收集
            this.addLog('等待 ICE 候选收集...', 'info');
            await this.waitForIceGathering();

            // 获取完整的 SDP（包含所有 ICE 候选）
            const fullSdp = this.peerConnection.localDescription.sdp;
            this.addLog(`完整 SDP 长度: ${fullSdp.length} 字节`, 'info');

            // 发送 WHIP 请求
            this.addLog('发送 WHIP POST 请求...', 'info');
            const token = this.extractToken(this.whipUrl);
            const headers = {
                'Content-Type': 'application/sdp',
                Accept: 'application/sdp'
            };
            if (token) {
                headers.Authorization = `Bearer ${token}`;
            }

            const response = await fetch(this.whipUrl, {
                method: 'POST',
                headers,
                body: fullSdp
            });

            this.addLog(`服务器响应: ${response.status} ${response.statusText}`, 'info');

            // WHIP 协议：201 或 200 表示成功
            if (response.status === 201 || response.status === 200) {
                const answerSdp = await response.text();
                this.addLog(`收到 Answer SDP，长度: ${answerSdp.length} 字节`, 'success');

                // 检查 Answer 是否有效
                if (!answerSdp || answerSdp.length < 10) {
                    throw new Error('Answer SDP 无效');
                }

                // 设置远程描述
                await this.peerConnection.setRemoteDescription({
                    type: 'answer',
                    sdp: answerSdp
                });

                this.addLog('远程 SDP 设置成功', 'success');
                this.addLog('WHIP 协商完成，等待视频流...', 'success');
            } else if (response.status === 502) {
                throw new Error('后端服务不可用 (502)');
            } else {
                const errorText = await response.text();
                throw new Error(`HTTP ${response.status}: ${errorText.substring(0, 100)}`);
            }
        },

        // 启动状态监控
        startStatsMonitor() {
            if (this.statsTimer) {
                clearInterval(this.statsTimer);
            }

            this.statsTimer = setInterval(async () => {
                if (!this.peerConnection || !this.playing) return;

                try {
                    const stats = await this.peerConnection.getStats();
                    let videoBytes = 0;
                    let packetsReceived = 0;

                    stats.forEach((report) => {
                        if (report.type === 'inbound-rtp' && report.kind === 'video') {
                            videoBytes = report.bytesReceived || 0;
                            packetsReceived = report.packetsReceived || 0;
                        }
                    });

                    if (videoBytes > 0) {
                        this.videoState = `播放中 (${(videoBytes / 1024).toFixed(0)} KB)`;
                    }
                } catch (e) {
                    // 忽略统计错误
                }
            }, 2000);
        }
    }
};
</script>

<style scoped>
.whip-container {
    background: #0a0a0a;
    min-height: 100vh;
    padding: 20px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.control-bar {
    display: flex;
    gap: 12px;
    margin-bottom: 20px;
    flex-wrap: wrap;
}

.video-area {
    position: relative;
    background: #000;
    border-radius: 12px;
    overflow: hidden;
    margin-bottom: 20px;
    min-height: 450px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.video-player {
    width: 100%;
    max-height: 70vh;
    object-fit: contain;
}

.video-player.has-stream {
    border: 2px solid #4caf50;
}

.status-overlay {
    position: absolute;
    top: 15px;
    right: 15px;
    background: rgba(0, 0, 0, 0.75);
    backdrop-filter: blur(5px);
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
    font-family: monospace;
    z-index: 10;
}

.status-overlay.connected {
    background: #4caf50;
    box-shadow: 0 0 10px rgba(76, 175, 80, 0.5);
}

.status-overlay.error {
    background: #f44336;
}

.info-panel {
    background: #1e1e1e;
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 15px;
}

.stats {
    display: flex;
    gap: 24px;
    flex-wrap: wrap;
}

.stat {
    font-size: 13px;
}

.stat .label {
    color: #888;
    margin-right: 6px;
}

.stat .value {
    color: #4caf50;
    font-family: monospace;
    font-weight: 500;
}

.log-area {
    background: #1e1e1e;
    border-radius: 10px;
    padding: 12px;
    max-height: 280px;
    overflow-y: auto;
    font-family: 'Courier New', monospace;
    font-size: 12px;
}

.log-item {
    padding: 5px 8px;
    margin-bottom: 4px;
    border-left: 3px solid;
    border-radius: 4px;
    display: flex;
    gap: 12px;
}

.log-time {
    color: #666;
    font-family: monospace;
    min-width: 65px;
}

.log-message {
    color: #ccc;
    word-break: break-all;
}

.log-info {
    border-left-color: #2196f3;
    background: rgba(33, 150, 243, 0.05);
}

.log-success {
    border-left-color: #4caf50;
    background: rgba(76, 175, 80, 0.05);
}

.log-success .log-message {
    color: #a5d6a7;
}

.log-error {
    border-left-color: #f44336;
    background: rgba(244, 67, 54, 0.05);
}

.log-error .log-message {
    color: #ff9a9a;
}

.log-warning {
    border-left-color: #ff9800;
    background: rgba(255, 152, 0, 0.05);
}

.log-warning .log-message {
    color: #ffcc80;
}
</style>
