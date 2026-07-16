<template>
  <div class="settings-root">
      <!-- Canvas: 动态极光 + 粒子连接网 -->
      <canvas ref="auroraCanvas" class="aurora-canvas" aria-hidden="true"></canvas>

      <!-- CSS 呼吸光斑（iOS 26 风格，交错延迟） -->
      <div class="bg-orb bg-orb-1" aria-hidden="true"></div>
      <div class="bg-orb bg-orb-2" aria-hidden="true"></div>
      <div class="bg-orb bg-orb-3" aria-hidden="true"></div>

      <!-- 噪点纹理叠加层 -->
      <div class="noise-overlay" aria-hidden="true"></div>

    <main class="settings-main">
      <!-- 返回按钮 -->
      <button class="back-btn" @click="$router.back()" aria-label="返回">
        <svg class="icon" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 19-7-7 7-7"/><path d="M19 12H5"/></svg>
      </button>

      <!-- 头部：打字机标题 -->
      <header ref="headerEl" class="page-header">
        <span class="eyebrow">
          {{ typedEyebrow }}<span v-if="typingLine === 'eyebrow'" class="typing-cursor">|</span>
        </span>
        <h1>
          {{ typedTitle }}<span v-if="typingLine === 'title'" class="typing-cursor">|</span>
        </h1>
        <p class="subtitle">
          {{ typedSubtitle }}<span v-if="typingLine === 'subtitle'" class="typing-cursor">|</span>
        </p>
      </header>

      <!-- 便当盒网格 -->
      <div class="bento-grid">
        <!-- ===== 模型与参数 (占 2 列) ===== -->
        <div ref="card1" class="card-pod col-wide curtain-item curtain-bottom">
          <!-- 外壳 -->
          <div class="pod-shell">
            <!-- 内核 -->
            <div class="pod-core">
              <div class="pod-icon-wrap">
                <svg class="pod-icon" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4.5a2.5 2.5 0 0 0-4.96-.46 2.5 2.5 0 0 0-1.98 3 2.5 2.5 0 0 0-1.32 4.24 3 3 0 0 0 .34 5.58 2.5 2.5 0 0 0 2.96 3.08A2.5 2.5 0 0 0 12 19.5a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 12 4.5Z"/><path d="m14.5 12-4.5 4.5L8 14.5"/></svg>
              </div>
              <h3>模型与参数</h3>
              <p class="pod-desc">控制 AI 回复的创造性与精确度</p>

              <div class="field-group">
                <label class="field-label">
                  模型选择
                  <span class="field-help" data-tip="DeepSeek-V3 适合日常对话与快速问答；R1 适合复杂分析（图斑变化、报告生成），响应稍慢但推理更深入">?</span>
                </label>
                <div class="select-wrap">
                  <select v-model="model" class="field-select">
                    <option value="deepseek-chat">DeepSeek-V3 (通用对话)</option>
                    <option value="deepseek-reasoner">DeepSeek-R1 (深度推理)</option>
                  </select>
                  <svg class="select-chevron" xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg>
                </div>
              </div>

              <div class="field-group">
                <div class="field-label-row">
                  <label class="field-label">
                    Temperature
                    <span class="field-help" data-tip="控制回复的随机性：0 = 确定性精确，2 = 最大创造性。巡检数据分析建议 0.3-0.7，创意生成建议 0.7-1.2">?</span>
                  </label>
                  <span
                    class="field-val temp-val"
                    :class="tempClass"
                    :key="temperature.toFixed(1)"
                  >{{ temperature.toFixed(1) }}</span>
                </div>
                <input
                  type="range"
                  class="field-slider"
                  min="0"
                  max="2"
                  step="0.1"
                  v-model.number="temperature"
                />
                <div class="slider-hints">
                  <span>精确</span>
                  <span>平衡</span>
                  <span>创造</span>
                </div>
              </div>

              <div class="field-group">
                <div class="field-label-row">
                  <label class="field-label">
                    最大输出长度
                    <span class="field-help" data-tip="控制单次回复的最大 Token 数。512 = 简短摘要，4096 = 标准分析，8192 = 详尽报告（响应时间相应增加）">?</span>
                  </label>
                  <span class="field-val">{{ maxTokens.toLocaleString() }}</span>
                </div>
                <input
                  type="range"
                  class="field-slider"
                  min="512"
                  max="8192"
                  step="512"
                  v-model.number="maxTokens"
                />
                <div class="slider-hints">
                  <span>512</span>
                  <span>4096</span>
                  <span>8192</span>
                </div>
                <div class="token-preview-bar">
                  <span class="token-label">简短回复</span>
                  <span class="token-track">
                    <span class="token-fill" :style="{ width: (maxTokens / 8192 * 100) + '%' }"></span>
                  </span>
                  <span class="token-label">详尽分析</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ===== 外观 (占 1 列) ===== -->
        <div ref="card2" class="card-pod curtain-item curtain-left">
          <div class="pod-shell">
            <div class="pod-core">
              <div class="pod-icon-wrap">
                <svg class="pod-icon" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="13.5" cy="6.5" r="2.5"/><circle cx="17.5" cy="10.5" r="2.5"/><circle cx="8.5" cy="7.5" r="2.5"/><circle cx="6.5" cy="12.5" r="2.5"/><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.554C21.965 6.012 17.461 2 12 2z"/></svg>
              </div>
              <h3>外观</h3>
              <p class="pod-desc">视觉偏好与动效控制</p>

              <div class="field-group">
                <div class="toggle-row" @click="toggleTheme">
                  <div>
                    <label class="field-label toggle-label">深色主题</label>
                    <span class="toggle-hint">{{ isDark ? '已启用' : '已关闭' }}</span>
                  </div>
                  <button
                    class="toggle-switch"
                    :class="{ active: isDark }"
                    role="switch"
                    :aria-checked="isDark"
                  >
                    <span class="toggle-knob"></span>
                  </button>
                </div>
              </div>

              <div class="field-group">
                <div class="toggle-row" @click="reduceMotion = !reduceMotion">
                  <div>
                    <label class="field-label toggle-label">
                      减少动态效果
                      <span class="field-help" data-tip="关闭入场动画与背景动态效果，适合低性能设备或偏好静态界面的用户">?</span>
                    </label>
                    <span class="toggle-hint">{{ reduceMotion ? '已启用' : '已关闭' }}</span>
                  </div>
                  <button
                    class="toggle-switch"
                    :class="{ active: reduceMotion }"
                    role="switch"
                    :aria-checked="reduceMotion"
                  >
                    <span class="toggle-knob"></span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ===== 对话默认 (占 1 列) ===== -->
        <div ref="card3" class="card-pod curtain-item curtain-right">
          <div class="pod-shell">
            <div class="pod-core">
              <div class="pod-icon-wrap">
                <svg class="pod-icon" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
              </div>
              <h3>对话默认</h3>
              <p class="pod-desc">新对话的起始模式与行为</p>

              <div class="field-group">
                <label class="field-label">默认模式</label>
                <div class="mode-chips">
                  <button
                    v-for="m in modes"
                    :key="m.value"
                    class="mode-chip"
                    :class="{ active: defaultMode === m.value }"
                    :data-mode="m.value"
                    :title="m.tip"
                    @click="defaultMode = m.value"
                  >
                    <svg class="chip-icon" xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" v-html="m.iconSvg"></svg>
                    <span class="chip-label">{{ m.label }}</span>
                  </button>
                </div>
              </div>

              <div class="field-group">
                <div class="toggle-row" @click="autoSummary = !autoSummary">
                  <div>
                    <label class="field-label toggle-label">进入页面时自动摘要</label>
                    <span class="toggle-hint">有选中对象时触发</span>
                  </div>
                  <button
                    class="toggle-switch"
                    :class="{ active: autoSummary }"
                    role="switch"
                    :aria-checked="autoSummary"
                  >
                    <span class="toggle-knob"></span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ===== 键盘快捷键 (占 1 列) ===== -->
        <div ref="card4" class="card-pod curtain-item curtain-left">
          <div class="pod-shell">
            <div class="pod-core">
              <div class="pod-icon-wrap">
                <svg class="pod-icon" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="M6 8h.01M10 8h.01M14 8h.01M18 8h.01M8 12h.01M12 12h.01M16 12h.01M18 12h.01M6 16h.01M10 16h.01M14 16h.01M18 16h.01"/></svg>
              </div>
              <h3>键盘快捷键</h3>
              <p class="pod-desc">高效操作参考</p>

              <div class="kbd-list">
                <div class="kbd-row" v-for="kb in shortcuts" :key="kb.label">
                  <span class="kbd-label">{{ kb.label }}</span>
                  <div class="kbd-keys">
                    <kbd v-for="key in kb.keys" :key="key">{{ key }}</kbd>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ===== 关于 (占 1 列) ===== -->
        <div ref="card5" class="card-pod curtain-item curtain-right">
          <div class="pod-shell">
            <div class="pod-core">
              <div class="pod-icon-wrap">
                <svg class="pod-icon" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/></svg>
              </div>
              <h3>关于</h3>
              <p class="pod-desc">金陵阡陌 AI 助手</p>

              <div class="about-meta">
                <div class="meta-row">
                  <span class="meta-key">版本</span>
                  <span class="meta-val version-glow">v2.1.0</span>
                </div>
                <div class="meta-row">
                  <span class="meta-key">引擎</span>
                  <span class="meta-val">DeepSeek API</span>
                </div>
                <div class="meta-row">
                  <span class="meta-key">框架</span>
                  <span class="meta-val">Vue 2 + Element UI</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <!-- 操作行 -->
      <div class="actions-bar">
        <button class="btn-reset" @click="restoreDefaults" aria-label="恢复默认设置">
          <svg class="btn-reset-icon" xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/></svg>
          恢复默认
        </button>
      </div>
    </main>

    <!-- 保存确认 Toast -->
    <transition name="toast">
      <div v-if="toastVisible" class="save-toast" :class="{ 'save-toast--error': _storageError }">{{ toastMessage }}</div>
    </transition>

    <!-- localStorage 异常警告 -->
    <div v-if="_storageError" class="storage-warning" role="alert">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
      设置无法持久保存，请检查浏览器存储空间或隐私设置
    </div>
  </div>
