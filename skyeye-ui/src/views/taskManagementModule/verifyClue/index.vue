<template>
  <task-list v-if="!taskId" />
  <task-detail v-else :task-id="taskId" :key="taskId" />
</template>

<script>
import TaskList from '@/views/taskManagementModule/taskList/index.vue';
import TaskDetail from '@/views/taskManagementModule/verifyClue/detail.vue';

export default {
  name: 'TaskMgmtVerify',
  components: { TaskList, TaskDetail },
  computed: {
    taskId() {
      return this.$route.query.id || '';
    },
  },
};
</script>
