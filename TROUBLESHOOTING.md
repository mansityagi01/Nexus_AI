# NexusAI Troubleshooting Guide

## Common Issues and Solutions

### Installation Issues

#### Issue: Python Virtual Environment Creation Fails
**Symptoms**: `python -m venv venv` command fails
**Solutions**:
```bash
# Try with python3 explicitly
python3 -m venv venv

# Or use virtualenv if available
pip install virtualenv
virtualenv venv

# On Windows, ensure Python is in PATH
where python
```

#### Issue: Node.js Dependencies Installation Fails
**Symptoms**: `npm install` fails with permission or network errors
**Solutions**:
```bash
# Clear npm cache
npm cache clean --force

# Use yarn as alternative
npm install -g yarn
yarn install

# On Windows, run as administrator
# On macOS/Linux, check node permissions
sudo chown -R $(whoami) ~/.npm
```

#### Issue: Requirements.txt Installation Fails
**Symptoms**: pip install fails with dependency conflicts
**Solutions**:
```bash
# Upgrade pip first
pip install --upgrade pip

# Install with no-cache
pip install --no-cache-dir -r requirements.txt

# Install individually if conflicts persist
pip install flask flask-socketio google-generativeai mcp
```

### Configuration Issues

#### Issue: Missing Environment Variables
**Symptoms**: Application fails to start with "Environment variable not found"
**Solutions**:
1. Verify `.env` file exists in root directory
2. Check `.env` file contains all required variables:
   ```
   GEMINI_API_KEY=your_key_here
   MCP_SERVER_HOST=localhost
   MCP_SERVER_PORT=8001
   FLASK_HOST=localhost
   FLASK_PORT=5000
   ```
3. Ensure no spaces around `=` in `.env` file
4. Restart application after changes

#### Issue: Invalid Gemini API Key
**Symptoms**: "API key invalid" or authentication errors
**Solutions**:
1. Verify API key is correct (no extra spaces/characters)
2. Check API key has proper permissions
3. Verify billing is enabled for Gemini API
4. Test API key with simple curl request:
   ```bash
   curl -H "Authorization: Bearer YOUR_API_KEY" \
        https://generativelanguage.googleapis.com/v1/models
   ```

### Runtime Issues

#### Issue: MCP Server Won't Start
**Symptoms**: "Failed to start MCP server" or port binding errors
**Solutions**:
```bash
# Check if port is already in use
netstat -an | grep 8001  # Windows
lsof -i :8001           # macOS/Linux

# Kill process using port
# Windows:
netstat -ano | findstr :8001
taskkill /PID <process_id> /F

# macOS/Linux:
kill -9 $(lsof -t -i:8001)

# Try different port in .env
MCP_SERVER_PORT=8002
```

#### Issue: Flask Server Connection Refused
**Symptoms**: Browser can't connect to localhost:5000
**Solutions**:
1. Check Flask server started successfully
2. Verify firewall isn't blocking port 5000
3. Try different port in `.env`:
   ```
   FLASK_PORT=5001
   ```
4. Check if another service is using port 5000
5. Try accessing via 127.0.0.1 instead of localhost

#### Issue: WebSocket Connection Fails
**Symptoms**: Dashboard loads but no real-time updates
**Solutions**:
1. Check browser console for WebSocket errors
2. Verify Flask-SocketIO is properly configured
3. Test with different browser
4. Check network/proxy settings
5. Ensure CORS is properly configured

### Agent and Workflow Issues

#### Issue: Master Agent Classification Fails
**Symptoms**: All tickets classified as "General Inquiry"
**Solutions**:
1. Check Gemini API key is working
2. Verify internet connection
3. Check API rate limits
4. Review agent prompt in `backend/agents/master_agent.py`
5. Check logs for specific error messages

#### Issue: PhishGuard Agent Doesn't Execute
**Symptoms**: Tickets classified correctly but no remediation actions
**Solutions**:
1. Verify MCP server is running and accessible
2. Check MCP client connection in logs
3. Ensure security tools are properly registered
4. Review PhishGuard agent configuration
5. Check for tool execution errors in logs

#### Issue: Real-time Updates Not Working
**Symptoms**: Workflow starts but UI doesn't update
**Solutions**:
1. Check WebSocket connection in browser dev tools
2. Verify SocketIO events are being emitted
3. Check for JavaScript errors in browser console
4. Restart both frontend and backend services
5. Clear browser cache and reload

### Performance Issues

#### Issue: Slow Agent Response Times
**Symptoms**: Long delays between workflow steps
**Solutions**:
1. Check internet connection speed
2. Verify Gemini API response times
3. Reduce agent prompt complexity
4. Enable demo mode for faster responses:
   ```
   DEMO_MODE=true
   ```
5. Monitor system resource usage

#### Issue: High Memory Usage
**Symptoms**: System becomes slow or unresponsive
**Solutions**:
1. Monitor memory usage with task manager
2. Restart application periodically
3. Reduce concurrent ticket processing
4. Check for memory leaks in logs
5. Increase system RAM if possible

### Frontend Issues

#### Issue: Svelte Build Fails
**Symptoms**: `npm run build` fails with compilation errors
**Solutions**:
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check Node.js version compatibility
node --version  # Should be 16+

# Try building with verbose output
npm run build -- --verbose
```

#### Issue: CSS Styles Not Loading
**Symptoms**: Dashboard appears unstyled or broken
**Solutions**:
1. Verify Tailwind CSS is properly configured
2. Check if build process completed successfully
3. Clear browser cache
4. Inspect network tab for failed CSS requests
5. Rebuild frontend: `npm run build`

## Diagnostic Commands

### System Health Check
```bash
# Run comprehensive health check
python scripts/health_check.py

# Check individual components
python -c "import backend.agents.master_agent; print('Master Agent OK')"
python -c "import backend.tools.security_mcp_server; print('MCP Server OK')"
```

### Log Analysis
```bash
# Check application logs
tail -f logs/nexusai.log  # If logging to file

# Check system logs
# Windows: Event Viewer
# macOS: Console app
# Linux: journalctl or /var/log/
```

### Network Diagnostics
```bash
# Test local connectivity
curl http://localhost:5000/health
curl http://localhost:8001/health

# Test external API connectivity
curl -H "Authorization: Bearer $GEMINI_API_KEY" \
     https://generativelanguage.googleapis.com/v1/models
```

## Getting Help

### Debug Mode
Enable debug mode for more detailed logging:
```bash
# Set in .env file
LOG_LEVEL=DEBUG
FLASK_DEBUG=true
```

### Log Collection
When reporting issues, include:
1. Full error messages and stack traces
2. Environment configuration (without API keys)
3. System specifications (OS, Python version, Node.js version)
4. Steps to reproduce the issue
5. Expected vs actual behavior

### Support Resources
1. Check GitHub issues for similar problems
2. Review documentation for configuration options
3. Test with minimal configuration first
4. Use demo mode to isolate API-related issues

## Prevention Tips

### Regular Maintenance
1. Keep dependencies updated
2. Monitor API usage and limits
3. Regular system health checks
4. Backup configuration files
5. Document any customizations

### Best Practices
1. Use virtual environments for Python
2. Pin dependency versions in production
3. Monitor system resources during demos
4. Test setup on clean environment before important demos
5. Have backup demo scenarios ready