</template>

<script>
import { mapState } from 'vuex';

export default {
  name: 'AiSettings',

  data() {
    const saved = this._loadPrefs();
    return {
      model: saved.model || 'deepseek-chat',
      temperature: saved.temperature ?? 0.7,
      maxTokens: saved.maxTokens ?? 4096,
      reduceMotion: saved.reduceMotion ?? false,
      defaultMode: saved.defaultMode || 'chat',
      autoSummary: saved.autoSummary ?? false,
      modes: [
        { value: 'chat',    iconSvg: '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>', label: '自由对话', tip: '通用 AI 对话，适合日常问答与讨论' },
        { value: 'query',   iconSvg: '<path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/>', label: '数据查询',  tip: '结构化数据检索与分析，适合图斑查询、统计报表' },
        { value: 'summary', iconSvg: '<path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><path d="M16 13H8"/><path d="M16 17H8"/><path d="M10 9H8"/>', label: '智能摘要',  tip: '对当前选中要素自动生成综合摘要报告' },
      ],
      shortcuts: [
        { label: '唤起助手',    keys: this._isMac() ? ['⌘', 'K'] : ['Ctrl', 'K'] },
        { label: '关闭面板',    keys: ['Esc'] },
        { label: '发送消息',    keys: ['Enter'] },
        { label: '消息中换行',  keys: ['Shift', 'Enter'] },
      ],
      // 打字机
      typedEyebrow: '',
      typedTitle: '',
      typedSubtitle: '',
      typingLine: '', // 'eyebrow' | 'title' | 'subtitle' | 'done'
      _typewriterCancelled: false,
      // Toast
      toastVisible: false,
      toastMessage: '设置已保存',
      _toastTimer: null,
      _saveTimer: null,        // savePrefs 防抖定时器
      _storageError: false,     // localStorage 读写异常标志
      _themeWasLight: false,    // 追踪主题切换，重启 WebGL
    }
  },

  computed: {
    ...mapState({ theme: state => state.theme }),
    isDark() {
      return this.theme !== 'light';
    },
    tempClass() {
      const t = this.temperature;
      if (t < 0.5) return 'temp-cool';
      if (t < 1.0) return 'temp-warm';
      if (t < 1.5) return 'temp-hot';
      return 'temp-blaze';
    },
  },

  mounted() {
    this._themeWasLight = this.theme === 'light';
    this._startTypewriter();
    this._initAuroraCanvas();
  },

  beforeDestroy() {
    this._typewriterCancelled = true;
    clearTimeout(this._toastTimer);
    clearTimeout(this._saveTimer);
    this._destroyAurora();
  },

  watch: {
    theme(val) {
      if (val === 'dark' && this._themeWasLight) {
        this._themeWasLight = false;
        if (!this.reduceMotion) this._initAuroraCanvas();
      }
      if (val === 'light') {
        this._themeWasLight = true;
        this._destroyAurora();
      }
    },
    model:             { handler: 'savePrefs', deep: false },
    temperature:       { handler: 'savePrefs', deep: false },
    maxTokens:         { handler: 'savePrefs', deep: false },
    reduceMotion(v) {
      this.savePrefs();
      if (v) {
        this._destroyAurora();
      } else {
        this._initAuroraCanvas();
      }
    },
    defaultMode:       { handler: 'savePrefs', deep: false },
    autoSummary:       { handler: 'savePrefs', deep: false },
  },

  methods: {
    _isMac() {
      return /Mac|iPod|iPhone|iPad/.test(navigator.platform || '');
    },

    toggleTheme() {
      const next = this.theme === 'light' ? 'dark' : 'light';
      this.$store.commit('changeTheme', next);
    },

    // ==================== 打字机 + 幕布入场 ====================

    _startTypewriter() {
      // reduceMotion 关闭时跳过打字机，直接展示完整内容
      if (this.reduceMotion) {
        this.typedEyebrow = 'AI 助手'
        this.typedTitle = '设置'
        this.typedSubtitle = '个性化你的智能对话体验'
        this.typingLine = 'done'
        this.$nextTick(() => this._revealCurtains())
        return
      }
      const eyebrows = 'AI 助手';
      const title = '设置';
      const subtitle = '个性化你的智能对话体验';

      // 依次打字：眉题 → 标题 → 副标题
      this.typingLine = 'eyebrow';
      this._typeChars(eyebrows, 'typedEyebrow', 50, () => {
        this.typingLine = 'title';
        setTimeout(() => {
          this._typeChars(title, 'typedTitle', 70, () => {
            this.typingLine = 'subtitle';
            setTimeout(() => {
              this._typeChars(subtitle, 'typedSubtitle', 40, () => {
                this.typingLine = 'done';
                setTimeout(() => {
                  this._revealCurtains();
                }, 200);
              });
            }, 200);
          });
        }, 300);
      });
    },

    _typeChars(text, targetProp, delay, onDone) {
      let i = 0;
      const tick = () => {
        if (this._typewriterCancelled) return;
        if (i <= text.length) {
          this[targetProp] = text.slice(0, i);
          i++;
          setTimeout(tick, delay);
        } else if (onDone) {
          onDone();
        }
      };
      tick();
    },

    _revealCurtains() {
      this.$nextTick(() => {
        const items = this.$el.querySelectorAll('.curtain-item');
        items.forEach(el => el.classList.add('curtain-revealed'));
      });
    },

    // ==================== WebGL: Ether Shader 背景 ====================

    _initAuroraCanvas() {
      const canvas = this.$refs.auroraCanvas;
      if (!canvas) return;

      const gl = canvas.getContext('webgl', { alpha: true });
      if (!gl) { console.warn('WebGL not supported'); return; }

      this._gl = gl;
      this._glProgram = null;
      this._glRaf = null;
      this._glUniforms = null;
      this._glStartTime = performance.now();
      this._glMouse = [0.5, 0.5];
      this._glCanvas = canvas;

      // 编译 shader program
      const prog = this._compileShaderProgram(gl, VERTEX_SHADER, ETHER_FRAGMENT_SHADER);
      if (!prog) return;
      this._glProgram = prog;

      this._glUniforms = {
        iResolution: gl.getUniformLocation(prog, 'iResolution'),
        iTime: gl.getUniformLocation(prog, 'iTime'),
        iMouse: gl.getUniformLocation(prog, 'iMouse'),
      };

      // 鼠标追踪（mousemove 回调写入 ref，不触发 Vue 重渲染）
      this._onGlMouseMove = (e) => {
        const rect = canvas.getBoundingClientRect();
        this._glMouse = [
          (e.clientX - rect.left) / rect.width,
          1.0 - (e.clientY - rect.top) / rect.height, // WebGL Y 轴反向
        ];
      };
      canvas.addEventListener('mousemove', this._onGlMouseMove);

      // resize
      this._onGlResize = () => this._resizeAurora();
      window.addEventListener('resize', this._onGlResize);

      this.$nextTick(() => {
        this._resizeAurora();
        this._tickAurora();
      });
    },

    _resizeAurora() {
      const canvas = this._glCanvas;
      if (!canvas) return;
      const rect = canvas.parentElement.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      canvas.style.width = rect.width + 'px';
      canvas.style.height = rect.height + 'px';
      if (this._gl) {
        this._gl.viewport(0, 0, canvas.width, canvas.height);
      }
    },

    _tickAurora() {
      const gl = this._gl;
      const prog = this._glProgram;
      const canvas = this._glCanvas;
      const u = this._glUniforms;
      if (!gl || !prog || !u || !canvas) return;

      // 浅色模式不绘制 WebGL，停止 rAF 循环（主题 watcher 会在切回深色时重启）
      if (this.theme === 'light') {
        gl.clear(gl.COLOR_BUFFER_BIT);
        cancelAnimationFrame(this._glRaf);
        this._glRaf = null;
        return;
      }

      const t = (performance.now() - this._glStartTime) / 1000;

      gl.useProgram(prog);
      gl.uniform2f(u.iResolution, canvas.width, canvas.height);
      gl.uniform1f(u.iTime, t);
      gl.uniform2f(u.iMouse, this._glMouse[0], this._glMouse[1]);

      // 全屏 quad（顶点数据在 shader 编译时已绑定）
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);

      this._glRaf = requestAnimationFrame(() => this._tickAurora());
    },

    _destroyAurora() {
      if (this._glRaf) cancelAnimationFrame(this._glRaf);
      if (this._glProgram && this._gl) this._gl.deleteProgram(this._glProgram);
      window.removeEventListener('resize', this._onGlResize);
      if (this._glCanvas) {
        this._glCanvas.removeEventListener('mousemove', this._onGlMouseMove);
      }
      this._glRaf = null;
      this._gl = null;
      this._glProgram = null;
      this._glCanvas = null;
      this._glUniforms = null;
    },

    _compileShaderProgram(gl, vsSource, fsSource) {
      const compile = (type, source) => {
        const shader = gl.createShader(type);
        gl.shaderSource(shader, source);
        gl.compileShader(shader);
        if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
          console.warn('Shader compile error:', gl.getShaderInfoLog(shader));
          gl.deleteShader(shader);
          return null;
        }
        return shader;
      };
      const vs = compile(gl.VERTEX_SHADER, vsSource);
      const fs = compile(gl.FRAGMENT_SHADER, fsSource);
      if (!vs || !fs) return null;

      const prog = gl.createProgram();
      gl.attachShader(prog, vs);
      gl.attachShader(prog, fs);
      gl.linkProgram(prog);
      if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) {
        console.warn('Program link error:', gl.getProgramInfoLog(prog));
        return null;
      }
      // 绑定全屏 quad 顶点（无需 VBO，用顶点 id 推导）
      gl.useProgram(prog);
      const posAttr = gl.getAttribLocation(prog, 'aVertexPosition');
      if (posAttr >= 0) {
        const buf = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, buf);
        gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 1,-1, -1,1, 1,1]), gl.STATIC_DRAW);
        gl.enableVertexAttribArray(posAttr);
        gl.vertexAttribPointer(posAttr, 2, gl.FLOAT, false, 0, 0);
      }
      return prog;
    },

    // ==================== 偏好持久化 ====================

    _prefKey() {
      return 'skyeye_ai_settings';
    },

    _loadPrefs() {
      try {
        const prefs = JSON.parse(localStorage.getItem(this._prefKey())) || {};
        this._storageError = false;
        return prefs;
      } catch (e) {
        console.warn('[aiSettings] localStorage 读取失败', e);
        this._storageError = true;
        return {};
      }
    },

    savePrefs() {
      clearTimeout(this._saveTimer);
      this._saveTimer = setTimeout(() => {
        const prefs = {
          model: this.model,
          temperature: this.temperature,
          maxTokens: this.maxTokens,
          reduceMotion: this.reduceMotion,
          defaultMode: this.defaultMode,
          autoSummary: this.autoSummary,
        };
        try {
          localStorage.setItem(this._prefKey(), JSON.stringify(prefs));
          this._storageError = false;
        } catch (e) {
          console.warn('[aiSettings] localStorage 写入失败', e);
          this._storageError = true;
        }
        this._showToast(this._storageError ? '写入存储失败，请检查浏览器空间' : '设置已保存');
      }, 300);
    },

    _showToast(msg) {
      clearTimeout(this._toastTimer);
      this.toastMessage = msg;
      this.toastVisible = true;
      this._toastTimer = setTimeout(() => {
        this.toastVisible = false;
      }, 1800);
    },

    restoreDefaults() {
      const DEFAULTS = {
        model: 'deepseek-chat',
        temperature: 0.7,
        maxTokens: 4096,
        reduceMotion: false,
        defaultMode: 'chat',
        autoSummary: false,
      };
      this.model = DEFAULTS.model;
      this.temperature = DEFAULTS.temperature;
      this.maxTokens = DEFAULTS.maxTokens;
      this.reduceMotion = DEFAULTS.reduceMotion;
      this.defaultMode = DEFAULTS.defaultMode;
      this.autoSummary = DEFAULTS.autoSummary;
      this.savePrefs();
      this._showToast('已恢复默认设置');
    },
  },
};

