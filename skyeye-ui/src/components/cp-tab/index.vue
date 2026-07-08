<template>
  <div class="cp-tab">
    <div class="cp-tab-bar">
      <span
        v-for="item in cpTablList"
        :key="item.id"
        :class="['cp-tab-item', { 'is-active': current === item.id }]"
        @click="handleItemClick(item)"
      >
        <i v-if="item.icon" :class="getIconClass(item.icon)"></i>
        {{ item.name }}
      </span>
      <el-button class="batch-delete" v-if="showButton" @click="batchDelete">
        <i class="el-icon-delete" style="font-size: 15px; color: red;"></i>
        批量删除
      </el-button>
    </div>
  </div>
</template>

<script>
const iconMap = {
  'arrow-down': 'el-icon-bottom',
  delete: 'el-icon-delete'
};

export default {
  props: {
    cpTablList: {
      type: Array,
      default() {
        return [];
      }
    },
    selectTab: String,
    showButton: {
      type: Boolean,
      default() {
        return false;
      }
    }
  },
  data() {
    return {
      current: this.selectTab || ''
    };
  },
  watch: {
    selectTab(val) {
      this.current = val || '';
    }
  },
  methods: {
    getIconClass(icon) {
      return iconMap[icon] || icon;
    },
    batchDelete() {
      this.$emit('cpTabClick');
    },
    handleItemClick(item) {
      if (this.current === item.id) {
        return;
      }
      this.current = item.id;
      this.$emit('cpTabItemClick', { key: item.id, item });
    }
  }
};
</script>

<style scoped>
.cp-tab-bar {
  position: relative;
  line-height: 40px;
}

.cp-tab-item {
  display: inline-block;
  padding: 0 16px;
  margin-right: 8px;
  cursor: pointer;
  color: var(--chip-color);
  background: var(--chip-bg);
  border: 1px solid var(--chip-border);
  border-radius: 4px;
  white-space: nowrap;
  transition: color 0.2s, border-color 0.2s, background 0.2s, box-shadow 0.2s;
  vertical-align: top;
}

.cp-tab-item:hover {
  border-color: var(--button-hover-border);
  color: var(--brand-accent);
}

.cp-tab-item.is-active {
  color: var(--chip-active-color);
  background: var(--chip-active-bg);
  border-color: var(--chip-active-border);
  box-shadow: 0 0 12px var(--button-hover-shadow);
}

.batch-delete {
  position: absolute;
  top: 4px;
  right: 0;
}
</style>
