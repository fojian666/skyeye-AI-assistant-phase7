<template>
  <div class="chat-wrapper" :class="[`theme-${theme}`, { 'query-mode': chatMode === 'query', 'summary-mode': chatMode === 'summary', 'reduce-motion': reduceMotion }]" :style="wrapperStyle" role="complementary" aria-label="AI 助手面板">
    <!-- 悬浮按钮 -->
    <div v-if="!visible" class="chat-fab" @click="open" @mousedown="startDrag" title="AI 助手" aria-label="打开 AI 助手" role="button">
        <span class="fab-robot-icon"><svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg></span>
        <span class="fab-label">AI 助手</span>
        <span v-if="messages.length > 0" class="fab-badge" aria-label="有历史对话"></span>
      </div>

    <!-- 聊天窗口 + 拓展槽 -->
      <div v-show="visible" class="panel-row" :class="{ docked }">
        <div class="panel-shell">
          <div ref="panel" :class="['chat-panel', { docked, 'thinking-glow': streaming }]" :style="panelStyle" role="dialog" aria-label="AI 助手对话窗口" :aria-modal="docked">
        <!-- 头部 -->
        <div class="chat-header" @mousedown="startDrag">
          <div class="chat-header-left">
            <span class="chat-logo-icon"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg></span>
            <div>
              <strong>金陵阡陌 AI 助手</strong>
              <small>
                <template v-if="chatMode === 'query'">数据查询模式</template>
                <template v-else-if="chatMode === 'summary'">智能摘要</template>
                <template v-else>Powered by DeepSeek</template>
              </small>
            </div>
          </div>
          <div class="chat-header-right">
            <button class="chat-btn-icon" :title="reduceMotion ? '启用动态效果' : '减少动态效果'" @click="reduceMotion = !reduceMotion" aria-label="切换动态效果">
              <svg v-if="reduceMotion" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="6 3 20 12 6 21 6 3"/></svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg>
            </button>
            <button class="chat-btn-icon" :title="docked ? '取消吸附' : '吸附到右侧'" @click="docked = !docked" aria-label="切换吸附">
              <svg v-if="docked" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 19-7-7 7-7"/><path d="M19 12H5"/></svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 5 7 7-7 7"/><path d="M5 12h14"/></svg>
            </button>
            <button class="chat-btn-icon" title="AI 助手设置" @click="openSettings" aria-label="AI 助手设置">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>
            </button>
            <button class="chat-btn-icon" title="清空对话" @click="clearMessages" aria-label="清空对话">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
            </button>
            <button class="chat-btn-icon" title="关闭" @click="closeChat" aria-label="关闭面板">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
            </button>
          </div>
        </div>

        <!-- 消息列表 -->
        <div class="chat-body" ref="chatBody" role="log" aria-live="polite" aria-label="对话内容" @scroll="onChatScroll">
          <div v-if="messages.length === 0" class="chat-empty">
            <span class="empty-icon"><svg xmlns="http://www.w3.org/2000/svg" width="52" height="52" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg></span>
            <p>你好！我是金陵阡陌 AI 助手</p>
            <span>可以问我关于无人机巡检、航线规划、全景分析等问题</span>
            <div class="quick-questions">
              <button v-for="q in quickQuestions" :key="q" @click="sendQuick(q)">{{ q }}</button>
            </div>
          </div>

          <div
            v-for="(msg, idx) in messages"
            :key="idx">
            <div
              v-show="msg.role !== 'tool'"
              class="chat-msg"
              :class="msg.role">
              <span class="msg-name">{{ msg.role === 'user' ? username : msg.role === 'tool-info' ? '系统' : modelName }}</span>
              <div class="msg-row">
                <div class="msg-avatar">
                  <svg v-if="msg.role === 'user'" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                  <svg v-else-if="msg.role === 'tool-info'" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
                  <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg>
                </div>
                <div class="msg-content" v-if="msg.role === 'tool-info'" style="background:rgba(0,243,255,0.08);font-style:italic">
                  {{ msg.content }}
                </div>
                <div class="msg-content" v-else-if="msg.role === 'tool'">
                  <!-- tool messages are hidden -->
                </div>
                <div class="msg-content" v-else v-html="renderContent(msg.content)"></div>
              </div>
              <div v-if="msg.role === 'assistant'" class="msg-actions">
                <button class="msg-action-btn" @click="copyMessage(msg.content, idx)" :title="copiedMsgIdx === idx ? '已复制' : '复制回答'">
                  <svg v-if="copiedMsgIdx === idx" xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                  <svg v-else xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>
                </button>
                <span v-if="copiedMsgIdx === idx" class="copy-toast">已复制</span>
                <button v-if="msg._error || msg._interrupted" class="msg-action-btn retry" @click="retry(idx)" title="重试">
                  <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/></svg>
                </button>
              </div>
            </div>
            <div v-if="msg.role === 'assistant' && msg.suggestions && msg.suggestions.length" class="msg-suggestions">
              <button
                v-for="(q, qi) in msg.suggestions"
                :key="qi"
                :style="{ transitionDelay: (0.08 * (qi + 1)) + 's' }"
                @click="sendQuick(q)">
                {{ q }}
              </button>
            </div>
          </div>

          <!-- 打字中 / 思考中 -->
          <div v-if="streaming" class="chat-msg assistant">
            <span class="msg-name">{{ modelName }}</span>
            <div class="msg-row">
              <div class="msg-avatar">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg>
              </div>
              <div class="msg-content" :class="{ 'streaming-cursor': streamingText }">
                <span v-if="streamingText" v-html="streamingText"></span>
                <div v-else class="thinking-status">
                  <span v-if="phase" class="phase-indicator">
                    <span class="phase-icon">{{ phaseIcons[phase.phase] || '...' }}</span>
                    {{ phase.message }}
                  </span>
                  <span class="dots-container"><span class="dot"></span><span class="dot"></span><span class="dot"></span></span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 回到底部按钮 -->
        <button
          v-show="showScrollBtn"
          class="scroll-bottom-btn"
          @click="scrollToBottom(true)"
          title="回到底部"
          aria-label="滚动到最新消息"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>
        </button>

        <!-- 输入区 -->
        <div class="chat-footer">
          <div class="chat-input-wrap">
            <textarea
              ref="inputArea"
              v-model="input"
              class="chat-input"
              :placeholder="streaming ? 'AI 正在回复...' : '输入消息，Enter 发送'"
              :disabled="streaming"
              rows="1"
              aria-label="输入消息"
              maxlength="4000"
              @keydown.enter.exact.prevent="send"
              @keydown.enter.shift.prevent="insertNewline"
              @input="autoResize"
            ></textarea>
            <button
              v-if="streaming"
              class="chat-stop-btn"
              @click="stopGeneration"
              title="停止生成">
              <span class="stop-icon"></span>
              <span>停止</span>
            </button>
            <button
              v-else
              class="chat-send-btn"
              :disabled="!input.trim()"
              @click="send"
              title="发送">
              <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>
            </button>
          </div>
        </div>

        <!-- 拖拽缩放把手 -->
        <div class="resize-handle" @mousedown.prevent="startResize"></div>
        </div>
        </div>

        <!-- 左侧拓展槽 -->
        <div v-show="!docked" class="side-rail" :class="{ visible: sideRailVisible, 'show-hint': !railHintShown }">
          <div class="rail-item small spread-top-1" title="搜索定位" aria-label="搜索定位"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg></div>
          <div class="rail-item large" @click="toggleChatMode"
            :title="chatMode === 'query' ? '切换到智能摘要' : chatMode === 'summary' ? '切换到聊天模式' : '切换到数据查询模式'">
            <svg v-if="chatMode === 'query'" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
            <svg v-else-if="chatMode === 'summary'" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><path d="M16 13H8"/><path d="M16 17H8"/><path d="M10 9H8"/></svg>
            <svg v-else xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/></svg>
          </div>
          <div class="rail-item small spread-bot-1" title="系统设置" @click="openSettings" aria-label="系统设置"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg></div>
        </div>
      </div>
  </div>
</template>

<script>
import router from '@/router'
import { mapState } from 'vuex';
import gsap from 'gsap';

const ROUTES = [
  { path: '/task-mgmt/verify-clue',                              title: '项目管理' },
  { path: '/data-management/one-map',                             title: '一张图' },
  { path: '/data-management/table',                               title: '影像管理' },
  { path: '/route-planning/panoramicpoint-planning',              title: '全景规划' },
  { path: '/route-planning/algorithm-planning',                   title: '算法规划' },
  { path: '/route-planning/manual-planning',                      title: '人工选点' },
  { path: '/panoramic-detection/map-view',                        title: '地图总览' },
  { path: '/panoramic-detection/grid-management',                 title: '范围管理' },
  { path: '/panoramic-detection/task-management',                 title: '批次管理' },
  { path: '/panoramic-detection/main-detection',                  title: '全景检测' },
  { path: '/panoramic-detection/frame-area',                      title: '不检测区域' },
  { path: '/panoramic-detection/panorama-change-detection',       title: '全景变化' },
  { path: '/panoramic-detection/scene',                           title: '场景管理' },
  { path: '/panoramic-detection/clue-view',                       title: '线索总览' },
  { path: '/panoramic-detection/main-detection-temp',             title: '临时批次' },
  { path: '/panoramic-detection/report',                          title: '报告管理' },
  { path: '/pattern-verifiy/task_management',                     title: '任务管理' },
  { path: '/ai-settings',                                        title: 'AI 设置' },
];