// ==================== GLSL Shaders (WebGL Ether 背景) ====================

// Vertex shader — 全屏 quad
const VERTEX_SHADER = `
attribute vec4 aVertexPosition;
void main() {
  gl_Position = aVertexPosition;
}
`;

// Fragment shader — Ether by nimitz (Shadertoy)
// 深色主题专用（浅色模式 WebGL 不渲染）
const ETHER_FRAGMENT_SHADER = `
precision mediump float;
uniform vec2 iResolution;
uniform float iTime;
uniform vec2 iMouse;

mat2 m(float a){float c=cos(a),s=sin(a);return mat2(c,-s,s,c);}
float map(vec3 p){
    p.xz*=m(iTime*0.4);p.xy*=m(iTime*0.3);
    vec3 q=p*2.+iTime;
    return length(p+vec3(sin(iTime*0.7)))*log(length(p)+1.)+sin(q.x+sin(q.z+sin(q.y)))*0.5-1.;
}

void main(){
    vec2 uv=(gl_FragCoord.xy/iResolution.xy)*2.-1.;
    uv.x*=iResolution.x/iResolution.y;

    vec3 cl=vec3(0.);
    float d=2.5;
    for(int i=0;i<=5;i++){
        vec3 p3d=vec3(0,0,5.)+normalize(vec3(uv,-1.))*d;
        float rz=map(p3d);
        float f=clamp((rz-map(p3d+.1))*0.5,-.1,1.);
        vec3 base=vec3(0.08,0.22,0.38)+vec3(4.0,2.0,5.5)*f;
        cl=cl*base+smoothstep(2.5,.0,rz)*.7*base;
        d+=min(rz,1.);
    }

    // 鼠标微光影响
    float mx=smoothstep(0.5,0.0,length(uv-iMouse*2.+1.));
    cl+=vec3(0.15,0.3,0.6)*mx*0.2;

    gl_FragColor=vec4(cl,1.0);
}
`;
</script>

