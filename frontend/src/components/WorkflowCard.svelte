<script>
  export let workflow;
  
  // Error handling state
  let showErrorDetails = false;
  let retryAttempts = 0;
  let maxRetryAttempts = 3;
  
  // Status configuration with colors and icons
  const statusConfig = {
    received: {
      color: 'bg-blue-500',
      textColor: 'text-blue-400',
      borderColor: 'border-blue-400/30',
      icon: '📥',
      label: 'Received'
    },
    processing: {
      color: 'bg-yellow-500',
      textColor: 'text-yellow-400',
      borderColor: 'border-yellow-400/30',
      icon: '🔄',
      label: 'Processing'
    },
    classified: {
      color: 'bg-purple-500',
      textColor: 'text-purple-400',
      borderColor: 'border-purple-400/30',
      icon: '🎯',
      label: 'Classified'
    },
    delegating: {
      color: 'bg-indigo-500',
      textColor: 'text-indigo-400',
      borderColor: 'border-indigo-400/30',
      icon: '🔀',
      label: 'Delegating'
    },
    working: {
      color: 'bg-orange-500',
      textColor: 'text-orange-400',
      borderColor: 'border-orange-400/30',
      icon: '⚡',
      label: 'Working'
    },
    resolved: {
      color: 'bg-green-500',
      textColor: 'text-green-400',
      borderColor: 'border-green-400/30',
      icon: '✅',
      label: 'Resolved'
    },
    escalated: {
      color: 'bg-red-500',
      textColor: 'text-red-400',
      borderColor: 'border-red-400/30',
      icon: '🚨',
      label: 'Escalated'
    },
    failed: {
      color: 'bg-red-600',
      textColor: 'text-red-300',
      borderColor: 'border-red-500/50',
      icon: '❌',
      label: 'Failed'
    },
    error: {
      color: 'bg-red-700',
      textColor: 'text-red-200',
      borderColor: 'border-red-600/50',
      icon: '⚠️',
      label: 'Error'
    }
  };
  
  // Agent configuration with icons and colors
  const agentConfig = {
    'Master Agent': {
      icon: '🧠',
      color: 'text-blue-400',
      bgColor: 'bg-blue-500/20'
    },
    'PhishGuard Agent': {
      icon: '🛡️',
      color: 'text-red-400',
      bgColor: 'bg-red-500/20'
    },
    'System': {
      icon: '⚙️',
      color: 'text-gray-400',
      bgColor: 'bg-gray-500/20'
    }
  };
  
  // Get current status configuration
  $: currentStatus = statusConfig[workflow.status] || statusConfig.received;
  
  // Format timestamp for display
  function formatTime(timestamp) {
    return new Date(timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  }
  
  // Format relative time
  function getRelativeTime(timestamp) {
    const now = new Date();
    const time = new Date(timestamp);
    const diffMs = now - time;
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    
    if (diffSecs < 60) return `${diffSecs}s ago`;
    if (diffMins < 60) return `${diffMins}m ago`;
    return formatTime(timestamp);
  }
  
  // Get agent configuration
  function getAgentConfig(agentName) {
    return agentConfig[agentName] || agentConfig['System'];
  }
  
  // Check if workflow has errors
  function hasErrors(workflow) {
    return workflow.status === 'failed' || 
           workflow.status === 'error' || 
           workflow.error || 
           workflow.error_message ||
           (workflow.error_count && workflow.error_count > 0);
  }
  
  // Get error summary
  function getErrorSummary(workflow) {
    if (workflow.error_message) return workflow.error_message;
    if (workflow.error) return workflow.error;
    if (workflow.status === 'failed') return 'Workflow execution failed';
    if (workflow.status === 'error') return 'System error occurred';
    return 'Unknown error';
  }
  
  // Handle retry action
  function handleRetry() {
    if (retryAttempts >= maxRetryAttempts) {
      return;
    }
    
    retryAttempts++;
    
    // Emit retry event to parent
    const event = new CustomEvent('retryWorkflow', {
      detail: { 
        workflowId: workflow.id,
        attempt: retryAttempts
      }
    });
    
    if (typeof window !== 'undefined') {
      window.dispatchEvent(event);
    }
  }
  
  // Format error timestamp
  function formatErrorTime(timestamp) {
    if (!timestamp) return '';
    return new Date(timestamp).toLocaleString();
  }
</script>

<div class="glass-dark rounded-xl p-6 border {currentStatus.borderColor} transition-all duration-300 hover:scale-[1.01]
            {hasErrors(workflow) ? 'ring-2 ring-red-500/20' : ''}">
  <!-- Header -->
  <div class="flex items-center justify-between mb-4">
    <div class="flex items-center space-x-3">
      <!-- Status indicator -->
      <div class="flex items-center space-x-2">
        <div class="relative">
          <div class="w-3 h-3 {currentStatus.color} rounded-full 
                      {workflow.status === 'processing' || workflow.status === 'working' ? 'animate-pulse' : ''}"></div>
          {#if workflow.status === 'processing' || workflow.status === 'working'}
            <div class="absolute inset-0 w-3 h-3 {currentStatus.color} rounded-full animate-ping opacity-20"></div>
          {/if}
        </div>
        <span class="text-sm font-medium {currentStatus.textColor}">
          {currentStatus.icon} {currentStatus.label}
        </span>
        
        <!-- Error indicator -->
        {#if hasErrors(workflow)}
          <button
            on:click={() => showErrorDetails = !showErrorDetails}
            class="text-red-400 hover:text-red-300 transition-colors"
            title="Show error details"
          >
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
            </svg>
          </button>
        {/if}
      </div>
    </div>
    
    <!-- Ticket ID and timestamp -->
    <div class="text-right">
      <div class="text-sm font-mono text-white">{workflow.id}</div>
      <div class="text-xs text-gray-400">{getRelativeTime(workflow.created_at)}</div>
      {#if workflow.is_local}
        <div class="text-xs text-orange-400">Local</div>
      {/if}
    </div>
  </div>
  
  <!-- Error Details Panel -->
  {#if hasErrors(workflow) && showErrorDetails}
    <div class="mb-4 p-3 bg-red-900/20 border border-red-500/30 rounded-lg animate-fade-in">
      <div class="flex items-start justify-between mb-2">
        <h4 class="text-red-400 font-medium text-sm">Error Details</h4>
        <button
          on:click={() => showErrorDetails = false}
          class="text-red-400 hover:text-red-300"
        >
          <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
          </svg>
        </button>
      </div>
      
      <p class="text-sm text-red-300 mb-2">{getErrorSummary(workflow)}</p>
      
      {#if workflow.failed_at}
        <p class="text-xs text-gray-400 mb-2">
          Failed at: {formatErrorTime(workflow.failed_at)}
        </p>
      {/if}
      
      {#if workflow.error_count}
        <p class="text-xs text-gray-400 mb-2">
          Error count: {workflow.error_count}
        </p>
      {/if}
      
      <!-- Retry button for failed workflows -->
      {#if (workflow.status === 'failed' || workflow.status === 'error') && retryAttempts < maxRetryAttempts}
        <button
          on:click={handleRetry}
          class="px-3 py-1 bg-blue-500 hover:bg-blue-600 text-white text-xs rounded
                 transition-colors duration-200"
        >
          Retry ({retryAttempts}/{maxRetryAttempts})
        </button>
      {:else if retryAttempts >= maxRetryAttempts}
        <p class="text-xs text-gray-400">Maximum retry attempts reached</p>
      {/if}
    </div>
  {/if}
  
  <!-- Subject -->
  <div class="mb-4">
    <h3 class="text-lg font-medium text-white mb-1">
      {workflow.subject}
    </h3>
  </div>
  
  <!-- Logs section -->
  <div class="space-y-2">
    <div class="flex items-center justify-between">
      <h4 class="text-sm font-medium text-gray-300">Activity Log</h4>
      {#if workflow.logs && workflow.logs.length > 0}
        <span class="text-xs text-gray-500">{workflow.logs.length} entries</span>
      {/if}
    </div>
    
    <!-- Log entries -->
    <div class="max-h-48 overflow-y-auto space-y-2 scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-transparent">
      {#if workflow.logs && workflow.logs.length > 0}
        {#each workflow.logs as log, index (log.id || log.timestamp + index)}
          <div class="flex items-start space-x-3 p-3 rounded-lg border 
                      {log.type === 'error' ? 'bg-red-900/20 border-red-500/30' :
                       log.type === 'warning' ? 'bg-yellow-900/20 border-yellow-500/30' :
                       log.type === 'success' ? 'bg-green-900/20 border-green-500/30' :
                       'bg-black/20 border-white/5'}
                      animate-fade-in" style="animation-delay: {index * 100}ms">
            <!-- Agent icon -->
            <div class="flex-shrink-0 w-8 h-8 rounded-full {getAgentConfig(log.agent).bgColor} 
                        flex items-center justify-center text-sm">
              {getAgentConfig(log.agent).icon}
            </div>
            
            <!-- Log content -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center space-x-2 mb-1">
                <span class="text-sm font-medium {getAgentConfig(log.agent).color}">
                  {log.agent}
                </span>
                <span class="text-xs text-gray-500">
                  {formatTime(log.timestamp)}
                </span>
                {#if log.type && log.type !== 'info'}
                  <span class="text-xs px-2 py-0.5 rounded-full
                              {log.type === 'error' ? 'bg-red-500/20 text-red-400' :
                               log.type === 'warning' ? 'bg-yellow-500/20 text-yellow-400' :
                               log.type === 'success' ? 'bg-green-500/20 text-green-400' :
                               'bg-blue-500/20 text-blue-400'}">
                    {log.type}
                  </span>
                {/if}
              </div>
              <p class="text-sm leading-relaxed
                        {log.type === 'error' ? 'text-red-300' :
                         log.type === 'warning' ? 'text-yellow-300' :
                         log.type === 'success' ? 'text-green-300' :
                         'text-gray-300'}">
                {log.message}
              </p>
            </div>
          </div>
        {/each}
      {:else}
        <div class="text-center py-6 text-gray-500">
          <div class="text-2xl mb-2">⏳</div>
          <p class="text-sm">Waiting for agent activity...</p>
        </div>
      {/if}
    </div>
  </div>
  
  <!-- Progress indicator for active workflows -->
  {#if workflow.status === 'processing' || workflow.status === 'working'}
    <div class="mt-4 pt-4 border-t border-white/10">
      <div class="flex items-center space-x-2 text-sm text-gray-400">
        <svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span>Agents are working on this ticket...</span>
      </div>
    </div>
  {/if}
</div>

<style>
  /* Custom scrollbar styles */
  .scrollbar-thin {
    scrollbar-width: thin;
  }
  
  .scrollbar-thumb-gray-600::-webkit-scrollbar-thumb {
    background-color: #4b5563;
    border-radius: 0.375rem;
  }
  
  .scrollbar-track-transparent::-webkit-scrollbar-track {
    background-color: transparent;
  }
  
  ::-webkit-scrollbar {
    width: 6px;
  }
  
  /* Fade-in animation for log entries */
  @keyframes fade-in {
    from {
      opacity: 0;
      transform: translateY(10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  .animate-fade-in {
    animation: fade-in 0.3s ease-out forwards;
    opacity: 0;
  }
  
  /* Smooth hover effects */
  .glass-dark:hover {
    background: rgba(0, 0, 0, 0.3);
    backdrop-filter: blur(12px);
  }
</style>