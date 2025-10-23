<script>
  import { createEventDispatcher } from 'svelte';
  
  const dispatch = createEventDispatcher();
  
  let subject = '';
  let isSubmitting = false;
  let validationError = '';
  let submitError = '';
  let submitSuccess = false;
  let lastSubmitTime = 0;
  let submitAttempts = 0;
  let maxSubmitAttempts = 3;
  
  // Enhanced form validation
  function validateForm() {
    // Clear previous errors
    validationError = '';
    
    if (!subject || typeof subject !== 'string') {
      validationError = 'Subject is required';
      return false;
    }
    
    const trimmedSubject = subject.trim();
    
    if (!trimmedSubject) {
      validationError = 'Subject cannot be empty';
      return false;
    }
    
    if (trimmedSubject.length < 3) {
      validationError = 'Subject must be at least 3 characters';
      return false;
    }
    
    if (trimmedSubject.length > 200) {
      validationError = 'Subject must be less than 200 characters';
      return false;
    }
    
    // Check for potentially harmful content
    const suspiciousPatterns = [
      /<script/i,
      /javascript:/i,
      /on\w+\s*=/i
    ];
    
    if (suspiciousPatterns.some(pattern => pattern.test(trimmedSubject))) {
      validationError = 'Subject contains invalid characters';
      return false;
    }
    
    return true;
  }
  
  // Rate limiting check
  function checkRateLimit() {
    const now = Date.now();
    const timeSinceLastSubmit = now - lastSubmitTime;
    
    // Prevent rapid submissions (less than 2 seconds apart)
    if (timeSinceLastSubmit < 2000) {
      submitError = 'Please wait before submitting another ticket';
      return false;
    }
    
    // Check attempt count in the last minute
    if (submitAttempts >= maxSubmitAttempts && timeSinceLastSubmit < 60000) {
      submitError = 'Too many attempts. Please wait a minute before trying again';
      return false;
    }
    
    return true;
  }
  
  // Enhanced form submission with comprehensive error handling
  async function handleSubmit() {
    // Clear previous errors
    submitError = '';
    submitSuccess = false;
    
    // Validate form
    if (!validateForm()) {
      return;
    }
    
    // Check rate limiting
    if (!checkRateLimit()) {
      return;
    }
    
    isSubmitting = true;
    
    try {
      // Update submission tracking
      lastSubmitTime = Date.now();
      submitAttempts++;
      
      // Dispatch event to parent component
      dispatch('createTicket', {
        subject: subject.trim(),
        timestamp: new Date().toISOString(),
        clientId: generateClientId()
      });
      
      // Show success state
      submitSuccess = true;
      
      // Clear form after successful submission
      setTimeout(() => {
        subject = '';
        validationError = '';
        submitSuccess = false;
        submitAttempts = 0; // Reset attempts on success
      }, 1500);
      
    } catch (error) {
      console.error('Error submitting ticket:', error);
      
      // Handle different types of errors
      if (error.name === 'NetworkError' || error.message.includes('network')) {
        submitError = 'Network error. Your ticket will be queued and sent when connection is restored.';
      } else if (error.message.includes('rate limit')) {
        submitError = 'Too many requests. Please wait before submitting another ticket.';
      } else if (error.message.includes('validation')) {
        submitError = 'Invalid ticket data. Please check your input and try again.';
      } else {
        submitError = 'Failed to create ticket. Please try again.';
      }
      
      // Auto-clear error after 5 seconds
      setTimeout(() => {
        submitError = '';
      }, 5000);
      
    } finally {
      isSubmitting = false;
    }
  }
  
  // Generate unique client ID for tracking
  function generateClientId() {
    return `client_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
  
  // Handle input changes for real-time validation
  function handleInput() {
    // Clear errors on input
    if (validationError) {
      validateForm();
    }
    if (submitError) {
      submitError = '';
    }
    if (submitSuccess) {
      submitSuccess = false;
    }
  }
  
  // Handle Enter key submission
  function handleKeydown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSubmit();
    }
  }
</script>

<form on:submit|preventDefault={handleSubmit} class="space-y-4">
  <!-- Subject Input -->
  <div class="space-y-2">
    <label for="subject" class="block text-sm font-medium text-gray-300">
      Ticket Subject
    </label>
    <div class="relative">
      <input
        id="subject"
        type="text"
        bind:value={subject}
        on:input={handleInput}
        on:keydown={handleKeydown}
        placeholder="Describe your IT issue or request..."
        disabled={isSubmitting}
        class="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-xl 
               text-white placeholder-gray-400 backdrop-blur-sm
               focus:outline-none focus:ring-2 focus:ring-blue-400/50 focus:border-blue-400/50
               disabled:opacity-50 disabled:cursor-not-allowed
               transition-all duration-200"
        maxlength="200"
      />
      <!-- Character counter -->
      <div class="absolute right-3 top-3 text-xs text-gray-500">
        {subject.length}/200
      </div>
    </div>
    
    <!-- Error and success messages -->
    {#if validationError}
      <div class="flex items-center space-x-2 text-red-400 text-sm animate-fade-in">
        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
        </svg>
        <span>{validationError}</span>
      </div>
    {/if}
    
    {#if submitError}
      <div class="flex items-center space-x-2 text-orange-400 text-sm animate-fade-in">
        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
        </svg>
        <span>{submitError}</span>
      </div>
    {/if}
    
    {#if submitSuccess}
      <div class="flex items-center space-x-2 text-green-400 text-sm animate-fade-in">
        <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
        </svg>
        <span>Ticket created successfully!</span>
      </div>
    {/if}
  </div>
  
  <!-- Submit Button -->
  <button
    type="submit"
    disabled={isSubmitting || !subject.trim() || validationError || submitError}
    class="w-full px-6 py-3 font-medium rounded-xl
           focus:outline-none focus:ring-2 focus:ring-blue-400/50
           disabled:opacity-50 disabled:cursor-not-allowed
           transform transition-all duration-200
           hover:scale-[1.02] active:scale-[0.98]
           shadow-lg hover:shadow-xl
           {submitSuccess ? 'bg-gradient-to-r from-green-500 to-green-600 text-white' :
            submitError ? 'bg-gradient-to-r from-red-500 to-red-600 text-white' :
            'bg-gradient-to-r from-blue-500 to-purple-600 text-white hover:from-blue-600 hover:to-purple-700'}"
  >
    {#if isSubmitting}
      <div class="flex items-center justify-center space-x-2">
        <svg class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span>Creating Ticket...</span>
      </div>
    {:else if submitSuccess}
      <div class="flex items-center justify-center space-x-2">
        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
        </svg>
        <span>Ticket Created!</span>
      </div>
    {:else if submitError}
      <div class="flex items-center justify-center space-x-2">
        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
        </svg>
        <span>Try Again</span>
      </div>
    {:else}
      <div class="flex items-center justify-center space-x-2">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
        </svg>
        <span>Create Ticket</span>
      </div>
    {/if}
  </button>
  
  <!-- Help text -->
  <div class="text-xs text-gray-400 text-center">
    <p>Describe your IT issue clearly. Our AI agents will automatically triage and handle your request.</p>
  </div>
</form>

<style>
  /* Custom focus styles for better accessibility */
  input:focus {
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }
  
  /* Error state styles */
  input.error {
    border-color: #ef4444;
    box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1);
  }
  
  /* Success state styles */
  input.success {
    border-color: #10b981;
    box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
  }
  
  /* Fade-in animation for messages */
  @keyframes fade-in {
    from {
      opacity: 0;
      transform: translateY(-10px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }
  
  .animate-fade-in {
    animation: fade-in 0.3s ease-out;
  }
  
  /* Button state transitions */
  button {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  }
  
  button:disabled {
    transform: none !important;
  }
  
  /* Smooth transitions for all interactive elements */
  input {
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  }
  
  /* Loading state animation */
  .loading-pulse {
    animation: pulse 2s infinite;
  }
  
  @keyframes pulse {
    0%, 100% {
      opacity: 1;
    }
    50% {
      opacity: 0.5;
    }
  }
</style>