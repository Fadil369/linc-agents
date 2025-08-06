// BrainSAIT LINC Agents - Interactive Web Interface
console.log('🧠 BrainSAIT LINC Agents - Interactive Interface Loaded');

// Alpine.js App State
function app() {
    return {
        currentView: 'dashboard',
        selectedAgent: null,
        currentMessage: '',
        messages: [],
        isTyping: false,
        systemHealthy: false,
        totalRequests: 1247,
        avgResponseTime: 156,
        onlineAgents: [],
        
        // Agent Configuration
        agents: [
            // Healthcare Agents
            {
                id: 'doctor',
                name: 'Doctor LINC',
                description: 'Clinical decision support and medical consultation',
                port: 8010,
                category: 'healthcare',
                icon: '👨‍⚕️',
                status: 'online',
                specialties: ['Diagnosis', 'Treatment Plans', 'Medical Queries']
            },
            {
                id: 'nurse',
                name: 'Nurse LINC',
                description: 'Patient care coordination and medication management',
                port: 8011,
                category: 'healthcare',
                icon: '👩‍⚕️',
                status: 'online',
                specialties: ['Patient Care', 'Medication', 'Care Plans']
            },
            {
                id: 'patient',
                name: 'Patient LINC',
                description: 'Patient engagement and health education',
                port: 8012,
                category: 'healthcare',
                icon: '🏥',
                status: 'online',
                specialties: ['Health Education', 'Appointment Scheduling', 'Wellness Tips']
            },
            {
                id: 'careteam',
                name: 'CareTeam LINC',
                description: 'Multi-disciplinary care coordination',
                port: 8013,
                category: 'healthcare',
                icon: '👥',
                status: 'online',
                specialties: ['Team Coordination', 'Care Plans', 'Communication']
            },

            // Business Agents
            {
                id: 'business',
                name: 'Business LINC',
                description: 'Operational analytics and performance monitoring',
                port: 8020,
                category: 'business',
                icon: '📊',
                status: 'online',
                specialties: ['Analytics', 'Reports', 'Performance Metrics']
            },
            {
                id: 'payment',
                name: 'Payment LINC',
                description: 'Financial transactions and billing automation',
                port: 8021,
                category: 'business',
                icon: '💳',
                status: 'online',
                specialties: ['Billing', 'Payments', 'Financial Reports']
            },
            {
                id: 'insight',
                name: 'Insight LINC',
                description: 'Data analytics and business intelligence',
                port: 8022,
                category: 'business',
                icon: '🔍',
                status: 'online',
                specialties: ['Data Analysis', 'Insights', 'Predictions']
            },

            // Development & Automation Agents
            {
                id: 'dev',
                name: 'Dev LINC',
                description: 'Code generation and development workflow',
                port: 8030,
                category: 'development',
                icon: '💻',
                status: 'online',
                specialties: ['Code Generation', 'Development', 'Automation']
            },
            {
                id: 'auto',
                name: 'Auto LINC',
                description: 'Process automation and workflow orchestration',
                port: 8031,
                category: 'development',
                icon: '🤖',
                status: 'online',
                specialties: ['Automation', 'Workflows', 'Process Optimization']
            },
            {
                id: 'code',
                name: 'Code LINC',
                description: 'Code analysis and security scanning',
                port: 8032,
                category: 'development',
                icon: '🔧',
                status: 'online',
                specialties: ['Code Review', 'Security', 'Quality Assurance']
            },

            // Core Infrastructure
            {
                id: 'master',
                name: 'Master LINC',
                description: 'Central orchestration and routing hub',
                port: 8000,
                category: 'infrastructure',
                icon: '🎯',
                status: 'online',
                specialties: ['Orchestration', 'Routing', 'Coordination']
            },
            {
                id: 'auth',
                name: 'Auth LINC',
                description: 'Authentication and authorization service',
                port: 8001,
                category: 'infrastructure',
                icon: '🔐',
                status: 'online',
                specialties: ['Authentication', 'Authorization', 'Security']
            }
        ],

        init() {
            console.log('🚀 Initializing BrainSAIT LINC Interface...');
            this.checkSystemHealth();
            this.updateOnlineAgents();
            
            // Update system status every 30 seconds
            setInterval(() => {
                this.checkSystemHealth();
                this.updateOnlineAgents();
            }, 30000);
        },

        async checkSystemHealth() {
            try {
                // In a real implementation, this would check actual health endpoints
                // For demo purposes, we'll simulate the health check
                let healthyCount = 0;
                
                for (const agent of this.agents) {
                    try {
                        // Simulate health check - in production, uncomment the real check
                        // const response = await fetch(`http://localhost:${agent.port}/health`);
                        // agent.status = response.ok ? 'online' : 'offline';
                        
                        // For demo, randomly set some agents as online/offline
                        agent.status = Math.random() > 0.1 ? 'online' : 'offline';
                        if (agent.status === 'online') healthyCount++;
                    } catch (error) {
                        agent.status = 'offline';
                        console.warn(`❌ ${agent.name} health check failed:`, error.message);
                    }
                }
                
                this.systemHealthy = healthyCount > this.agents.length * 0.7;
                console.log(`💪 System Health: ${healthyCount}/${this.agents.length} agents online`);
                
            } catch (error) {
                console.error('❌ System health check failed:', error);
                this.systemHealthy = false;
            }
        },

        updateOnlineAgents() {
            this.onlineAgents = this.agents.filter(agent => agent.status === 'online');
        },

        selectAgent(agent) {
            this.selectedAgent = agent;
            this.currentView = 'chat';
            this.messages = [
                {
                    id: Date.now(),
                    sender: 'agent',
                    text: `Hello! I'm ${agent.name}. I can help you with ${agent.specialties.join(', ')}. How can I assist you today?`,
                    timestamp: new Date().toLocaleTimeString()
                }
            ];
            console.log(`🤖 Selected agent: ${agent.name}`);
        },

        async sendMessage() {
            if (!this.currentMessage.trim() || !this.selectedAgent || this.isTyping) return;

            const userMessage = {
                id: Date.now(),
                sender: 'user',
                text: this.currentMessage,
                timestamp: new Date().toLocaleTimeString()
            };

            this.messages.push(userMessage);
            const messageText = this.currentMessage;
            this.currentMessage = '';
            this.isTyping = true;

            // Scroll to bottom
            this.$nextTick(() => {
                if (this.$refs.messagesContainer) {
                    this.$refs.messagesContainer.scrollTop = this.$refs.messagesContainer.scrollHeight;
                }
            });

            try {
                // Simulate agent response
                await this.getAgentResponse(messageText);
            } catch (error) {
                console.error('❌ Failed to get agent response:', error);
                this.messages.push({
                    id: Date.now() + 1,
                    sender: 'agent',
                    text: 'I apologize, but I\'m experiencing technical difficulties. Please try again later.',
                    timestamp: new Date().toLocaleTimeString()
                });
            } finally {
                this.isTyping = false;
                this.$nextTick(() => {
                    if (this.$refs.messagesContainer) {
                        this.$refs.messagesContainer.scrollTop = this.$refs.messagesContainer.scrollHeight;
                    }
                });
            }
        },

        async getAgentResponse(message) {
            // Simulate network delay
            await new Promise(resolve => setTimeout(resolve, 1000 + Math.random() * 2000));

            // Generate contextual responses based on agent type and message
            const responses = this.generateAgentResponse(message);
            
            const agentMessage = {
                id: Date.now() + 1,
                sender: 'agent',
                text: responses,
                timestamp: new Date().toLocaleTimeString()
            };

            this.messages.push(agentMessage);
            this.totalRequests++;
        },

        generateAgentResponse(message) {
            const agent = this.selectedAgent;
            const lowerMessage = message.toLowerCase();

            // Agent-specific responses
            if (agent.category === 'healthcare') {
                if (lowerMessage.includes('symptom') || lowerMessage.includes('pain') || lowerMessage.includes('sick')) {
                    return `As ${agent.name}, I understand you're experiencing health concerns. Please describe your symptoms in detail so I can provide appropriate guidance. Remember, for emergencies, please contact emergency services immediately.`;
                }
                if (lowerMessage.includes('medication') || lowerMessage.includes('drug') || lowerMessage.includes('prescription')) {
                    return `Regarding medications, I can help you understand dosages, interactions, and schedules. Always consult with your healthcare provider before making any changes to your medication regimen.`;
                }
                if (lowerMessage.includes('appointment') || lowerMessage.includes('schedule')) {
                    return `I can help you with appointment scheduling and preparation. What type of appointment would you like to schedule, and do you have any preferred dates or times?`;
                }
                return `Thank you for reaching out to ${agent.name}. I'm here to help with medical consultations, health guidance, and care coordination. How can I assist you with your healthcare needs today?`;
            }

            if (agent.category === 'business') {
                if (lowerMessage.includes('report') || lowerMessage.includes('analytics') || lowerMessage.includes('data')) {
                    return `I can generate detailed reports and analytics for you. What specific metrics or time period would you like me to analyze?`;
                }
                if (lowerMessage.includes('payment') || lowerMessage.includes('billing') || lowerMessage.includes('invoice')) {
                    return `I can help with billing inquiries, payment processing, and financial reports. What specific payment or billing information do you need?`;
                }
                return `As ${agent.name}, I'm here to help with business operations, analytics, and performance monitoring. What business insights can I provide for you today?`;
            }

            if (agent.category === 'development') {
                if (lowerMessage.includes('code') || lowerMessage.includes('bug') || lowerMessage.includes('error')) {
                    return `I can help with code analysis, debugging, and quality assurance. Please share the code or describe the issue you're experiencing.`;
                }
                if (lowerMessage.includes('automate') || lowerMessage.includes('workflow') || lowerMessage.includes('process')) {
                    return `I specialize in automation and workflow optimization. What process would you like me to help automate or improve?`;
                }
                return `As ${agent.name}, I'm ready to assist with development tasks, code analysis, and automation. What development challenge can I help you solve?`;
            }

            // Default response
            return `Thank you for your message! As ${agent.name}, I'm specialized in ${agent.specialties.join(', ')}. Could you please provide more details about how I can help you?`;
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('✅ BrainSAIT LINC Interface Ready');
});