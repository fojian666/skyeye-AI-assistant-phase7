<template>
  <div class="chat-wrapper" :class="`theme-${theme}`" :style="wrapperStyle">
    <!-- 悬浮按钮 -->
    <div v-if="!visible" class="chat-fab" @click="open" @mousedown="startDrag" title="AI 助手">
        <span class="fab-emoji">🤖</span>
        <span class="fab-label">AI 助手</span>
      </div>

    <!-- 聊天窗口 -->
      <div v-show="visible" ref="panel" :class="['chat-panel', { docked }]">
        <!-- 头部 -->
        <div class="chat-header" @mousedown="startDrag">
          <div class="chat-header-left">
            <span class="chat-logo-emoji">&#x1F916;</span>
            <div>
              <strong>天巡 AI 助手</strong>
              <small>Powered by DeepSeek</small>
            </div>
          </div>
          <div class="chat-header-right">
            <button class="chat-btn-icon" :title="docked ? '取消吸附' : '吸附到右侧'" @click="docked = !docked">
              <i :class="docked ? 'el-icon-d-arrow-left' : 'el-icon-d-arrow-right'"></i>
            </button>
            <button class="chat-btn-icon" title="清空对话" @click="clearMessages">
              <i class="el-icon-delete"></i>
            </button>
            <button class="chat-btn-icon" title="关闭" @click="closeChat">
              <i class="el-icon-close"></i>
            </button>
          </div>
        </div>

        <!-- 消息列表 -->
        <div class="chat-body" ref="chatBody">
          <div v-if="messages.length === 0" class="chat-empty">
            <span class="empty-emoji">&#x1F916;</span>
            <p>你好！我是天巡 AI 助手</p>
            <span>可以问我关于无人机巡检、航线规划、全景分析等问题</span>
            <div class="quick-questions">
              <button v-for="q in quickQuestions" :key="q" @click="sendQuick(q)">{{ q }}</button>
            </div>
          </div>

          <div
            v-for="(msg, idx) in messages"
            :key="idx"
            v-show="msg.role !== 'tool'"
            class="chat-msg"
            :class="msg.role">
            <div class="msg-avatar">
              <i v-if="msg.role === 'user'" class="el-icon-user"></i>
              <span v-else-if="msg.role === 'tool-info'" class="avatar-emoji">&#x1F4CD;</span>
              <span v-else class="avatar-emoji">&#x1F916;</span>
            </div>
            <div class="msg-content" v-if="msg.role === 'tool-info'" style="background:rgba(0,243,255,0.08);font-style:italic">
              {{ msg.content }}
            </div>
            <div class="msg-content" v-else-if="msg.role === 'tool'">
              <!-- tool messages are hidden -->
            </div>
            <div class="msg-content" v-else v-html="renderContent(msg.content)"></div>
          </div>

          <!-- 打字中 -->
          <div v-if="streaming" class="chat-msg assistant">
            <div class="msg-avatar">
              <span class="avatar-emoji">&#x1F916;</span>
            </div>
            <div class="msg-content streaming-cursor">{{ streamingText || '思考中...' }}</div>
          </div>
        </div>

        <!-- 输入区 -->
        <div class="chat-footer">
          <textarea
            ref="inputArea"
            v-model="input"
            class="chat-input"
            :placeholder="streaming ? 'AI 正在回复...' : '输入消息，Enter 发送，Shift+Enter 换行'"
            :disabled="streaming"
            rows="1"
            @keydown.enter.exact.prevent="send"
            @input="autoResize"
          ></textarea>
          <button
            class="chat-send-btn"
            :disabled="!input.trim() || streaming"
            @click="send">
            <i class="el-icon-position"></i>
          </button>
        </div>
      </div>
  </div>
</template>

<script>
import axios from 'axios';
import router from '@/router'
import { mapState } from 'vuex';
import gsap from 'gsap';

