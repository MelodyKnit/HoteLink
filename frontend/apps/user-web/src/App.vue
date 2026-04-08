<template>
  <router-view />
  <Toast :visible="toastVisible" :message="toastMessage" :type="toastType" @close="closeToast" />
  <ConfirmDialog />
</template>

<script setup lang="ts">
import { Toast, ConfirmDialog, useToast } from '@hotelink/ui'
const { toastVisible, toastMessage, toastType, closeToast } = useToast()
</script>
