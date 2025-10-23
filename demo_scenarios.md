# NexusAI Demonstration Scenarios

## Sample Phishing Ticket Subjects

### High-Impact Phishing Scenarios
These ticket subjects will trigger the PhishGuard Agent and demonstrate the complete autonomous remediation workflow:

1. **"Urgent: Suspicious email from CEO requesting wire transfer"**
   - Demonstrates: Executive impersonation detection
   - Expected workflow: Analyze → Block sender → Search/destroy emails → Document

2. **"Multiple users reporting fake Microsoft login page"**
   - Demonstrates: Credential harvesting attack response
   - Expected workflow: URL analysis → Network blocking → Email cleanup → User notification

3. **"Malicious attachment in payroll department emails"**
   - Demonstrates: Malware distribution response
   - Expected workflow: IOC extraction → Email quarantine → System scanning → Incident report

4. **"Phishing campaign targeting customer data"**
   - Demonstrates: Data theft attempt response
   - Expected workflow: Threat analysis → Containment → Evidence collection → Compliance reporting

5. **"Fake invoice emails with suspicious links detected"**
   - Demonstrates: Business email compromise (BEC) response
   - Expected workflow: Link analysis → Domain blocking → Email removal → User awareness

### General Inquiry Scenarios
These will be handled by the Master Agent and demonstrate proper ticket classification:

1. **"Password reset request for user account"**
   - Expected: Classified as General Inquiry, escalated for manual handling

2. **"Printer not working in conference room"**
   - Expected: Classified as General Inquiry, routed to IT support

3. **"Software installation request for new employee"**
   - Expected: Classified as General Inquiry, standard IT workflow

## Demonstration Flow Recommendations

### Quick Demo (5 minutes)
1. Start with "Urgent: Suspicious email from CEO requesting wire transfer"
2. Show real-time workflow visualization
3. Highlight autonomous tool execution
4. Display final resolution summary

### Comprehensive Demo (10-15 minutes)
1. Create 2-3 tickets simultaneously to show concurrent processing
2. Mix phishing and general inquiry tickets to show classification
3. Demonstrate error handling with invalid input
4. Show system recovery and continued operation

### Technical Deep-Dive (20+ minutes)
1. Walk through complete phishing remediation workflow
2. Explain each agent's decision-making process
3. Show MCP tool integration and responses
4. Demonstrate real-time logging and transparency
5. Discuss scalability and production considerations