<style lang="scss" scoped>
/* ========================= 背景 ========================= */
.settings-root {
  position: relative;
  height: 100%;
  background: #05070b;
  overflow-y: auto;
  overflow-x: hidden;
  transition: background 0.5s cubic-bezier(0.32, 0.72, 0, 1);

  /* 美化滚动条 — iOS 风格：默认隐藏，hover 显现 */
  &::-webkit-scrollbar {
    width: 5px;
  }
  &::-webkit-scrollbar-track {
    background: transparent;
  }
  &::-webkit-scrollbar-thumb {
    background: transparent;
    border-radius: 3px;
    transition: background 0.3s;
  }
  &:hover::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.15);
  }
}

/* ========================= 噪点纹理 (background-image, 避免合成层导致光标异常) ========================= */
.noise-overlay {
  position: fixed;
  inset: 0;
  z-index: 1;
  pointer-events: none;
  opacity: 0.03;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  background-repeat: repeat;
  background-size: 256px 256px;
}

/* ========================= 返回按钮 ========================= */
.back-btn {
  position: absolute;
  top: 28px;
  left: -56px;
  z-index: 10;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  color: rgba(255, 255, 255, 0.45);
  cursor: pointer;
  transition:
    background 0.25s ease,
    border-color 0.25s ease,
    color 0.25s ease,
    transform 0.25s cubic-bezier(0.32, 0.72, 0, 1);

  &:hover {
    background: rgba(255, 255, 255, 0.12);
    border-color: rgba(255, 255, 255, 0.2);
    color: rgba(255, 255, 255, 0.85);
    transform: translateX(-2px);
  }

  &:active {
    transform: scale(0.95);
  }

  &:focus-visible {
    outline: 2px solid rgba(99, 102, 241, 0.6);
    outline-offset: 2px;
  }

  .icon {
    display: block;
  }
}

