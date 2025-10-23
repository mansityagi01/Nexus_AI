<script>
  import { onMount } from 'svelte';
  import { io } from 'socket.io-client';
  
  // Component imports
  import TicketForm from './components/TicketForm.svelte';
  import WorkflowCard from './components/WorkflowCard.svelte';
  
  // Application state
  let workflows = [];
  let socket;
  let connected = false;
  let reconnectAttempts = 0;
  let maxReconnectAttempts = 5;
  let reconnectTimeout;
  
  // Error handling state
  let connectionError = null;
  let systemError = null;
  let isOfflineMode = false;
  let queuedActions = [];
  let lastHeartbeat = null;
  let heartbeatInterval;
  
  // UI state for error handling
  let showErrorDetails = false;
  let errorNotifications = [];
  
  // Initialize WebSocket connection with comprehensive error handling
  function initializeSocket() {
    try {
      clearError('connection');
      
      socket = io('/', {
        transports: ['websocket', 'polling'],
        timeout: 10000,
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionDelayMax: 10000,
        maxReconnectionAttempts: maxReconnectAttempts,
        forceNew: true
      });
      
      // Connection event handlers
      socket.on('connect', () => {
        console.log('Connected to server');
        connected = true;
        isOfflineMode = false;
        reconnectAttempts = 0;
        connectionError = null;
        clearTimeout(reconnectTimeout);
        
        // Start heartbeat monitoring
        startHeartbeat();
        
        // Process queued actions
        processQueuedActions();
        
        // Show success notification
        addNotification('Connected to server', 'success');
      });
      
      socket.on('disconnect', (reason) => {
        console.log('Disconnected from server:', reason);
        connected = false;
        stopHeartbeat();
        
        // Set appropriate error message based on reason
        if (reason === 'io server disconnect') {
          connectionError = 'Server disconnected the connection';
          handleReconnection();
        } else if (reason === 'transport close') {
          connectionError = 'Connection lost due to network issues';
          handleReconnection();
        } else if (reason === 'transport error') {
          connectionError = 'Network transport error occurred';
          handleReconnection();
        } else {
          connectionError = `Connection lost: ${reason}`;
          handleReconnection();
        }
        
        addNotification('Connection lost - attempting to reconnect', 'warning');
      });
      
      socket.on('connect_error', (error) => {
        console.error('Connection error:', error);
        connected = false;
        connectionError = `Connection failed: ${error.message || error}`;
        handleReconnection();
      });
      
      socket.on('reconnect_error', (error) => {
        console.error('Reconnection error:', error);
        connectionError = `Reconnection failed: ${error.message || error}`;
      });
      
      socket.on('reconnect_failed', () => {
        console.error('Reconnection failed after maximum attempts');
        connectionError = 'Unable to reconnect to server';
        isOfflineMode = true;
        addNotification('Switched to offline mode', 'error');
      });
      
      // Workflow event handlers with error handling
      socket.on('workflow_update', (data) => {
        try {
          console.log('Workflow update received:', data);
          handleWorkflowUpdate(data);
        } catch (error) {
          console.error('Error processing workflow update:', error);
          handleError('Failed to process workflow update', error);
        }
      });
      
      socket.on('log_update', (data) => {
        try {
          console.log('Log update received:', data);
          handleLogUpdate(data);
        } catch (error) {
          console.error('Error processing log update:', error);
          handleError('Failed to process log update', error);
        }
      });
      
      // Server error handling
      socket.on('error', (error) => {
        console.error('Socket error:', error);
        handleError('Server error occurred', error);
      });
      
      // Custom error events from server
      socket.on('workflow_error', (data) => {
        console.error('Workflow error:', data);
        handleWorkflowError(data);
      });
      
      socket.on('system_error', (data) => {
        console.error('System error:', data);
        handleSystemError(data);
      });
      
    } catch (error) {
      console.error('Failed to initialize socket:', error);
      handleError('Failed to initialize connection', error);
      handleReconnection();
    }
  }
  
  // Enhanced reconnection logic with exponential backoff
  function handleReconnection() {
    if (reconnectAttempts < maxReconnectAttempts) {
      reconnectAttempts++;
      const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
      
      console.log(`Attempting to reconnect (${reconnectAttempts}/${maxReconnectAttempts}) in ${delay}ms`);
      
      reconnectTimeout = setTimeout(() => {
        if (!connected) {
          try {
            // Clean up existing socket before creating new one
            if (socket) {
              socket.removeAllListeners();
              socket.disconnect();
            }
            initializeSocket();
          } catch (error) {
            console.error('Error during reconnection attempt:', error);
            handleError('Reconnection attempt failed', error);
          }
        }
      }, delay);
    } else {
      console.error('Max reconnection attempts reached');
      isOfflineMode = true;
      connectionError = 'Unable to connect to server after multiple attempts';
      addNotification('Connection failed - switched to offline mode', 'error');
    }
  }
  
  // Manual retry connection
  function retryConnection() {
    reconnectAttempts = 0;
    connectionError = null;
    isOfflineMode = false;
    clearTimeout(reconnectTimeout);
    initializeSocket();
  }
  
  // Heartbeat monitoring
  function startHeartbeat() {
    lastHeartbeat = Date.now();
    heartbeatInterval = setInterval(() => {
      if (connected && socket) {
        socket.emit('ping', Date.now());
      }
    }, 30000); // Send ping every 30 seconds
    
    if (socket) {
      socket.on('pong', (timestamp) => {
        lastHeartbeat = Date.now();
      });
    }
  }
  
  function stopHeartbeat() {
    if (heartbeatInterval) {
      clearInterval(heartbeatInterval);
      heartbeatInterval = null;
    }
  }
  
  // Error handling functions
  function handleError(message, error = null) {
    console.error(message, error);
    
    const errorDetails = {
      message,
      error: error ? error.toString() : null,
      timestamp: new Date().toISOString(),
      stack: error ? error.stack : null
    };
    
    systemError = errorDetails;
    addNotification(message, 'error');
  }
  
  function handleWorkflowError(data) {
    const { ticket_id, error, message } = data;
    
    // Find and update the workflow with error state
    const workflowIndex = workflows.findIndex(w => w.id === ticket_id);
    if (workflowIndex !== -1) {
      workflows[workflowIndex].status = 'failed';
      workflows[workflowIndex].error = error;
      workflows[workflowIndex].error_message = message;
      workflows = [...workflows];
    }
    
    addNotification(`Workflow ${ticket_id} failed: ${message}`, 'error');
  }
  
  function handleSystemError(data) {
    const { error, message, component } = data;
    
    systemError = {
      message: message || 'System error occurred',
      error,
      component,
      timestamp: new Date().toISOString()
    };
    
    addNotification(`System error in ${component}: ${message}`, 'error');
  }
  
  function clearError(type) {
    if (type === 'connection') {
      connectionError = null;
    } else if (type === 'system') {
      systemError = null;
    }
  }
  
  // Notification system
  function addNotification(message, type = 'info', duration = 5000) {
    const notification = {
      id: Date.now() + Math.random(),
      message,
      type,
      timestamp: new Date().toISOString()
    };
    
    errorNotifications = [...errorNotifications, notification];
    
    // Auto-remove notification after duration
    if (duration > 0) {
      setTimeout(() => {
        removeNotification(notification.id);
      }, duration);
    }
  }
  
  function removeNotification(id) {
    errorNotifications = errorNotifications.filter(n => n.id !== id);
  }
  
  // Queued actions for offline mode
  function queueAction(action) {
    queuedActions = [...queuedActions, {
      ...action,
      timestamp: new Date().toISOString()
    }];
  }
  
  function processQueuedActions() {
    if (queuedActions.length === 0) return;
    
    console.log(`Processing ${queuedActions.length} queued actions`);
    
    queuedActions.forEach(action => {
      try {
        if (action.type === 'create_ticket') {
          socket.emit('create_ticket', action.data);
        }
      } catch (error) {
        console.error('Error processing queued action:', error);
        handleError('Failed to process queued action', error);
      }
    });
    
    queuedActions = [];
    addNotification('Processed queued actions', 'success');
  }
  
  // Handle workflow updates from server with error handling
  function handleWorkflowUpdate(data) {
    try {
      const { ticket_id, status, ...updateData } = data;
      
      if (!ticket_id) {
        throw new Error('Workflow update missing ticket_id');
      }
      
      const workflowIndex = workflows.findIndex(w => w.id === ticket_id);
      if (workflowIndex !== -1) {
        // Update existing workflow with validation
        const existingWorkflow = workflows[workflowIndex];
        const updatedWorkflow = {
          ...existingWorkflow,
          status: status || existingWorkflow.status,
          last_updated: new Date().toISOString(),
          ...updateData
        };
        
        // Validate status transition
        if (status && !isValidStatusTransition(existingWorkflow.status, status)) {
          console.warn(`Invalid status transition: ${existingWorkflow.status} -> ${status}`);
        }
        
        workflows[workflowIndex] = updatedWorkflow;
        workflows = [...workflows];
      } else {
        // Create new workflow if it doesn't exist
        const newWorkflow = {
          id: ticket_id,
          status: status || 'received',
          created_at: updateData.created_at || new Date().toISOString(),
          last_updated: new Date().toISOString(),
          logs: [],
          error_count: 0,
          ...updateData
        };
        workflows = [...workflows, newWorkflow];
      }
    } catch (error) {
      console.error('Error handling workflow update:', error);
      handleError('Failed to update workflow', error);
    }
  }
  
  // Validate status transitions
  function isValidStatusTransition(currentStatus, newStatus) {
    const validTransitions = {
      'received': ['processing', 'failed'],
      'processing': ['classified', 'failed', 'escalated'],
      'classified': ['delegating', 'failed', 'escalated'],
      'delegating': ['working', 'failed', 'escalated'],
      'working': ['resolved', 'failed', 'escalated'],
      'resolved': [], // Terminal state
      'failed': ['processing'], // Can retry
      'escalated': ['processing'] // Can retry
    };
    
    return validTransitions[currentStatus]?.includes(newStatus) || false;
  }
  
  // Handle log updates from server with error handling
  function handleLogUpdate(data) {
    try {
      const { ticket_id, message, agent, timestamp, status } = data;
      
      if (!ticket_id || !message) {
        throw new Error('Log update missing required fields');
      }
      
      const workflowIndex = workflows.findIndex(w => w.id === ticket_id);
      if (workflowIndex !== -1) {
        const newLog = {
          id: Date.now() + Math.random(), // Unique log ID
          agent: agent || 'System',
          message: message.toString(), // Ensure message is string
          timestamp: timestamp || new Date().toISOString(),
          status,
          type: data.type || 'info'
        };
        
        // Prevent duplicate logs
        const existingLogs = workflows[workflowIndex].logs || [];
        const isDuplicate = existingLogs.some(log => 
          log.message === newLog.message && 
          log.agent === newLog.agent &&
          Math.abs(new Date(log.timestamp) - new Date(newLog.timestamp)) < 1000
        );
        
        if (!isDuplicate) {
          workflows[workflowIndex].logs = [...existingLogs, newLog];
          
          // Update status if provided and valid
          if (status && isValidStatusTransition(workflows[workflowIndex].status, status)) {
            workflows[workflowIndex].status = status;
          }
          
          workflows[workflowIndex].last_updated = new Date().toISOString();
          workflows = [...workflows];
        }
      } else {
        console.warn(`Received log update for unknown workflow: ${ticket_id}`);
      }
    } catch (error) {
      console.error('Error handling log update:', error);
      handleError('Failed to update workflow log', error);
    }
  }
  
  // Handle ticket creation from TicketForm with comprehensive error handling
  function handleCreateTicket(event) {
    try {
      const { subject } = event.detail;
      
      if (!subject || !subject.trim()) {
        throw new Error('Ticket subject is required');
      }
      
      console.log('Creating ticket:', subject);
      
      if (connected && socket) {
        // Send ticket creation request via WebSocket
        try {
          socket.emit('create_ticket', { 
            subject: subject.trim(),
            timestamp: new Date().toISOString()
          });
          
          addNotification('Ticket creation request sent', 'success', 3000);
        } catch (error) {
          console.error('Error sending ticket creation request:', error);
          handleOfflineTicketCreation(subject);
        }
      } else {
        // Handle offline mode
        handleOfflineTicketCreation(subject);
      }
    } catch (error) {
      console.error('Error creating ticket:', error);
      handleError('Failed to create ticket', error);
    }
  }
  
  // Handle ticket creation in offline mode
  function handleOfflineTicketCreation(subject) {
    console.warn('Not connected to server, handling offline');
    
    if (isOfflineMode) {
      // Queue the action for when connection is restored
      queueAction({
        type: 'create_ticket',
        data: { subject: subject.trim() }
      });
      
      addNotification('Ticket queued - will be created when connection is restored', 'warning');
    }
    
    // Create local workflow for immediate feedback
    const localWorkflow = {
      id: `LOCAL-${Math.random().toString(36).substr(2, 8).toUpperCase()}`,
      subject: subject.trim(),
      status: 'received',
      created_at: new Date().toISOString(),
      last_updated: new Date().toISOString(),
      is_local: true,
      error_count: 0,
      logs: [
        {
          id: Date.now(),
          agent: 'System',
          message: isOfflineMode ? 
            'Ticket created locally - will sync when connection is restored' :
            'Ticket created locally (connection unavailable)',
          timestamp: new Date().toISOString(),
          status: 'received',
          type: 'info'
        }
      ]
    };
    
    workflows = [...workflows, localWorkflow];
  }
  
  onMount(() => {
    console.log('NexusAI Dashboard initialized');
    
    // Initialize error handling
    window.addEventListener('error', (event) => {
      console.error('Global error:', event.error);
      handleError('Application error occurred', event.error);
    });
    
    window.addEventListener('unhandledrejection', (event) => {
      console.error('Unhandled promise rejection:', event.reason);
      handleError('Unhandled promise rejection', event.reason);
    });
    
    // Initialize connection
    initializeSocket();
    
    // Cleanup on component destroy
    return () => {
      try {
        if (socket) {
          socket.removeAllListeners();
          socket.disconnect();
        }
        clearTimeout(reconnectTimeout);
        stopHeartbeat();
        
        // Clear error notifications
        errorNotifications = [];
      } catch (error) {
        console.error('Error during cleanup:', error);
      }
    };
  });
