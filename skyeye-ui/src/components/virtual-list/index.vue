<template>

  <recycle-scroller
    class="details-left-content"
    :items="listData"
    :item-size="50"
    key-field="id"
  >
    <template v-slot="{ item, index }">
      <div class="list-item" @click="clickList(item, index)">
        <div class="list-item-content">
          <a-icon class="location-icon" type="environment" />
          <span :class="{ 'list-item-active': item.selected }">{{
            item.title
          }}</span>
        </div>
        <a-divider />
      </div>
    </template>
  </recycle-scroller>
</template>

<script>
export default {
  name: 'VirtualList',
  data() {
    return {
      currentIndex: 0
    };
  },
  props: {
    listData: {
      type: Array,
      required: true,
    },
      cindex:{
        default:0,
          type:Number
      },
  },
    mounted() {
    },
    methods: {

    clickList(item, index) {
      this.listData[this.currentIndex].selected = false;
      this.listData[index].selected = true;
      this.currentIndex = index;
      this.$emit('changePolygon', item.SmID);
    }
  }
};
</script>

<style scoped>
/*左侧列表*/
.details-left-content {
  position: absolute;
  top: 4rem;
  bottom: 1rem;
  left: 1rem;
  right: 0;
  overflow: auto;
    color: white;
}

.list-item-content {
  display: flex;
  align-items: center;
}

::v-deep(.ant-divider) {
  margin: 1rem 0 !important;
}

.list-item-content i {
  color: #3989ca;
  font-size: 1.5rem;
}

.list-item-content span {
  font-size: 0.95rem;
  margin-left: 0.5rem;
}

.list-item:hover {
  cursor: pointer;
  color: yellowgreen;
  font-weight: 600;
  transition: all 100ms linear;
}

.list-item-active {
  color: rgb(0, 241, 243);
  font-weight: 600;
}
</style>
