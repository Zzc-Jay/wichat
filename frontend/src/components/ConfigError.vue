<script setup lang="ts">
defineProps<{ error: string }>()
</script>

<template>
  <div class="flex items-center justify-center h-screen" style="background:var(--bg-primary)">
    <div class="text-center max-w-md p-8">
      <div class="text-4xl mb-4">🔑</div>
      <h1 class="text-xl font-semibold mb-2" style="color:var(--text-primary)">Configuration Error</h1>
      <p class="mb-4 text-sm" style="color:var(--text-secondary)">{{ error }}</p>
      <div class="text-left rounded-lg p-4 text-sm" style="background:var(--bg-tertiary); color:var(--text-secondary)">
        <p class="font-medium mb-1" style="color:var(--text-primary)">Solution:</p>
        <code class="block mb-2 text-xs" style="background:var(--bg-secondary); padding:4px 8px; border-radius:4px">export DASHSCOPE_API_KEY="your-api-key"</code>
        <p>Get your key at:
          <a href="https://dashscope.console.aliyun.com/apiKey" target="_blank" style="color:var(--accent)" class="hover:underline">
            DashScope Console
          </a>
        </p>
      </div>
    </div>
  </div>
</template>