</script>

<main class="min-h-screen p-6">
  <!-- Error Notifications -->
  {#if errorNotifications.length > 0}
    <div class="fixed top-4 right-4 z-50 space-y-2">
      {#each errorNotifications as notification (notification.id)}
        <div class="glass rounded-lg p-4 max-w-sm border-l-4 
                    {notification.type === 'error' ? 'border-red-400 bg-red-900/20' : 
                     notification.type === 'warning' ? 'border-yellow-400 bg-yellow-900/20' :
                     notification.type === 'success' ? 'border-green-400 bg-green-900/20' :
                     'border-blue-400 bg-blue-900/20'}
                    animate-slide-in">
          <div class="flex items-start justify-between">
            <div class="flex items-start space-x-2">
              <div class="flex-shrink-0 mt-0.5">
                {#if notification.type === 'error'}
                  <svg class="w-4 h-4 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
                  </svg>
                {:else if notification.type === 'warning'}
                  <svg class="w-4 h-4 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                  </svg>
                {:else if notification.type === 'success'}
                  <svg class="w-4 h-4 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                  </svg>
                {:else}
                  <svg class="w-4 h-4 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
                  </svg>
                {/if}
              </div>
              <div class="flex-1">
                <p class="text-sm text-white font-medium">{notification.message}</p>
                <p class="text-xs text-gray-400 mt-1">
                  {new Date(notification.timestamp).toLocaleTimeString()}
                </p>
              </div>
            </div>
            <button
              on:click={() => removeNotification(notification.id)}
              class="flex-shrink-0 ml-2 text-gray-400 hover:text-white transition-colors"
            >
              <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
              </svg>
            </button>
          </div>
        </div>
      {/each}
    </div>
  {/if}

  <div class="max-w-7xl mx-auto">
    <!-- Header -->
    <header class="mb-8">
      <div class="glass rounded-2xl p-6">
        <h1 class="text-4xl font-bold text-white mb-2">
          NexusAI
          <span class="text-blue-400">Operations</span>
        </h1>
        <p class="text-gray-300">
          Autonomous IT Operations Platform
        </p>
        <div class="flex items-center justify-between mt-4">
          <div class="flex items-center space-x-4">
            <!-- Connection Status -->
            <div class="flex items-center space-x-2">
              <div class="w-3 h-3 rounded-full mr-2 
                          {connected ? 'bg-green-400 animate-pulse' : 
                           isOfflineMode ? 'bg-gray-400' : 'bg-red-400'}"></div>
              <span class="text-sm text-gray-300">
                {connected ? 'Connected' : isOfflineMode ? 'Offline Mode' : 'Disconnected'}
              </span>
            </div>
            
            <!-- Reconnection Status -->
            {#if !connected && reconnectAttempts > 0 && !isOfflineMode}
              <div class="flex items-center space-x-2 text-yellow-400 text-sm">
                <svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>Reconnecting... ({reconnectAttempts}/{maxReconnectAttempts})</span>
              </div>
            {/if}
            
            <!-- Queued Actions Indicator -->
            {#if queuedActions.length > 0}
              <div class="flex items-center space-x-2 text-orange-400 text-sm">
                <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M3 4a1 1 0 011-1h12a1 1 0 011 1v2a1 1 0 01-1 1H4a1 1 0 01-1-1V4zM3 10a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H4a1 1 0 01-1-1v-6zM14 9a1 1 0 00-1 1v6a1 1 0 001 1h2a1 1 0 001-1v-6a1 1 0 00-1-1h-2z" />
                </svg>
                <span>{queuedActions.length} queued</span>
              </div>
            {/if}
          </div>
          
          <!-- Action Buttons -->
          <div class="flex items-center space-x-2">
            {#if connectionError || systemError}
              <button
                on:click={() => showErrorDetails = !showErrorDetails}
                class="px-3 py-1 bg-red-500/20 border border-red-400/30 text-red-400 text-sm rounded-lg
                       hover:bg-red-500/30 transition-colors duration-200"
              >
                {showErrorDetails ? 'Hide' : 'Show'} Error Details
              </button>
            {/if}
            
            {#if !connected && (reconnectAttempts >= maxReconnectAttempts || isOfflineMode)}
              <button
                on:click={retryConnection}
                class="px-3 py-1 bg-blue-500 hover:bg-blue-600 text-white text-sm rounded-lg
                       transition-colors duration-200"
              >
                Retry Connection
              </button>
            {/if}
          </div>
        </div>
        
        <!-- Error Details Panel -->
        {#if showErrorDetails && (connectionError || systemError)}
          <div class="mt-4 p-4 bg-red-900/20 border border-red-400/30 rounded-lg">
            <h3 class="text-red-400 font-medium mb-2">Error Details</h3>
            {#if connectionError}
              <div class="mb-2">
                <p class="text-sm text-red-300">Connection Error:</p>
                <p class="text-xs text-gray-300 font-mono">{connectionError}</p>
              </div>
            {/if}
            {#if systemError}
              <div class="mb-2">
                <p class="text-sm text-red-300">System Error:</p>
                <p class="text-xs text-gray-300 font-mono">{systemError.message}</p>
                {#if systemError.error}
                  <p class="text-xs text-gray-400 font-mono mt-1">{systemError.error}</p>
                {/if}
              </div>
            {/if}
            <div class="flex items-center space-x-2 mt-3">
              <button
                on:click={() => clearError('connection')}
                class="px-2 py-1 bg-gray-600 hover:bg-gray-500 text-white text-xs rounded"
              >
                Clear Connection Error
              </button>
              <button
                on:click={() => clearError('system')}
                class="px-2 py-1 bg-gray-600 hover:bg-gray-500 text-white text-xs rounded"
              >
                Clear System Error
              </button>
            </div>
          </div>
        {/if}
      </div>
    </header>

    <!-- Main Content Grid -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- Ticket Creation Panel -->
      <div class="lg:col-span-1">
        <div class="glass rounded-2xl p-6">
          <h2 class="text-xl font-semibold text-white mb-4">
            Create Ticket
          </h2>
          <TicketForm on:createTicket={handleCreateTicket} />
        </div>
      </div>

      <!-- Workflow Visualization Panel -->
      <div class="lg:col-span-2">
        <div class="glass rounded-2xl p-6">
          <h2 class="text-xl font-semibold text-white mb-4">
            Active Workflows
          </h2>
          {#if workflows.length === 0}
            <div class="text-gray-400 text-center py-12">
              <div class="text-6xl mb-4">🤖</div>
              <p class="text-lg">No active workflows</p>
              <p class="text-sm">Create a ticket to see autonomous agents in action</p>
            </div>
          {:else}
            <div class="space-y-4">
              {#each workflows as workflow (workflow.id)}
                <WorkflowCard {workflow} />
              {/each}
            </div>
          {/if}
        </div>
      </div>
    </div>
  </div>
</main>

<style>
  /* Notification animations */
  @keyframes slide-in {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
  
  .animate-slide-in {
    animation: slide-in 0.3s ease-out;
  }
  
  /* Error state styles */
  .error-border {
    border-color: #ef4444;
    box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
  }
  
  /* Offline mode styles */
  .offline-indicator {
    background: linear-gradient(45deg, #374151, #4b5563);
    animation: pulse 2s infinite;
  }
  
  /* Connection status animations */
  .connection-pulse {
    animation: connection-pulse 2s infinite;
  }
  
  @keyframes connection-pulse {
    0%, 100% {
      opacity: 1;
    }
    50% {
      opacity: 0.5;
    }
  }
  
  /* Smooth transitions for all interactive elements */
  button, input, .glass {
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  }
  
  /* Enhanced glass effect for error states */
  .glass-error {
    background: rgba(239, 68, 68, 0.1);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(239, 68, 68, 0.2);
  }
  
  .glass-warning {
    background: rgba(245, 158, 11, 0.1);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(245, 158, 11, 0.2);
  }
  
  .glass-success {
    background: rgba(34, 197, 94, 0.1);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(34, 197, 94, 0.2);
  }
</style>