[data-theme="light"] .back-btn {
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-color: rgba(0, 0, 0, 0.08);
  color: rgba(0, 0, 0, 0.35);

  &:hover {
    background: rgba(255, 255, 255, 0.7);
    border-color: rgba(0, 0, 0, 0.15);
    color: rgba(0, 0, 0, 0.6);
  }
}

/* Canvas: 动态极光 + 粒子 */
.aurora-canvas {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
}

/* ========================= 呼吸光斑 (iOS 26 风格) ========================= */
.bg-orb {
  position: fixed;
  border-radius: 50%;
  filter: blur(80px);
  pointer-events: none;
  z-index: 0;
  animation: orb-breathe 4s ease-in-out infinite;
}

.bg-orb-1 {
  width: 384px; height: 384px;
  top: 15%; left: 15%;
  background: rgba(59, 130, 246, 0.06);
  animation-delay: 0s;
}

.bg-orb-2 {
  width: 320px; height: 320px;
  bottom: 20%; right: 15%;
  background: rgba(139, 92, 246, 0.06);
  animation-delay: 1.5s;
}

.bg-orb-3 {
  width: 280px; height: 280px;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  background: rgba(236, 72, 153, 0.05);
  animation-delay: 3s;
}

@keyframes orb-breathe {
  0%, 100% { opacity: 0.5; transform: translate(-50%, -50%) scale(1); }
  50%      { opacity: 1;   transform: translate(-50%, -50%) scale(1.15); }
}

/* orb-1 和 orb-2 不使用 translate(-50%,-50%)，需要分写 */
.bg-orb-1 { animation-name: orb-breathe-1; }
.bg-orb-2 { animation-name: orb-breathe-2; }

@keyframes orb-breathe-1 {
  0%, 100% { opacity: 0.5; transform: scale(1); }
  50%      { opacity: 1;   transform: scale(1.15); }
}

@keyframes orb-breathe-2 {
  0%, 100% { opacity: 0.4; transform: scale(1); }
  50%      { opacity: 0.9; transform: scale(1.12); }
}

/* 浅色主题下光斑不可见（已有浅色背景） */
[data-theme="light"] .bg-orb {
  display: none;
}

/* 减少动效模式下光斑不呼吸 */
.reduce-motion .bg-orb {
  animation: none;
  opacity: 0.3;
}

/* ========================= 主容器 ========================= */
.settings-main {
  position: relative;
  z-index: 2;
  max-width: 880px;
  margin: 0 auto;
  padding: 72px 32px 96px;
}

/* ========================= 头部 ========================= */
.page-header {
  margin-bottom: 56px;

  .eyebrow {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 20px;
    background: rgba(99, 102, 241, 0.12);
    border: 1px solid rgba(99, 102, 241, 0.2);
    color: rgba(165, 180, 252, 0.9);
    font-size: 12px;
    font-weight: 500;
    letter-spacing: 0.04em;
    margin-bottom: 18px;
  }

  h1 {
    font-size: clamp(36px, 5vw, 54px);
    font-weight: 700;
    color: rgba(255, 255, 255, 0.95);
    margin: 0 0 12px;
    line-height: 1.1;
    letter-spacing: -0.025em;
  }

  .subtitle {
    color: rgba(255, 255, 255, 0.55);
    font-size: 16px;
    margin: 0;
  }
}

/* ========================= 便当盒网格 ========================= */
.bento-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;

  .col-wide {
    grid-column: span 2;
  }
}

/* ========================= 操作行 ========================= */
.actions-bar {
  display: flex;
  justify-content: center;
  margin-top: 28px;
}

.btn-reset {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 20px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  color: rgba(255, 255, 255, 0.4);
  font-size: 13px;
  font-family: inherit;
  cursor: pointer;
  transition:
    background 0.25s ease,
    border-color 0.25s ease,
    color 0.25s ease;

  &:hover {
    background: rgba(255, 255, 255, 0.12);
    border-color: rgba(255, 255, 255, 0.2);
    color: rgba(255, 255, 255, 0.8);
  }

  &:active {
    background: rgba(255, 255, 255, 0.08);
  }

  &:focus-visible {
    outline: 2px solid rgba(99, 102, 241, 0.6);
    outline-offset: 2px;
  }
}

.btn-reset-icon {
  display: block;
}

/* ========================= Save Toast ========================= */
.save-toast {
  position: fixed;
  bottom: 32px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 50;
  padding: 10px 22px;
  border-radius: 14px;
  background: rgba(15, 23, 42, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(32px);
  -webkit-backdrop-filter: blur(32px);
  color: rgba(255, 255, 255, 0.85);
  font-size: 13px;
  font-weight: 500;
  letter-spacing: 0.02em;
  pointer-events: none;
  white-space: nowrap;
}

/* Toast transition */
.toast-enter-active {
  transition:
    opacity 0.25s cubic-bezier(0.32, 0.72, 0, 1),
    transform 0.25s cubic-bezier(0.32, 0.72, 0, 1);
}
.toast-leave-active {
  transition:
    opacity 0.3s ease,
    transform 0.3s cubic-bezier(0.32, 0.72, 0, 1);
}
.toast-enter,
.toast-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(8px);
}