const ROUTES = [
  { path: '/task-mgmt',             title: '任务管理' },
  { path: '/data-management',       title: '低空数据管理（一张图/地图）' },
  { path: '/route-planning',        title: '航线规划' },
  { path: '/panoramic-detection',   title: '全景检测（全景观测/全景图/全景任务）' },
  { path: '/pattern-verifiy',       title: '图斑核实' },
  { path: '/data_overview',         title: '统计大屏' },
];

const TOOLS = [
  {
    type: 'function',
    function: {
      name: 'navigate_page',
      description:
        '跳转到系统的页面。根据用户意图从下面列表中选择最匹配的路由：\n' +
        ROUTES.map(r => `  ${r.path} → ${r.title}`).join('\n'),
      parameters: {
        type: 'object',
        properties: {
          path: { type: 'string', description: '目标页面路由路径，必须从上面的路由列表中选择' },
          reason: { type: 'string', description: '简短说明跳转原因' },
        },
        required: ['path', 'reason'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'map_action',
      description: '地图相关操作。用户提到任何地点/区域/行政区时必须调用此工具，不要反问。系统会自动定位并绘制边界。',
      parameters: {
        type: 'object',
        properties: {
          location: { type: 'string', description: '目标地点/区域名称，如城市名、区名、街道名、地标名' },
          city: { type: 'string', description: '所在城市，默认南京' },
        },
        required: ['location'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'query_data',
      description: '查询系统数据，如资源数量、任务状态、航线信息等',
      parameters: {
        type: 'object',
        properties: {
          query: { type: 'string', description: '用户想问的问题或要查询的内容' },
        },
        required: ['query'],
      },
    },
  },
];

export default {
  name: 'ChatModel',
  data() {
    return {
      visible: false,
      input: '',
      messages: [],
      streaming: false,
      streamingText: '',
      dragging: false,
      hasMoved: false,
      dragPos: { x: null, y: null },
      dragStart: { x: 0, y: 0, elX: 0, elY: 0 },
      docked: false,
      quickQuestions: [
        '带我去南京鼓楼区看看',
        '带我去航线规划页面',
        '打开全景检测',
      ],
    }
  },
  computed: {
    ...mapState({ theme: state => state.theme }),
    wrapperStyle() {
      if (this.docked) {
        return { right: '0', top: '0', bottom: '0', left: 'auto', width: '400px', height: '100%' }
      }
      if (this.dragPos.x != null) {
        return {
          right: 'auto',
          bottom: 'auto',
          left: this.dragPos.x + 'px',
          top: this.dragPos.y + 'px',
        }
      }
      return { right: '32px', bottom: '32px' }
    },
  },
  mounted() {
    this._onDragMove = this.onDragMove.bind(this)
    this._onDragEnd = this.onDragEnd.bind(this)
    document.addEventListener('mousemove', this._onDragMove)
    document.addEventListener('mouseup', this._onDragEnd)
  },
  beforeDestroy() {
    document.removeEventListener('mousemove', this._onDragMove)
    document.removeEventListener('mouseup', this._onDragEnd)
  },
  methods: {
    startDrag(e) {
      // 不干扰按钮点击
      if (e.target.closest('.chat-btn-icon') || e.target.closest('.chat-send-btn')) return
      e.preventDefault()
      const rect = this.$el.getBoundingClientRect()
      this.dragging = true
      this.hasMoved = false
      this.dragStart = {
        x: e.clientX,
        y: e.clientY,
        elX: rect.left,
        elY: rect.top,
      }
    },
    onDragMove(e) {
      if (!this.dragging) return
      const dx = e.clientX - this.dragStart.x
      const dy = e.clientY - this.dragStart.y
      // 超过 4px 才算拖拽，防止误判
      if (Math.abs(dx) < 4 && Math.abs(dy) < 4) return
      this.hasMoved = true
      const w = this.visible ? 400 : 56
      const h = this.visible ? 560 : 56
      let nx = this.dragStart.elX + (e.clientX - this.dragStart.x)
      let ny = this.dragStart.elY + (e.clientY - this.dragStart.y)

      // 触碰边界时重置参考点，防止粘连
      if (nx < 0)          { nx = 0;           this.dragStart.x = e.clientX; this.dragStart.elX = 0 }
      if (nx > innerWidth  - w) { nx = innerWidth  - w; this.dragStart.x = e.clientX; this.dragStart.elX = nx }
      if (ny < 0)          { ny = 0;           this.dragStart.y = e.clientY; this.dragStart.elY = 0 }
      if (ny > innerHeight - h) { ny = innerHeight - h; this.dragStart.y = e.clientY; this.dragStart.elY = ny }

      this.dragPos = { x: nx, y: ny }
    },
    onDragEnd() {
      this.dragging = false
    },
    open() {
      // 拖拽后不触发点击打开
      if (this.hasMoved) return
      // 跳转后的残留消息，重置为欢迎界面
      if (this.messages.length === 1 && this.messages[0].content.startsWith('已为您跳转到')) {
        this.messages = []
      }
      // 展开面板前，确保面板不超出屏幕
      let x = this.dragPos.x != null ? this.dragPos.x : window.innerWidth - 24 - 56
      let y = this.dragPos.y != null ? this.dragPos.y : window.innerHeight - 24 - 56
      const pw = 400, ph = 560
      if (x + pw > window.innerWidth) x = window.innerWidth - pw - 12
      if (y + ph > window.innerHeight) y = window.innerHeight - ph - 12
      this.dragPos = { x: Math.max(0, x), y: Math.max(0, y) }
      this.visible = true
      this.$nextTick(() => {
        const panel = this.$refs.panel
        if (panel) {
          gsap.fromTo(panel,
            { scale: 0.1, opacity: 0 },
            { scale: 1, opacity: 1, duration: 0.4, ease: 'back.out(1.7)' }
          )
        }
        this.$refs.inputArea?.focus()
        this.scrollToBottom()
      })
    },

    resolveRoute(path) {
      const m = {
        '/task-mgmt':           '/task-mgmt/verify-clue',
        '/data-management':     '/data-management/one-map',
        '/route-planning':      '/route-planning/manual-planning',
        '/panoramic-detection': '/panoramic-detection/task-management',
        '/pattern-verifiy':     '/pattern-verifiy/map_overview',
      }
      return m[path] || path
    },

    closeChat() {
      this.visible = false
      this.docked = false
      this.dragPos = { x: null, y: null }
      this.messages = []
    },

    sendQuick(question) {
      this.input = question
      this.send()
    },

    async send() {
      const text = this.input.trim()
      if (!text || this.streaming) return

      this.messages.push({ role: 'user', content: text })
      this.input = ''
      this.$nextTick(() => this.autoResize())
      this.streaming = true

      await this.chatLoop()
    },

    async chatLoop() {
      const allMessages = this.messages
          .filter(m => m.role !== 'tool-info' && m.role !== 'tool' && !m.tool_calls)
          .map(m => ({ role: m.role, content: m.content }))

      try {
        const { data } = await axios({
          method: 'POST',
          url: 'http://127.0.0.1:8009/api/system/chat/completions',
          data: { messages: allMessages, tools: TOOLS },
          withCredentials: false,
        })
        const result = data.result || data.data || {}
        const finishReason = result.finish_reason

        // 处理工具调用
        if (result.tool_calls && finishReason === 'tool_calls') {
          const assistantMsg = { role: 'assistant', content: '', tool_calls: result.tool_calls }
          if (result.content) assistantMsg.content = result.content
          this.messages.push(assistantMsg)

          // 执行每个工具
          for (const tc of result.tool_calls) {
            const fn = tc.function
            const args = JSON.parse(fn.arguments)
            const toolResult = await this.executeTool(fn.name, args)
            // 导航类工具执行后直接结束，清空消息历史
            if (toolResult._stop) {
              this.messages = []
              this.dragPos = { x: null, y: null }
              const label = fn.name === 'map_action'
                ? (args.name || args.location)
                : (args.reason || args.path)
              this.messages.push({ role: 'assistant', content: `已为您跳转到 ${label}` })
              this.streaming = false
              return
            }
            this.messages.push({
              role: 'tool',
              tool_call_id: tc.id,
              content: JSON.stringify(toolResult),
            })
          }
          // 继续对话循环（非导航类工具）
          await this.chatLoop()
          return
        }

        // 普通文本回复
        const content = result.content || ''
        await this.typewriter(content)
      } catch (err) {
        const msg = err.response?.data?.msg || err.message
        this.messages.push({ role: 'assistant', content: `抱歉，请求失败：${msg}` })
        this.streaming = false
      }
    },

    async executeTool(name, args) {
      if (name === 'navigate_page') {
        const path = this.resolveRoute(args.path)
        this.messages.push({ role: 'tool-info', content: `正在跳转到：${args.reason}` })
        this.$nextTick(() => {
          this.visible = false
          router.push(path).catch(() => {})
        })
        return { _stop: true, path, reason: args.reason }
      }
      if (name === 'map_action') {
        const detail = {
          name: args.name || args.location,
          location: args.location,
          polygon: args.polygon || [],
          lat: args.lat,
          lng: args.lng,
          city: args.city || '南京',
        }
        const hasPolygon = detail.polygon && detail.polygon.length > 0
        this.messages.push({ role: 'tool-info', content: hasPolygon
          ? `正在定位并圈定 ${detail.name}...`
          : `正在定位到 ${detail.name}...` })
        const dispatch = () => {
          if (hasPolygon) window.dispatchEvent(new CustomEvent('draw-region', { detail }))
          if (detail.lat != null) window.dispatchEvent(new CustomEvent('navigate-map', { detail }))
        }
        if (this.$route.path !== '/data-management/one-map') {
          router.push('/data-management/one-map')
          setTimeout(dispatch, 1500)
        } else {
          dispatch()
        }
        return { _stop: true, success: true, ...detail }
      }
      if (name === 'query_data') {
        return { message: `关于"${args.query}"的查询已收到，具体数据需要通过系统界面查看。` }
      }
      return { error: `未知工具: ${name}` }
    },

    async typewriter(text) {
      this.streamingText = ''
      const chars = [...text]
      const renderInline = (raw) => {
        let t = raw
          .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
          .replace(/\*\*[^*]*$/, m => m.slice(2))
          .replace(/\*([^*]+)\*/g, '<em>$1</em>')
          .replace(/\*([^*]*)$/, '')
          .replace(/`([^`]+)`/g, '<code>$1</code>')
          .replace(/`([^`]*)$/, '')
          .replace(/```\w*\n?([\s\S]*)$/, (_, c) => c ? `<pre><code>${c}</code></pre>` : '')
        return t
      }
      for (let i = 0; i < chars.length; i++) {
        this.streamingText = renderInline(this.streamingText.replace(/<[^>]*>/g, '') + chars[i])
        await new Promise(r => setTimeout(r, 25))
        this.scrollToBottom()
      }
      this.messages.push({ role: 'assistant', content: text })
      this.streamingText = ''
      this.streaming = false
    },

    clearMessages() {
      this.messages = []
    },

    scrollToBottom() {
      this.$nextTick(() => {
        const el = this.$refs.chatBody
        if (el) el.scrollTop = el.scrollHeight
      })
    },

    autoResize() {
      this.$nextTick(() => {
        const el = this.$refs.inputArea
        if (el) {
          el.style.height = 'auto'
          el.style.height = Math.min(el.scrollHeight, 120) + 'px'
        }
      })
    },

    renderContent(text) {
      if (!text) return ''
      const codeBlocks = []
      let processed = text
        .replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) => {
          codeBlocks.push(`<pre><code>${this.esc(code.trim())}</code></pre>`)
          return `%%CODEBLOCK_${codeBlocks.length - 1}%%`
        })
        .replace(/`([^`]+)`/g, (_, code) => {
          codeBlocks.push(`<code>${this.esc(code)}</code>`)
          return `%%CODEBLOCK_${codeBlocks.length - 1}%%`
        })
      processed = this.esc(processed)
      processed = processed.replace(/\n/g, '<br>')
      processed = processed
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        .replace(/\*([^*]+)\*/g, '<em>$1</em>')
      processed = processed.replace(/%%CODEBLOCK_(\d+)%%/g, (_, i) => codeBlocks[+i])
      return processed
    },
    esc(s) {
      return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    },
  },
}
</script>

<style lang="scss" scoped>
.chat-wrapper {
  position: fixed;
  z-index: 9999;
}

/* 悬浮按钮 — 灵动岛胶囊形 */
.chat-fab {
  height: 48px;
  min-width: 48px;
  padding: 0 18px;
  border-radius: 28px;
  background: rgba(0, 0, 0, 0.55);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25), 0 0 0 1px rgba(255, 255, 255, 0.06) inset;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
  cursor: pointer;
  color: #fff;
  user-select: none;
  transition:
    all 0.55s cubic-bezier(0.16, 1, 0.3, 1),
    gap 0.45s 0.08s,
    padding 0.45s 0.08s;

  &:hover {
    transform: scale(1.05);
    min-width: auto;
    padding: 0 22px 0 20px;
    gap: 7px;
    background: rgba(0, 0, 0, 0.7);
    border-color: rgba(255, 255, 255, 0.28);
    box-shadow:
      0 16px 48px rgba(0, 0, 0, 0.4),
      0 0 20px rgba(59, 130, 246, 0.2),
      0 0 0 1px rgba(255, 255, 255, 0.12) inset;
  }

  .fab-emoji {
    font-size: 22px;
    line-height: 1;
    transition: transform 0.55s cubic-bezier(0.16, 1, 0.3, 1);
  }

  &:hover .fab-emoji {
    transform: rotate(-12deg) scale(1.15);
  }

  .fab-label {
    font-size: 13px;
    font-weight: 600;
    white-space: nowrap;
    max-width: 0;
    overflow: hidden;
    opacity: 0;
    transition:
      max-width 0.5s cubic-bezier(0.16, 1, 0.3, 1),
      opacity 0.35s 0.1s;
  }

  &:hover .fab-label {
    max-width: 80px;
    opacity: 1;
  }
}

/* 聊天面板 — 毛玻璃 */
.chat-panel {
  width: 400px;
  height: 560px;
  border-radius: 20px;
  background: rgba(12, 20, 40, 0.72);
  backdrop-filter: blur(24px) saturate(1.2);
  -webkit-backdrop-filter: blur(24px) saturate(1.2);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow:
    0 24px 64px rgba(0, 0, 0, 0.45),
    0 0 0 1px rgba(255, 255, 255, 0.05) inset,
    0 1px 0 rgba(255, 255, 255, 0.06) inset;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transform-origin: bottom right;
  will-change: transform, opacity;
  transition: height 0.3s ease, border-radius 0.3s ease;
}

.chat-panel.docked {
  height: 100%;
  border-radius: 12px 0 0 12px;
  border-right: none;
  margin-top: 48px;
  height: calc(100% - 48px);
}

/* 头部 — 毛玻璃顶栏 */
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.03);
  user-select: none;

  &:active {
    cursor: grabbing;
  }
}

.chat-header-left {
  display: flex;
  align-items: center;
  gap: 10px;

  .chat-logo-emoji {
    font-size: 24px;
  }

  strong {
    display: block;
    font-size: 14px;
    color: var(--text-primary, #fff);
  }

  small {
    font-size: 11px;
    color: var(--text-muted, rgba(140, 182, 214, 0.78));
  }
}

.chat-header-right {
  display: flex;
  gap: 4px;
}

.chat-btn-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.4);
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;

  &:hover {
    background: rgba(255, 255, 255, 0.08);
    color: rgba(255, 255, 255, 0.9);
  }
}

/* 消息区 */
.chat-body {
  flex: 1;
  overflow-y: overlay;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;

  &::-webkit-scrollbar { width: 5px; }
  &::-webkit-scrollbar-thumb {
    background: transparent;
    border-radius: 3px;
    transition: background 0.3s;
  }
  &::-webkit-scrollbar-track { background: transparent; }

  &:hover::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.15);
  }
}

/* 空状态 */
.chat-empty {
  text-align: center;
  padding: 32px 10px;

  .empty-emoji {
    font-size: 52px;
    opacity: 0.4;
  }

  p {
    margin: 14px 0 4px;
    color: rgba(255, 255, 255, 0.9);
    font-size: 16px;
    font-weight: 600;
  }

  span {
    color: rgba(255, 255, 255, 0.45);
    font-size: 12px;
  }

  .quick-questions {
    margin-top: 20px;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;

    button {
      padding: 8px 16px;
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 20px;
      background: rgba(255, 255, 255, 0.06);
      color: rgba(255, 255, 255, 0.75);
      font-size: 12px;
      cursor: pointer;
      white-space: nowrap;
      transition: all 0.2s;
      backdrop-filter: blur(8px);
      -webkit-backdrop-filter: blur(8px);

      &:hover {
        background: rgba(255, 255, 255, 0.12);
        border-color: rgba(255, 255, 255, 0.25);
        color: #fff;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
      }
    }
  }
}

/* 消息气泡 */
.chat-msg {
  display: flex;
  gap: 8px;
  max-width: 100%;

  &.user {
    flex-direction: row-reverse;

    .msg-avatar {
      background: linear-gradient(135deg, #3b82f6, #2563eb);
      color: #fff;
      border-radius: 50%;
    }

    .msg-content {
      background: linear-gradient(135deg, #3b82f6, #2563eb);
      border: none;
      border-radius: 18px 4px 18px 18px;
      color: #fff;
      box-shadow: 0 4px 14px rgba(37, 99, 235, 0.25);
    }
  }

  &.assistant {
    .msg-avatar {
      background: rgba(255, 255, 255, 0.1);
      color: rgba(255, 255, 255, 0.7);
      border-radius: 50%;
    }

    .msg-content {
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 4px 18px 18px 18px;
      color: rgba(255, 255, 255, 0.9);
    }
  }
}

.msg-avatar {
  width: 34px;
  height: 34px;
  min-width: 34px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;

  .avatar-emoji {
    font-size: 16px;
    line-height: 1;
  }
}

.msg-content {
  padding: 12px 16px;
  font-size: 13px;
  line-height: 1.6;
  word-break: break-word;

  :deep(pre) {
    background: rgba(0, 0, 0, 0.25);
    border-radius: 10px;
    padding: 10px;
    margin: 8px 0;
    overflow-x: auto;
    font-size: 12px;

    code {
      background: none;
      padding: 0;
    }
  }

  :deep(code) {
    background: rgba(0, 0, 0, 0.2);
    padding: 2px 5px;
    border-radius: 4px;
    font-size: 12px;
  }

  :deep(strong) {
    color: var(--brand-accent, #60a5fa);
  }
}

.streaming-cursor::after {
  content: '|';
  animation: blink 0.8s infinite;
  color: var(--brand-accent, #00f3ff);
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* 输入区 */
.chat-footer {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  padding: 14px 18px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.02);
}

.chat-input {
  flex: 1;
  resize: none;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 10px 18px;
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.9);
  font-size: 13px;
  line-height: 1.5;
  font-family: inherit;
  outline: none;
  max-height: 120px;
  transition: all 0.2s;

  &::placeholder {
    color: rgba(255, 255, 255, 0.3);
  }

  &:focus {
    border-color: rgba(255, 255, 255, 0.25);
    background: rgba(255, 255, 255, 0.08);
  }

  &:disabled {
    opacity: 0.4;
  }
}

.chat-send-btn {
  width: 38px;
  height: 38px;
  min-width: 38px;
  border-radius: 50%;
  border: none;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: #fff;
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);

  &:hover:not(:disabled) {
    transform: scale(1.08);
    box-shadow: 0 6px 18px rgba(37, 99, 235, 0.45);
  }

  &:disabled {
    opacity: 0.3;
    cursor: not-allowed;
  }
}

/* 过渡动画 — 由 GSAP JS 钩子驱动 */

/* ======================== 亮色主题 ======================== */
.theme-light .chat-fab {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border-color: rgba(0, 0, 0, 0.08);
  color: #475569;
  box-shadow: 0 8px 32px rgba(0,0,0,0.08), 0 0 0 1px rgba(255,255,255,0.5) inset;
}
.theme-light .chat-fab:hover {
  background: rgba(255, 255, 255, 0.85);
  border-color: rgba(37, 99, 235, 0.3);
  color: #2563eb;
  box-shadow: 0 12px 40px rgba(0,0,0,0.12), 0 0 0 1px rgba(255,255,255,0.6) inset;
}
.theme-light .chat-panel {
  background: rgba(255, 255, 255, 0.62);
  backdrop-filter: blur(28px) saturate(1.4);
  -webkit-backdrop-filter: blur(28px) saturate(1.4);
  border-color: rgba(0, 0, 0, 0.06);
  box-shadow: 0 24px 64px rgba(0,0,0,0.12), 0 0 0 1px rgba(255,255,255,0.4) inset;
}
.theme-light .chat-header {
  border-bottom-color: rgba(0, 0, 0, 0.05);
}
.theme-light .chat-header h3 {
  color: #1e293b;
}
.theme-light .chat-header-left strong {
  color: #1e293b !important;
}
.theme-light .chat-header-left small {
  color: #94a3b8 !important;
}
.theme-light .chat-btn-icon {
  color: #94a3b8;
}
.theme-light .chat-btn-icon:hover {
  background: rgba(0, 0, 0, 0.05);
  color: #475569;
}
.theme-light .chat-body {
  background: transparent;
}
.theme-light .chat-body:hover::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.12);
}
.theme-light .chat-empty p {
  color: #1e293b;
}
.theme-light .chat-empty span {
  color: #94a3b8;
}
.theme-light .quick-questions button {
  background: rgba(0, 0, 0, 0.04);
  border-color: rgba(0, 0, 0, 0.08);
  color: #475569;
}
.theme-light .quick-questions button:hover {
  background: rgba(37, 99, 235, 0.08);
  border-color: rgba(37, 99, 235, 0.25);
  color: #2563eb;
}
.theme-light .msg-role-user .msg-content {
  background: linear-gradient(135deg, #2563eb, #3b82f6);
  color: #ffffff;
  box-shadow: 0 4px 14px rgba(37, 99, 235, 0.3);
}
.theme-light .msg-role-assistant .msg-content {
  background: rgba(0, 0, 0, 0.04);
  border-color: rgba(0, 0, 0, 0.06);
  color: #334155;
}
.theme-light .msg-role-assistant .msg-avatar {
  background: rgba(0, 0, 0, 0.06);
  color: #64748b;
}
.theme-light .chat-footer {
  border-top-color: rgba(0, 0, 0, 0.05);
}
.theme-light .chat-input {
  background: rgba(0, 0, 0, 0.03);
  border-color: rgba(0, 0, 0, 0.08);
  color: #1e293b;
}
.theme-light .chat-input::placeholder {
  color: #94a3b8;
}
.theme-light .chat-input:focus {
  border-color: rgba(37, 99, 235, 0.3);
  background: rgba(0, 0, 0, 0.04);
}
.theme-light .chat-send-btn {
  background: linear-gradient(135deg, #2563eb, #3b82f6);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}
.theme-light .streaming-cursor::after {
  color: #2563eb;
}
</style>