const TOOLS = [
  {
    type: 'function',
    function: {
      name: 'navigate_page',
      description:
        '跳转到系统的指定页面。仅在用户明确表达跳转/打开/前往/进入某个页面的意图时调用。' +
        '\n当用户询问数据、统计等问题（如"有多少""状态是什么"）时，不要调用此工具。' +
        '\n【禁止调用场景】以下措辞的核心意图是查询数据，不是跳转页面：' +
        '\n  - "数据概览""数据概况""查看数据""统计汇总" → 应使用 query_data' +
        '\n  - "当前页面"开头 → 应使用 query_data' +
        '\n  - 即使用户说"打开""查看"，如果后面是数据相关词汇（概览、统计、汇总、列表、明细），不调用此工具。' +
        '\n根据用户意图从下面列表中选择最匹配的路由：\n' +
        ROUTES.map(r => `  ${r.path} → ${r.title}`).join('\n') +
        '\n示例：打开全景检测 → navigate_page\n带我去航线规划 → navigate_page\n报告管理在哪 → navigate_page',
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
      description: '地图定位操作。仅在用户明确要求打开/查看/定位某个具体地点（如城市名、区名、街道名、地标名）时调用。' +
        '\n【禁止调用场景】以下不是地点，不要调用此工具：' +
        '\n  - "防尘网""线索""图斑""批次""全景图""网格""任务"等业务术语' +
        '\n  - "数据概览""统计""汇总""有多少""状态"等数据查询词汇 → 应使用 query_data' +
        '\n  - "一张图""全景检测""航线规划"等页面名称 → 应使用 navigate_page' +
        '\n  - 即使用户说"打开""查看"，后面跟的不是具体地名，也不调用。' +
        '\n示例：带我去南京鼓楼区看看 → map_action\n鼓楼区在哪 → map_action\n打开玄武区 → map_action',
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
      name: 'lookup_task',
      description: '根据用户输入的任务编号（batch_id）查询任务。仅在用户明确提供编号格式的字符串时才调用。' +
        '\n编号格式通常类似 LS32020000120260701 或 32011300500120250715。如果任务存在则跳转到任务详情页。' +
        '\n【禁止调用场景】以下不是任务编号，不要调用：' +
        '\n  - 普通数字（如"3个""5条""10个批次"）— 这是统计数量，应使用 query_data' +
        '\n  - 地名（如"鼓楼区""玄武区"）— 应使用 map_action' +
        '\n  - 页面名称（如"一张图""全景检测"）— 应使用 navigate_page' +
        '\n  - 任务名称/描述（如"唐山市巡查任务""上周的检测"）— 没有编号就不调用' +
        '\n示例：查询 LS32020000120260701 → lookup_task\n帮我查一下 32011300500120250715 → lookup_task',
      parameters: {
        type: 'object',
        properties: {
          task_id: { type: 'string', description: '用户提供的任务编号（batch_id）' },
        },
        required: ['task_id'],
      },
    },
  },
  {
    type: 'function',
    function: {
      name: 'query_data',
      description: '查询系统数据。当用户询问任何关于数据量、统计、数量、状态的信息时必须调用此工具，不要反问。' +
        '\n【禁止调用场景】以下意图不是数据查询，不要调用：' +
        '\n  - "打开""跳转""前往" + 具体页面名 → 应使用 navigate_page' +
        '\n  - "定位""在哪""带我去" + 具体地名 → 应使用 map_action' +
        '\n  - 明确的 20 位任务编号（如 LS32020000120260701）→ 应使用 lookup_task' +
        '\n  - "你好""你是谁""你能做什么"等闲聊 → 直接回复，不调用任何工具' +
        '\n示例：有多少全景图？ → query_data\n线索数据有多少条？ → query_data\n任务状态是什么？ → query_data',
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
      sideRailVisible: false,
      panelW: 480,
      panelH: Math.min(window.innerHeight * 0.78, 640),
      resizing: false,
      resizeStart: { x: 0, y: 0, w: 0, h: 0 },
      chatQuickQuestions: [
        '带我去南京鼓楼区看看',
        '帮我打开航线规划页面',
        '当前有哪些检测任务？',
      ],
      queryQuickQuestions: [
        '当前页面数据概览',
        '最近有哪些异常情况？',
        '按状态分类统计',
      ],
      summaryQuickQuestions: [
        '有哪些高风险项？',
        '整体完成进度如何？',
        '下一步建议怎么做？',
      ],
      username: '用户',
      modelName: 'DeepSeek',
      phase: null,
      phaseIcons: {
        understanding: '🔍',
        geocoding: '🗺️',
        querying: '📊',
        looking_up: '🔎',
        generating: '✍️',
      },
      abortController: null,
      lastUserMessage: '',
      _stopRequested: false,
      copiedMsgIdx: -1,
      chatMode: 'chat',  // 'chat' | 'query' | 'summary'
      currentContext: null,
      lastAutoSummaryKey: null,  // 防重复触发
      reduceMotion: false,       // 减少动态效果
      railHintShown: false,     // side-rail 发现性提示（首次打开展示一次）
      showScrollBtn: false,     // "回到底部"浮动按钮
      _userScrolledUp: false,   // 用户手动上翻后暂停自动滚动
      _storageError: false,     // localStorage 读写异常标志
      _typewriterCancelled: false, // 组件销毁时取消打字机
      _mapDispatchTimer: null,     // map_action 延迟 dispatch 定时器
      _copyTimer: null,             // 复制成功提示恢复定时器
      _animLockTimer: null,         // 并发动画锁定时器
      _animating: false,            // 并发动画锁（模式切换/dock/开合）
      _sending: false,              // 并发发送锁（send/sendQuick）
      model: 'deepseek-chat',   // 模型选择（从设置页同步）
      temperature: 0.7,          // Temperature 参数
      maxTokens: 4096,           // 最大输出 token
    }
  },
  computed: {
    ...mapState({ theme: state => state.theme }),
    panelStyle() {
      if (this.docked) return {}
      return { width: this.panelW + 'px', height: this.panelH + 'px' }
    },
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
    activeTools() {
      if (this.chatMode === 'query' || this.chatMode === 'summary') return TOOLS
      return TOOLS.filter(t => t.function.name !== 'query_data')
    },
    quickQuestions() {
      if (this.chatMode === 'query') return this.queryQuickQuestions
      if (this.chatMode === 'summary') return this.summaryQuickQuestions
      return this.chatQuickQuestions
    },
  },
  mounted() {
    this._loadSettings()
    this._onDragMove = this.onDragMove.bind(this)
    this._onDragEnd = this.onDragEnd.bind(this)
    this._onGlobalMouse = this.onGlobalMouse.bind(this)
    this._onResizeMove = this.onResizeMove.bind(this)
    this._onResizeEnd = this.onResizeEnd.bind(this)
    this._onKeydown = this.onKeydown.bind(this)
    document.addEventListener('mousemove', this._onDragMove)
    document.addEventListener('mouseup', this._onDragEnd)
    document.addEventListener('mousemove', this._onGlobalMouse)
    document.addEventListener('mousemove', this._onResizeMove)
    document.addEventListener('mouseup', this._onResizeEnd)
    document.addEventListener('keydown', this._onKeydown)
  },
  beforeDestroy() {
    // 中止正在进行的流式请求
    this._typewriterCancelled = true;
    if (this.abortController) {
      this.abortController.abort();
      this.abortController = null;
    }
    // 终止 GSAP 动画，防止 onComplete 回调在已销毁组件上执行
    gsap.killTweensOf(this.$refs.panel);
    const shell = this.$refs.panel?.parentElement;
    if (shell) gsap.killTweensOf(shell);
    // 清理栅栏定时器
    clearTimeout(this._mapDispatchTimer);
    clearTimeout(this._copyTimer);
    clearTimeout(this._animLockTimer);
    document.removeEventListener('mousemove', this._onDragMove)
    document.removeEventListener('mouseup', this._onDragEnd)
    document.removeEventListener('mousemove', this._onGlobalMouse)
    document.removeEventListener('mousemove', this._onResizeMove)
    document.removeEventListener('mouseup', this._onResizeEnd)
    document.removeEventListener('keydown', this._onKeydown)
  },
  watch: {
    // streaming 结束时释放发送锁
    streaming(val) {
      if (!val) this._sending = false;
    },
    // 路由变化：进入新页面且有选中对象 → 自动生成摘要
    $route: {
      immediate: true,
      handler() {
        this.$nextTick(() => { this.maybeAutoSummary() })
        // 从设置页返回 → 恢复聊天面板（不在设置页时才触发）
        if (this.$route.path !== '/ai-settings' && sessionStorage.getItem('skyeye_from_chat') === '1') {
          sessionStorage.removeItem('skyeye_from_chat')
          this.$nextTick(() => { if (!this.visible) this.openChat() })
        }
      },
    },
    // 切换到数据查询模式或摘要模式且有选中对象 → 自动生成摘要
    chatMode(val) {
      if (val === 'query' || val === 'summary') this.maybeAutoSummary()
      this._saveSettingsKey('defaultMode', val)
    },
    // 动态效果切换 → 同步到设置页
    reduceMotion(val) {
      this._saveSettingsKey('reduceMotion', val)
    },
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
      // 面板关闭时用 FAB 实际尺寸，打开时用面板尺寸
      const fabRect = this.$el.getBoundingClientRect()
      const w = this.visible ? this.panelW : fabRect.width
      const h = this.visible ? this.panelH : fabRect.height
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
    startResize(e) {
      this.resizing = true
      this.resizeStart = { x: e.clientX, y: e.clientY, w: this.panelW, h: this.panelH }
    },
    onResizeMove(e) {
      if (!this.resizing) return
      const dx = e.clientX - this.resizeStart.x
      const dy = e.clientY - this.resizeStart.y
      this.panelW = Math.min(700, Math.max(320, this.resizeStart.w + dx))
      this.panelH = Math.min(window.innerHeight * 0.85, Math.max(400, this.resizeStart.h + dy))
    },
    onResizeEnd() {
      this.resizing = false
    },
    onGlobalMouse(e) {
      // 面板打开时，鼠标靠近面板左侧边缘浮现拓展槽
      if (!this.visible || this.docked) {
        this.sideRailVisible = false
        return
      }
      const panel = this.$refs.panel
      if (!panel) { this.sideRailVisible = false; return }
      const rect = panel.getBoundingClientRect()
      // 鼠标在面板左侧 100px 范围内触发
      const nearLeft = e.clientX > rect.left - 100 && e.clientX < rect.left
      // 鼠标垂直方向也要在面板范围内
      const inVert = e.clientY > rect.top && e.clientY < rect.bottom
      this.sideRailVisible = nearLeft && inVert
    },
    onKeydown(e) {
      // Esc 关闭面板
      if (e.key === 'Escape' && this.visible) {
        e.preventDefault()
        this.closeChat()
        return
      }
      // Cmd+K / Ctrl+K 唤起面板
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        if (this.visible) {
          this.closeChat()
        } else {
          this.open()
        }
        return
      }
    },

    /** 并发动画锁：duration 毫秒内阻止重复操作。返回 true 表示已锁（应跳过） */
    _lockAnim(durationMs) {
      if (this._animating) return true;
      this._animating = true;
      clearTimeout(this._animLockTimer);
      this._animLockTimer = setTimeout(() => { this._animating = false; }, durationMs);
      return false;
    },

    open() {
      // 拖拽后不触发点击打开
      if (this.hasMoved) return
      this.railHintShown = true  // 首次打开即标记提示已展示
      // 跳转后的残留消息，重置为欢迎界面
      if (this.messages.length === 1 && this.messages[0].content.startsWith('已为您跳转到')) {
        this.messages = []
      }
      // 展开面板前，确保面板不超出屏幕
      let x = this.dragPos.x != null ? this.dragPos.x : window.innerWidth - 24 - 56
      let y = this.dragPos.y != null ? this.dragPos.y : window.innerHeight - 24 - 56
      this.visible = true
      this.$nextTick(() => {
        // 用实际渲染尺寸做边界修正（含 border）
        const rect = this.$el.getBoundingClientRect()
        const pw = rect.width || 400
        const ph = rect.height || 560
        if (x + pw > window.innerWidth) x = window.innerWidth - pw - 12
        if (y + ph > window.innerHeight) y = window.innerHeight - ph - 12
        this.dragPos = { x: Math.max(0, x), y: Math.max(0, y) }

        const panel = this.$refs.panel
        if (panel) {
          const shell = panel.parentElement // .panel-shell 外壳
          // requestAnimationFrame 确保 display:none 解除后浏览器完成布局
          requestAnimationFrame(() => {
            gsap.fromTo(panel,
              {
                scale: 0.95, opacity: 0, y: 20,
                boxShadow: '0 0 20px rgba(100,180,255,0.3), 0 0 40px rgba(100,180,255,0.1), 0 0 0 1px rgba(255,255,255,0.05) inset',
                borderColor: 'rgba(100,180,255,0.35)',
              },
              {
                scale: 1, opacity: 1, y: 0,
                boxShadow: '0 24px 64px rgba(0,0,0,0.45), 0 0 0 1px rgba(255,255,255,0.05) inset, 0 1px 0 rgba(255,255,255,0.06) inset',
                borderColor: 'rgba(255,255,255,0.1)',
                duration: 0.5,
                ease: 'power3.out',
              }
            )
            gsap.fromTo(shell, { opacity: 0 }, { opacity: 1, duration: 0.5, ease: 'power3.out' })
          })
        }
        this.$refs.inputArea?.focus()
        this.scrollToBottom(true)
      })
    },

    resolveRoute(path) {
      return path
    },

    closeChat() {
      const panel = this.$refs.panel
      if (panel && this.visible) {
        const shell = panel.parentElement // .panel-shell 外壳
        gsap.to(panel, {
          scale: 0.95, opacity: 0, y: 10,
          boxShadow: '0 0 16px rgba(100,180,255,0.25), 0 0 32px rgba(100,180,255,0.08), 0 0 0 1px rgba(255,255,255,0.05) inset',
          borderColor: 'rgba(100,180,255,0.3)',
          duration: 0.2,
          ease: 'power3.in',
          onComplete: () => {
            this.visible = false
            this.docked = false
            this.dragPos = { x: null, y: null }
            gsap.set([panel, shell], { clearProps: 'all' })
          },
        })
        gsap.to(shell, { opacity: 0, duration: 0.2, ease: 'power3.in' })
      } else {
        this.visible = false
        this.docked = false
        this.dragPos = { x: null, y: null }
      }
    },

    /** 收起面板回到 FAB（保留对话内容，用于跳转地图等场景） */
    collapseToFab() {
      const panel = this.$refs.panel
      if (panel && this.visible) {
        const shell = panel.parentElement
        gsap.to(panel, {
          scale: 0.95, opacity: 0, y: 10,
          duration: 0.15,
          ease: 'power3.in',
          onComplete: () => {
            this.visible = false
            this.docked = false
            this.dragPos = { x: null, y: null }
            gsap.set([panel, shell], { clearProps: 'all' })
          },
        })
        gsap.to(shell, { opacity: 0, duration: 0.15, ease: 'power3.in' })
      } else {
        this.visible = false
        this.docked = false
        this.dragPos = { x: null, y: null }
      }
    },

    toggleChatMode() {
      if (this._lockAnim(400)) return;
      const map = { chat: 'query', query: 'summary', summary: 'chat' }
      this.chatMode = map[this.chatMode]
      const labels = { chat: '聊天模式 — 自由对话', query: '数据查询模式 — 检索系统数据', summary: '智能摘要 — 页面数据分析' }
      this.$message({ message: labels[this.chatMode], type: 'info', duration: 2000, showClose: false })
    },

    openSettings() {
      if (this._lockAnim(500)) return;
      sessionStorage.setItem('skyeye_from_chat', '1')
      this.closeChat()
      router.push('/ai-settings').catch(() => {})
    },

    /** 从设置页 localStorage 加载参数 */
    _loadSettings() {
      try {
        const prefs = JSON.parse(localStorage.getItem('skyeye_ai_settings')) || {}
        this._storageError = false
        if (prefs.model) this.model = prefs.model
        if (prefs.temperature !== undefined && prefs.temperature !== null) this.temperature = prefs.temperature
        if (prefs.maxTokens !== undefined && prefs.maxTokens !== null) this.maxTokens = prefs.maxTokens
        if (prefs.reduceMotion !== undefined) this.reduceMotion = prefs.reduceMotion
        if (prefs.defaultMode) this.chatMode = prefs.defaultMode
        if (prefs.autoSummary !== undefined) this.autoSummary = prefs.autoSummary
      } catch (e) {
        console.warn('[ChatModel] localStorage 读取失败', e)
        this._storageError = true
      }
    },

    /** 将单个 key 回写到设置页 localStorage */
    _saveSettingsKey(key, val) {
      try {
        const prefs = JSON.parse(localStorage.getItem('skyeye_ai_settings')) || {}
        prefs[key] = val
        localStorage.setItem('skyeye_ai_settings', JSON.stringify(prefs))
        this._storageError = false
      } catch (e) {
        console.warn('[ChatModel] localStorage 回写失败', e)
        this._storageError = true
      }
    },

    collectContext() {
      const route = this.$route
      if (!route) return
      this.currentContext = {
        page: {
          path: route.path,
          name: route.name || '',
          title: (route.matched[route.matched.length - 1]?.meta?.title) || route.meta?.title || document.title || '',
        },
        params: { ...route.params },
        query: { ...route.query },
      }
    },

    // 检测是否有选中对象的上下文参数
    _hasSelection() {
      this.collectContext()
      const ctx = this.currentContext
      if (!ctx) return false
      const selectKeys = ['selectedId', 'taskId', 'batchId', 'clueId', 'gridId', 'id',
                          'clue_id', 'batch_id', 'task_id', 'grid_id']
      const params = { ...ctx.params, ...ctx.query }
      return selectKeys.some(k => params[k])
    },

    // 进入页面或切到摘要模式时，自动生成摘要
    maybeAutoSummary() {
      if (this.chatMode !== 'summary') return
      if (this.streaming) return
      if (!this._hasSelection()) return
      // 防重复：同一页面+同一选中对象不重复触发
      const ctx = this.currentContext
      const key = ctx.page.path + '|' + JSON.stringify({ ...ctx.params, ...ctx.query })
      if (key === this.lastAutoSummaryKey) return
      this.lastAutoSummaryKey = key
      // 打开面板
      if (!this.visible) this.visible = true
      // 自动发送摘要请求
      const summaryPrompt = '帮我生成一份摘要'
      this.lastUserMessage = summaryPrompt
      this.messages.push({ role: 'user', content: summaryPrompt })
      this.streaming = true
      this.chatLoop()
    },

    sendQuick(question) {
      if (this.streaming || this._sending) return
      this._sending = true
      this.lastUserMessage = question
      this.messages.push({ role: 'user', content: question })
      this._userScrolledUp = false
      this.showScrollBtn = false
      this.streaming = true
      this.collectContext()
      this.chatLoop()
      this.scrollToBottom(true)
    },

    insertNewline(e) {
      const el = e.target
      const start = el.selectionStart
      const end = el.selectionEnd
      this.input = this.input.substring(0, start) + '\n' + this.input.substring(end)
      this.$nextTick(() => {
        el.selectionStart = el.selectionEnd = start + 1
        this.autoResize()
      })
    },

    /** 将 fetch 错误映射为友好消息 */
    _friendlyError(err) {
      if (err.name === 'AbortError') return '已停止生成'
      if (err.name === 'TypeError' && err.message.includes('fetch')) return '网络连接异常，请检查网络'
      const msg = err.message || ''
      if (msg.includes('500') || msg.includes('502') || msg.includes('503')) return '服务繁忙，请稍后再试'
      if (msg.includes('401') || msg.includes('403')) return '访问被拒绝，请检查权限'
      if (msg.includes('404')) return '接口不存在，请联系管理员'
      if (msg.includes('429')) return '请求过于频繁，请稍后再试'
      console.error('[ChatModel] 未知错误', err)
      return '服务暂时不可用，请稍后再试'
    },

    async send() {
      const text = this.input.trim()
      if (!text || this.streaming || this._sending) return

      this._sending = true
      this.lastUserMessage = text
      this.messages.push({ role: 'user', content: text })
      this.input = ''
      this.$nextTick(() => this.autoResize())
      this._userScrolledUp = false
      this.showScrollBtn = false
      this.streaming = true
      this.collectContext()
      this.scrollToBottom(true)

      await this.chatLoop()
    },

    async chatLoop() {
      const allMessages = this.messages
          .filter(m => m.role !== 'tool-info' && m.role !== 'tool' && !m.tool_calls)
          .map(m => ({ role: m.role, content: m.content }))

      this.phase = null
      this.abortController = new AbortController()
      // 60s 请求超时（防止后端挂起永久阻塞）
      const timeoutId = setTimeout(() => this.abortController.abort(), 60000)

      try {
        const apiBase = (window.config && window.config.baseUrl) || 'http://127.0.0.1:8009/'
        const response = await fetch(`${apiBase}api/system/chat/completions`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ messages: allMessages, tools: this.activeTools, chat_mode: this.chatMode, context: this.currentContext, model: this.model, temperature: this.temperature, max_tokens: this.maxTokens }),
          signal: this.abortController.signal,
        })

        clearTimeout(timeoutId)

        if (!response.ok) {
          const errData = await response.json().catch(() => ({}))
          throw new Error(errData.msg || `HTTP ${response.status}`)
        }

        // 兼容旧后端 JSON 响应（非 SSE）
        const ct = response.headers.get('content-type') || ''
        if (!ct.includes('text/event-stream')) {
          const data = await response.json()
          const result = data.result || data.data || {}
          this.phase = null
          await this._processResult(result)
          return
        }

        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''

        while (true) {
          const { value, done } = await reader.read()
          if (value) buffer += decoder.decode(value, { stream: true })

          const events = buffer.split('\n\n')
          buffer = events.pop() || ''

          for (const event of events) {
            const line = event.trim()
            if (!line.startsWith('data: ')) continue
            try {
              const evt = JSON.parse(line.slice(6))
              if (evt.phase === 'error') {
                console.warn('SSE error phase:', evt.message)
                continue
              }
              if (evt.phase === 'done') {
                reader.cancel()
                // 给足够时间让最后的 phase 文本可见
                await new Promise(r => setTimeout(r, 400))
                this.phase = null
                await this._processResult(evt.result)
                return
              }
              this.phase = evt
              // 每个阶段至少显示一段时间
              await new Promise(r => setTimeout(r, this.reduceMotion ? 50 : 200))
            } catch (e) {
              /* non-JSON event line */
            }
          }

          if (done) break
        }
        // 流意外结束未收到 done 事件
        if (this.streaming) {
          this.phase = null
          this.messages.push({ role: 'assistant', content: '抱歉，响应被中断，请重试。' })
          this.streaming = false
        }
      } catch (err) {
        clearTimeout(timeoutId)
        this.phase = null
        if (err.name === 'AbortError') {
          if (this.streamingText) {
            this.messages.push({ role: 'assistant', content: this.streamingText.replace(/<[^>]*>/g, ''), _interrupted: true })
          }
          this.streamingText = ''
        } else {
          this.messages.push({ role: 'assistant', content: `抱歉，${this._friendlyError(err)}`, _error: true })
        }
        this.streaming = false
      }
    },

    async _processResult(result) {
      const finishReason = result.finish_reason

      // 提取用户名和模型名
      if (result.username) this.username = result.username
      if (result.model) this.modelName = result.model

      // 处理工具调用
      if (result.tool_calls && finishReason === 'tool_calls') {
        const assistantMsg = { role: 'assistant', content: '', tool_calls: result.tool_calls }
        if (result.content) assistantMsg.content = result.content
        this.messages.push(assistantMsg)
        const toolCallIdx = this.messages.length // 记录工具调用消息后的位置

        // 执行每个工具
        for (const tc of result.tool_calls) {
          const fn = tc.function
          let args
          try {
            args = JSON.parse(fn.arguments)
          } catch (e) {
            console.warn('[ChatModel] tool_call arguments JSON 解析失败', fn.arguments)
            this.messages.pop() // 移除空 assistant 消息
            this.messages.push({ role: 'assistant', content: '工具调用参数解析失败，请重试', _error: true })
            this.streaming = false
            return
          }
          const toolResult = await this.executeTool(fn.name, args)
          // 导航类工具执行后折叠面板，保留对话历史供后续追问
          if (toolResult._navigate) {
            // 清理中间消息（空白 assistant tool_call + tool-info），只留最终跳转提示
            this.messages.splice(toolCallIdx - 1)
            this.collapseToFab()
            let label
            if (fn.name === 'map_action') {
              label = args.name || args.location
            } else if (fn.name === 'lookup_task') {
              label = `任务 ${toolResult.batch_name || args.task_id}`
            } else {
              label = args.reason || args.path
            }
            this.messages.push({ role: 'assistant', content: `已为您跳转到 ${label}` })
            this.streaming = false
            return
          }
          if (toolResult._stop) {
            // 非导航类 stop：错误消息已由 executeTool 直接推入 messages，直接退出
            this.streaming = false
            return
          }
          if (toolResult._display) {
            // 移除 LLM 的"思考中"气泡，直接展示结果
            this.messages.pop()
            const followUps = '查看线索数据统计\n图斑有哪些状态？\n还有什么可以帮您的？'
            await this.typewriter(toolResult.message + '\n|||\n' + followUps)
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
    },

    async executeTool(name, args) {
      if (name === 'navigate_page') {
        const path = this.resolveRoute(args.path)
        // 跳转到 AI 设置时标记，返回后自动恢复聊天面板
        if (path === '/ai-settings') sessionStorage.setItem('skyeye_from_chat', '1')
        this.messages.push({ role: 'tool-info', content: `正在跳转到：${args.reason}` })
        this.$nextTick(() => {
          this.collapseToFab()
          router.push(path).catch(() => {})
        })
        return { _navigate: true, path, reason: args.reason }
      }
      if (name === 'map_action') {
        const detail = {
          name: args.name || args.location,
          location: args.location,
          polygon: args.polygon || [],
          subRegions: args.sub_regions || [],
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
          this._mapDispatchTimer = setTimeout(dispatch, 1500)
        } else {
          dispatch()
        }
        return { _navigate: true, success: true, ...detail }
      }
      if (name === 'lookup_task') {
        const taskId = args.task_id
        // 结果已由后端后处理注入 _lookup_found，无需二次请求
        if (args._lookup_found) {
          this.messages.push({ role: 'tool-info', content: `找到任务：${args._batch_name}` })
          this.$nextTick(() => {
            this.collapseToFab()
            router.push(`/panoramic-detection/verifyClue?id=${taskId}`).catch(() => {})
          })
          return { _navigate: true, task_id: taskId, batch_name: args._batch_name }
        } else {
          const msg = args._msg || `未查询到任务编号为 ${taskId} 的任务`
          this.messages.push({ role: 'assistant', content: msg })
          return { _stop: true, message: msg }
        }
      }
      if (name === 'query_data') {
        const result = args._query_result || `关于"${args.query}"的查询暂无结果。`
        return { message: result, _display: true }
      }
      return { error: `未知工具: ${name}` }
    },

    async typewriter(text) {
      // 解析 ||| 分隔符：前半是正文，后半是 3 个建议问题
      let body = text
      let suggestions = []
      const m = text.match(/[\s\S]*?\n\|\|\|\n([\s\S]*)$/)
      if (m) {
        body = text.substring(0, m.index + m[0].indexOf('\n|||')).trimEnd()
        suggestions = m[1].split('\n').map(s => s.replace(/^[\d.\-•\s]+/, '').trim()).filter(Boolean).slice(0, 3)
      } else if (text.includes('|||')) {
        // 降级：||| 前可能没换行
        const idx = text.indexOf('|||')
        body = text.substring(0, idx).trimEnd()
        suggestions = text.substring(idx + 3).split('\n').map(s => s.replace(/^[\d.\-•\s]+/, '').trim()).filter(Boolean).slice(0, 3)
      }
      this.streamingText = ''
      this._stopRequested = false
      const chars = [...body]
      const renderInline = (raw) => {
        let t = raw
          .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
          .replace(/\*\*[^*]*$/, m => m.slice(2))
          .replace(/\*([^*]+)\*/g, '<em>$1</em>')
          .replace(/\*([^*]*)$/, '')
          .replace(/`([^`]+)`/g, '<code>$1</code>')
          .replace(/`([^`]*)$/, '')
          .replace(/```\w*\n?([\s\S]*)$/, (_, c) => c ? `<pre><code>${c}</code></pre>` : '')
          .replace(/数据查询模式/g, '<strong>数据查询模式</strong>')
        return t
      }
      if (this.reduceMotion) {
        // 减少动效模式：跳过打字机，直接渲染全文
        this.streamingText = renderInline(chars.join(''))
        this.messages.push({ role: 'assistant', content: body, suggestions })
        this.streamingText = ''
        this.streaming = false
        this.scrollToBottom()
        return
      }
      for (let i = 0; i < chars.length; i++) {
        if (this._stopRequested || this._typewriterCancelled) {
          const partial = this.streamingText.replace(/<[^>]*>/g, '')
          if (partial) this.messages.push({ role: 'assistant', content: partial, _interrupted: true })
          this.streamingText = ''
          this.streaming = false
          return
        }
        this.streamingText = renderInline(this.streamingText.replace(/<[^>]*>/g, '') + chars[i])
        await new Promise(r => setTimeout(r, 25))
        this.scrollToBottom()
      }
      this.messages.push({ role: 'assistant', content: body, suggestions })
      this.streamingText = ''
      this.streaming = false
    },

    stopGeneration() {
      if (this._lockAnim(200)) return;
      this._stopRequested = true
      if (this.abortController) {
        this.abortController.abort()
        this.abortController = null
      }
    },

    retry(idx) {
      // 找到最后一条用户消息位置，移除之后的所有消息
      let lastUserIdx = -1
      for (let i = idx - 1; i >= 0; i--) {
        if (this.messages[i].role === 'user') {
          lastUserIdx = i
          break
        }
      }
      if (lastUserIdx >= 0) {
        this.messages.splice(lastUserIdx + 1)
      }
      this.streaming = true
      this.chatLoop()
    },

    async copyMessage(text, idx) {
      if (!text) return
      try {
        await navigator.clipboard.writeText(text)
        this.copiedMsgIdx = idx
        clearTimeout(this._copyTimer)
        this._copyTimer = setTimeout(() => { this.copiedMsgIdx = -1 }, 2000)
      } catch {
        const ta = document.createElement('textarea')
        ta.value = text
        ta.style.position = 'fixed'
        ta.style.opacity = '0'
        document.body.appendChild(ta)
        ta.select()
        document.execCommand('copy')
        document.body.removeChild(ta)
        this.copiedMsgIdx = idx
        clearTimeout(this._copyTimer)
        this._copyTimer = setTimeout(() => { this.copiedMsgIdx = -1 }, 2000)
      }
    },

    clearMessages() {
      if (this.messages.length === 0 || this._lockAnim(300)) return
      this.$confirm('确定要清空所有对话记录吗？此操作不可撤销。', '清空对话', {
        confirmButtonText: '清空',
        cancelButtonText: '取消',
        type: 'warning',
        confirmButtonClass: 'el-button--danger'
      }).then(() => {
        this.messages = []
      }).catch(() => {})
    },

    scrollToBottom(force = false) {
      this.$nextTick(() => {
        const el = this.$refs.chatBody
        if (!el) return
        // 用户手动上翻且有历史消息时，不自动滚动（除非 force）
        if (!force && this._userScrolledUp && this.messages.length > 0) return
        el.scrollTo({ top: el.scrollHeight, behavior: force ? 'smooth' : 'instant' })
        if (force) {
          this._userScrolledUp = false
          this.showScrollBtn = false
        }
      })
    },

    onChatScroll() {
      const el = this.$refs.chatBody
      if (!el) return
      const distFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight
      this._userScrolledUp = distFromBottom > 60
      this.showScrollBtn = distFromBottom > el.clientHeight * 0.5
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
      // esc() 转义 <>& 字符，后续 markdown 注入的标签（strong/em/br）由代码自身生成，非用户输入
      processed = this.esc(processed)
      processed = processed.replace(/\n/g, '<br>')
      processed = processed
        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
        .replace(/__([^_]+)__/g, '<strong>$1</strong>')
        .replace(/\*([^*]+)\*/g, '<em>$1</em>')
        // 自动加粗特定关键词（兜底）
        .replace(/数据查询模式/g, '<strong data-mode-hint>数据查询模式</strong>')
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
  z-index: 1000;  /* z: 面板层，高于普通页面元素 */
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

  .fab-robot-icon {
    display: flex;
    line-height: 1;
    transition: transform 0.55s cubic-bezier(0.16, 1, 0.3, 1);

    svg { display: block; }
  }

  &:hover .fab-robot-icon {
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

/* FAB 历史对话指示器 */
.fab-badge {
  position: absolute;
  top: 6px;
  right: 6px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--app-accent, #6366f1);
  box-shadow: 0 0 6px rgba(99, 102, 241, 0.5);
}

/* 面板行 — flex 并排聊天面板 + 拓展槽 */
.panel-row {
  position: relative;
  display: flex;
  align-items: center;

  &.docked {
    height: 100%;
    align-items: flex-start;
  }
}

/* ======================== 左侧拓展槽 — 透明半圆弧 ======================== */
.side-rail {
  position: absolute;
  right: 100%;
  margin-right: 4px;
  top: 50%;
  width: 120px;
  height: 210px;
  z-index: 1010;  /* z: 侧栏层 */
  opacity: 0;
  transform: translate(-16px, -50%);
  pointer-events: none;
  transition: opacity 0.35s cubic-bezier(0.32, 0.72, 0, 1), transform 0.35s cubic-bezier(0.16, 1, 0.3, 1);

  &.visible {
    opacity: 1;
    transform: translate(0, -50%);
    pointer-events: auto;
  }

  /* 首次展示提示：短暂可见后消退 */
  &.show-hint {
    opacity: 0.45;
    transform: translate(0, -50%);
    pointer-events: auto;
    animation: rail-hint-fade 2.5s ease-out forwards;
    animation-delay: 0.5s;
  }

  /* hover 时强制保持可见，不受 JS sideRailVisible 影响 */
  &:hover {
    opacity: 1 !important;
    transform: translate(0, -50%) !important;
    pointer-events: auto !important;
    animation: none !important;
  }
}

@keyframes rail-hint-fade {
  0%, 30% { opacity: 0.45; }
  100% { opacity: 0; pointer-events: none; }
}

.rail-item {
  position: absolute;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.35s cubic-bezier(0.32, 0.72, 0, 1);

  /* 大圆：右中，始终可见 */
  &.large {
    width: 56px;
    height: 56px;
    right: 4px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 24px;
    background: rgba(59, 130, 246, 0.18);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(59, 130, 246, 0.35);
    color: rgba(200, 220, 255, 0.9);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
    z-index: 1;

    &:hover {
      background: rgba(59, 130, 246, 0.28);
      border-color: rgba(59, 130, 246, 0.55);
    }
  }

  /* 小圆：默认隐藏，hover 时从大圆向外散开成弧 */
  &.small {
    width: 36px;
    height: 36px;
    font-size: 14px;
    background: rgba(255, 255, 255, 0.12);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.16);
    color: rgba(255, 255, 255, 0.65);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
    opacity: 0;
    transform: scale(0);
    transition:
      opacity 0.3s cubic-bezier(0.32, 0.72, 0, 1) 0.25s,
      transform 0.4s cubic-bezier(0.16, 1, 0.3, 1) 0.25s,
      background 0.25s cubic-bezier(0.32, 0.72, 0, 1),
      border-color 0.25s cubic-bezier(0.32, 0.72, 0, 1),
      color 0.25s cubic-bezier(0.32, 0.72, 0, 1);

    &:hover {
      background: rgba(255, 255, 255, 0.22);
      border-color: rgba(255, 255, 255, 0.35);
      color: #fff;
    }
  }
}

/* 小圆半圆弧位置 */
.spread-top-2 { left: 36px; top: 8px; }
.spread-top-1 { left: 8px; top: 54px; }
.spread-bot-1 { left: 8px; top: 120px; }
.spread-bot-2 { left: 36px; top: 166px; }

/* hover 时小圆散开 — 交错延迟 */
.side-rail:hover .rail-item.small {
  opacity: 1;
  transform: scale(1);
}
.side-rail:hover .spread-top-2 { transition-delay: 0s; }
.side-rail:hover .spread-top-1 { transition-delay: 0.06s; }
.side-rail:hover .spread-bot-1 { transition-delay: 0.06s; }
.side-rail:hover .spread-bot-2 { transition-delay: 0.12s; }

/* 亮色主题适配 */
.theme-light .rail-item.large {
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.5), rgba(59, 130, 246, 0.3));
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-color: rgba(37, 99, 235, 0.45);
  color: #fff;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.12), inset 0 1px 0 rgba(255, 255, 255, 0.25), 0 0 22px rgba(37, 99, 235, 0.25);

  &:hover {
    background: linear-gradient(135deg, rgba(37, 99, 235, 0.65), rgba(59, 130, 246, 0.45));
    box-shadow: 0 2px 16px rgba(0, 0, 0, 0.18), inset 0 1px 0 rgba(255, 255, 255, 0.3), 0 0 32px rgba(37, 99, 235, 0.45);
  }
}
.theme-light .rail-item.small {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-color: rgba(0, 0, 0, 0.18);
  color: #374151;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.6);

  &:hover {
    background: rgba(37, 99, 235, 0.2);
    border-color: rgba(37, 99, 235, 0.45);
    color: #1e40af;
    box-shadow: 0 2px 14px rgba(0, 0, 0, 0.12), 0 0 18px rgba(37, 99, 235, 0.25);
  }
}

/* —— 外壳：铝合金托盘 + 面板内核（Double-Bezel） —— */
.panel-shell {
  padding: 4px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.06),
    0 12px 48px rgba(0, 0, 0, 0.55);
}

.docked .panel-shell {
  height: 100%;
}

/* 聊天面板 — 内核 */
.chat-panel {
  position: relative;
  box-sizing: border-box;
  max-width: 520px;
  max-height: 85vh;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(40px);
  -webkit-backdrop-filter: blur(40px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.06),
    0 4px 12px rgba(0, 0, 0, 0.35);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transform-origin: bottom right;
  transition: height 0.3s ease, border-radius 0.3s ease,
    border-color 0.3s ease,
    box-shadow 0.3s ease;

  &::before {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: 20px;
    background: linear-gradient(135deg, rgba(255,255,255,0.06) 0%, transparent 50%);
    pointer-events: none;
    z-index: 0;
  }

  > * {
    position: relative;
    z-index: 1;
  }
}

.chat-panel.docked {
  width: 390px;
  max-width: none;
  height: calc(100% - 48px);
  max-height: none;
  border-radius: 12px 0 0 12px;
  border-right: none;
  margin-top: 48px;
}

/* 数据查询模式 */
.chat-wrapper.query-mode .chat-panel {
  border-color: rgba(239, 68, 68, 0.3);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06),
    0 0 24px rgba(239, 68, 68, 0.08);
  transition: border-color 0.35s cubic-bezier(0.4, 0, 0.2, 1),
    box-shadow 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}