/* ========================= 卡片 Pod — Liquid Glass ========================= */
.card-pod {
  /* 外壳 — 半透明玻璃托盘 */
  .pod-shell {
    padding: 4px;
    border-radius: 24px;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.06),
      0 4px 24px rgba(0, 0, 0, 0.3);
    transition:
      border-color 0.6s cubic-bezier(0.32, 0.72, 0, 1),
      box-shadow 0.6s cubic-bezier(0.32, 0.72, 0, 1);

    &:hover {
      border-color: rgba(255, 255, 255, 0.15);
      box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.08),
        0 12px 40px rgba(0, 0, 0, 0.45);
    }
  }

  /* 内核 — 深层玻璃面板 */
  .pod-core {
    position: relative;
    padding: 28px 28px 32px;
    border-radius: 21px;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(40px);
    -webkit-backdrop-filter: blur(40px);
    box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.06);
    /* overflow: visible — 确保 field-help tooltip 不被裁剪 */

    /* 双层玻璃深度：伪元素叠加高光渐变 */
    &::before {
      content: '';
      position: absolute;
      inset: 0;
      border-radius: 21px;
      background: linear-gradient(135deg, rgba(255,255,255,0.06) 0%, transparent 50%);
      pointer-events: none;
      z-index: 0;
    }

    > * {
      position: relative;
      z-index: 1;
    }
  }

  .pod-icon-wrap {
    width: 44px;
    height: 44px;
    border-radius: 14px;
    background: rgba(99, 102, 241, 0.12);
    border: 1px solid rgba(99, 102, 241, 0.2);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 16px;

    .pod-icon {
      display: block;
      color: rgba(165, 180, 252, 0.9);
    }
  }

  h3 {
    font-size: 17px;
    font-weight: 650;
    color: rgba(255, 255, 255, 0.9);
    margin: 0 0 4px;
  }

  .pod-desc {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.5);
    margin: 0 0 24px;
    line-height: 1.5;
  }
}

/* ========================= 表单项 ========================= */
.field-group {
  margin-bottom: 22px;

  &:last-child {
    margin-bottom: 0;
  }
}

.field-label {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.55);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 8px;
}

/* 帮助提示 ? 徽标 */
.field-help {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.35);
  font-size: 10px;
  font-weight: 600;
  font-family: inherit;
  line-height: 1;
  cursor: help;
  text-transform: none;
  letter-spacing: 0;
  transition:
    background 0.25s ease,
    border-color 0.25s ease,
    color 0.25s ease;

  &:hover {
    background: rgba(99, 102, 241, 0.2);
    border-color: rgba(99, 102, 241, 0.35);
    color: rgba(165, 180, 252, 0.9);
  }

  /* 自定义 tooltip 气泡 */
  &::after {
    content: attr(data-tip);
    position: absolute;
    bottom: calc(100% + 10px);
    /* 默认居中，右侧空间不足时从右边对齐 */
    left: 50%;
    right: auto;
    transform: translateX(-50%) translateY(4px);
    padding: 8px 14px;
    border-radius: 10px;
    background: rgba(15, 23, 42, 0.97);
    border: 1px solid rgba(99, 102, 241, 0.25);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.45);
    color: rgba(255, 255, 255, 0.85);
    font-size: 12px;
    font-weight: 400;
    line-height: 1.55;
    white-space: normal;
    width: 260px;
    max-width: min(260px, calc(100vw - 32px));
    text-align: left;
    letter-spacing: 0;
    text-transform: none;
    pointer-events: none;
    opacity: 0;
    transition:
      opacity 0.2s ease,
      transform 0.2s cubic-bezier(0.32, 0.72, 0, 1);
    z-index: 100;
  }

  /* 右侧问号：tooltip 右对齐防止出界 */
  &.right &::after {
    left: auto;
    right: 0;
    transform: translateY(4px);
  }

  /* 气泡三角箭头 */
  &::before {
    content: '';
    position: absolute;
    left: 50%;
    bottom: calc(100% + 4px);
    transform: translateX(-50%) translateY(4px);
    width: 0;
    height: 0;
    border-left: 6px solid transparent;
    border-right: 6px solid transparent;
    border-top: 6px solid rgba(15, 23, 42, 0.95);
    opacity: 0;
    transition:
      opacity 0.2s ease,
      transform 0.2s cubic-bezier(0.32, 0.72, 0, 1);
    z-index: 100;
    pointer-events: none;
  }

  &:hover::after,
  &:hover::before {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}

.field-label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;

  .field-label {
    margin-bottom: 0;
  }

  .field-val {
    font-size: 13px;
    font-weight: 650;
    color: rgba(165, 180, 252, 0.9);
    font-variant-numeric: tabular-nums;
  }
}

/* ---- 下拉选择 ---- */
.select-wrap {
  position: relative;

  .field-select {
    width: 100%;
    padding: 11px 36px 11px 14px;
    border-radius: 14px;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    color: rgba(255, 255, 255, 0.85);
    font-size: 14px;
    font-family: inherit;
    appearance: none;
    cursor: pointer;
    outline: none;
    transition:
      border-color 0.35s cubic-bezier(0.32, 0.72, 0, 1),
      background 0.35s cubic-bezier(0.32, 0.72, 0, 1),
      box-shadow 0.35s cubic-bezier(0.32, 0.72, 0, 1);

    &:focus {
      border-color: rgba(99, 102, 241, 0.45);
      background: rgba(255, 255, 255, 0.1);
      box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1);
    }
  }

  .select-chevron {
    position: absolute;
    right: 14px;
    top: 50%;
    transform: translateY(-50%);
    color: rgba(255, 255, 255, 0.3);
    pointer-events: none;
    transition: transform 0.35s cubic-bezier(0.32, 0.72, 0, 1), color 0.35s cubic-bezier(0.32, 0.72, 0, 1);
  }

  &:focus-within .select-chevron {
    transform: translateY(-50%) rotate(180deg);
    color: rgba(165, 180, 252, 0.7);
  }
}

/* ---- 滑块 ---- */
.field-slider {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 6px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.1);
  outline: none;
  margin: 0 0 4px;
  cursor: pointer;

  &::-webkit-slider-thumb {
    -webkit-appearance: none;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background: #fff;
    border: 2px solid rgba(99, 102, 241, 0.5);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3), 0 0 12px rgba(99, 102, 241, 0.25);
    cursor: pointer;
    transition:
      transform 0.25s cubic-bezier(0.32, 0.72, 0, 1),
      box-shadow 0.25s cubic-bezier(0.32, 0.72, 0, 1);
  }

  &::-webkit-slider-thumb:hover {
    transform: scale(1.15);
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.4), 0 0 20px rgba(99, 102, 241, 0.4);
  }

  &::-webkit-slider-thumb:active {
    transform: scale(0.95);
    cursor: grabbing;
  }

  &::-moz-range-thumb {
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background: #fff;
    border: 2px solid rgba(99, 102, 241, 0.5);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    cursor: pointer;
  }
}

.slider-hints {
  display: flex;
  justify-content: space-between;
  font-size: 10px;
  color: rgba(255, 255, 255, 0.35);
  padding-top: 2px;
}

/* ---- 切换开关 ---- */
.toggle-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  padding: 6px 0;
  user-select: none;
}

.toggle-label {
  margin-bottom: 1px !important;
}

.toggle-hint {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
}

.toggle-switch {
  position: relative;
  width: 48px;
  height: 28px;
  border-radius: 28px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  cursor: pointer;
  outline: none;
  flex-shrink: 0;

  &:focus-visible {
    outline: 2px solid rgba(99, 102, 241, 0.6);
    outline-offset: 2px;
  }

  transition:
    background 0.45s cubic-bezier(0.32, 0.72, 0, 1),
    border-color 0.45s cubic-bezier(0.32, 0.72, 0, 1),
    box-shadow 0.45s cubic-bezier(0.32, 0.72, 0, 1);

  &.active {
    background: rgba(99, 102, 241, 0.4);
    border-color: rgba(99, 102, 241, 0.5);
    box-shadow: 0 0 20px rgba(99, 102, 241, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.1);
  }

  .toggle-knob {
    position: absolute;
    top: 3px;
    left: 3px;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background: #fff;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.25);
    transition: transform 0.4s cubic-bezier(0.32, 0.72, 0, 1);
  }

  &.active .toggle-knob {
    transform: translateX(20px);
  }

  &:active .toggle-knob {
    width: 24px;
  }
}

/* ---- 模式芯片 ---- */
.mode-chips {
  display: flex;
  gap: 8px;
}

.mode-chip {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px 8px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  color: rgba(255, 255, 255, 0.45);
  cursor: pointer;
  outline: none;
  font-family: inherit;

  &:focus-visible {
    outline: 2px solid rgba(99, 102, 241, 0.6);
    outline-offset: 2px;
  }

  transition:
    all 0.4s cubic-bezier(0.32, 0.72, 0, 1);

  .chip-icon {
    display: block;
    transition: transform 0.4s cubic-bezier(0.32, 0.72, 0, 1);
  }

  .chip-label {
    font-size: 12px;
    font-weight: 550;
  }

  &:hover {
    border-color: rgba(255, 255, 255, 0.2);
    background: rgba(255, 255, 255, 0.08);
    color: rgba(255, 255, 255, 0.75);

    .chip-icon {
      transform: scale(1.15);
    }
  }

  &.active {
    border-color: rgba(99, 102, 241, 0.5);
    background: rgba(99, 102, 241, 0.15);
    color: #fff;
    box-shadow: 0 0 24px rgba(99, 102, 241, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.08);

    .chip-icon {
      transform: scale(1.1);
    }
  }

  &:active {
    transform: scale(0.97);
  }
}

/* ---- 快捷键列表 ---- */
.kbd-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.kbd-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.kbd-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
}

.kbd-keys {
  display: flex;
  gap: 4px;
  align-items: center;

  kbd {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 26px;
    height: 26px;
    padding: 0 8px;
    border-radius: 7px;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.12);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.06),
      0 2px 0 rgba(0, 0, 0, 0.3);
    color: rgba(255, 255, 255, 0.6);
    font-size: 11px;
    font-weight: 600;
    font-family: inherit;
  }
}

/* ---- 关于元信息 ---- */
.about-meta {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.meta-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  transition:
    border-color 0.4s cubic-bezier(0.32, 0.72, 0, 1),
    background 0.4s cubic-bezier(0.32, 0.72, 0, 1);

  &:hover {
    border-color: rgba(255, 255, 255, 0.15);
    background: rgba(255, 255, 255, 0.06);
  }

  .meta-key {
    font-size: 13px;
    color: rgba(255, 255, 255, 0.4);
  }

  .meta-val {
    font-size: 13px;
    font-weight: 550;
    color: rgba(255, 255, 255, 0.7);
  }
}

/* ========================= 打字机光标 ========================= */
.typing-cursor {
  display: inline-block;
  color: rgba(99, 102, 241, 0.7);
  font-weight: 300;
  animation: cursor-blink 0.8s step-end infinite;
  margin-left: 2px;
}

@keyframes cursor-blink {
  0%, 100% { opacity: 1; }
  50%      { opacity: 0; }
}

/* ========================= 垂直幕布入场 (iOS 26 style) ========================= */
.curtain-item {
  opacity: 0;
  transform: scale(0.97);
  filter: blur(8px);
  transition:
    opacity 0.5s cubic-bezier(0.32, 0.72, 0, 1),
    transform 0.5s cubic-bezier(0.32, 0.72, 0, 1),
    filter 0.5s cubic-bezier(0.32, 0.72, 0, 1);

  &.curtain-revealed {
    opacity: 1;
    transform: translate(0, 0) scale(1) !important;
    filter: blur(0);
  }
}

/* 方向偏移量（更克制） */
.curtain-top    { transform: translateY(-20px) scale(0.97); }
.curtain-left   { transform: translateX(-40px) scale(0.97); }
.curtain-right  { transform: translateX(40px)  scale(0.97); }
.curtain-bottom { transform: translateY(30px)  scale(0.97); }

/* 交错过场延迟 */
.bento-grid .curtain-item:nth-child(1) { transition-delay: 0s;    }
.bento-grid .curtain-item:nth-child(2) { transition-delay: 0.08s; }
.bento-grid .curtain-item:nth-child(3) { transition-delay: 0.14s; }
.bento-grid .curtain-item:nth-child(4) { transition-delay: 0.20s; }
.bento-grid .curtain-item:nth-child(5) { transition-delay: 0.26s; }

/* ========================= 亮色主题覆盖 ========================= */
[data-theme="light"] .settings-root {
  background: #f4f5f9;
  transition: background 0.5s cubic-bezier(0.32, 0.72, 0, 1);

  &::-webkit-scrollbar-thumb {
    background: transparent;
  }
  &:hover::-webkit-scrollbar-thumb {
    background: rgba(0, 0, 0, 0.12);
  }
}

[data-theme="light"] .typing-cursor {
  color: rgba(99, 102, 241, 0.6);
}

[data-theme="light"] .field-help {
  background: rgba(99, 102, 241, 0.06);
  border-color: rgba(99, 102, 241, 0.12);
  color: rgba(99, 102, 241, 0.35);

  &:hover {
    background: rgba(99, 102, 241, 0.15);
    border-color: rgba(99, 102, 241, 0.3);
    color: rgba(99, 102, 241, 0.75);
  }

  &::after {
    background: rgba(255, 255, 255, 0.96);
    border-color: rgba(99, 102, 241, 0.2);
    color: #1e293b;
  }

  &::before {
    border-top-color: rgba(255, 255, 255, 0.96);
  }
}