.chat-wrapper.query-mode .chat-header {
  background: rgba(239, 68, 68, 0.08);
  border-bottom-color: rgba(239, 68, 68, 0.12);
  transition: background 0.3s 0.15s cubic-bezier(0.4, 0, 0.2, 1), border-color 0.3s 0.1s cubic-bezier(0.4, 0, 0.2, 1);
}
.chat-wrapper.query-mode .chat-header-left small {
  color: #ef4444 !important;
  transition: color 0.25s 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.chat-wrapper.query-mode .chat-footer {
  border-top-color: rgba(239, 68, 68, 0.12);
  transition: border-color 0.3s 0.05s cubic-bezier(0.4, 0, 0.2, 1);
}
.chat-wrapper.query-mode .chat-input-wrap:focus-within {
  border-color: rgba(239, 68, 68, 0.5);
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1), 0 0 0 4px rgba(239, 68, 68, 0.12);
}
.chat-wrapper.query-mode .chat-send-btn {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  transition: background 0.3s 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  &:hover:not(:disabled) { background: linear-gradient(135deg, #f87171, #ef4444); }
}
.chat-wrapper.query-mode .chat-msg.user .msg-content {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  box-shadow: 0 4px 14px rgba(239, 68, 68, 0.25);
  transition: background 0.35s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}
.chat-wrapper.query-mode .chat-msg.user .msg-avatar {
  background: linear-gradient(135deg, #ef4444, #dc2626);
  transition: background 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}
.chat-wrapper.query-mode .chat-msg.user .msg-name {
  color: #f87171;
  transition: color 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 智能摘要模式 — 琥珀/金色 */
.chat-wrapper.summary-mode .chat-panel {
  border-color: rgba(245, 158, 11, 0.3);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06),
    0 0 24px rgba(245, 158, 11, 0.08);
  transition: border-color 0.35s cubic-bezier(0.4, 0, 0.2, 1),
    box-shadow 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}
.chat-wrapper.summary-mode .chat-header {
  background: rgba(245, 158, 11, 0.08);
  border-bottom-color: rgba(245, 158, 11, 0.12);
  transition: background 0.3s 0.15s cubic-bezier(0.4, 0, 0.2, 1), border-color 0.3s 0.1s cubic-bezier(0.4, 0, 0.2, 1);
}
.chat-wrapper.summary-mode .chat-header-left small {
  color: #f59e0b !important;
  transition: color 0.25s 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}
.chat-wrapper.summary-mode .chat-footer {
  border-top-color: rgba(245, 158, 11, 0.12);
  transition: border-color 0.3s 0.05s cubic-bezier(0.4, 0, 0.2, 1);
}
.chat-wrapper.summary-mode .chat-input-wrap:focus-within {
  border-color: rgba(245, 158, 11, 0.5);
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.1), 0 0 0 4px rgba(245, 158, 11, 0.12);
}
.chat-wrapper.summary-mode .chat-send-btn {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  transition: background 0.3s 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  &:hover:not(:disabled) { background: linear-gradient(135deg, #fbbf24, #f59e0b); }
}
.chat-wrapper.summary-mode .chat-msg.user .msg-content {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  box-shadow: 0 4px 14px rgba(245, 158, 11, 0.25);
  transition: background 0.35s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}
.chat-wrapper.summary-mode .chat-msg.user .msg-avatar {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  transition: background 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}
.chat-wrapper.summary-mode .chat-msg.user .msg-name {
  color: #fbbf24;
  transition: color 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}

/* —— 侧边栏模式色 —— */
/* 查询模式 */
.chat-wrapper.query-mode .rail-item.large {
  background: rgba(239, 68, 68, 0.18);
  border-color: rgba(239, 68, 68, 0.35);
  color: rgba(255, 180, 170, 0.9);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease;
  &:hover {
    background: rgba(239, 68, 68, 0.28);
    border-color: rgba(239, 68, 68, 0.55);
  }
}
.chat-wrapper.query-mode .rail-item.small {
  border-color: rgba(239, 68, 68, 0.2);
  color: rgba(255, 160, 140, 0.7);
  transition: all 0.3s ease;
  &:hover {
    border-color: rgba(239, 68, 68, 0.45);
    color: #fff;
  }
}

/* 摘要模式 */
.chat-wrapper.summary-mode .rail-item.large {
  background: rgba(245, 158, 11, 0.18);
  border-color: rgba(245, 158, 11, 0.35);
  color: rgba(255, 220, 160, 0.9);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease;
  &:hover {
    background: rgba(245, 158, 11, 0.28);
    border-color: rgba(245, 158, 11, 0.55);
  }
}
.chat-wrapper.summary-mode .rail-item.small {
  border-color: rgba(245, 158, 11, 0.2);
  color: rgba(255, 200, 120, 0.7);
  transition: all 0.3s ease;
  &:hover {
    border-color: rgba(245, 158, 11, 0.45);
    color: #fff;
  }
}

/* 头部 — 毛玻璃顶栏 */
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 18px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  user-select: none;
  transition: background 0.3s 0.1s cubic-bezier(0.4, 0, 0.2, 1), border-color 0.3s 0.15s cubic-bezier(0.4, 0, 0.2, 1);

  &:active {
    cursor: grabbing;
  }
}

.chat-header-left {
  display: flex;
  align-items: center;
  gap: 10px;

  .chat-logo-icon {
    svg { display: block; }
  }

  strong {
    display: block;
    font-size: 14px;
    color: var(--text-primary, #fff);
    transition: color 0.25s 0.05s cubic-bezier(0.4, 0, 0.2, 1);
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

  svg { display: block; }

  &:hover {
    background: rgba(255, 255, 255, 0.08);
    color: rgba(255, 255, 255, 0.9);
  }

  &:focus-visible {
    outline: 2px solid rgba(99, 102, 241, 0.6);
    outline-offset: 2px;
  }
}

/* 消息区 */
.chat-body {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  scroll-behavior: smooth;
  min-height: 0;

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

  .empty-icon {
    opacity: 0.4;
    svg { display: block; }
  }

  p {
    margin: 14px 0 4px;
    color: rgba(255, 255, 255, 0.9);
    font-size: 16px;
    font-weight: 600;
  }

  span {
    color: rgba(255, 255, 255, 0.55);
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

      &:focus-visible {
        outline: 2px solid rgba(99, 102, 241, 0.6);
        outline-offset: 2px;
      }
    }
  }
}

/* 回到底部按钮 */
.scroll-bottom-btn {
  position: absolute;
  bottom: 12px;
  left: 50%;
  transform: translateX(-50%);
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(15, 23, 42, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  color: rgba(255, 255, 255, 0.6);
  font-size: 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.35);
  animation: scroll-btn-in 0.25s cubic-bezier(0.32, 0.72, 0, 1);
  transition: all 0.25s ease;

  &:hover {
    background: rgba(30, 41, 59, 0.9);
    border-color: rgba(255, 255, 255, 0.25);
    color: #fff;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.45);
    transform: translateX(-50%) translateY(-2px);
  }
}

@keyframes scroll-btn-in {
  from { opacity: 0; transform: translateX(-50%) translateY(8px); }
  to   { opacity: 1; transform: translateX(-50%) translateY(0); }
}

.theme-light .scroll-bottom-btn {
  background: rgba(255, 255, 255, 0.85);
  border-color: rgba(0, 0, 0, 0.1);
  color: #64748b;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
  &:hover {
    background: #fff;
    border-color: rgba(37, 99, 235, 0.3);
    color: #2563eb;
  }
}

/* 消息气泡 */
.chat-msg {
  display: flex;
  flex-direction: column;
  gap: 3px;
  max-width: 100%;

  &.user {
    align-items: flex-end;

    .msg-name {
      text-align: right;
      padding-right: 2px;
      color: #60a5fa;
    }

    .msg-row {
      flex-direction: row-reverse;
    }

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
    .msg-name {
      padding-left: 2px;
      color: rgba(200, 220, 255, 0.6);
    }

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

.msg-name {
  font-size: 11px;
  font-weight: 500;
  user-select: none;
}

.msg-row {
  display: flex;
  gap: 8px;
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

  svg { display: block; }
}

.msg-content {
  max-width: 70%;
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

.msg-suggestions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-left: 42px;
  margin-bottom: 8px;
  margin-top: 4px;

  button {
    all: unset;
    cursor: pointer;
    padding: 6px 14px;
    font-size: 12px;
    line-height: 1.4;
    border-radius: 16px;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: rgba(255, 255, 255, 0.75);
    transition: all 0.25s ease;
    white-space: nowrap;

    &:hover {
      background: rgba(37, 99, 235, 0.15);
      border-color: rgba(37, 99, 235, 0.35);
      color: #fff;
      transform: translateY(-1px);
    }
  }
}

.theme-light .msg-suggestions button {
  background: rgba(0, 0, 0, 0.04);
  border-color: rgba(0, 0, 0, 0.08);
  color: #475569;

  &:hover {
    background: rgba(37, 99, 235, 0.08);
    border-color: rgba(37, 99, 235, 0.25);
    color: #2563eb;
    transform: translateY(-1px);
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

/* 思考状态容器 */
.thinking-status {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  min-height: 24px;
}
.dots-container {
  display: inline-flex;
  gap: 5px;
  align-items: center;
  padding: 2px 0;
}
.dots-container .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--brand-accent, #00f3ff);
  animation: dot-bounce 1.4s infinite ease-in-out both;
}
.dots-container .dot:nth-child(1) { animation-delay: 0s; }
.dots-container .dot:nth-child(2) { animation-delay: 0.2s; }
.dots-container .dot:nth-child(3) { animation-delay: 0.4s; }

/* 阶段指示器 */
.phase-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 2px 0;
  font-size: 13px;
  color: var(--brand-accent, #00f3ff);
  animation: phase-fade-in 0.3s ease-out;
}
.phase-icon {
  font-size: 14px;
  line-height: 1;
}
@keyframes phase-fade-in {
  from { opacity: 0; transform: translateY(-4px); }
  to   { opacity: 1; transform: translateY(0); }
}

@keyframes dot-bounce {
  0%, 80%, 100% { transform: translateY(0); opacity: 0.3; }
  40% { transform: translateY(-6px); opacity: 1; }
}

/* 面板脉冲呼吸光环 */
.chat-panel.thinking-glow {
  border-color: rgba(0, 243, 255, 0.2);
  animation: breathe-glow 3s ease-in-out infinite;
}

.chat-panel.thinking-glow::after {
  content: '';
  position: absolute;
  inset: -2px;
  border-radius: 22px;
  pointer-events: none;
  z-index: -1;
  animation: breathe-ring 3s ease-in-out infinite;
}

@keyframes breathe-glow {
  0%, 100% {
    box-shadow: 0 16px 48px rgba(0, 0, 0, 0.5);
  }
  50% {
    box-shadow:
      0 16px 48px rgba(0, 0, 0, 0.5),
      0 0 40px rgba(0, 243, 255, 0.08);
  }
}

@keyframes breathe-ring {
  0%, 100% {
    box-shadow: 0 0 8px rgba(0, 243, 255, 0.05);
    opacity: 0.5;
  }
  50% {
    box-shadow: 0 0 16px rgba(0, 243, 255, 0.12);
    opacity: 0.8;
  }
}

/* 输入区 */
.chat-footer {
  padding: 14px 18px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  transition: border-color 0.3s 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.chat-input-wrap {
  position: relative;
  display: flex;
  align-items: flex-end;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 24px;
  background: linear-gradient(145deg,
    rgba(255, 255, 255, 0.1) 0%,
    rgba(255, 255, 255, 0.04) 40%,
    rgba(255, 255, 255, 0.06) 100%);
  padding: 3px 3px 3px 14px;
  transition: border-color 0.35s cubic-bezier(0.32, 0.72, 0, 1),
    box-shadow 0.35s cubic-bezier(0.32, 0.72, 0, 1),
    background 0.35s cubic-bezier(0.32, 0.72, 0, 1);
  box-shadow:
    inset 0 2px 4px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.06);

  &::before {
    content: '';
    position: absolute;
    top: 2px;
    left: 4%;
    right: 4%;
    height: 35%;
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.12) 0%, transparent 100%);
    border-radius: 24px 24px 50% 50%;
    pointer-events: none;
    z-index: 0;
  }

  &:focus-within {
    border-color: rgba(59, 130, 246, 0.5);
    background: linear-gradient(145deg,
      rgba(255, 255, 255, 0.15) 0%,
      rgba(255, 255, 255, 0.06) 40%,
      rgba(255, 255, 255, 0.08) 100%);
    box-shadow:
      inset 0 2px 4px rgba(0, 0, 0, 0.3),
      inset 0 1px 0 rgba(255, 255, 255, 0.1),
      0 0 0 4px rgba(59, 130, 246, 0.15);
  }
}

.chat-input {
  flex: 1;
  resize: none;
  border: none;
  padding: 7px 0;
  background: transparent;
  color: rgba(255, 255, 255, 0.9);
  font-size: 13px;
  line-height: 1.5;
  font-family: inherit;
  outline: none;
  max-height: 120px;

  &::placeholder {
    color: rgba(255, 255, 255, 0.55); /* WCAG AA ≥4.5:1 对比度 */
  }

  &:disabled {
    opacity: 0.4;
  }
}

.chat-send-btn {
  width: 34px;
  height: 34px;
  min-width: 34px;
  border-radius: 50%;
  border: none;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: #fff;
  font-size: 15px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition:
    transform 0.35s cubic-bezier(0.32, 0.72, 0, 1),
    background 0.3s ease,
    box-shadow 0.3s ease;
  flex-shrink: 0;

  &:hover:not(:disabled) {
    transform: scale(1.06);
    background: linear-gradient(135deg, #4f8bf9, #3070f0);
    box-shadow: 0 4px 20px rgba(59, 130, 246, 0.35);
  }

  &:active:not(:disabled) {
    transform: scale(0.96);
    transition: transform 0.12s cubic-bezier(0.32, 0.72, 0, 1);
  }

  &:disabled {
    opacity: 0.3;
    cursor: not-allowed;
  }

  &:focus-visible {
    outline: 2px solid rgba(99, 102, 241, 0.6);
    outline-offset: 2px;
  }
}

.chat-stop-btn {
  height: 34px;
  padding: 0 14px;
  border-radius: 20px;
  border: 1px solid rgba(239, 68, 68, 0.35);
  background: rgba(239, 68, 68, 0.12);
  color: rgba(248, 113, 113, 0.9);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.25s ease;
  flex-shrink: 0;

  .stop-icon {
    width: 10px;
    height: 10px;
    background: currentColor;
    border-radius: 2px;
    flex-shrink: 0;
    animation: stop-pulse 1.5s ease-in-out infinite;
  }

  &:hover {
    background: rgba(239, 68, 68, 0.22);
    border-color: rgba(239, 68, 68, 0.55);
    color: #fca5a5;
    box-shadow: 0 0 12px rgba(239, 68, 68, 0.15);
  }

  &:active {
    transform: scale(0.96);
  }
}

@keyframes stop-pulse {
  0%, 100% { opacity: 0.7; }
  50% { opacity: 1; }
}

/* 消息操作按钮 */
.msg-actions {
  display: flex;
  gap: 4px;
  margin-left: 42px;
  margin-top: 2px;
  opacity: 0;
  transition: opacity 0.2s ease;
}
.chat-msg:hover .msg-actions {
  opacity: 1;
}
.msg-action-btn {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.4);
  font-size: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;

  &:hover {
    background: rgba(255, 255, 255, 0.16);
    color: rgba(255, 255, 255, 0.85);
  }

  &.retry {
    color: rgba(251, 191, 36, 0.7);
    &:hover {
      background: rgba(251, 191, 36, 0.15);
      color: #fbbf24;
    }
  }
}

.copy-toast {
  font-size: 11px;
  color: #34d399;
  white-space: nowrap;
  line-height: 26px;
  animation: toast-in 0.25s ease-out;
}
@keyframes toast-in {
  from { opacity: 0; transform: translateX(-4px); }
  to   { opacity: 1; transform: translateX(0); }
}

/* 拖拽缩放把手 */
.resize-handle {
  position: absolute;
  right: 0;
  bottom: 0;
  width: 24px;
  height: 24px;
  cursor: nwse-resize;
  z-index: 3;
  background:
    linear-gradient(135deg, transparent 50%, rgba(255,255,255,0.15) 50%),
    linear-gradient(135deg, transparent 50%, rgba(255,255,255,0.15) 50%);
  background-size: 6px 6px, 10px 10px;
  background-position: 100% 100%, calc(100% - 8px) calc(100% - 8px);
  background-repeat: no-repeat;
  opacity: 0.4;
  transition: opacity 0.2s;

  &:hover {
    opacity: 0.9;
  }
}

.theme-light .resize-handle {
  background:
    linear-gradient(135deg, transparent 50%, rgba(0,0,0,0.12) 50%),
    linear-gradient(135deg, transparent 50%, rgba(0,0,0,0.12) 50%);
  background-size: 6px 6px, 10px 10px;
  background-position: 100% 100%, calc(100% - 8px) calc(100% - 8px);
  background-repeat: no-repeat;
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
  background: rgba(255, 255, 255, 0.45);
  backdrop-filter: blur(40px);
  -webkit-backdrop-filter: blur(40px);
  border-color: rgba(0, 0, 0, 0.06);
  box-shadow: 0 16px 48px rgba(0,0,0,0.1), 0 0 0 1px rgba(255,255,255,0.5) inset;

  &::before {
    background: linear-gradient(135deg, rgba(255,255,255,0.2) 0%, transparent 50%);
  }
}
.theme-light .chat-panel.thinking-glow {
  border-color: rgba(37, 99, 235, 0.3);
  animation: breathe-glow-light 2.2s ease-in-out infinite;
}
.theme-light .chat-panel.thinking-glow::after {
  animation: breathe-ring-light 3s ease-in-out infinite;
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
.theme-light .chat-msg.user .msg-content {
  background: linear-gradient(135deg, #2563eb, #3b82f6);
  color: #ffffff;
  box-shadow: 0 4px 14px rgba(37, 99, 235, 0.3);
}
.theme-light .chat-msg.assistant .msg-content {
  background: rgba(0, 0, 0, 0.04);
  border-color: rgba(0, 0, 0, 0.06);
  color: #334155;
}
.theme-light .chat-msg.assistant .msg-avatar {
  background: rgba(0, 0, 0, 0.06);
  color: #64748b;
}
.theme-light .chat-msg.user .msg-name {
  color: #2563eb;
}
.theme-light .chat-msg.assistant .msg-name {
  color: #94a3b8;
}
.theme-light .chat-msg .msg-content :deep(strong) {
  color: #2563eb;
}

/* 亮色主题 — 查询模式用户气泡 */
.chat-wrapper.theme-light.query-mode .chat-msg.user .msg-content {
  background: linear-gradient(135deg, #dc2626, #ef4444);
  box-shadow: 0 4px 14px rgba(220, 38, 38, 0.25);
}
.chat-wrapper.theme-light.query-mode .chat-msg.user .msg-avatar {
  background: linear-gradient(135deg, #dc2626, #ef4444);
}
.chat-wrapper.theme-light.query-mode .chat-msg.user .msg-name {
  color: #dc2626;
}

/* 亮色主题 — 摘要模式用户气泡 */
.chat-wrapper.theme-light.summary-mode .chat-msg.user .msg-content {
  background: linear-gradient(135deg, #d97706, #f59e0b);
  box-shadow: 0 4px 14px rgba(217, 119, 6, 0.25);
}
.chat-wrapper.theme-light.summary-mode .chat-msg.user .msg-avatar {
  background: linear-gradient(135deg, #d97706, #f59e0b);
}
.chat-wrapper.theme-light.summary-mode .chat-msg.user .msg-name {
  color: #b45309;
}

.theme-light .chat-footer {
  border-top-color: rgba(0, 0, 0, 0.05);
}
.theme-light .chat-input-wrap {
  border-color: rgba(0, 0, 0, 0.08);
  background: linear-gradient(145deg,
    rgba(255, 255, 255, 0.9) 0%,
    rgba(255, 255, 255, 0.55) 40%,
    rgba(240, 248, 255, 0.65) 100%);
  box-shadow:
    inset 0 2px 4px rgba(0, 0, 0, 0.04),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);

  &::before {
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.6) 0%, transparent 100%);
  }

  &:focus-within {
    border-color: rgba(37, 99, 235, 0.5);
    box-shadow:
      inset 0 2px 4px rgba(0, 0, 0, 0.04),
      inset 0 1px 0 rgba(255, 255, 255, 0.8),
      0 0 0 4px rgba(37, 99, 235, 0.12);
  }
}
.theme-light .chat-input {
  color: #1e293b;
  background: transparent;
}
.theme-light .chat-input::placeholder {
  color: #94a3b8;
}
.theme-light .chat-send-btn {
  background: linear-gradient(135deg, #2563eb, #3b82f6);
}
.theme-light .chat-stop-btn {
  border-color: rgba(220, 38, 38, 0.3);
  background: rgba(239, 68, 68, 0.08);
  color: #dc2626;
  &:hover {
    background: rgba(239, 68, 68, 0.15);
    border-color: rgba(220, 38, 38, 0.5);
    color: #b91c1c;
    box-shadow: 0 0 12px rgba(239, 68, 68, 0.12);
  }
}
.theme-light .msg-action-btn {
  background: rgba(0, 0, 0, 0.06);
  color: #94a3b8;
  &:hover {
    background: rgba(0, 0, 0, 0.1);
    color: #475569;
  }
  &.retry {
    color: #d97706;
    &:hover {
      background: rgba(245, 158, 11, 0.12);
      color: #b45309;
    }
  }
}
.theme-light .copy-toast {
  color: #059669;
}
.theme-light .streaming-cursor::after {
  color: #2563eb;
}
.theme-light .dots-container .dot {
  background: #2563eb;
}
.theme-light .phase-indicator {
  color: #2563eb;
}

/* 亮色主题脉冲呼吸光环 */
@keyframes breathe-glow-light {
  0%, 100% {
    box-shadow:
      0 24px 64px rgba(0, 0, 0, 0.12),
      0 0 20px rgba(37, 99, 235, 0.08),
      0 0 0 1px rgba(255, 255, 255, 0.4) inset;
  }
  50% {
    box-shadow:
      0 24px 64px rgba(0, 0, 0, 0.12),
      0 0 40px rgba(37, 99, 235, 0.2),
      0 0 80px rgba(37, 99, 235, 0.12),
      0 0 0 1px rgba(255, 255, 255, 0.5) inset;
  }
}

@keyframes breathe-ring-light {
  0%, 100% {
    box-shadow: 0 0 12px rgba(37, 99, 235, 0.1), 0 0 30px rgba(37, 99, 235, 0.05);
    opacity: 0.5;
  }
  50% {
    box-shadow: 0 0 24px rgba(37, 99, 235, 0.25), 0 0 60px rgba(37, 99, 235, 0.12);
    opacity: 1;
  }
}

/* —— 减少动态效果 —— */
.reduce-motion .chat-panel.thinking-glow {
  animation: none;
  border-color: rgba(0, 243, 255, 0.15);
}
.reduce-motion .chat-panel.thinking-glow::after {
  animation: none;
  box-shadow: none;
  opacity: 0;
}
.reduce-motion .streaming-cursor::after {
  animation: none;
  opacity: 0;
}
.reduce-motion .dots-container .dot {
  animation: none;
  opacity: 0.5;
}
.reduce-motion .phase-text {
  animation: none;
  opacity: 1;
}
/* footer/header 过渡加速 */
.reduce-motion .chat-footer,
.reduce-motion .chat-header,
.reduce-motion .chat-header-right .chat-btn-icon {
  transition-duration: 0.1s !important;
  transition-delay: 0s !important;
}
.reduce-motion .query-send-btn,
.reduce-motion .quick-item {
  transition-duration: 0.1s !important;
}

/* ========================= prefers-reduced-motion ========================= */
@media (prefers-reduced-motion: reduce) {
  .chat-wrapper * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
</style>