[data-theme="light"] .page-header {
  h1 { color: #0f172a; }
  .subtitle { color: #64748b; }
  .eyebrow {
    background: rgba(99, 102, 241, 0.1);
    border-color: rgba(99, 102, 241, 0.15);
    color: #4f46e5;
  }
}

[data-theme="light"] .card-pod {
  .pod-shell {
    background: rgba(0, 0, 0, 0.03);
    border-color: rgba(0, 0, 0, 0.06);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.5),
      0 4px 20px rgba(0, 0, 0, 0.06);
  }

  &:hover .pod-shell {
    border-color: rgba(0, 0, 0, 0.1);
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.6),
      0 8px 32px rgba(0, 0, 0, 0.1);
  }

  .pod-core {
    background: rgba(255, 255, 255, 0.45);
    border-color: rgba(0, 0, 0, 0.06);
    backdrop-filter: blur(40px);
    -webkit-backdrop-filter: blur(40px);
    box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.7);

    &::before {
      background: linear-gradient(135deg, rgba(255,255,255,0.3) 0%, transparent 50%);
    }
  }

  h3 { color: #1e293b; }
  .pod-desc { color: #94a3b8; }
  .pod-icon-wrap {
    background: rgba(99, 102, 241, 0.08);
    border-color: rgba(99, 102, 241, 0.12);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);

    .pod-icon {
      color: rgba(99, 102, 241, 0.7);
    }
  }
}

[data-theme="light"] .field-label { color: #64748b; }
[data-theme="light"] .field-val { color: #4f46e5; }

[data-theme="light"] .field-slider {
  background: rgba(0, 0, 0, 0.08);
  &::-webkit-slider-thumb { box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); }
}

[data-theme="light"] .select-wrap .field-select {
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border-color: rgba(0, 0, 0, 0.1);
  color: #334155;
  &:focus {
    border-color: rgba(99, 102, 241, 0.4);
    background: rgba(255, 255, 255, 0.7);
  }
}

[data-theme="light"] .select-chevron { color: #94a3b8; }

[data-theme="light"] .toggle-switch {
  background: rgba(0, 0, 0, 0.08);
  border-color: rgba(0, 0, 0, 0.12);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

[data-theme="light"] .mode-chip {
  background: rgba(0, 0, 0, 0.03);
  border-color: rgba(0, 0, 0, 0.08);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  color: #64748b;
  &:hover { background: rgba(0, 0, 0, 0.06); color: #334155; }
  &.active { color: #1e293b; }
}

[data-theme="light"] .kbd-row kbd {
  background: rgba(0, 0, 0, 0.04);
  border-color: rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8), 0 1px 0 rgba(0, 0, 0, 0.08);
  color: #475569;
}

[data-theme="light"] .kbd-label { color: #475569; }
[data-theme="light"] .toggle-hint { color: #94a3b8; }
[data-theme="light"] .slider-hints { color: rgba(0, 0, 0, 0.2); }

[data-theme="light"] .meta-row {
  background: rgba(0, 0, 0, 0.02);
  border-color: rgba(0, 0, 0, 0.05);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  .meta-key { color: #94a3b8; }
  .meta-val { color: #475569; }
}

[data-theme="light"] .btn-reset {
  background: rgba(0, 0, 0, 0.03);
  border-color: rgba(0, 0, 0, 0.08);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  color: rgba(0, 0, 0, 0.3);

  &:hover {
    background: rgba(0, 0, 0, 0.06);
    border-color: rgba(0, 0, 0, 0.14);
    color: rgba(0, 0, 0, 0.55);
  }
}

[data-theme="light"] .save-toast {
  background: rgba(255, 255, 255, 0.85);
  border-color: rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(32px);
  -webkit-backdrop-filter: blur(32px);
  color: #1e293b;
}

/* ========================= Token 预览条 ========================= */
.token-preview-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
}

.token-label {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.2);
  white-space: nowrap;
}

.token-track {
  flex: 1;
  height: 4px;
  border-radius: 4px;
  background: rgba(255, 255, 255, 0.08);
  overflow: hidden;
}

.token-fill {
  display: block;
  height: 100%;
  border-radius: 4px;
  background: linear-gradient(90deg, rgba(99, 102, 241, 0.5), rgba(129, 140, 248, 0.7));
  transition: width 0.4s cubic-bezier(0.32, 0.72, 0, 1);
}

[data-theme="light"] .token-label {
  color: rgba(0, 0, 0, 0.25);
}

[data-theme="light"] .token-track {
  background: rgba(0, 0, 0, 0.06);
}

/* ========================= Temperature 颜色 ========================= */
.temp-cool  { color: #60a5fa !important; }
.temp-warm  { color: #facc15 !important; }
.temp-hot   { color: #f97316 !important; }
.temp-blaze { color: #ef4444 !important; }

[data-theme="light"] .temp-cool  { color: #3b82f6 !important; }
[data-theme="light"] .temp-warm  { color: #eab308 !important; }
[data-theme="light"] .temp-hot   { color: #ea580c !important; }
[data-theme="light"] .temp-blaze { color: #dc2626 !important; }

/* ========================= 响应式 ========================= */
@media (max-width: 768px) {
  .settings-main {
    padding: 40px 16px 64px;
  }

  .back-btn {
    top: 12px;
    left: 8px;
  }

  .bento-grid {
    grid-template-columns: 1fr;
    gap: 14px;

    .col-wide {
      grid-column: span 1;
    }
  }

  .pod-core {
    padding: 20px 18px 24px;
  }
}

/* ========================= localStorage 异常警告 ========================= */
.storage-warning {
  margin: 16px auto 0;
  max-width: 520px;
  padding: 10px 16px;
  border-radius: var(--radius-md, 12px);
  background: rgba(239, 68, 68, 0.08);
  border: 1px solid rgba(239, 68, 68, 0.2);
  color: rgba(252, 165, 165, 0.9);
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: center;
}

[data-theme="light"] .storage-warning {
  background: rgba(239, 68, 68, 0.06);
  border-color: rgba(239, 68, 68, 0.25);
  color: #b91c1c;
}

/* ========================= prefers-reduced-motion ========================= */
@media (prefers-reduced-motion: reduce) {
  .settings-root * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
</style>